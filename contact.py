"""Contact data model for the Digital Rolodex."""

from __future__ import annotations

from utils import (
    clean_optional,
    normalize_phone,
    normalize_tags,
    parse_bool,
    validate_email,
    validate_iso_date,
    validate_phone,
)


class Contact:
    """Blueprint for each contact in Digital Rolodex."""

    def __init__(
        self,
        name,
        address=None,
        phone_num=None,
        email=None,
        birth_date=None,
        tags=None,
        category=None,
        notes=None,
        favorite=False,
    ):
        """Create a contact.

        Name is required. The Rolodex layer requires email when adding or
        loading contacts from storage.
        """
        self.name = str(name).strip() if name is not None else name
        self.address = clean_optional(address)
        raw_phone = clean_optional(phone_num)
        normalized_phone = normalize_phone(raw_phone)
        self.phone_num = normalized_phone if normalized_phone is not None else raw_phone
        self.email = str(email).strip() if email is not None else email
        self.birth_date = clean_optional(birth_date)
        self.tags = normalize_tags(tags)
        self.category = clean_optional(category)
        self.notes = clean_optional(notes)
        self.favorite = parse_bool(favorite)

    def __str__(self):
        """Return a readable multi-line contact summary."""
        return (
            f"Name: {self.name}\n"
            f"Address: {self.address}\n"
            f"Phone: {self.phone_num}\n"
            f"Email: {self.email}\n"
            f"Date of Birth: {self.birth_date}\n"
            f"Category: {self.category}\n"
            f"Notes: {self.notes}\n"
            f"Favorite: {'Yes' if self.favorite else 'No'}\n"
            f"Tags: {', '.join(self.tags) if self.tags else None}"
        )

    def to_dict(self):
        """Serialize the contact into a dictionary for storage/export."""
        return {
            "name": self.name,
            "address": self.address,
            "phone_num": self.phone_num,
            "email": self.email,
            "birth_date": self.birth_date,
            "category": self.category,
            "notes": self.notes,
            "favorite": self.favorite,
            "tags": self.tags,
        }

    def is_minimally_complete(self) -> bool:
        """Return True if this contact has name and at least one contact method."""
        return bool(self.name and (self.email or self.phone_num))

    @classmethod
    def from_dict(cls, data):
        """Reconstruct a Contact object from a dictionary."""
        name = data.get("name")
        if not name:
            raise ValueError("Contact 'name' is required")

        return cls(
            name=name,
            address=data.get("address"),
            phone_num=data.get("phone_num"),
            email=data.get("email"),
            birth_date=data.get("birth_date"),
            tags=data.get("tags", []),
            category=data.get("category"),
            notes=data.get("notes"),
            favorite=data.get("favorite", False),
        )

    @classmethod
    def create_validated(
        cls,
        name,
        address,
        phone_num,
        email,
        birth_date,
        tags=None,
        category=None,
        notes=None,
        favorite=False,
    ):
        """Create a contact after validating email, phone, and birth date."""
        if not cls.is_valid_email(email):
            raise ValueError("Invalid email")
        if not cls.is_valid_phone(phone_num):
            raise ValueError("Invalid phone number")
        if not cls.is_valid_birth_date(birth_date):
            raise ValueError("Invalid birth date")
        return cls(name, address, phone_num, email, birth_date, tags, category, notes, favorite)

    @staticmethod
    def is_valid_email(email):
        """Check whether email matches the expected local@domain.tld shape."""
        return validate_email(email)

    @staticmethod
    def is_valid_phone(phone_num):
        """Check whether a phone number is blank or in an accepted format."""
        return validate_phone(phone_num)

    @staticmethod
    def normalize_phone(phone_num):
        """Return a phone number in standardized storage/display form."""
        return normalize_phone(phone_num)

    @staticmethod
    def is_valid_birth_date(birth_date):
        """Check whether birth_date is blank or formatted as YYYY-MM-DD."""
        return validate_iso_date(birth_date)
