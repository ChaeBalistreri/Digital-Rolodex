"""CSV round-trip test for custom categories.

This script:
- Creates 5 custom categories
- Creates 5 dummy contacts using those categories
- Exports the contacts to CSV
- Deletes all contacts and clears the saved category list
- Imports the CSV
- Verifies contacts and custom categories are restored from imported data

Run:
    python Tests/custom_categories_csv_TestScript.py
"""

from __future__ import annotations

import csv
import os
import sys


CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from contact import Contact
from gui import categories_from_contacts, load_custom_categories, save_custom_categories
from rolodex import Rolodex


CUSTOM_CATEGORIES = ["Alumni", "Contractors", "Mentors", "Neighbors", "Volunteers"]


def ensure_artifacts_dir() -> str:
    artifacts = os.path.join(CURRENT_DIR, "_artifacts")
    os.makedirs(artifacts, exist_ok=True)
    return artifacts


def remove_if_exists(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def dummy_contacts() -> list[Contact]:
    return [
        Contact(
            name="Avery Alumni",
            address="101 Alumni Way, Austin, TX 78701",
            phone_num="8175551001",
            email="avery.alumni@example.com",
            birth_date="1991-01-01",
            category="Alumni",
            notes="Custom category test contact 1.",
            favorite=True,
        ),
        Contact(
            name="Casey Contractor",
            address="202 Contractor Rd, Dallas, TX 75201",
            phone_num="8175551002",
            email="casey.contractor@example.com",
            birth_date="1992-02-02",
            category="Contractors",
            notes="Custom category test contact 2.",
            favorite=False,
        ),
        Contact(
            name="Morgan Mentor",
            address="303 Mentor St, Houston, TX 77002",
            phone_num="8175551003",
            email="morgan.mentor@example.com",
            birth_date="1993-03-03",
            category="Mentors",
            notes="Custom category test contact 3.",
            favorite=True,
        ),
        Contact(
            name="Nico Neighbor",
            address="404 Neighbor Ln, San Antonio, TX 78205",
            phone_num="8175551004",
            email="nico.neighbor@example.com",
            birth_date="1994-04-04",
            category="Neighbors",
            notes="Custom category test contact 4.",
            favorite=False,
        ),
        Contact(
            name="Val Volunteer",
            address="505 Volunteer Blvd, Fort Worth, TX 76102",
            phone_num="8175551005",
            email="val.volunteer@example.com",
            birth_date="1995-05-05",
            category="Volunteers",
            notes="Custom category test contact 5.",
            favorite=True,
        ),
    ]


def snapshot_by_email(rx: Rolodex) -> dict[str, dict]:
    return {contact.email: contact.to_dict() for contact in rx.list_contacts(sort_by="email")}


def main() -> None:
    artifacts = ensure_artifacts_dir()
    data_file = os.path.join(artifacts, "custom_categories_contacts.json")
    csv_file = os.path.join(artifacts, "custom_categories_export.csv")
    categories_file = os.path.join(artifacts, "custom_categories.json")
    for path in (data_file, csv_file, categories_file):
        remove_if_exists(path)

    save_custom_categories(CUSTOM_CATEGORIES, file_path=categories_file)
    assert load_custom_categories(file_path=categories_file) == CUSTOM_CATEGORIES
    print("Created 5 custom categories.")

    rx = Rolodex(data_file)
    for contact in dummy_contacts():
        rx.add_contact(contact)
    original = snapshot_by_email(rx)
    assert len(original) == 5
    assert categories_from_contacts(rx.list_contacts()) == CUSTOM_CATEGORIES
    print("Created 5 dummy contacts using custom categories.")

    exported_count = rx.export_contacts(csv_file, file_format="csv")
    assert exported_count == 5
    with open(csv_file, "r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert sorted(row["category"] for row in rows) == CUSTOM_CATEGORIES
    print("Exported contacts with custom category values.")

    for contact in list(rx.list_contacts()):
        assert rx.delete_contact(contact.email)
    save_custom_categories([], file_path=categories_file)
    assert rx.list_contacts() == []
    assert load_custom_categories(file_path=categories_file) == []
    print("Deleted all contacts and cleared saved custom categories.")

    import_result = rx.import_contacts(csv_file, merge=False)
    assert import_result == {"imported": 5, "skipped": 0, "errors": []}
    imported = snapshot_by_email(rx)
    assert imported == original

    restored_categories = categories_from_contacts(rx.list_contacts())
    save_custom_categories(restored_categories, file_path=categories_file)
    assert load_custom_categories(file_path=categories_file) == CUSTOM_CATEGORIES
    print("Imported CSV restored contacts and custom category choices.")

    print("Custom category CSV round-trip verified.")


if __name__ == "__main__":
    main()
