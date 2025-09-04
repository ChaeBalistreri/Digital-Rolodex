"""
Storage module test script for Digital Rolodex (DR).

What this script does:
- Verifies save/load round-trip using UTF-8 JSON
- Verifies mixed inputs to save_contacts (Contact instances + dicts)
- Verifies robustness when JSON has malformed items (skips bad entries)
- Emits soft warnings for incomplete records via Contact.is_minimally_complete()
- Enforces stricter load policy (requires name + email), skipping otherwise
- Verifies behavior on corrupt JSON (returns empty list)

Run from repo root or any directory:
    python Tests/storage_TestScript.py

The script writes artifacts under Tests/_artifacts/ so it won't touch any
production data files.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import List


# Make project root importable when running the script directly.
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from contact import Contact  # type: ignore  # Local import from project
import storage  # type: ignore


def setup_logging() -> None:
    """Configure logging to show INFO-level messages from storage module."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )
    # Optionally make storage chatter more visible during tests
    logging.getLogger(storage.__name__).setLevel(logging.INFO)


def ensure_artifacts_dir() -> str:
    """Ensure a local artifacts directory exists and return its path."""
    artifacts = os.path.join(CURRENT_DIR, "_artifacts")
    os.makedirs(artifacts, exist_ok=True)
    return artifacts


def make_sample_contacts() -> List[Contact | dict]:
    """Build a small sample list including a pre-serialized dict entry."""
    c1 = Contact(
        name="Ada Lovelace",
        address="10 Downing St, London",
        phone_num="+44 20 7946 0991",
        email="ada@example.com",
        birth_date="1815-12-10",
    )

    c2 = Contact(
        name="José Piñera",  # Non-ASCII test
        address="Av. Libertador 1234, Santiago",
        phone_num="+56 2 2345 6789",
        email="jose.pinera@example.cl",
        birth_date="1954-10-06",
    )

    # Pre-serialized dict (mixed input support)
    c3_dict = {
        "name": "Grace Hopper",
        "address": "Arlington, VA",
        "phone_num": "+1 555 867-5309",
        "email": "grace.hopper@nvlabs.mil",
        "birth_date": "1906-12-09",
    }

    return [c1, c2, c3_dict]


def test_roundtrip(file_path: str) -> None:
    print("\n== Test: Save/Load Round-Trip and Mixed Inputs ==")
    contacts_in = make_sample_contacts()

    storage.save_contacts(file_path, contacts_in)

    # Atomic write should not leave a .tmp file behind
    tmp_path = f"{file_path}.tmp"
    if os.path.exists(tmp_path):
        raise AssertionError("Temporary file left behind after atomic write.")

    contacts_out = storage.load_contacts(file_path)

    print(f"Saved {len(contacts_in)} entries; loaded {len(contacts_out)} contacts.")
    for i, c in enumerate(contacts_out, 1):
        print(f"[{i}] {c}")


def test_malformed_items(file_path: str) -> None:
    print("\n== Test: Robustness Against Malformed Items (with stricter policy) ==")

    # Start from a known-good file
    storage.save_contacts(file_path, make_sample_contacts())

    # Manually inject malformed entries
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.append(123)  # Not a dict
    data.append({"name": "Incomplete"})  # Missing fields expected by from_dict

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    contacts_out = storage.load_contacts(file_path)
    print(
        f"Loaded {len(contacts_out)} valid contacts after injecting malformed entries (expected 3 due to required email)."
    )
    # Stricter policy requires email; the 'Incomplete' record is skipped.
    if len(contacts_out) != 3:
        raise AssertionError(
            f"Expected 3 valid contacts after skipping incomplete entries, got {len(contacts_out)}"
        )
    for i, c in enumerate(contacts_out, 1):
        print(f"[{i}] {c.name} | {c.email}")


def test_corrupt_json(file_path: str) -> None:
    print("\n== Test: Corrupt JSON Handling ==")
    # Write deliberately corrupt content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("{")

    contacts_out = storage.load_contacts(file_path)
    print(f"Corrupt file -> loaded {len(contacts_out)} contacts (expected 0).")


def main() -> None:
    setup_logging()
    artifacts = ensure_artifacts_dir()

    test_file = os.path.join(artifacts, "contacts_test.json")
    print(f"Artifacts directory: {artifacts}")
    print(f"Primary test file:   {test_file}")

    # Execute tests
    test_roundtrip(test_file)
    test_malformed_items(test_file)
    test_corrupt_json(test_file)

    print("\nAll tests completed. Inspect outputs above for details.")


if __name__ == "__main__":
    main()
