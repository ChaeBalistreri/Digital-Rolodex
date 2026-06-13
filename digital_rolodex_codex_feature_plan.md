# Digital Rolodex — Codex Implementation Plan

## Project Context

This project is a Python-based Digital Rolodex used to store and manage personal and professional contacts. The current repository already includes a `Contact` model, JSON-based persistence, a `Rolodex` core logic class, validation, duplicate email enforcement, and test scripts for storage and Rolodex behavior.

The next development phase should focus on improving usability, completing the CLI layer, and adding practical features that fit the current project scope without overcomplicating the architecture.

---

## Implementation Priority

Implement the following features in this order:

1. Complete `main.py` command-line interface
2. Add upcoming birthday report
3. Add phone number validation and normalization
4. Add contact categories
5. Add CSV import/export
6. Add optional notes field
7. Add possible duplicate detection beyond email
8. Add basic contact statistics
9. Add optional favorite contacts

Avoid adding SQLite, GUI, cloud sync, authentication, encryption, or web functionality at this stage.

---

# 1. Complete `main.py` CLI

## Goal

Create a functional command-line interface that allows users to interact with the Digital Rolodex without manually running test scripts or calling class methods directly.

## Target File

- `main.py`

## Required Menu

The CLI should display a menu similar to:

```text
--- DIGITAL ROLODEX ---
1. Add Contact
2. View Contact
3. Edit Contact
4. Delete Contact
5. Search Contacts
6. List All Contacts
7. Upcoming Birthdays
8. Exit
```

## Functional Requirements

- Load contacts from the configured JSON file at startup.
- Save changes after add, edit, or delete operations.
- Continue running until the user selects Exit.
- Handle invalid menu choices gracefully.
- Use existing `Rolodex` methods where possible instead of duplicating logic.
- Keep UI logic in `main.py`; do not place business logic in `main.py`.

## Suggested Behavior

- Add Contact: prompt for name, address, phone, email, and birth date.
- View Contact: allow lookup by email or name.
- Edit Contact: allow user to update one or more fields.
- Delete Contact: confirm before deleting.
- Search Contacts: search across available contact fields.
- List All Contacts: print contacts in sorted order.
- Upcoming Birthdays: call the birthday report feature described below.

## Acceptance Criteria

- Running `python main.py` starts the program.
- User can add, view, edit, delete, search, and list contacts through the menu.
- Changes persist after exiting and restarting the program.
- Invalid input does not crash the program.

---

# 2. Upcoming Birthday Report

## Goal

Add a feature that shows contacts with birthdays occurring within a user-defined number of days, defaulting to 30 days.

## Target Files

- `rolodex.py`
- `main.py`
- Tests may be added under `Tests/`

## Suggested Method

Add a method to the `Rolodex` class:

```python
def upcoming_birthdays(self, days=30):
    """Return contacts with birthdays occurring within the next given number of days."""
```

## Functional Requirements

- Use `datetime` for date calculations.
- Ignore contacts without a valid birth date.
- Correctly handle birthdays that cross into the next calendar year.
- Return results sorted by soonest birthday.
- Include the number of days until each birthday.

## Suggested Return Format

Return a list of dictionaries or tuples, for example:

```python
[
    {
        "contact": contact,
        "birthday": "2026-06-18",
        "days_until": 6
    }
]
```

## CLI Output Example

```text
Upcoming Birthdays — Next 30 Days

John Smith - June 18 - 6 days away
Sarah Johnson - June 25 - 13 days away
```

## Acceptance Criteria

- Birthdays within the next 30 days are displayed.
- Birthdays outside the selected window are not displayed.
- Year-end rollover is handled correctly.
- Contacts with missing or invalid birthdays are skipped safely.

---

# 3. Phone Number Validation and Normalization

## Goal

Add validation for phone numbers and normalize accepted phone numbers into one consistent display/storage format.

## Target Files

- `contact.py`
- `rolodex.py`
- `main.py`
- Tests under `Tests/`

## Accepted Input Examples

The program should accept common U.S. phone number formats:

```text
8175551234
817-555-1234
(817) 555-1234
817.555.1234
```

## Normalized Output Format

Store or display valid phone numbers as:

```text
(817) 555-1234
```

## Suggested Contact Methods

Add static methods to `Contact`:

```python
@staticmethod
def is_valid_phone(phone_num):
    """Return True if phone number is valid or empty/None."""

@staticmethod
def normalize_phone(phone_num):
    """Return phone number in standardized format."""
```

