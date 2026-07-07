# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 11:04:05 2026

@author: c10265
"""

import re


def parse_inches(value: str) -> float:
    """

    Convert a string like '6"', '2 1/2"', '3 1/4"' into a float (inches).

    Args:
        value (str): the raw string value of the inch length from the file.

    Raises:
        ValueError: if invalid value type is given as an argument.
        ValueError: if the format of the inch increment is not correct.
            (needs to be in whole numbers, fractions, and with an " marking).

    Returns:
        float: the length in inches
    """
    if isinstance(value, int):
        return float(value)
    elif isinstance(value, float):
        return value
    elif not isinstance(value, str):
        print(f"Type: {type(value)}")
        raise ValueError("Input must be a string")
    
    if len(value) == 0:
        return 0.0

    # Remove the double-quote and strip spaces
    s = value.replace('"', "").strip()

    # Match patterns like:
    # - '6'
    # - '2 1/2'
    pattern = r"^\s*(?:(\d+)\s+)?(\d+)?(?:/(\d+))?\s*$"
    match = re.match(pattern, s)

    if not match:
        raise ValueError(f"Invalid format: {value}")

    whole, num, den = match.groups()

    result = 0.0

    # Whole number part
    if whole:
        result += float(whole)
    elif not num and not den:
        # Case: just a whole number like '6'
        return float(s)

    # Fraction part
    if num and den:
        result += float(num) / float(den)

    return result


def has_text(s: object) -> bool:
    """

    Determines whether a value, presumably a string, has any text
    inside of it.

    Args:
        s (object): the value to check.

    Returns:
        bool: whether or not the value has text inside of it.
    """
    return isinstance(s, str) and len(s.strip()) > 0
