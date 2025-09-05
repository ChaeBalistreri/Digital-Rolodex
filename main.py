"""
Digital Rolodex (DR) - CLI

A minimal interactive command-line interface wired to the Rolodex layer.

Menu:
  1) Add contact
  2) View contact (by email)
  3) Edit contact (by email)
  4) Delete contact (by email)
  5) Search contacts
  6) List all contacts
  7) Exit
"""

from __future__ import annotations

import logging
from typing import Optional, List

from contact import Contact
from rolodex import Rolodex


# Configure root logging once for this CLI.
# - Level WARNING by default to reduce noise; switch to INFO for more detail.
# - Format includes severity, logger name, and message.
logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(name)s:%(message)s")


# Single source of truth for the storage path used by this CLI runtime.
# The Rolodex class accepts any JSON file path; here we use a simple default
# in the project root for an end-user run of the CLI.
CONTACTS_FILE = "contacts.json"


# ---------- Helpers ----------

def prompt_nonempty(prompt: str) -> str:
    """Prompt the user until a non-empty (non-whitespace) string is entered."""
    while True:
        # input() returns the raw string typed by the user, including spaces.
        val = input(prompt).strip()
        # .strip() removes leading/trailing whitespace; empty string means invalid entry.
        if val:
            return val
        print("Value cannot be empty. Please try again.")


def prompt_optional(prompt: str) -> Optional[str]:
    """Prompt the user once; return None if the user left it blank."""
    val = input(prompt).strip()
    # Return the string if non-empty; else explicit None to signal "no change"/"missing".
    return val if val else None


def confirm(prompt: str) -> bool:
    """Ask a yes/no question; treat anything other than y/yes as No."""
    ans = input(f"{prompt} [y/N]: ").strip().lower()
    # Accept 'y' or 'yes' (case-insensitive). Default is No.
    return ans in {"y", "yes"}


def print_contact(c: Contact) -> None:
    """Pretty-print a single Contact using Contact.__str__ output."""
    print("-" * 40)
    print(c)
    print("-" * 40)


def print_contacts(items: List[Contact]) -> None:
    """Print a compact one-line summary for each contact in a list."""
    if not items:
        print("No contacts found.")
        return
    for idx, c in enumerate(items, 1):
        # Show index, display name, primary email, and optional phone/address.
        print(f"{idx}. {c.name} <{c.email}> | {c.phone_num or ''} | {c.address or ''}")


# ---------- Actions ----------

def action_add(rolodex: Rolodex) -> None:
    """Collect fields from the user and add a new contact.

    Validates email and optional birth date format before attempting to add.
    Duplicate emails and other business rules are enforced by Rolodex.add_contact.
    """
    print("\nAdd New Contact")
    # Required fields
    name = prompt_nonempty("Name: ")
    email = prompt_nonempty("Email: ")
    # Quick client-side email format check (business layer also validates on edits).
    if not Contact.is_valid_email(email):
        print("Invalid email format. Aborting add.")
        return

    # Optional fields
    address = prompt_optional("Address (optional): ")
    phone = prompt_optional("Phone (optional): ")
    birth_date = prompt_optional("Date of Birth YYYY-MM-DD (optional): ")
    # If provided, DOB must be ISO (YYYY-MM-DD)
    if birth_date and not Contact.is_valid_birth_date(birth_date):
        print("Invalid date (expected YYYY-MM-DD). Aborting add.")
        return

    try:
        # Construct a Contact (the Rolodex API also accepts dicts, but we use the class here).
        contact = Contact(name=name, address=address, phone_num=phone, email=email, birth_date=birth_date)
        # Add persists immediately via Rolodex.save().
        rolodex.add_contact(contact)
        print("Contact added.")
    except Exception as e:
        # Surface a readable error (e.g., duplicate email).
        print("Failed to add contact:", e)


def action_view(rolodex: Rolodex) -> None:
    """Lookup a contact by email and print details."""
    print("\nView Contact")
    email = prompt_nonempty("Email to view: ")
    c = rolodex.view_contact(email)
    if not c:
        print("No contact found with that email.")
        return
    print_contact(c)


