"""Feature-plan coverage for Digital Rolodex.

Exercises plan items that are not fully covered by the legacy scripts:
- Phone normalization
- Categories and category filtering
- Notes persistence and search
- Favorite contacts
- Possible duplicate detection
- Statistics
- Backward-compatible loading of old records

Run:
    python Tests/feature_plan_TestScript.py
"""

from __future__ import annotations

from datetime import date
import json
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


def main() -> None:
    artifacts = ensure_artifacts_dir()
    data_file = os.path.join(artifacts, "feature_plan_contacts.json")
    fresh(data_file)

    rx = Rolodex(data_file)
    john = rx.add_contact(
        Contact(
            name="John Smith",
            address="1 Main St, Fort Worth, TX 76102",
            phone_num="8175551234",
            email="john@example.com",
            birth_date="1990-12-30",
            tags="golf, friend",
            category="Friends",
            notes="Likes golf.",
            favorite=True,
        )
    )
    assert john.phone_num == "(817) 555-1234"

    jane = rx.add_contact(
        Contact(
            name="Jane Smith",
            address="2 Main St, Fort Worth, TX 76102",
            phone_num="(817) 555-1234",
            email="jane@example.com",
            birth_date="1988-01-02",
            category="Family",
            notes="Emergency contact.",
            favorite=False,
        )
    )
    assert jane.phone_num == "(817) 555-1234"
    print("Phone normalization passed")

    friends = rx.list_by_category("friends")
    assert [c.email for c in friends] == ["john@example.com"]
    print("Category filtering passed")

    notes_results = rx.search_contacts("golf", fields=("notes",))
    assert len(notes_results) == 1 and notes_results[0].email == "john@example.com"
    print("Notes search passed")

    favorites = rx.list_favorites()
    assert len(favorites) == 1 and favorites[0].email == "john@example.com"
    rx.edit_contact("john@example.com", favorite="no")
    assert rx.list_favorites() == []
    rx.edit_contact("john@example.com", favorite="yes")
    print("Favorite mark/unmark passed")

    duplicates = rx.find_possible_duplicates()
    assert any(sorted(c.email for c in group) == ["jane@example.com", "john@example.com"] for group in duplicates)
    print("Possible duplicate detection passed")

    stats = rx.get_statistics(today=date(2026, 12, 1))
    assert stats["total_contacts"] == 2
    assert stats["contacts_with_birthdays"] == 2
    assert stats["missing_email"] == 0
    assert stats["missing_phone_number"] == 0
    assert stats["birthdays_this_month"] == 1
    assert stats["categories"] == {"Family": 1, "Friends": 1}
    assert stats["favorite_contacts"] == 1
    print("Statistics passed")

    reloaded = Rolodex(data_file)
    persisted = reloaded.get_by_email("john@example.com")
    assert persisted is not None
    assert persisted.category == "Friends"
    assert persisted.notes == "Likes golf."
    assert persisted.favorite is True
    print("New fields persisted across reload")

    old_data_file = os.path.join(artifacts, "old_contact_compat.json")
    with open(old_data_file, "w", encoding="utf-8") as handle:
        json.dump(
            [
                {
                    "name": "Legacy Contact",
                    "address": "3 Old Rd",
                    "phone_num": "817.555.9999",
                    "email": "legacy@example.com",
                    "birth_date": "1970-07-04",
                }
            ],
            handle,
            indent=4,
        )
    old_rx = Rolodex(old_data_file)
    legacy = old_rx.get_by_email("legacy@example.com")
    assert legacy is not None
    assert legacy.category is None
    assert legacy.notes is None
    assert legacy.favorite is False
    assert legacy.phone_num == "(817) 555-9999"
    print("Backward-compatible loading passed")

    print("All feature-plan tests completed.")


if __name__ == "__main__":
    main()
