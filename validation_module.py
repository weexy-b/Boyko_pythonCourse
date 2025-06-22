"""Validation utilities for user and account input."""

import re
from datetime import datetime


def validate_user_full_name(full_name):
    """Validate and split full name into name and surname."""
    parts = re.sub(r"[^a-zA-Z\s]", "", full_name).strip().split()
    if len(parts) < 2:
        raise ValueError("User full name must contain at least name and surname")
    return parts[0], " ".join(parts[1:])


def validate_enum(field, value, allowed):
    """Check if value is within allowed enum options."""
    if value not in allowed:
        raise ValueError(f"not allowed value {value} for field {field}!")


def validate_account_number(account_number):
    """Check account number format and sanitize it."""
    account_number = re.sub(r"[#%_?&]", "-", account_number)

    if len(account_number) != 18:
        raise ValueError("too little/many chars!")

    if not account_number.startswith("ID--"):
        raise ValueError("wrong format!")

    pattern = r"[a-zA-Z]{1,3}-\d+-"
    if not re.search(pattern, account_number):
        raise ValueError("broken ID!")

    return account_number


def validate_datetime(dt):
    """Return ISO datetime or current time if missing."""
    return dt or datetime.now().isoformat()