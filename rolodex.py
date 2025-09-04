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

from dataclasses import dataclass
import logging
from typing import List, Iterable, Optional, Union

from contact import Contact
import storage


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
    def add_contact(self, contact_or_dict: Union[Contact, dict]) -> Contact:
        """Add a new contact and persist immediately.

        - Accepts either a Contact or a dict (which is coerced via Contact.from_dict).
        - Requires non-empty name and email; raises ValueError otherwise.
        - Prevents duplicate emails (case-insensitive); raises ValueError.

        Returns the Contact instance added.
        """
        contact = (
            contact_or_dict
            if isinstance(contact_or_dict, Contact)
            else Contact.from_dict(contact_or_dict)
        )

        # Basic required fields
        name = (contact.name or "").strip()
        email = (contact.email or "").strip()
        if not name or not email:
            raise ValueError("Both 'name' and 'email' are required to add a contact")

        # Enforce unique email (case-insensitive)
        email_key = email.lower()
        if any((c.email or "").lower() == email_key for c in self._contacts):
            raise ValueError(f"A contact with email '{contact.email}' already exists")

        # Use trimmed values
        contact.name = name
        contact.email = email

        self._contacts.append(contact)
        self.save()
        logger.info("Added contact '%s' <%s>", contact.name, contact.email)
        return contact

    def list_contacts(self, sort_by: str = "name", reverse: bool = False) -> List[Contact]:
        """Return a new list of contacts sorted by the given field.

        Supported sort keys: 'name', 'email', 'birth_date'. Defaults to 'name'.
        Missing fields sort as empty strings.
        """
        key = sort_by.lower().strip()
        if key not in {"name", "email", "birth_date"}:
            raise ValueError("sort_by must be one of: 'name', 'email', 'birth_date'")

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

        valid_fields = {"name", "email", "address", "phone_num", "birth_date"}
        fields_norm = [f for f in (f.lower().strip() for f in fields) if f in valid_fields]
        if not fields_norm:
            raise ValueError("fields must include one or more of: " + ", ".join(sorted(valid_fields)))

        def matches(c: Contact) -> bool:
            for f in fields_norm:
                val = getattr(c, f, None)
                if val is None:
                    continue
                s = str(val).lower()
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

        Accepts keyword updates among: name, address, phone_num, email, birth_date.
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

        # Apply updates after validation
        contact.name = new_name
        contact.email = new_email
        if "address" in updates:
            contact.address = updates["address"]
        if "phone_num" in updates:
            contact.phone_num = updates["phone_num"]
        if "birth_date" in updates and updates["birth_date"] is not None:
            contact.birth_date = str(updates["birth_date"]).strip() or None

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
