# Digital-Rolodex
I'm building a **Digital Rolodex (DR)** to help keep track of my personal and professional contacts. This exercise is to further familiarize myself with Python in a utilitarian manner. Normally, I would have to rely on social media or some external entity to keep track of when someone's birthday is. But with this DR, I will be able to see upcoming birthdays.
<br>
I am following programming best practices in this project.
<br>
<br>
<br>
<br>

## ✅ FEATURE SET

**Core Features**
- Add a new contact
- View a contact
- Edit a contact
- Delete a contact
- Search for contacts (by name or email, etc.)
- List all contacts

**Optional Advanced Features**
- Sort contacts (alphabetically, by birthday, etc.)
- Export/import contacts (CSV, JSON)
- Reminder for upcoming birthdays
- Duplicate detection
- Tagging/categorization
<br>
<br>
<br>

## 📦 DATA MODEL
**Contact Fields:**
|Field|	Data Type|
|-------|------|
|Name	|String|
|Address|String|
|Phone Number|	String|
|Email|	String|
|Date of Birth|	Date (YYYY-MM-DD)|
<br>
<br>
<br>

## 🗃️ STORAGE OPTIONS
1. **Local File-Based Storage**
- JSON – good for structured storage and human-readability
- CSV – simple but more limited (harder to store nested data like tags)
- Pickle – fast but not human-readable
- SQLite – lightweight database, if querying or sorting becomes complex

2. **Cloud/External Database (optional, later stage)**
- Not needed initially, but could be integrated later (e.g., Firebase, SQLite via web)
<br>
<br>
<br>

## 🧱 PROGRAM STRUCTURE (Modular Design)
**Modules (Python Files or Classes)**
|Title| Purpose|Complete|
|-----|--------|--------|
|main.py|entry point and UI handling| <center>  </center> |
|contact.py|defines Contact class| <center> ✔ </center> |
|storage.py|handles saving/loading contacts from file (JSON or DB)| <center> ✔ </center> |
|utils.py|for helper functions (input validation, formatting)| <center>  </center> |
|rolodex.py|core logic (add/edit/delete/search contacts)| <center> ✔ </center> |
<br>
<br>
<br>

## 🧪 FUNCTIONAL REQUIREMENTS

**Each of these will be functions:**
- add_contact()
- view_contact(name)
- edit_contact(name)
- delete_contact(name)
- search_contacts(query)
- list_contacts()
- save_contacts() and load_contacts()
<br>
<br>
<br>

## ✅ NON-FUNCTIONAL REQUIREMENTS / BEST PRACTICES
- *Modularity* – Break code into small, reusable functions
- *Separation of Concerns* – UI logic separate from business logic and storage
- *Validation* – Ensure phone numbers, emails, and DOB are correctly formatted
- *Error Handling* – Gracefully catch errors (e.g., file not found, invalid input)
- *Documentation* – Docstrings and comments
- *Version Control* – GitHub repository for tracking changes
<br>
<br>
<br>

## 🔐 DATA VALIDATION RULES
- Email must contain @ and a domain
- Phone number should be in consistent format ( e.g., (123) 456-7890 or 123-456-7890 )
- Date of Birth must be in ISO format (YYYY-MM-DD)
- Storage requires name + email on load; missing required fields are skipped with a warning.
- Emails are unique across contacts (case-insensitive); duplicates are rejected when adding or editing.
<br>
<br>
<br>

## 🎨 USER INTERFACE (Initial Plan)
**CLI-Based Menu Example:**

--- DIGITAL ROLODEX ---
1. Add new contact
2. View contact
3. Edit contact
4. Delete contact
5. Search contacts
6. List all contacts
7. Exit
8. Select an option

## 🧫 TEST SCRIPTS

**Tests/storage_TestScript.py:**
- Purpose: Exercises the storage layer (`storage.py`).
- Covers: UTF-8 JSON save/load round-trip, mixed inputs (Contact + dict), per-item robustness (skips malformed records), soft warnings for incomplete records, stricter policy (requires name + email), corrupt JSON handling, and atomic writes (no leftover `.tmp`).
- Outcome: Current behavior passes. Warnings are emitted for incomplete or invalid inputs; corrupt files return an empty list without crashing.

**Tests/rolodex_TestScript.py:**
- Purpose: Exercises the Rolodex layer (`rolodex.py`).
- Covers: Adding contacts (Contact + dict), unique email enforcement, sorted listing, case-insensitive lookup by email, partial/exact search across fields, editing (field updates, duplicate email rejection, validation), deleting, and persistence across reloads.
- Outcome: Current behavior passes. All operations are validated and persisted; duplicates are correctly rejected.

## 📝 RECENT CHANGES

- storage.py
  - Switched to UTF-8 with `ensure_ascii=False`; ensures parent directories exist.
  - Robust per-item loading with logging; skips malformed entries without failing all.
  - Atomic writes via temp file + `os.replace`; no leftover `.tmp` files.
  - Replaced prints with `logging`; callers configure verbosity (e.g., in `main.py`).
- contact.py
  - `from_dict` now lenient: only requires `name`; other fields via `dict.get(...)`.
  - Added `Contact.is_minimally_complete()` for soft completeness checks.
- rolodex.py
  - Added `Rolodex` class with `add_contact`, `list_contacts`, `get_by_email`, `search_contacts`, `view_contact`, `edit_contact`, and `delete_contact`.
  - Enforces unique emails (case-insensitive) and validates email/DOB on edits.
- Tests
  - Added `Tests/storage_TestScript.py` and `Tests/rolodex_TestScript.py` covering the above behaviors.
