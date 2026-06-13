"""GUI helper tests that do not open Tkinter windows.

Run:
    python Tests/gui_helpers_TestScript.py
"""

from __future__ import annotations

import os
import sys


CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from gui import (
    display_to_iso_date,
    format_birthday_for_entry,
    format_phone_for_entry,
    iso_to_display_date,
    load_custom_categories,
    save_custom_categories,
)


def ensure_artifacts_dir() -> str:
    artifacts = os.path.join(CURRENT_DIR, "_artifacts")
    os.makedirs(artifacts, exist_ok=True)
    return artifacts


def main() -> None:
    print("== GUI Helper Tests ==")

    assert format_phone_for_entry("8175551234") == "(817) 555-1234"
    assert format_phone_for_entry("817-555-1234") == "(817) 555-1234"
    assert format_phone_for_entry("(817) 555-1234") == "(817) 555-1234"
    assert format_phone_for_entry("817.555.1234") == "(817) 555-1234"
    assert format_phone_for_entry("+44 20 7946 0991") == "+44 20 7946 0991"
    print("Phone entry formatting passed")

    assert iso_to_display_date("2026-06-12") == "06/12/2026"
    assert format_birthday_for_entry("01012000") == "01/01/2000"
    assert format_birthday_for_entry("01/01/2000") == "01/01/2000"
    assert format_birthday_for_entry("0101") == "01/01"
    assert format_birthday_for_entry("06202000") == "06/20/2000"
    assert display_to_iso_date("06/12/2026") == "2026-06-12"
    assert display_to_iso_date("20/06/2026") == "2026-06-20"
    assert display_to_iso_date("06/20/2000") == "2000-06-20"
    assert display_to_iso_date("2026-06-12") == "2026-06-12"
    assert display_to_iso_date("") is None
    print("Birthday display conversion passed")

    categories_file = os.path.join(ensure_artifacts_dir(), "gui_categories_test.json")
    if os.path.exists(categories_file):
        os.remove(categories_file)
    save_custom_categories(["Friends", "Alumni", "Friends"], file_path=categories_file)
    assert load_custom_categories(file_path=categories_file) == ["Alumni", "Friends"]
    print("Category persistence helpers passed")

    print("All GUI helper tests completed.")


if __name__ == "__main__":
    main()
