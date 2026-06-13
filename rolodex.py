"""
Rolodex core logic: manage contacts in-memory with JSON persistence.

Implements a small API that higher layers (CLI/UI) can use:
- Rolodex.add_contact(Contact|dict) -> Contact  (persists immediately)
- Rolodex.list_contacts(sort_by="name", reverse=False) -> list[Contact]

Notes:
- Persistence is delegated to storage.py; this module maintains no globals.
- Duplicate prevention: enforces unique email (case-insensitive) on add.
- Validation: requires non-empty name and email on add; raises ValueError if missing.
"""

from __future__ import annotations

import csv
import json
import logging
import os
from datetime import date
from typing import List, Iterable, Optional, Union

from contact import Contact
import storage
from utils import clean_optional, days_until_birthday, normalize_tags, parse_bool, parse_iso_date


logger = logging.getLogger(__name__)


class Rolodex:
    """A simple contact manager backed by a JSON file."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        # Load existing contacts. storage enforces name+email policy on load.
        self._contacts: List[Contact] = storage.load_contacts(file_path)

    # ----- Persistence helpers -----
    def save(self) -> None:
        """Persist the current contact list to disk."""
        storage.save_contacts(self.file_path, self._contacts)

    # ----- Core operations -----
    def _validate_contact(self, contact: Contact) -> None:
        """Validate fields that have explicit Rolodex data rules."""
        if not (contact.name or "").strip():
            raise ValueError("'name' is required")
        if not (contact.email or "").strip():
            raise ValueError("'email' is required")
        if not Contact.is_valid_email(contact.email):
            raise ValueError("Invalid email format")
        if not Contact.is_valid_phone(contact.phone_num):
            raise ValueError("Invalid phone number")
        if not Contact.is_valid_birth_date(contact.birth_date):
            raise ValueError("Invalid birth date (expected YYYY-MM-DD)")

    def _coerce_contact(self, contact_or_dict: Union[Contact, dict]) -> Contact:
        """Return a Contact from either a Contact instance or dict."""
        return (
            contact_or_dict
            if isinstance(contact_or_dict, Contact)
            else Contact.from_dict(contact_or_dict)
        )

    def add_contact(self, contact_or_dict: Union[Contact, dict]) -> Contact:
        """Add a new contact and persist immediately.

        - Accepts either a Contact or a dict (which is coerced via Contact.from_dict).
        - Requires non-empty name and email; raises ValueError otherwise.
        - Prevents duplicate emails (case-insensitive); raises ValueError.

        Returns the Contact instance added.
        """
        contact = self._coerce_contact(contact_or_dict)

        # Basic required fields
        name = (contact.name or "").strip()
        email = (contact.email or "").strip()
        self._validate_contact(contact)

        # Enforce unique email (case-insensitive)
        email_key = email.lower()
        if any((c.email or "").lower() == email_key for c in self._contacts):
            raise ValueError(f"A contact with email '{contact.email}' already exists")

        # Use trimmed values
        contact.name = name
        contact.email = email
        contact.phone_num = Contact.normalize_phone(contact.phone_num)
        contact.tags = normalize_tags(contact.tags)

        self._contacts.append(contact)
        self.save()
        logger.info("Added contact '%s' <%s>", contact.name, contact.email)
        return contact

    def list_contacts(self, sort_by: str = "name", reverse: bool = False) -> List[Contact]:
        """Return a new list of contacts sorted by the given field.

        Supported sort keys: 'name', 'email', 'birth_date', 'category'. Defaults to 'name'.
        Missing fields sort as empty strings.
        """
        key = sort_by.lower().strip()
        if key not in {"name", "email", "birth_date", "category"}:
            raise ValueError("sort_by must be one of: 'name', 'email', 'birth_date', 'category'")

        def sort_key(c: Contact) -> str:
            value = getattr(c, key, None)
            return (value or "").lower() if isinstance(value, str) else (value or "")

        return sorted(list(self._contacts), key=sort_key, reverse=reverse)

    def get_by_email(self, email: str) -> Optional[Contact]:
        """Return the contact with the given email (case-insensitive), or None."""
        if not email:
            return None
        key = email.strip().lower()
        for c in self._contacts:
            if (c.email or "").strip().lower() == key:
                return c
        return None

    def view_contact(self, email: str) -> Optional[Contact]:
        """Alias for get_by_email for clearer intent at the call site."""
        return self.get_by_email(email)

    def get_by_name(self, name: str) -> List[Contact]:
        """Return contacts whose name matches exactly, case-insensitively."""
        if not name:
            return []
        key = name.strip().lower()
        return [c for c in self._contacts if (c.name or "").strip().lower() == key]

    def search_contacts(
        self,
        query: str,
        fields: Iterable[str] = ("name", "email"),
        exact: bool = False,
    ) -> List[Contact]:
        """Search contacts across selected fields.

        - Case-insensitive.
        - Partial match by default; exact equality if exact=True.
        - fields controls which attributes to search (e.g., ("name",), ("email",)).
        """
        if not query:
            return []
        q = query.strip().lower()

        valid_fields = {
            "name",
            "email",
            "address",
            "phone_num",
            "birth_date",
            "category",
            "notes",
            "favorite",
            "tags",
        }
        fields_norm = [f for f in (f.lower().strip() for f in fields) if f in valid_fields]
        if not fields_norm:
            raise ValueError("fields must include one or more of: " + ", ".join(sorted(valid_fields)))

        def matches(c: Contact) -> bool:
            for f in fields_norm:
                val = getattr(c, f, None)
                if val is None:
                    continue
                s = " ".join(val).lower() if isinstance(val, list) else str(val).lower()
                if exact:
                    if s == q:
                        return True
                else:
                    if q in s:
                        return True
            return False

        return [c for c in self._contacts if matches(c)]

    def edit_contact(self, current_email: str, **updates) -> Contact:
        """Edit an existing contact identified by current email.

        Accepts keyword updates among: name, address, phone_num, email, birth_date,
        category, notes, favorite, tags.
        Validates:
        - name must be non-empty if provided
        - email must be valid format if provided, and unique (case-insensitive)
        - birth_date must be valid YYYY-MM-DD if provided

        Persists changes and returns the updated Contact.
        """
        contact = self.get_by_email(current_email)
        if not contact:
            raise ValueError(f"No contact found with email '{current_email}'")

        # Prepare prospective values
        new_name = contact.name
        if "name" in updates and updates["name"] is not None:
            new_name = str(updates["name"]).strip()
            if not new_name:
                raise ValueError("'name' cannot be empty")

        new_email = contact.email
        if "email" in updates and updates["email"] is not None:
            proposed = str(updates["email"]).strip()
            if not proposed:
                raise ValueError("'email' cannot be empty")
            if not Contact.is_valid_email(proposed):
                raise ValueError("Invalid email format")
            # Enforce uniqueness if actually changing normalized email
            old_key = (contact.email or "").strip().lower()
            new_key = proposed.lower()
            if new_key != old_key and any(
                (c.email or "").strip().lower() == new_key for c in self._contacts
            ):
                raise ValueError(f"A contact with email '{proposed}' already exists")
            new_email = proposed

        if "birth_date" in updates and updates["birth_date"] is not None:
            bd = str(updates["birth_date"]).strip()
            if bd and not Contact.is_valid_birth_date(bd):
                raise ValueError("Invalid birth date (expected YYYY-MM-DD)")

        if "phone_num" in updates and updates["phone_num"] is not None:
            phone = str(updates["phone_num"]).strip()
            if phone and not Contact.is_valid_phone(phone):
                raise ValueError("Invalid phone number")

        # Apply updates after validation
        contact.name = new_name
        contact.email = new_email
        if "address" in updates:
            contact.address = clean_optional(updates["address"])
        if "phone_num" in updates:
            contact.phone_num = Contact.normalize_phone(updates["phone_num"])
        if "birth_date" in updates and updates["birth_date"] is not None:
            contact.birth_date = str(updates["birth_date"]).strip() or None
        if "category" in updates:
            contact.category = clean_optional(updates["category"])
        if "notes" in updates:
            contact.notes = clean_optional(updates["notes"])
        if "favorite" in updates:
            contact.favorite = parse_bool(updates["favorite"])
        if "tags" in updates:
            contact.tags = normalize_tags(updates["tags"])

        self.save()
        logger.info("Edited contact '%s' <%s>", contact.name, contact.email)
        return contact

    def delete_contact(self, email: str) -> bool:
        """Delete the contact with the given email. Returns True if deleted."""
        if not email:
            return False
        key = email.strip().lower()
        for idx, c in enumerate(self._contacts):
            if (c.email or "").strip().lower() == key:
                removed = self._contacts.pop(idx)
                self.save()
                logger.info("Deleted contact '%s' <%s>", removed.name, removed.email)
                return True
        return False

    # ----- Advanced operations -----
    def find_possible_duplicates(self) -> List[List[Contact]]:
        """Return groups of contacts that may represent the same person."""
        buckets: dict[str, List[Contact]] = {}
        for contact in self._contacts:
            email = (contact.email or "").strip().lower()
            if email:
                buckets.setdefault(f"email:{email}", []).append(contact)

            name = (contact.name or "").strip().lower()
            phone = (contact.phone_num or "").strip().lower()
            if name:
                buckets.setdefault(f"name:{name}", []).append(contact)
            if name and phone:
                buckets.setdefault(f"name_phone:{name}:{phone}", []).append(contact)
            if phone:
                buckets.setdefault(f"phone:{phone}", []).append(contact)

        duplicate_groups = []
        seen_ids = set()
        for group in buckets.values():
            if len(group) < 2:
                continue
            key = tuple(sorted(id(c) for c in group))
            if key not in seen_ids:
                seen_ids.add(key)
                duplicate_groups.append(group)
        return duplicate_groups

    def find_duplicates(self) -> List[List[Contact]]:
        """Backward-compatible alias for find_possible_duplicates."""
        return self.find_possible_duplicates()

    def list_by_category(self, category: str) -> List[Contact]:
        """Return contacts matching the specified category."""
        key = (category or "").strip().lower()
        if not key:
            return []
        return sorted(
            [c for c in self._contacts if (c.category or "").strip().lower() == key],
            key=lambda c: (c.name or "").lower(),
        )

    def list_favorites(self) -> List[Contact]:
        """Return contacts marked as favorites."""
        return sorted([c for c in self._contacts if c.favorite], key=lambda c: (c.name or "").lower())

    def upcoming_birthdays(self, days: int = 30, today=None) -> List[tuple[Contact, int]]:
        """Return contacts with birthdays within the next number of days."""
        if days < 0:
            raise ValueError("days must be 0 or greater")
        upcoming = []
        for contact in self._contacts:
            remaining = days_until_birthday(contact.birth_date, today=today)
            if remaining is not None and remaining <= days:
                upcoming.append((contact, remaining))
        return sorted(upcoming, key=lambda item: (item[1], item[0].name.lower()))

    def get_statistics(self, today=None) -> dict:
        """Return summary statistics about the Rolodex."""
        today = today or date.today()
        category_counts: dict[str, int] = {}
        birthdays_this_month = 0
        contacts_with_birthdays = 0

        for contact in self._contacts:
            category = contact.category or "Uncategorized"
            category_counts[category] = category_counts.get(category, 0) + 1

            parsed_birthday = parse_iso_date(contact.birth_date)
            if parsed_birthday is not None:
                contacts_with_birthdays += 1
                if parsed_birthday.month == today.month:
                    birthdays_this_month += 1

        return {
            "total_contacts": len(self._contacts),
            "contacts_with_birthdays": contacts_with_birthdays,
            "missing_email": sum(1 for c in self._contacts if not c.email),
            "missing_phone_number": sum(1 for c in self._contacts if not c.phone_num),
            "birthdays_this_month": birthdays_this_month,
            "categories": dict(sorted(category_counts.items())),
            "favorite_contacts": sum(1 for c in self._contacts if c.favorite),
        }

    def export_contacts(self, file_path: str, file_format: Optional[str] = None) -> int:
        """Export contacts to JSON or CSV. Returns the number exported."""
        fmt = (file_format or os.path.splitext(file_path)[1].lstrip(".") or "json").lower()
        if fmt not in {"json", "csv"}:
            raise ValueError("file_format must be 'json' or 'csv'")

        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        if fmt == "json":
            with open(file_path, "w", encoding="utf-8") as handle:
                json.dump([c.to_dict() for c in self._contacts], handle, indent=4, ensure_ascii=False)
        else:
            with open(file_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "name",
                        "address",
                        "phone_num",
                        "email",
                        "birth_date",
                        "category",
                        "notes",
                        "favorite",
                        "tags",
                    ],
                )
                writer.writeheader()
                for contact in self._contacts:
                    row = contact.to_dict()
                    row["tags"] = ", ".join(row.get("tags", []))
                    writer.writerow(row)
        return len(self._contacts)

    def import_contacts(self, file_path: str, merge: bool = False) -> dict:
        """Import contacts from JSON or CSV.

        When merge is False, existing contacts are replaced by imported valid
        records. When merge is True, imported contacts are added while skipping
        duplicate emails.
        """
        fmt = os.path.splitext(file_path)[1].lstrip(".").lower()
        if fmt not in {"json", "csv"}:
            raise ValueError("Import supports .json and .csv files")

        with open(file_path, "r", encoding="utf-8-sig", newline="") as handle:
            leading = handle.read(2048).lstrip()

        # Be forgiving of user-created files with the wrong extension, such as
        # a JSON export named Addy.csv. The importer follows the real contents.
        if leading.startswith("[") or leading.startswith("{"):
            fmt = "json"

        if fmt == "json":
            with open(file_path, "r", encoding="utf-8-sig") as handle:
                raw_rows = json.load(handle)
            if not isinstance(raw_rows, list):
                raise ValueError("JSON import file must contain a list")
        else:
            with open(file_path, "r", encoding="utf-8-sig", newline="") as handle:
                raw_rows = list(csv.DictReader(handle))

        imported: List[Contact] = []
        skipped = 0
        errors = []
        existing_keys = {(c.email or "").strip().lower() for c in self._contacts} if merge else set()
        pending_keys = set()

        for idx, row in enumerate(raw_rows, 1):
            try:
                contact = self._coerce_contact(row)
                self._validate_contact(contact)
                key = (contact.email or "").strip().lower()
                if key in existing_keys or key in pending_keys:
                    skipped += 1
                    errors.append(f"row {idx}: duplicate email {contact.email}")
                    continue
                contact.name = contact.name.strip()
                contact.email = contact.email.strip()
                contact.phone_num = Contact.normalize_phone(contact.phone_num)
                contact.tags = normalize_tags(contact.tags)
                imported.append(contact)
                pending_keys.add(key)
            except Exception as exc:
                skipped += 1
                errors.append(f"row {idx}: {exc}")

        if merge:
            self._contacts.extend(imported)
        else:
            self._contacts = imported
        self.save()

        return {"imported": len(imported), "skipped": skipped, "errors": errors}
