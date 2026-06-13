"""
Digital Rolodex (DR) - CLI

A minimal interactive command-line interface wired to the Rolodex layer.

Menu:
  1) Add Contact
  2) View Contact
  3) Edit Contact
  4) Delete Contact
  5) Search Contacts
  6) List All Contacts
  7) List Contacts by Category
  8) Upcoming Birthdays
  9) Export Contacts to CSV
  10) Import Contacts from CSV
  11) Find Possible Duplicates
  12) View Statistics
  13) List Favorite Contacts
  14) Exit
"""

from __future__ import annotations

import argparse
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
        tags = f" | tags: {', '.join(c.tags)}" if getattr(c, "tags", None) else ""
        favorite = " | favorite" if getattr(c, "favorite", False) else ""
        category = f" | {c.category}" if getattr(c, "category", None) else ""
        print(f"{idx}. {c.name} <{c.email}> | {c.phone_num or ''} | {c.address or ''}{category}{favorite}{tags}")


def prompt_yes_no(prompt: str, default: bool = False) -> bool:
    """Prompt for a yes/no answer with a configurable default."""
    suffix = "[Y/n]" if default else "[y/N]"
    ans = input(f"{prompt} {suffix}: ").strip().lower()
    if not ans:
        return default
    return ans in {"y", "yes"}


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
    phone = phone.strip() if phone else None
    if phone and not Contact.is_valid_phone(phone):
        print("Invalid phone format. Aborting add.")
        return
    category = prompt_optional("Category (optional): ")
    notes = prompt_optional("Notes (optional): ")
    favorite = prompt_yes_no("Mark as favorite?", default=False)
    tags = prompt_optional("Tags comma-separated (optional): ")

    try:
        # Construct a Contact (the Rolodex API also accepts dicts, but we use the class here).
        contact = Contact(
            name=name,
            address=address,
            phone_num=phone,
            email=email,
            birth_date=birth_date,
            tags=tags,
            category=category,
            notes=notes,
            favorite=favorite,
        )
        # Add persists immediately via Rolodex.save().
        rolodex.add_contact(contact)
        print("Contact added.")
    except Exception as e:
        # Surface a readable error (e.g., duplicate email).
        print("Failed to add contact:", e)


def action_view(rolodex: Rolodex) -> None:
    """Lookup a contact by email or exact name and print details."""
    print("\nView Contact")
    lookup = prompt_nonempty("Email or exact name to view: ")
    c = rolodex.view_contact(lookup)
    if c:
        print_contact(c)
        return
    matches = rolodex.get_by_name(lookup)
    if not matches:
        print("No contact found with that email or name.")
        return
    print_contacts(matches)


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
    category = prompt_optional(f"Category [{c.category or ''}]: ")
    notes = prompt_optional(f"Notes [{c.notes or ''}]: ")
    favorite = prompt_optional(f"Favorite y/n [{'y' if c.favorite else 'n'}]: ")
    tags = prompt_optional(f"Tags comma-separated [{', '.join(c.tags)}]: ")

    # Validate user-provided email and DOB if given
    if new_email and not Contact.is_valid_email(new_email):
        print("Invalid email format. Aborting edit.")
        return
    if birth_date and not Contact.is_valid_birth_date(birth_date):
        print("Invalid birth date (expected YYYY-MM-DD). Aborting edit.")
        return
    if phone and not Contact.is_valid_phone(phone):
        print("Invalid phone format. Aborting edit.")
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
    if category is not None:
        updates["category"] = category
    if notes is not None:
        updates["notes"] = notes
    if favorite is not None:
        updates["favorite"] = favorite
    if tags is not None:
        updates["tags"] = tags

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
    fields_text = input(
        "Fields comma-separated [name,email,address,phone_num,birth_date,category,notes,favorite,tags] (default all): "
    ).strip()
    fields = (
        tuple(f.strip() for f in fields_text.split(","))
        if fields_text
        else ("name", "email", "address", "phone_num", "birth_date", "category", "notes", "tags")
    )
    # Exact match restricts results to equality (case-insensitive); otherwise substring match.
    exact_ans = input("Exact match? [y/N]: ").strip().lower() in {"y", "yes"}
    try:
        results = rolodex.search_contacts(q, fields=fields, exact=exact_ans)
        print_contacts(results)
    except Exception as e:
        print("Search failed:", e)


def action_list(rolodex: Rolodex) -> None:
    """List all contacts with optional sort field and order."""
    print("\nAll Contacts")
    sort_by = input("Sort by [name/email/birth_date/category] (default name): ").strip().lower() or "name"
    reverse = input("Reverse order? [y/N]: ").strip().lower() in {"y", "yes"}
    try:
        items = rolodex.list_contacts(sort_by=sort_by, reverse=reverse)
        print_contacts(items)
    except Exception as e:
        print("Invalid sort option:", e)


def action_list_category(rolodex: Rolodex) -> None:
    """List contacts in a specific category."""
    print("\nContacts by Category")
    category = prompt_nonempty("Category: ")
    print_contacts(rolodex.list_by_category(category))


