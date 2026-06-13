"""Import format detection regression tests.

Protects the case where a JSON export is saved with a .csv extension. The
Rolodex importer should detect the JSON contents and import it successfully.

Run:
    python Tests/import_format_detection_TestScript.py
"""

from __future__ import annotations

import json
import os
import sys


CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from rolodex import Rolodex


def ensure_artifacts_dir() -> str:
    artifacts = os.path.join(CURRENT_DIR, "_artifacts")
    os.makedirs(artifacts, exist_ok=True)
    return artifacts


def remove_if_exists(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def main() -> None:
    artifacts = ensure_artifacts_dir()
    mislabeled_import = os.path.join(artifacts, "mislabeled_json_export.csv")
    rolodex_file = os.path.join(artifacts, "format_detection_contacts.json")

    for path in (mislabeled_import, rolodex_file):
        remove_if_exists(path)

    contact_rows = [
        {
            "name": "Format Probe",
            "address": "101 Test Way, Austin, TX 78701",
            "phone_num": "555-010-1000",
            "email": "format.probe@example.com",
            "birth_date": "1991-06-12",
            "tags": ["regression", "import"],
        }
    ]
    with open(mislabeled_import, "w", encoding="utf-8") as handle:
        json.dump(contact_rows, handle, indent=4)

    rx = Rolodex(rolodex_file)
    result = rx.import_contacts(mislabeled_import, merge=False)

    assert result == {"imported": 1, "skipped": 0, "errors": []}
    imported = rx.get_by_email("format.probe@example.com")
    assert imported is not None
    assert imported.name == "Format Probe"
    assert imported.tags == ["import", "regression"]

    print("Import format detection regression test passed.")


if __name__ == "__main__":
    main()
