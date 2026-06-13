"""Utility helper tests for Digital Rolodex.

Run:
    python Tests/utils_TestScript.py
"""

from __future__ import annotations

from datetime import date
import os
import sys


CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils import (
    days_until_birthday,
    normalize_phone,
    normalize_tags,
    validate_email,
    validate_iso_date,
    validate_phone,
)


def main() -> None:
    print("== Utility Tests ==")

    assert validate_email("person@example.com")
    assert not validate_email("person.example.com")
    assert not validate_email("")
    print("Email validation passed")

    assert validate_phone("(123) 456-7890")
    assert validate_phone("123-456-7890")
    assert validate_phone("123.456.7890")
    assert validate_phone("1234567890")
    assert validate_phone("+44 20 7946 0991")
    assert validate_phone(None)
    assert not validate_phone("12")
    assert normalize_phone("1234567890") == "(123) 456-7890"
    assert normalize_phone("1-123-456-7890") == "(123) 456-7890"
    print("Phone validation passed")

    assert validate_iso_date("2000-02-29")
    assert validate_iso_date(None)
    assert not validate_iso_date("02/29/2000")
    print("ISO date validation passed")

    assert normalize_tags("Friend, VIP, friend") == ["friend", "vip"]
    assert normalize_tags(["Work", "client", "work"]) == ["client", "work"]
    print("Tag normalization passed")

    assert days_until_birthday("2000-06-12", today=date(2026, 6, 12)) == 0
    assert days_until_birthday("2000-06-20", today=date(2026, 6, 12)) == 8
    assert days_until_birthday("2000-01-01", today=date(2026, 6, 12)) == 203
    print("Birthday calculation passed")

    print("All utility tests completed.")


if __name__ == "__main__":
    main()