## Functional Requirements

- Phone number should remain optional.
- Empty or `None` phone number should be allowed.
- Invalid phone numbers should be rejected when adding or editing contacts.
- Phone numbers should be normalized before saving.

## Acceptance Criteria

- Valid phone formats are accepted.
- Invalid phone formats are rejected.
- Saved phone numbers use a consistent format.
- Existing contacts without phone numbers remain valid.

---

# 4. Contact Categories

## Goal

Allow each contact to be assigned a simple category such as Family, Friends, Work, School, Veteran, or Other.

## Target Files

- `contact.py`
- `rolodex.py`
- `main.py`
- `storage.py`, only if needed for serialization compatibility
- Tests under `Tests/`

## Data Model Change

Add an optional field to `Contact`:

```python
category=None
```

## Functional Requirements

- Category should be optional.
- Existing JSON contacts without a category should still load successfully.
- Users should be able to set or edit the category.
- Users should be able to list or search contacts by category.

## Suggested Rolodex Method

```python
def list_by_category(self, category):
    """Return contacts matching the specified category."""
```

## Acceptance Criteria

- Contacts can be assigned categories.
- Contacts can be filtered by category.
- Existing saved contacts remain compatible.

---

# 5. CSV Import and Export

## Goal

Allow contacts to be exported to and imported from CSV files for backup, spreadsheet use, and migration.

## Target Files

- `storage.py` or a new `csv_storage.py`
- `main.py`
- Tests under `Tests/`

## Recommended Approach

Either add CSV-specific functions to `storage.py` or create a separate module named `csv_storage.py` to preserve separation of concerns.

## Suggested Functions

```python
def export_contacts_to_csv(file_path, contacts):
    """Export contacts to a CSV file."""


def import_contacts_from_csv(file_path):
    """Import contacts from a CSV file and return Contact objects."""
```

## Required CSV Columns

```text
name,address,phone_num,email,birth_date,category,notes,favorite
```

Optional fields may be blank.

## Functional Requirements

- Export all contacts to a CSV file.
- Import contacts from a CSV file.
- Skip malformed rows with a warning instead of crashing.
- Prevent duplicate emails during import.
- Preserve Unicode characters.

## Acceptance Criteria

- Contacts export successfully to CSV.
- Exported CSV can be opened in a spreadsheet application.
- CSV import creates valid contacts.
- Duplicate email handling remains consistent with existing Rolodex behavior.

---

# 6. Optional Notes Field

## Goal

Add a free-text notes field for practical information about a contact.

## Target Files

- `contact.py`
- `rolodex.py`
- `main.py`
- Tests under `Tests/`

## Data Model Change

Add:

```python
notes=None
```

## Example Notes

```text
Met through Oncor.
Likes golf.
Married to Susan.
```

## Functional Requirements

- Notes should be optional.
- Existing JSON contacts without notes should still load.
- Notes should be included in `to_dict()` and `from_dict()`.
- Search should include notes if practical.

## Acceptance Criteria

- Notes can be added and edited.
- Notes persist after saving and reloading.
- Existing contacts remain compatible.

---

# 7. Possible Duplicate Detection Beyond Email

## Goal

Add a non-destructive duplicate detection feature that flags possible duplicate contacts based on similar names or matching phone numbers.

## Target File

- `rolodex.py`
- `main.py`
- Tests under `Tests/`

## Important Design Constraint

Do not automatically delete or merge duplicates. Only report possible duplicates.

## Suggested Method

```python
def find_possible_duplicates(self):
    """Return groups of contacts that may represent the same person."""
```

## Matching Rules

Flag possible duplicates when:

- Emails match, case-insensitive. This should already be prevented but can be reported if found in imported data.
- Normalized phone numbers match.
- Names are exactly equal, case-insensitive.
- Optionally, names are very similar using simple string comparison.

Avoid complex fuzzy matching libraries for now.

## CLI Output Example

```text
Possible Duplicates:

Group 1:
- John Smith | john@email.com | (817) 555-1234
- John Smith | john.smith@email.com | (817) 555-1234
```

## Acceptance Criteria

- Duplicate report identifies likely duplicates.
- No contacts are deleted or modified automatically.
- Feature works even if some contacts are missing email or phone number.

---

# 8. Contact Statistics

## Goal

Add a simple report showing useful Rolodex summary statistics.

## Target Files

- `rolodex.py`
- `main.py`

## Suggested Method

```python
def get_statistics(self):
    """Return summary statistics about the Rolodex."""
```

