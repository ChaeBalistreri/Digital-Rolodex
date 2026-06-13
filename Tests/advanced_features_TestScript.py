"""Advanced feature tests for Digital Rolodex.

Exercises:
- Tags and tag search
- Upcoming birthday reminders
- Duplicate candidate detection by name + phone
- JSON and CSV export/import

Run:
    python Tests/advanced_features_TestScript.py
"""

from __future__ import annotations

from datetime import date
import os
import sys


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


def fresh(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def seed(rx: Rolodex) -> None:
    rx.add_contact(
        Contact(
            "Ada Lovelace",
            "London",
            "+44 20 7946 0991",
            "ada@example.com",
            "1815-12-10",
            tags="friend, math, friend",
        )
    )
    rx.add_contact(
        Contact(
            "Ada Lovelace",
            "Backup address",
            "+44 20 7946 0991",
            "ada.backup@example.com",
            "1815-12-10",
            tags=["duplicate-check"],
        )
    )
    rx.add_contact(
        Contact(
            "Grace Hopper",
            "Arlington, VA",
            "+1 555 867-5309",
            "grace@example.com",
            "1906-06-20",
            tags=["work", "navy"],
        )
    )


def main() -> None:
    artifacts = ensure_artifacts_dir()
    data_file = os.path.join(artifacts, "advanced_features.json")
    fresh(data_file)

    rx = Rolodex(data_file)
    seed(rx)

    tag_results = rx.search_contacts("math", fields=("tags",))
    assert len(tag_results) == 1 and tag_results[0].email == "ada@example.com"
    assert tag_results[0].tags == ["friend", "math"]
    print("Tag search and normalization passed")

    birthdays = rx.upcoming_birthdays(days=10, today=date(2026, 6, 12))
    assert [(c.email, days) for c, days in birthdays] == [("grace@example.com", 8)]
    print("Upcoming birthday reminder passed")

    duplicates = rx.find_duplicates()
    assert len(duplicates) == 1
    assert sorted(c.email for c in duplicates[0]) == ["ada.backup@example.com", "ada@example.com"]
    print("Duplicate detection passed")

    json_export = os.path.join(artifacts, "contacts_export.json")
    csv_export = os.path.join(artifacts, "contacts_export.csv")
    assert rx.export_contacts(json_export) == 3
    assert rx.export_contacts(csv_export) == 3
    assert os.path.exists(json_export)
    assert os.path.exists(csv_export)
    print("JSON and CSV export passed")

    json_import_file = os.path.join(artifacts, "imported_from_json.json")
    fresh(json_import_file)
    rx_json = Rolodex(json_import_file)
    result_json = rx_json.import_contacts(json_export, merge=False)
    assert result_json["imported"] == 3
    assert len(rx_json.list_contacts()) == 3
    print("JSON import replace passed")

    csv_import_file = os.path.join(artifacts, "imported_from_csv.json")
    fresh(csv_import_file)
    rx_csv = Rolodex(csv_import_file)
    result_csv = rx_csv.import_contacts(csv_export, merge=False)
    assert result_csv["imported"] == 3
    assert rx_csv.get_by_email("grace@example.com") is not None
    print("CSV import replace passed")

    merge_result = rx_csv.import_contacts(csv_export, merge=True)
    assert merge_result["imported"] == 0
    assert merge_result["skipped"] == 3
    print("Merge duplicate skip passed")

    print("All advanced feature tests completed.")


if __name__ == "__main__":
    main()