def action_edit(rolodex: Rolodex) -> None:
    """Edit selected fields of an existing contact identified by email.

    Blank inputs mean "keep current value"; we only include provided fields
    in the update dict passed to Rolodex.edit_contact.
    """
    print("\nEdit Contact")
    current_email = prompt_nonempty("Email of contact to edit: ")
    c = rolodex.view_contact(current_email)
    if not c:
        print("No contact found with that email.")
        return
    print("Leave a field blank to keep current value.")
    print_contact(c)

    # Collect possibly-updated values (None means unchanged)
    name = prompt_optional(f"Name [{c.name}]: ")
    address = prompt_optional(f"Address [{c.address or ''}]: ")
    phone = prompt_optional(f"Phone [{c.phone_num or ''}]: ")
    new_email = prompt_optional(f"Email [{c.email or ''}]: ")
    birth_date = prompt_optional(f"Birth Date YYYY-MM-DD [{c.birth_date or ''}]: ")

    # Validate user-provided email and DOB if given
    if new_email and not Contact.is_valid_email(new_email):
        print("Invalid email format. Aborting edit.")
        return
    if birth_date and not Contact.is_valid_birth_date(birth_date):
        print("Invalid birth date (expected YYYY-MM-DD). Aborting edit.")
        return

    # Build updates dict with only explicitly provided fields
    updates = {}
    if name is not None:
        updates["name"] = name
    if address is not None:
        updates["address"] = address
    if phone is not None:
        updates["phone_num"] = phone
    if new_email is not None:
        updates["email"] = new_email
    if birth_date is not None:
        updates["birth_date"] = birth_date

    try:
        # Persist the changes through the Rolodex layer
        updated = rolodex.edit_contact(current_email, **updates)
        print("Contact updated.")
        print_contact(updated)
    except Exception as e:
        print("Failed to edit contact:", e)


def action_delete(rolodex: Rolodex) -> None:
    """Delete a contact by email after user confirmation."""
    print("\nDelete Contact")
    email = prompt_nonempty("Email to delete: ")
    if not confirm(f"Are you sure you want to delete '{email}'?"):
        print("Cancelled.")
        return
    if rolodex.delete_contact(email):
        print("Contact deleted.")
    else:
        print("No contact found with that email.")


def action_search(rolodex: Rolodex) -> None:
    """Search for contacts by a query across name and email by default."""
    print("\nSearch Contacts")
    q = prompt_nonempty("Search query: ")
    # Exact match restricts results to equality (case-insensitive); otherwise substring match.
    exact_ans = input("Exact match? [y/N]: ").strip().lower() in {"y", "yes"}
    # Basic: search name+email by default
    results = rolodex.search_contacts(q, fields=("name", "email"), exact=exact_ans)
    print_contacts(results)


def action_list(rolodex: Rolodex) -> None:
    """List all contacts with optional sort field and order."""
    print("\nAll Contacts")
    sort_by = input("Sort by [name/email/birth_date] (default name): ").strip().lower() or "name"
    reverse = input("Reverse order? [y/N]: ").strip().lower() in {"y", "yes"}
    try:
        items = rolodex.list_contacts(sort_by=sort_by, reverse=reverse)
        print_contacts(items)
    except Exception as e:
        print("Invalid sort option:", e)


def main() -> None:
    """Entry point: create Rolodex bound to CONTACTS_FILE and run menu loop."""
    # Construct the application layer with the chosen JSON file for persistence.
    rx = Rolodex(CONTACTS_FILE)
    # Static menu text; kept as a single string for simple printing.
    menu = (
        "\n--- DIGITAL ROLODEX ---\n"
        "1. Add new contact\n"
        "2. View contact\n"
        "3. Edit contact\n"
        "4. Delete contact\n"
        "5. Search contacts\n"
        "6. List all contacts\n"
        "7. Exit\n"
    )

    # Map menu choices to their corresponding handler functions.
    actions = {
        "1": action_add,
        "2": action_view,
        "3": action_edit,
        "4": action_delete,
        "5": action_search,
        "6": action_list,
    }

    while True:
        print(menu)
        choice = input("Select an option: ").strip()
        # Option 7 exits the loop and ends the program.
        if choice == "7":
            print("Goodbye!")
            break
        # Look up the action by user choice and invoke it if valid.
        action = actions.get(choice)
        if action:
            action(rx)
        else:
            print("Invalid choice. Please select 1-7.")


if __name__ == "__main__":
    # Allow running the CLI by executing `python main.py` directly.
    main()