## Suggested Statistics

- Total number of contacts
- Number of contacts with birthdays
- Number of contacts missing email
- Number of contacts missing phone number
- Number of contacts by category
- Number of birthdays this month

## CLI Output Example

```text
Rolodex Statistics

Total Contacts: 137
Contacts with Birthdays: 93
Missing Email: 12
Missing Phone Number: 18
Birthdays This Month: 9

Categories:
Family: 18
Friends: 52
Work: 31
Other: 36
```

## Acceptance Criteria

- Statistics display without modifying contacts.
- Missing optional fields are handled safely.
- Category counts work even when category is missing.

---

# 9. Favorite Contacts

## Goal

Allow users to mark frequently used contacts as favorites.

## Target Files

- `contact.py`
- `rolodex.py`
- `main.py`

## Data Model Change

Add:

```python
favorite=False
```

## Suggested Rolodex Method

```python
def list_favorites(self):
    """Return contacts marked as favorites."""
```

## Functional Requirements

- Favorite should default to `False`.
- Users should be able to mark or unmark a contact as favorite.
- Users should be able to list favorite contacts.
- Existing contacts without the field should load with `favorite=False`.

## Acceptance Criteria

- Favorite status persists after saving and reloading.
- Favorites can be listed separately.
- Existing data remains compatible.

---

# Testing Requirements

For every new feature, add or update tests under the `Tests/` directory.

## Recommended Test Coverage

### CLI

Manual testing is acceptable initially, but keep CLI logic thin so core behavior remains testable through `Rolodex` methods.

### Birthday Report

Test:

- Birthday today
- Birthday tomorrow
- Birthday within 30 days
- Birthday outside 30 days
- Birthday across year boundary
- Missing birthday
- Invalid birthday

### Phone Validation

Test:

- Accepted phone formats
- Invalid phone formats
- Normalized output
- Empty phone value

### Categories

Test:

- Add category
- Edit category
- Filter by category
- Load old contacts without category

### CSV Import/Export

Test:

- Export produces expected columns
- Import creates contacts
- Malformed rows are skipped
- Duplicate emails are handled correctly
- Unicode data is preserved

### Notes

Test:

- Add notes
- Edit notes
- Persist notes
- Search notes, if implemented

### Duplicate Detection

Test:

- Matching phone number
- Matching name
- Different contacts not flagged
- Missing fields handled safely

### Statistics

Test:

- Correct total contact count
- Missing field counts
- Category counts
- Birthday counts

### Favorites

Test:

- Default favorite value is False
- Mark favorite
- Unmark favorite
- List favorites
- Persist favorite status

---

# Backward Compatibility Requirements

Because the project already has saved JSON behavior, new fields must be optional and backward-compatible.

When adding fields such as `category`, `notes`, or `favorite`:

- Update `Contact.__init__()` with default values.
- Update `Contact.to_dict()` to include the new fields.
- Update `Contact.from_dict()` using `dict.get()` so older saved contacts still load.

Example:

```python
category=data.get("category")
notes=data.get("notes")
favorite=data.get("favorite", False)
```

Do not require old JSON files to be manually edited.

---

# Design Guidelines

Follow these principles throughout implementation:

- Keep `contact.py` focused on the `Contact` data model and validation helpers.
- Keep `storage.py` focused on reading and writing files.
- Keep `rolodex.py` focused on business logic.
- Keep `main.py` focused on CLI interaction only.
- Avoid duplicating validation logic across modules.
- Prefer small, testable functions.
- Preserve existing tests.
- Do not break existing public methods unless necessary.
- Use logging for recoverable storage/import warnings.
- Use exceptions for invalid operations in core logic.
- Keep user-facing error handling in `main.py`.

---

# Suggested Final Menu After All Features

```text
--- DIGITAL ROLODEX ---
1. Add Contact
2. View Contact
3. Edit Contact
4. Delete Contact
5. Search Contacts
6. List All Contacts
7. List Contacts by Category
8. Upcoming Birthdays
9. Export Contacts to CSV
10. Import Contacts from CSV
11. Find Possible Duplicates
12. View Statistics
13. List Favorite Contacts
14. Exit
```

---

# Out of Scope for Now

Do not implement the following yet:

- SQLite database
- GUI using Tkinter, PyQt, or web framework
- Cloud sync
- User accounts
- Password protection
- Encryption
- Automated email or text birthday reminders
- External API integrations

These can be considered later after the CLI version is complete, tested, and stable.
