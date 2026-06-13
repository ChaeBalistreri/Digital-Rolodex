# Digital Rolodex

Digital Rolodex (DR) is a local contact manager for personal and professional contacts. It now launches as a Tkinter desktop app by default, while preserving the original CLI for terminal workflows. It stores contacts locally, supports practical validation, and helps surface information that is usually scattered across social media or external tools, such as upcoming birthdays.

Run the GUI:

```bash
python main.py
```

Run the preserved CLI:

```bash
python main.py --cli
```

Dependencies:

- Tkinter is used for the desktop GUI and is included with most standard Python installations.
- No third-party packages are required.

Run the test scripts:

```bash
python Tests/storage_TestScript.py
python Tests/rolodex_TestScript.py
python Tests/utils_TestScript.py
python Tests/advanced_features_TestScript.py
python Tests/csv_roundtrip_TestScript.py
python Tests/custom_categories_csv_TestScript.py
python Tests/import_format_detection_TestScript.py
python Tests/feature_plan_TestScript.py
python Tests/gui_helpers_TestScript.py
python Tests/cli_TestScript.py
```

## Feature Set

### Core Features

| Feature | Status |
| --- | --- |
| Add a new contact | Complete |
| View a contact by email | Complete |
| Edit a contact | Complete |
| Delete a contact | Complete |
| Search contacts by selected fields | Complete |
| List all contacts | Complete |

### Advanced Features

| Feature | Status |
| --- | --- |
| Sort contacts by name, email, or birthday | Complete |
| Export contacts to JSON or CSV | Complete |
| Import contacts from JSON or CSV | Complete |
| Upcoming birthday reminders | Complete |
| Duplicate candidate detection | Complete |
| Tagging/categorization | Complete |
| Phone number normalization | Complete |
| Optional notes | Complete |
| Favorite contacts | Complete |
| Contact statistics | Complete |
| Tkinter desktop GUI | Complete |

## Data Model

| Field | Data Type | Notes |
| --- | --- | --- |
| Name | String | Required |
| Address | String | Optional |
| Phone Number | String | Optional, validated when present |
| Email | String | Required and unique across contacts |
| Date of Birth | Date string | Optional, `YYYY-MM-DD` |
| Category | String | Optional |
| Notes | String | Optional free text |
| Favorite | Boolean | Optional, defaults to `False` |
| Tags | List of strings | Optional, normalized to lowercase unique tags |

## Storage

The app uses local JSON storage by default:

- Runtime data is stored in `contacts.json`.
- GUI-managed category choices are stored in `categories.json`.
- Save operations use UTF-8 and atomic replacement.
- Loading is defensive: malformed records are skipped with warnings.
- Imports and exports support `.json` and `.csv`.
- CSV import/export preserves contact category values; GUI imports also add imported contact categories to the managed category list.

SQLite or cloud storage could be added later, but local JSON is sufficient for the current CLI product.

## Program Structure

| File | Purpose | Status |
| --- | --- | --- |
| `main.py` | App entry point; GUI by default, CLI via `--cli` | Complete |
| `gui.py` | Tkinter desktop GUI | Complete |
| `contact.py` | `Contact` data model | Complete |
| `storage.py` | JSON save/load persistence | Complete |
| `utils.py` | Shared validation, tag, and birthday helpers | Complete |
| `rolodex.py` | Core add/edit/delete/search/import/export logic | Complete |

## Untracked File Inventory

These files and directories are currently present in the working tree but are not yet tracked by Git:

| Path | Description |
| --- | --- |
| `Addy.csv` | Root-level exported contact file from earlier manual Rolodex testing. |
| `TestData/` | Test-data directory for larger/manual import datasets. Currently includes `TestData/Addy.csv`, a generated 100-contact CSV for large-list import/search/sort testing. |
| `Tests/advanced_features_TestScript.py` | Script covering tags, birthday reminders, duplicate detection, JSON/CSV import/export, and merge duplicate behavior. |
| `Tests/cli_TestScript.py` | Non-interactive smoke test for the preserved CLI path via `python main.py --cli`. |
| `Tests/csv_roundtrip_TestScript.py` | CSV export/delete/import round-trip test using 5 complete dummy contacts. |
| `Tests/custom_categories_csv_TestScript.py` | CSV round-trip test for 5 custom categories and 5 contacts assigned to those categories. |
| `Tests/feature_plan_TestScript.py` | Coverage for feature-plan items such as phone normalization, categories, notes, favorites, duplicate detection, statistics, and backward-compatible loading. |
| `Tests/gui_helpers_TestScript.py` | Non-window GUI helper test for phone formatting, birthday conversion/formatting, and category persistence helpers. |
| `Tests/import_format_detection_TestScript.py` | Regression test for importing JSON content saved with a `.csv` extension. |
| `Tests/utils_TestScript.py` | Utility helper tests for email/phone/date validation, tag normalization, and birthday calculations. |
| `categories.json` | Runtime GUI category choices saved by Manage Categories. |
| `digital_rolodex_codex_feature_plan.md` | CLI/backend feature implementation plan used during development. |
| `digital_rolodex_gui_codex_plan.md` | Tkinter GUI implementation plan used during development. |
| `gui.py` | Tkinter desktop GUI implementation. |
| `utils.py` | Shared helper module for validation, formatting, birthday calculations, tag normalization, and boolean parsing. |

