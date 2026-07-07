# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 12:43:17 2026

@author: c10265
"""

from enum import Enum


class Status(Enum):
    """

    The current status regarding contact with the owner or legal gurantor
    of the service address.

    Args:
        Enum (Enum): uses the Enum class.
    """

    ACCEPTED = "ACCEPTED"
    TO_CONTACT = "TO CONTACT"
    DECLINED = "DECLINED"


# All supported file import extensions
SUPPORTED_FILE_EXTENSIONS = [
    "*.xls",
    "*.xlsx",
    "*.xlsm",
    "*.xlsb",
    "*.odf",
    "*.ods",
    "*.odt",
    "*.csv",
]

# All null or invalid values to filter out in any column
# of a DataFrame.
SORT_VALUES = {"nan", "null", "<Null>", "<NULL>", "Null", "NULL"}

# Invalid project number(s) to filter out from a DataFrame.
INVALID_PROJECT_NUMBERS = {"20SR05203"}

# Invalid project categor(y/ies) to filter out from a DataFrame.
INVALID_PROJECT_CATEGORIES = {"Maintenance"}
