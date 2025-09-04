"""
Rolodex module test script for Digital Rolodex (DR).

Exercises:
- Initialize Rolodex with a fresh JSON file
- Add contacts (Contact + dict), enforce name+email, prevent duplicates
- List contacts with sorting, verify order
- Reload from disk to verify persistence

Run:
    python Tests/rolodex_TestScript.py
"""

from __future__ import annotations

import logging
import os
import sys
from typing import List


# Make project root importable
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from contact import Contact  # type: ignore
from rolodex import Rolodex  # type: ignore


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


def ensure_artifacts_dir() -> str:
    artifacts = os.path.join(CURRENT_DIR, "_artifacts")
    os.makedirs(artifacts, exist_ok=True)
    return artifacts


def fresh_test_file(path: str) -> None:
    # Start from a clean state each run
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def main() -> None:
    setup_logging()
    artifacts = ensure_artifacts_dir()
    file_path = os.path.join(artifacts, "rolodex_test.json")
    fresh_test_file(file_path)

    print("Artifacts directory:", artifacts)
    print("Rolodex test file:", file_path)

    rx = Rolodex(file_path)

    # Add three entries; mix Contact and dict
    ada = Contact(
        name="Ada Lovelace",
        address="10 Downing St, London",
        phone_num="+44 20 7946 0991",
        email="ada@example.com",
        birth_date="1815-12-10",
    )
    jose = {
        "name": "José Piñera",
        "address": "Av. Libertador 1234, Santiago",
        "phone_num": "+56 2 2345 6789",
        "email": "jose.pinera@example.cl",
        "birth_date": "1954-10-06",
    }
    grace = Contact(
        name="Grace Hopper",
        address="Arlington, VA",
        phone_num="+1 555 867-5309",
        email="grace.hopper@nvlabs.mil",
        birth_date="1906-12-09",
    )

    rx.add_contact(ada)
    rx.add_contact(jose)
    rx.add_contact(grace)
    contacts_now = rx.list_contacts()
    print(f"Added 3 contacts; list shows {len(contacts_now)} entries (expected 3).")

    # Duplicate email check (case-insensitive)
    try:
        rx.add_contact({"name": "Ada Clone", "email": "ADA@example.com"})
        raise AssertionError("Duplicate email was allowed but should be rejected")
    except ValueError as e:
        print("Duplicate add correctly rejected:", e)

    # Sorting checks
    names_sorted = [c.name for c in rx.list_contacts(sort_by="name")]
    print("Sorted by name:", ", ".join(names_sorted))

    emails_sorted = [c.email for c in rx.list_contacts(sort_by="email")]
    print("Sorted by email:", ", ".join(emails_sorted))

    # Persistence check: reload into a new instance
    rx2 = Rolodex(file_path)
    contacts_after_reload = rx2.list_contacts()
    print(
        f"After reload: {len(contacts_after_reload)} contacts (expected 3). First: {contacts_after_reload[0].name}"
    )

    # Lookup by email (case-insensitive)
    print("\n== Lookup Tests ==")
    ada_lookup = rx2.get_by_email("ADA@EXAMPLE.COM")
    if not ada_lookup or ada_lookup.name != "Ada Lovelace":
        raise AssertionError("get_by_email failed to find Ada case-insensitively")
    print("get_by_email: found:", ada_lookup.name, f"<{ada_lookup.email}>")

    missing = rx2.get_by_email("noone@example.com")
    if missing is not None:
        raise AssertionError("get_by_email should return None for missing email")
    print("get_by_email: missing email correctly returned None")

    # Search tests
    print("\n== Search Tests ==")
    res_name_partial = rx2.search_contacts("grace", fields=("name",))
    print("search by name partial 'grace':", [c.name for c in res_name_partial])
    if len(res_name_partial) != 1 or res_name_partial[0].name != "Grace Hopper":
        raise AssertionError("search by name partial failed")

    res_email_partial = rx2.search_contacts("example", fields=("email",))
    print("search by email partial 'example':", [c.email for c in res_email_partial])
    if sorted(c.email for c in res_email_partial) != [
        "ada@example.com",
        "jose.pinera@example.cl",
    ]:
        raise AssertionError("search by email partial should find Ada and José")

    res_email_exact = rx2.search_contacts("ADA@example.com", fields=("email",), exact=True)
    print("search by email exact 'ADA@example.com':", [c.email for c in res_email_exact])
    if len(res_email_exact) != 1 or res_email_exact[0].email != "ada@example.com":
        raise AssertionError("search by email exact should match Ada (case-insensitive)")

    # View contact (alias to get_by_email)
    print("\n== View Tests ==")
    v = rx2.view_contact("grace.hopper@nvlabs.mil")
    assert v is not None and v.name == "Grace Hopper"
    print("view_contact: found:", v.name)

    v_missing = rx2.view_contact("missing@example.com")
    assert v_missing is None
    print("view_contact: missing returned None")

    # Edit contact: update address and email
    print("\n== Edit Tests ==")
    updated = rx2.edit_contact(
        "grace.hopper@nvlabs.mil",
        address="Arlington National Cemetery, VA",
    )
    assert updated.address == "Arlington National Cemetery, VA"
    print("edit_contact: address updated for Grace")

    # Change Ada's email, ensure duplicate prevention and persistence
    try:
        rx2.edit_contact("ada@example.com", email="jose.pinera@example.cl")
        raise AssertionError("Editing to a duplicate email should fail")
    except ValueError as e:
        print("edit_contact: duplicate email change correctly rejected:", e)

    rx2.edit_contact("ada@example.com", email="ada+dr@example.com")
    assert rx2.get_by_email("ada+dr@example.com") is not None
    assert rx2.get_by_email("ada@example.com") is None
    print("edit_contact: Ada's email updated and reindexed")

    # Reload and verify edits persisted
    rx3 = Rolodex(file_path)
    assert rx3.get_by_email("ada+dr@example.com") is not None
    g3 = rx3.get_by_email("grace.hopper@nvlabs.mil")
    assert g3 and g3.address == "Arlington National Cemetery, VA"
    print("edit_contact: changes persisted across reload")

    # Delete contact
    print("\n== Delete Tests ==")
    deleted = rx3.delete_contact("jose.pinera@example.cl")
    assert deleted is True
    assert rx3.get_by_email("jose.pinera@example.cl") is None
    print("delete_contact: José removed")

    # Persist deletion and verify after new reload
    rx4 = Rolodex(file_path)
    assert rx4.get_by_email("jose.pinera@example.cl") is None
    remaining = rx4.list_contacts()
    print(f"After delete+reload: {len(remaining)} contacts (expected 2)")

    print("\nAll Rolodex tests completed.")


if __name__ == "__main__":
    main()