## GUI

Running `python main.py` opens the desktop app.

The GUI includes:

- Searchable, sortable contact browser.
- Category filter.
- Manage Categories window for adding or deleting category choices.
- Read-only detail view with explicit Edit, Save, and Cancel workflow.
- Add Contact dialog with live U.S. phone formatting and live `DD/MM/YYYY` birthday formatting.
- Delete confirmation.
- CSV import/export menu items.
- Upcoming birthday summary and birthday popup window.
- Status bar for normal action feedback.

Screenshot placeholder: main window with contact browser on the left, detail form on the right, and upcoming birthday/status panel at the bottom.

## CLI Menu

Run with `python main.py --cli`.

```text
--- DIGITAL ROLODEX ---
1. Add new contact
2. View contact
3. Edit contact
4. Delete contact
5. Search contacts
6. List all contacts
7. List contacts by category
8. Upcoming birthdays
9. Export contacts to CSV
10. Import contacts from CSV
11. Find possible duplicates
12. View statistics
13. List favorite contacts
14. Exit
```

## Validation Rules

- Name and email are required when adding, importing, or loading contacts.
- Email must match a basic `local@domain.tld` format.
- Emails are unique case-insensitively.
- U.S. phone numbers may be blank or use common formats such as `8175551234`, `817-555-1234`, `(817) 555-1234`, or `817.555.1234`; accepted U.S. numbers are normalized to `(817) 555-1234`.
- Date of birth may be blank or must be `YYYY-MM-DD`.
- The GUI displays and accepts birthdays as `DD/MM/YYYY`, then converts to backend `YYYY-MM-DD` storage.
- Category, notes, and favorite are optional and backward-compatible with older saved contacts.
- Tags can be entered as comma-separated text and are normalized.
- Invalid imported records are skipped and reported in the import summary.

## Test Scripts

### `Tests/storage_TestScript.py`

Purpose: exercises the storage layer.

Covers: UTF-8 JSON save/load round-trip, mixed inputs (`Contact` + `dict`), per-item robustness, soft warnings for incomplete records, required name/email policy, corrupt JSON handling, and atomic writes.

### `Tests/rolodex_TestScript.py`

Purpose: exercises core Rolodex operations.

Covers: adding contacts, duplicate email enforcement, sorted listing, lookup, partial/exact search, viewing, editing, deleting, and persistence across reloads.

### `Tests/utils_TestScript.py`

Purpose: verifies shared helper behavior.

Covers: email validation, phone validation, ISO date validation, tag normalization, and birthday countdown calculation.

### `Tests/advanced_features_TestScript.py`

Purpose: exercises the completed advanced feature set.

Covers: tags, tag search, upcoming birthdays, duplicate candidate detection, JSON export/import, CSV export/import, and duplicate skipping during merge imports.

### `Tests/cli_TestScript.py`

Purpose: smoke-tests the actual CLI menu loop.

Covers: scripted add, list, search, and export through `main.py` without touching production `contacts.json`.

### `Tests/csv_roundtrip_TestScript.py`

Purpose: verifies CSV export/import works as an end-to-end workflow.

Covers: creating 5 complete dummy contacts, exporting them to CSV, deleting all contacts from the test Rolodex, importing the CSV, and confirming imported data matches the original data.

### `Tests/custom_categories_csv_TestScript.py`

Purpose: verifies CSV export/import preserves custom categories.

Covers: creating 5 custom categories, creating 5 contacts assigned to those categories, exporting to CSV, deleting contacts and clearing saved category choices, importing the CSV, and confirming contacts plus category choices are restored.

### `Tests/import_format_detection_TestScript.py`

Purpose: protects import behavior when a file extension and file contents disagree.

Covers: JSON contact data saved with a `.csv` extension, import content detection, tag preservation, and successful import without skipped rows.

### `Tests/feature_plan_TestScript.py`

Purpose: verifies the additional feature-plan items.

Covers: phone normalization, categories, category filtering, notes persistence/search, favorite mark/unmark, possible duplicate detection, statistics, and backward-compatible loading of older saved contacts.

### `Tests/gui_helpers_TestScript.py`

Purpose: verifies GUI helper behavior without opening Tkinter windows.

