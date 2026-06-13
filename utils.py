"""Shared helpers for the Digital Rolodex CLI and core logic."""

from __future__ import annotations

from datetime import date, datetime
import re
from typing import Iterable, List, Optional


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_ALLOWED_RE = re.compile(r"^\+?[\d\s().-]{7,24}$")


def clean_optional(value: object) -> Optional[str]:
    """Return a stripped string, or None for blanks/None."""
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def parse_bool(value: object, default: bool = False) -> bool:
    """Parse common bool-like values from storage or CSV input."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    cleaned = str(value).strip().lower()
    if cleaned in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if cleaned in {"0", "false", "f", "no", "n", "off", ""}:
        return False
    return default


def validate_email(email: object) -> bool:
    """Return True when email has a simple local@domain.tld shape."""
    cleaned = clean_optional(email)
    return bool(cleaned and EMAIL_RE.match(cleaned))


def validate_phone(phone: object) -> bool:
    """Return True for valid phone values; blanks are allowed."""
    if clean_optional(phone) is None:
        return True
    return normalize_phone(phone) is not None


def normalize_phone(phone: object) -> Optional[str]:
    """Normalize U.S. phone numbers, preserving valid international values.

    Accepted U.S. examples:
    - 8175551234
    - 817-555-1234
    - (817) 555-1234
    - 817.555.1234

    U.S. numbers are returned as ``(817) 555-1234``. Existing international
    values are accepted for backward compatibility and returned cleaned.
    """
    cleaned = clean_optional(phone)
    if cleaned is None:
        return None

    digits = re.sub(r"\D", "", cleaned)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

    if cleaned.startswith("+") and PHONE_ALLOWED_RE.match(cleaned) and len(digits) >= 10:
        return cleaned
    return None


def validate_iso_date(value: object) -> bool:
    """Return True for dates in YYYY-MM-DD format; blanks are allowed."""
    cleaned = clean_optional(value)
    if cleaned is None:
        return True
    try:
        datetime.strptime(cleaned, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def parse_iso_date(value: object) -> Optional[date]:
    """Parse a YYYY-MM-DD date, returning None for blanks."""
    cleaned = clean_optional(value)
    if cleaned is None:
        return None
    try:
        return datetime.strptime(cleaned, "%Y-%m-%d").date()
    except ValueError:
        return None


def normalize_tags(tags: object) -> List[str]:
    """Normalize tags from a comma string or iterable into sorted unique values."""
    if tags is None:
        return []
    if isinstance(tags, str):
        raw_items = tags.split(",")
    elif isinstance(tags, Iterable):
        raw_items = list(tags)
    else:
        raw_items = [tags]

    seen = set()
    normalized: List[str] = []
    for item in raw_items:
        tag = str(item).strip().lower()
        if tag and tag not in seen:
            seen.add(tag)
            normalized.append(tag)
    return sorted(normalized)


def days_until_birthday(birth_date: object, today: Optional[date] = None) -> Optional[int]:
    """Return days until the next birthday, or None when birth_date is blank."""
    parsed = parse_iso_date(birth_date)
    if parsed is None:
        return None

    today = today or date.today()
    next_birthday = parsed.replace(year=today.year)
    if next_birthday < today:
        next_birthday = parsed.replace(year=today.year + 1)
    return (next_birthday - today).days
