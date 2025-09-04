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


# Configure logging; adjust level as desired (e.g., INFO for more detail)
logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(name)s:%(message)s")


# Single source of truth for the storage path
CONTACTS_FILE = "contacts.json"


# ---------- Helpers ----------

def prompt_nonempty(prompt: str) -> str:
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("Value cannot be empty. Please try again.")


def prompt_optional(prompt: str) -> Optional[str]:
    val = input(prompt).strip()
    return val if val else None


def confirm(prompt: str) -> bool:
    ans = input(f"{prompt} [y/N]: ").strip().lower()
    return ans in {"y", "yes"}


def print_contact(c: Contact) -> None:
    print("-" * 40)
    print(c)
    print("-" * 40)


def print_contacts(items: List[Contact]) -> None:
    if not items:
        print("No contacts found.")
        return
    for idx, c in enumerate(items, 1):
        print(f"{idx}. {c.name} <{c.email}> | {c.phone_num or ''} | {c.address or ''}")


# ---------- Actions ----------

def action_add(rolodex: Rolodex) -> None:
    print("\nAdd New Contact")
    name = prompt_nonempty("Name: ")
    email = prompt_nonempty("Email: ")
    if not Contact.is_valid_email(email):
        print("Invalid email format. Aborting add.")
        return

    address = prompt_optional("Address (optional): ")
    phone = prompt_optional("Phone (optional): ")
    birth_date = prompt_optional("Date of Birth YYYY-MM-DD (optional): ")
    if birth_date and not Contact.is_valid_birth_date(birth_date):
        print("Invalid date (expected YYYY-MM-DD). Aborting add.")
        return

    try:
        contact = Contact(name=name, address=address, phone_num=phone, email=email, birth_date=birth_date)
        rolodex.add_contact(contact)
        print("Contact added.")
    except Exception as e:
        print("Failed to add contact:", e)


def action_view(rolodex: Rolodex) -> None:
    print("\nView Contact")
    email = prompt_nonempty("Email to view: ")
    c = rolodex.view_contact(email)
    if not c:
        print("No contact found with that email.")
        return
    print_contact(c)


def action_edit(rolodex: Rolodex) -> None:
    print("\nEdit Contact")
    current_email = prompt_nonempty("Email of contact to edit: ")
    c = rolodex.view_contact(current_email)
    if not c:
        print("No contact found with that email.")
        return
    print("Leave a field blank to keep current value.")
    print_contact(c)

    name = prompt_optional(f"Name [{c.name}]: ")
    address = prompt_optional(f"Address [{c.address or ''}]: ")
    phone = prompt_optional(f"Phone [{c.phone_num or ''}]: ")
    new_email = prompt_optional(f"Email [{c.email or ''}]: ")
    birth_date = prompt_optional(f"Birth Date YYYY-MM-DD [{c.birth_date or ''}]: ")

    if new_email and not Contact.is_valid_email(new_email):
        print("Invalid email format. Aborting edit.")
        return
    if birth_date and not Contact.is_valid_birth_date(birth_date):
        print("Invalid birth date (expected YYYY-MM-DD). Aborting edit.")
        return

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
        updated = rolodex.edit_contact(current_email, **updates)
        print("Contact updated.")
        print_contact(updated)
    except Exception as e:
        print("Failed to edit contact:", e)


def action_delete(rolodex: Rolodex) -> None:
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
    print("\nSearch Contacts")
    q = prompt_nonempty("Search query: ")
    exact_ans = input("Exact match? [y/N]: ").strip().lower() in {"y", "yes"}
    # Basic: search name+email by default
    results = rolodex.search_contacts(q, fields=("name", "email"), exact=exact_ans)
    print_contacts(results)


def action_list(rolodex: Rolodex) -> None:
    print("\nAll Contacts")
    sort_by = input("Sort by [name/email/birth_date] (default name): ").strip().lower() or "name"
    reverse = input("Reverse order? [y/N]: ").strip().lower() in {"y", "yes"}
    try:
        items = rolodex.list_contacts(sort_by=sort_by, reverse=reverse)
        print_contacts(items)
    except Exception as e:
        print("Invalid sort option:", e)


def main() -> None:
    rx = Rolodex(CONTACTS_FILE)
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
        if choice == "7":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action:
            action(rx)
        else:
            print("Invalid choice. Please select 1-7.")


if __name__ == "__main__":
    main()