Covers: live phone-entry formatting, `YYYY-MM-DD` to `DD/MM/YYYY` birthday conversion, `DD/MM/YYYY` to backend date conversion, and category list persistence helpers.

## Recent Changes

### 2026-06-12 Completion Pass

- Added `utils.py` for validation, tag normalization, optional string cleanup, ISO date parsing, and birthday countdowns.
- Rebuilt `contact.py` as a cleaner data model with tag support and centralized validation helpers.
- Expanded `rolodex.py` with phone/date validation, tag search, duplicate candidate detection, upcoming birthday reminders, JSON/CSV import, and JSON/CSV export.
- Expanded `main.py` into a complete CLI for all core and advanced project features.
- Hardened `storage.py` so loaded contacts must pass email, phone, and birth-date validation.
- Added comprehensive test scripts for utilities, advanced features, and CLI behavior.
- Verified all scripts and module compilation successfully.

### 2026-06-12 CSV Import Fix

- Fixed import format detection so a file with a `.csv` extension but JSON contents, such as `Addy.csv`, imports based on its actual contents instead of being misread as CSV rows.
- Added `Tests/csv_roundtrip_TestScript.py` for the requested 5-contact CSV export/delete/import verification workflow.
- Fixed a stray leading character in `main.py` that prevented the CLI from compiling.

### 2026-06-12 Full Verification Pass

- Ran the full application test suite and module compilation successfully.
- Added `Tests/import_format_detection_TestScript.py` to lock in the `Addy.csv` regression behavior.
- Confirmed CLI smoke behavior, storage robustness, Rolodex core operations, advanced features, CSV round-trip import/export, and import format detection.

### 2026-06-12 Feature Plan Implementation

- Implemented the final planned CLI menu with category listing, CSV import/export, possible duplicate report, statistics, and favorite contact listing.
- Added `category`, `notes`, and `favorite` to the `Contact` model with backward-compatible JSON loading.
- Added U.S. phone number normalization while preserving existing valid international phone data.
- Added `Rolodex.list_by_category`, `find_possible_duplicates`, `get_statistics`, and `list_favorites`.
- Expanded CSV export/import columns to include `category`, `notes`, and `favorite`, with tags retained as an extra supported column.
- Added `Tests/feature_plan_TestScript.py` and expanded CSV round-trip checks for the required CSV columns.

### 2026-06-12 GUI Implementation

- Added `gui.py` with a Tkinter desktop interface backed by the existing `Rolodex`, `Contact`, and storage layers.
- Changed `python main.py` to launch the GUI by default.
- Preserved the terminal interface with `python main.py --cli`.
- Added GUI contact browsing, search, sort, category filtering, add/edit/delete workflows, CSV import/export menu items, birthday summary, birthday popup, and status bar.
- Updated the CLI smoke test to use `--cli`.

### 2026-06-12 GUI Add Dialog and Category Management

- Updated the Add Contact dialog so the phone field formats U.S. phone numbers as `(817) 555-1234` while typing.
- Renamed the Add Contact date label to `Birthday` and made GUI birthday entry/display use `DD/MM/YYYY`.
- Added live birthday entry formatting so typing `01012000` becomes `01/01/2000`.
- Added a centered `Manage Categories` control below the category filter.
- Added a Manage Categories window for adding and deleting saved category choices.
- Added `Tests/gui_helpers_TestScript.py` for GUI formatting and category persistence helpers.

### 2026-06-12 Custom Category Import/Export

- Confirmed CSV export/import preserves custom category values assigned to contacts.
- Updated GUI import so imported contact categories are merged into the managed category list and persisted to `categories.json`.
- Added `Tests/custom_categories_csv_TestScript.py` covering 5 custom categories and 5 contacts through export, delete/clear, import, and restore verification.

### 2026-06-13 GUI Edit Form Formatting Fix

- Fixed edit-form phone formatting so the cursor returns to the end after live formatting, preventing digits from being reordered while typing.
- Added live birthday formatting to the edit form so values like `06202000` display as `06-20-2000`.

### 2026-06-13 Main Window Birthday Format Update

- Updated all GUI birthday fields to display and accept forward-slash dates.
- Kept backend storage in `YYYY-MM-DD` and expanded GUI conversion helpers so slash dates like `06/20/2000` save correctly.

## Verification Log

Last verified on 2026-06-12:

```bash
python -m py_compile main.py gui.py contact.py rolodex.py storage.py utils.py
python Tests/storage_TestScript.py
python Tests/rolodex_TestScript.py
python Tests/utils_TestScript.py
python Tests/advanced_features_TestScript.py
python Tests/csv_roundtrip_TestScript.py
python Tests/custom_categories_csv_TestScript.py
python Tests/import_format_detection_TestScript.py
python Tests/feature_plan_TestScript.py
python Tests/gui_helpers_TestScript.py
python Tests/cli_TestScript.py
```

All commands passed.