def action_birthdays(rolodex: Rolodex) -> None:
    """Show upcoming birthdays."""
    print("\nUpcoming Birthdays")
    days_text = input("Days ahead (default 30): ").strip()
    try:
        days = int(days_text) if days_text else 30
        results = rolodex.upcoming_birthdays(days=days)
    except Exception as e:
        print("Could not calculate birthdays:", e)
        return

    if not results:
        print("No upcoming birthdays found.")
        return
    for contact, remaining in results:
        label = "today" if remaining == 0 else f"in {remaining} day(s)"
        print(f"{contact.name} <{contact.email}>: {contact.birth_date} ({label})")


def action_duplicates(rolodex: Rolodex) -> None:
    """Show duplicate candidate groups."""
    print("\nPossible Duplicates")
    groups = rolodex.find_possible_duplicates()
    if not groups:
        print("No duplicate candidates found.")
        return
    for idx, group in enumerate(groups, 1):
        print(f"\nGroup {idx}")
        print_contacts(group)


def action_import_csv(rolodex: Rolodex) -> None:
    """Import contacts from CSV."""
    print("\nImport Contacts")
    path = prompt_nonempty("Import CSV file path: ")
    merge = input("Merge into current contacts? [Y/n]: ").strip().lower() not in {"n", "no"}
    try:
        result = rolodex.import_contacts(path, merge=merge)
        print(f"Imported {result['imported']} contact(s); skipped {result['skipped']}.")
        for error in result["errors"][:5]:
            print(" -", error)
        if len(result["errors"]) > 5:
            print(f" - ...and {len(result['errors']) - 5} more")
    except Exception as e:
        print("Import failed:", e)


def action_export_csv(rolodex: Rolodex) -> None:
    """Export contacts to CSV."""
    print("\nExport Contacts")
    path = prompt_nonempty("Export CSV file path: ")
    try:
        count = rolodex.export_contacts(path, file_format="csv")
        print(f"Exported {count} contact(s) to {path}.")
    except Exception as e:
        print("Export failed:", e)


def action_statistics(rolodex: Rolodex) -> None:
    """Print Rolodex summary statistics."""
    stats = rolodex.get_statistics()
    print("\nRolodex Statistics")
    print(f"Total Contacts: {stats['total_contacts']}")
    print(f"Contacts with Birthdays: {stats['contacts_with_birthdays']}")
    print(f"Missing Email: {stats['missing_email']}")
    print(f"Missing Phone Number: {stats['missing_phone_number']}")
    print(f"Birthdays This Month: {stats['birthdays_this_month']}")
    print(f"Favorite Contacts: {stats['favorite_contacts']}")
    print("\nCategories:")
    for category, count in stats["categories"].items():
        print(f"{category}: {count}")


def action_favorites(rolodex: Rolodex) -> None:
    """List favorite contacts."""
    print("\nFavorite Contacts")
    print_contacts(rolodex.list_favorites())


def run_cli() -> None:
    """Run the legacy command-line interface."""
    # Construct the application layer with the chosen JSON file for persistence.
    rx = Rolodex(CONTACTS_FILE)
    # Static menu text; kept as a single string for simple printing.
    menu = (
        "\n--- DIGITAL ROLODEX ---\n"
        "1. Add Contact\n"
        "2. View Contact\n"
        "3. Edit Contact\n"
        "4. Delete Contact\n"
        "5. Search Contacts\n"
        "6. List All Contacts\n"
        "7. List Contacts by Category\n"
        "8. Upcoming Birthdays\n"
        "9. Export Contacts to CSV\n"
        "10. Import Contacts from CSV\n"
        "11. Find Possible Duplicates\n"
        "12. View Statistics\n"
        "13. List Favorite Contacts\n"
        "14. Exit\n"
    )

    # Map menu choices to their corresponding handler functions.
    actions = {
        "1": action_add,
        "2": action_view,
        "3": action_edit,
        "4": action_delete,
        "5": action_search,
        "6": action_list,
        "7": action_list_category,
        "8": action_birthdays,
        "9": action_export_csv,
        "10": action_import_csv,
        "11": action_duplicates,
        "12": action_statistics,
        "13": action_favorites,
    }

    while True:
        print(menu)
        choice = input("Select an option: ").strip()
        # Option 14 exits the loop and ends the program.
        if choice == "14":
            print("Goodbye!")
            break
        # Look up the action by user choice and invoke it if valid.
        action = actions.get(choice)
        if action:
            action(rx)
        else:
            print("Invalid choice. Please select 1-14.")


def main() -> None:
    """Entry point: launch GUI by default, or CLI with --cli."""
    parser = argparse.ArgumentParser(description="Digital Rolodex")
    parser.add_argument("--cli", action="store_true", help="run the command-line interface")
    parser.add_argument("--gui", action="store_true", help="run the Tkinter GUI (default)")
    args = parser.parse_args()

    if args.cli:
        run_cli()
        return

    from gui import run_gui

    run_gui(CONTACTS_FILE)


if __name__ == "__main__":
    main()
