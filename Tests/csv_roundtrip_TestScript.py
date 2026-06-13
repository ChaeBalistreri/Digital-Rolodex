"""CSV round-trip test for Digital Rolodex import/export.

This script:
- Creates 5 dummy contacts with every field populated
- Exports those contacts to CSV
- Deletes all contacts from the test Rolodex
- Imports the exported CSV
- Verifies the imported contacts match the originals

It uses Tests/_artifacts so production contacts.json is not touched.

Run:
    python Tests/csv_roundtrip_TestScript.py
"""

from __future__ import annotations

import os
import sys
import csv


CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from contact import Contact
from rolodex import Rolodex


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
            name="Alex Rivera",
            address="100 Maple Ave, Austin, TX 78701",
            phone_num="555-100-1000",
            email="alex.rivera@example.com",
            birth_date="1990-01-15",
            tags="friend, gym",
        ),
        Contact(
            name="Blair Chen",
            address="200 Oak St, Dallas, TX 75201",
            phone_num="555-200-2000",
            email="blair.chen@example.com",
            birth_date="1988-02-20",
            tags="work, vendor",
        ),
        Contact(
            name="Casey Morgan",
            address="300 Pine Rd, Houston, TX 77002",
            phone_num="555-300-3000",
            email="casey.morgan@example.com",
            birth_date="1995-03-25",
            tags="family, emergency",
        ),
        Contact(
            name="Drew Patel",
            address="400 Cedar Blvd, San Antonio, TX 78205",
            phone_num="555-400-4000",
            email="drew.patel@example.com",
            birth_date="1992-04-30",
            tags="client, finance",
        ),
        Contact(
            name="Emery Brooks",
            address="500 Birch Ln, Fort Worth, TX 76102",
            phone_num="555-500-5000",
            email="emery.brooks@example.com",
            birth_date="1985-05-05",
            tags="friend, school",
        ),
    ]


def snapshot(rx: Rolodex) -> list[dict]:
    return [contact.to_dict() for contact in rx.list_contacts(sort_by="email")]


def main() -> None:
    artifacts = ensure_artifacts_dir()
    data_file = os.path.join(artifacts, "csv_roundtrip_contacts.json")
    csv_file = os.path.join(artifacts, "csv_roundtrip_export.csv")
    for path in (data_file, csv_file):
        remove_if_exists(path)

    rx = Rolodex(data_file)
    for contact in dummy_contacts():
        rx.add_contact(contact)

    original = snapshot(rx)
    assert len(original) == 5
    print("Created 5 dummy contacts with all fields populated.")

    exported_count = rx.export_contacts(csv_file)
    assert exported_count == 5
    assert os.path.exists(csv_file)
    with open(csv_file, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_columns = {
            "name",
            "address",
            "phone_num",
            "email",
            "birth_date",
            "category",
            "notes",
            "favorite",
        }
        assert expected_columns.issubset(set(reader.fieldnames or []))
    print(f"Exported {exported_count} contacts to CSV.")

    for contact in list(rx.list_contacts()):
        assert rx.delete_contact(contact.email)
    assert rx.list_contacts() == []
    print("Deleted all contacts from the test Rolodex.")

    import_result = rx.import_contacts(csv_file, merge=False)
    assert import_result["imported"] == 5
    assert import_result["skipped"] == 0
    print("Imported exported CSV back into the test Rolodex.")

    imported = snapshot(rx)
    assert imported == original
    print("CSV round-trip verified: imported contacts match original contacts.")


if __name__ == "__main__":
    main()
