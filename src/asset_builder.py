# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 10:27:04 2026

@author: c10265
"""

import math
import re

import numpy as np
import pandas as pd

from helpers import parse_inches

def mark_to_pothole_sample(
    df: pd.DataFrame,
    address_col: str = "Service Address",
    public_material_col: str = "Public Material",
    public_date_col: str = "Public Date of Material Confirmation",
    public_diameter_col: str = "Public Diameter",
    output_col: str = "To Pothole",
    random_state: int | None = 42,
    unknown_material_counts_as_unpopulated: bool = True,
    mark_value: str = "to pothole",
) -> pd.DataFrame:
    """
    Clean and sample a neighborhood DataFrame for potholing.

    Rules implemented:
    1. Duplicate service addresses are removed first, using normalized address text.
    2. Rows with anything populated in Public Date of Material Confirmation are excluded
       from the sampling pool.
    3. Sampling rate is:
       - 40% if more than half of Public Material entries are populated/known.
       - 60% if half or fewer are populated/known.
    4. For each unique street name:
       - If that street has 2 or fewer eligible entries, all are forced into the sample.
       - Remaining sample slots are allocated proportionally across larger streets.
    5. Within each street, the selection tries to keep even and odd house numbers
       roughly balanced.
    6. Returns the DataFrame with a new output column marking sampled rows as
       "to pothole"; non-selected rows are blank.

    Notes:
    - "Populated" Public Material defaults to not blank and not "Unknown".
      Set unknown_material_counts_as_unpopulated=False if you want "Unknown" to count
      as populated.
    - Public Date values of blank, NaN, or -1 are treated as not populated.
      Any other value, including Excel serial dates or text, excludes that row.
    """

    work = df.copy()

    # ------------------------------------------------------------------
    # Helper functions
    # ------------------------------------------------------------------

    def normalize_address(value):
        """Normalize address for duplicate detection."""
        if pd.isna(value):
            return np.nan
        text = str(value).upper().strip()
        text = re.sub(r"\s+", " ", text)
        text = text.replace(".", "")
        return text

    def extract_house_number(address):
        """Extract first numeric house number from a service address."""
        if pd.isna(address):
            return np.nan
        text = str(address).strip()
        match = re.match(r"^\s*(\d+)", text)
        if not match:
            return np.nan
        return int(match.group(1))

    def extract_street_name(address):
        """
        Extract street name by removing the leading service number.
        Example:
            '5229 E 34TH ST' -> 'E 34TH ST'
            '3002 N ARLINGTON AVE' -> 'N ARLINGTON AVE'
        """
        if pd.isna(address):
            return np.nan

        text = str(address).upper().strip()
        text = re.sub(r"\s+", " ", text)
        text = text.replace(".", "")

        # Remove leading house number
        text = re.sub(r"^\d+\s*", "", text).strip()

        # Remove common unit/apartment fragments after comma
        text = re.sub(r",\s*(UNIT|APT|APARTMENT|STE|SUITE|#).*$", "", text).strip()

        return text

    def public_material_is_populated(series):
        """Return boolean Series for populated/known Public Material."""
        s = series.astype("string").str.strip()

        populated = s.notna() & (s != "")

        if unknown_material_counts_as_unpopulated:
            populated &= ~s.str.upper().isin(
                ["UNKNOWN", "UNK", "N/A", "NA", "NONE", "-1"]
            )

        return populated

    def public_date_is_blank_or_sentinel(series):
        """
        A row is eligible only if Public Date is blank/NaN/-1.
        Any actual date, Excel serial number, or text excludes the row.
        """
        s = series.copy()

        blank = s.isna()

        as_text = s.astype("string").str.strip()
        text_blank = as_text.isna() | (as_text == "")
        sentinel = as_text.isin(["-1", "-1.0"])

        return blank | text_blank | sentinel

    def largest_remainder_allocation(weights, slots):
        """
        Allocate integer slots proportionally using largest remainder.
        weights: Series indexed by street, values are eligible counts.
        """
        if slots <= 0 or weights.sum() <= 0:
            return pd.Series(0, index=weights.index, dtype=int)

        raw = weights / weights.sum() * slots
        base = np.floor(raw).astype(int)
        remainder = raw - base

        remaining = slots - base.sum()

        if remaining > 0:
            add_to = remainder.sort_values(ascending=False).index[:remaining]
            base.loc[add_to] += 1

        return base.astype(int)

    def choose_even_odd_balanced(group, n, rng):
        """
        Choose n rows from one street group, trying to split between even/odd numbers.
        """
        if n <= 0:
            return []

        if n >= len(group):
            return list(group.index)

        even = group[group["_house_number"] % 2 == 0]
        odd = group[group["_house_number"] % 2 == 1]
        unknown = group[group["_house_number"].isna()]

        # Desired split
        desired_even = n // 2
        desired_odd = n - desired_even

        # Adjust for availability
        take_even = min(desired_even, len(even))
        take_odd = min(desired_odd, len(odd))

        leftover = n - take_even - take_odd

        # If one side is short, fill from the other side, then unknowns
        if leftover > 0:
            extra_even_available = len(even) - take_even
            add_even = min(leftover, extra_even_available)
            take_even += add_even
            leftover -= add_even

        if leftover > 0:
            extra_odd_available = len(odd) - take_odd
            add_odd = min(leftover, extra_odd_available)
            take_odd += add_odd
            leftover -= add_odd

        chosen = []

        if take_even > 0:
            chosen.extend(
                rng.choice(even.index.to_numpy(), size=take_even, replace=False)
            )

        if take_odd > 0:
            chosen.extend(
                rng.choice(odd.index.to_numpy(), size=take_odd, replace=False)
            )

        if leftover > 0 and len(unknown) > 0:
            take_unknown = min(leftover, len(unknown))
            chosen.extend(
                rng.choice(unknown.index.to_numpy(), size=take_unknown, replace=False)
            )
            leftover -= take_unknown

        # Safety fill if still short
        if len(chosen) < n:
            remaining_idx = group.index.difference(chosen)
            need = min(n - len(chosen), len(remaining_idx))
            if need > 0:
                chosen.extend(
                    rng.choice(remaining_idx.to_numpy(), size=need, replace=False)
                )

        return list(chosen)

    # ------------------------------------------------------------------
    # Validate required columns
    # ------------------------------------------------------------------

    required_cols = [address_col, public_material_col, public_date_col, public_diameter_col]
    missing = [col for col in required_cols if col not in work.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}")

    rng = np.random.default_rng(random_state)

    # ------------------------------------------------------------------
    # 1. Remove duplicate service addresses BEFORE anything else
    # ------------------------------------------------------------------

    work["_normalized_address"] = work[address_col].apply(normalize_address)
    work = work.drop_duplicates(subset="_normalized_address", keep="first").copy()

    # ------------------------------------------------------------------
    # 2. Create street name, house number, and parity helper columns
    # ------------------------------------------------------------------

    work["_street_name"] = work[address_col].apply(extract_street_name)
    work["_house_number"] = work[address_col].apply(extract_house_number)

    # ------------------------------------------------------------------
    # 3. Determine 40% vs 60% rate based on Public Material completeness
    # ------------------------------------------------------------------

    material_populated = public_material_is_populated(work[public_material_col])
    populated_ratio = material_populated.mean()

    sample_rate = 0.40 if populated_ratio > 0.50 else 0.60

    # ------------------------------------------------------------------
    # 4. Exclude rows with populated Public Date of Material Confirmation
    # ------------------------------------------------------------------

    
    public_date_eligible = public_date_is_blank_or_sentinel(work[public_date_col])

    parsed_public_diameter = work[public_diameter_col].apply(parse_inches)

    # Exclude only diameters that are successfully parsed and greater than 2.
    # Blank/unknown/unparseable diameters remain eligible unless your parse_inches
    # function returns a number greater than 2.
    public_diameter_eligible = parsed_public_diameter.isna() | (parsed_public_diameter <= 2)

    eligible_mask = public_date_eligible & public_diameter_eligible
    eligible = work[eligible_mask].copy()


    # If no eligible rows, return cleaned df with blank output column
    work[output_col] = ""
    if eligible.empty:
        return work.drop(
            columns=["_normalized_address", "_street_name", "_house_number"],
            errors="ignore",
        )

    # Target sample size from eligible rows
    target_n = math.ceil(len(eligible) * sample_rate)

    # ------------------------------------------------------------------
    # 5. Force streets with 2 or fewer eligible entries
    # ------------------------------------------------------------------

    street_counts = eligible["_street_name"].value_counts(dropna=False)

    small_streets = street_counts[street_counts <= 2].index
    forced = eligible[eligible["_street_name"].isin(small_streets)]

    selected_indices = set(forced.index)

    remaining_slots = target_n - len(selected_indices)

    # If forced rows exceed the target, keep all forced rows per rule
    if remaining_slots <= 0:
        work.loc[list(selected_indices), output_col] = mark_value
        return work.drop(
            columns=["_normalized_address", "_street_name", "_house_number"],
            errors="ignore",
        )

    # ------------------------------------------------------------------
    # 6. Allocate remaining slots proportionally across larger streets
    # ------------------------------------------------------------------

    remainder_pool = eligible[
        ~eligible.index.isin(selected_indices)
        & ~eligible["_street_name"].isin(small_streets)
    ].copy()

    if not remainder_pool.empty:
        large_street_counts = remainder_pool["_street_name"].value_counts(dropna=False)

        allocation = largest_remainder_allocation(
            weights=large_street_counts,
            slots=min(remaining_slots, len(remainder_pool)),
        )

        for street, n_for_street in allocation.items():
            street_group = remainder_pool[remainder_pool["_street_name"] == street]
            chosen = choose_even_odd_balanced(street_group, int(n_for_street), rng)
            selected_indices.update(chosen)

    # ------------------------------------------------------------------
    # 7. Safety fill if rounding/allocation left us short
    # ------------------------------------------------------------------

    if len(selected_indices) < target_n:
        remaining_candidates = eligible.index.difference(list(selected_indices))
        need = min(target_n - len(selected_indices), len(remaining_candidates))

        if need > 0:
            extra = rng.choice(
                remaining_candidates.to_numpy(), size=need, replace=False
            )
            selected_indices.update(extra)

    # ------------------------------------------------------------------
    # 8. Mark selected rows
    # ------------------------------------------------------------------

    work.loc[list(selected_indices), output_col] = mark_value
    work.sort_values(by=["_street_name", "_house_number"], inplace=True)

    # Remove helper columns before returning
    work = work.drop(
        columns=["_normalized_address", "_street_name", "_house_number"],
        errors="ignore",
    )

    return work.loc[work[output_col].eq(mark_value)].copy()
