# Digital Rolodex GUI Implementation Plan for Codex

## Objective

Convert the existing Digital Rolodex program from a CLI-first interface into a simple, user-friendly desktop GUI while preserving the existing backend architecture.

The GUI should tie into the current program functionality instead of duplicating business logic. Existing modules such as `contact.py`, `storage.py`, and `rolodex.py` should remain the source of truth for contact validation, persistence, searching, editing, deleting, and birthday-related logic.

---

## Recommended GUI Framework

Use **Tkinter**.

### Reasoning

- Tkinter is included with the Python standard library.
- No external dependency is required.
- It is sufficient for forms, buttons, menus, list boxes, dialogs, and simple table-like displays.
- It keeps the project beginner-friendly and aligned with the current learning goals.

Avoid PyQt, PySide, Kivy, or web frameworks for now unless explicitly requested later.

---

## High-Level Design

The GUI should consist of one main application window with three primary regions:

1. **Left panel:** searchable contact list
2. **Right panel:** selected contact details and edit form
3. **Bottom status panel:** upcoming birthday reminder summary

The GUI should be simple, practical, and easy to extend.

---

## Proposed Window Layout

```text
+-------------------------------------------------------------+
| Digital Rolodex                                             |
+-----------------------------+-------------------------------+
| Search: [______________]    | Name:        [_____________]   |
| Sort:   [Name ▼]            | Address:     [_____________]   |
| Category: [All ▼]           | Phone:       [_____________]   |
|                             | Email:       [_____________]   |
| Contacts                    | Birthday:    [YYYY-MM-DD___]   |
| -------------------------   | Category:    [_____________]   |
| John Smith                  | Favorite:    [ ]               |
| Sarah Johnson               | Notes:                       |
| Maria Garcia                | [__________________________]   |
|                             |                               |
| [Add] [Delete]              | [Edit] [Save] [Cancel]         |
+-----------------------------+-------------------------------+
| Upcoming Birthdays: Sarah Johnson in 6 days                 |
+-------------------------------------------------------------+
```

---

## Recommended File Changes

### Add

```text
gui.py
```

This file should contain the Tkinter GUI implementation.

### Modify

```text
main.py
```

Update `main.py` so it launches the GUI by default.

Example:

```python
from gui import run_gui

if __name__ == "__main__":
    run_gui()
```

Optional future enhancement:

```text
python main.py --gui
python main.py --cli
```

Do not remove CLI functionality if it already exists and can be preserved cleanly.

---

## Architecture Requirements

The GUI must not directly manage JSON file operations unless absolutely necessary.

Preferred dependency flow:

```text
gui.py -> rolodex.py -> storage.py -> contacts.json
       -> contact.py
```

The GUI should call existing backend methods such as:

```python
rolodex.add_contact(...)
rolodex.edit_contact(...)
rolodex.delete_contact(...)
rolodex.search_contacts(...)
rolodex.list_contacts(...)
rolodex.view_contact(...)
```

If the exact method names differ, inspect `rolodex.py` and call the existing equivalent methods.

Do not duplicate validation logic inside the GUI. The GUI may perform lightweight input checks for usability, but final validation should remain in the existing backend classes and functions.

---

## Main GUI Components

## 1. Main Application Window

Create a main Tkinter window titled:

```text
Digital Rolodex
```

Suggested default size:

```text
900x600
```

Minimum useful size:

```text
750x500
```

The app should be resizable.

---

## 2. Left Panel: Contact Browser

The left panel should contain:

- Search input field
- Sort dropdown
- Category filter dropdown, if category support exists
- Scrollable contact list
- Add button
- Delete button

### Search Box

The search field should filter contacts as the user types or after pressing Enter.

Search should use the existing `search_contacts()` backend method if available.

Search should support matching by at least:

- Name
- Email
- Phone number
- Address
- Category, if implemented
- Notes, if implemented

### Contact List

Use a Tkinter `Listbox` or `ttk.Treeview`.

Recommended: `ttk.Treeview`, because it can later support columns such as name, email, phone, and birthday.

Minimum acceptable display:

```text
Name
```

Better display:

```text
Name | Email | Phone
```

Selecting a contact should populate the right-side detail panel.

### Sort Dropdown

Include a dropdown with at least:

```text
Name
Birthday
Category
```

If category support is not implemented yet, disable or omit the category option.

Sorting by name should be the default.

### Category Filter

If category support exists, include:

```text
All
Family
Friends
Work
School
Other
```

If categories do not exist yet, structure the GUI so this can be added later without major refactoring.

---

## 3. Right Panel: Contact Detail Form

The right panel should show the selected contact’s information.

Fields:

```text
Name
Address
Phone Number
Email
Date of Birth
Category
Favorite
Notes
```

Only include `Category`, `Favorite`, and `Notes` if they exist in the data model. If they do not exist yet, either omit them or implement them as part of the broader feature roadmap.

### Field Behavior

Default state should be read-only.

The user should not accidentally edit fields just by clicking around.

Recommended workflow:

1. User selects a contact.
2. Contact details populate in read-only mode.
3. User clicks `Edit`.
4. Fields become editable.
5. User clicks `Save` to persist changes.
6. User clicks `Cancel` to discard changes.

### Buttons

Right panel buttons:

```text
Edit
Save
Cancel
```

Button behavior:

- `Edit`: enables form fields.
- `Save`: validates and persists changes through the backend.
- `Cancel`: discards unsaved changes and reloads the selected contact.

---

## 4. Add Contact Dialog

Use a modal dialog for adding a new contact.

Recommended fields:

```text
Name:          [____________]
Address:       [____________]
Phone:         [____________]
Email:         [____________]
Birth Date:    [YYYY-MM-DD__]
Category:      [____________]
Favorite:      [ ]
Notes:         [____________]

[Save] [Cancel]
```

### Add Contact Requirements

- Name is required.
- Other fields are optional unless the existing backend currently requires them.
- Email must be validated if provided.
- Date of birth must be validated if provided.
- Phone number should be validated if phone validation already exists.
- Duplicate email should be rejected if the backend enforces unique emails.

On successful save:

1. Add the contact using the backend.
2. Refresh the contact list.
3. Select the newly added contact if practical.
4. Show a brief success message or status update.

On failure:

- Show a Tkinter error dialog using `messagebox.showerror()`.
- Do not crash the program.

---

## 5. Delete Contact Confirmation

When the user clicks `Delete`, show a confirmation dialog.

Example:

```text
Delete John Smith?

This action cannot be undone.

[Delete] [Cancel]
```

Use `messagebox.askyesno()` or equivalent.

Only delete after confirmation.

After deletion:

1. Call the backend delete method.
2. Refresh the contact list.
3. Clear the detail panel.
4. Show a short status message.

---

## 6. Birthday Reminder Area

Add a bottom status panel showing upcoming birthdays.

Example:

```text
Upcoming Birthdays: Sarah Johnson in 6 days | John Smith in 12 days
```

If no upcoming birthdays exist:

```text
No birthdays in the next 30 days.
```

Include a button or menu item:

```text
View Upcoming Birthdays
```

This should open a separate birthday reminder window.

---

## 7. Birthday Reminder Window

Create a popup window showing upcoming birthdays in a simple table.

Example:

```text
Upcoming Birthdays - Next 30 Days

Name              Birthday       Days Away
Sarah Johnson     June 18        6
John Smith        June 25        13
```

Recommended controls:

```text
Show birthdays within: [30] days
[Refresh]
[Close]
```

The list should be sorted by soonest upcoming birthday.

Important: birthdays should be calculated using month/day, not birth year alone. The program should handle birthdays that occur in the next calendar year.

Example:

If today is December 20 and someone’s birthday is January 5, that should appear as 16 days away.

---

## 8. Menu Bar

Add a simple menu bar.

Recommended menus:

```text
File
  Export CSV
  Import CSV
  Exit

Contacts
  Add Contact
  Edit Selected Contact
  Delete Selected Contact
  Refresh List

Birthdays
  View Upcoming Birthdays

Help
  About
```

Only implement menu items for functionality that already exists or is part of the current Codex task.

If CSV import/export is not implemented yet, disable those menu items or leave TODO comments.

---

## 9. Status Bar

Add a small status bar at the bottom of the main window.

Example messages:

```text
Loaded 25 contacts.
Contact saved.
Contact deleted.
Search returned 4 contacts.
Invalid email address.
```

The status bar should help reduce unnecessary popup dialogs for normal actions.

Use popup dialogs only for:

- Errors
- Confirmations
- Important warnings

---

## Validation and Error Handling

All backend validation errors should be caught by the GUI and shown in a user-friendly way.

Example:

```python
try:
    self.rolodex.add_contact(contact)
except ValueError as error:
    messagebox.showerror("Invalid Contact", str(error))
```

The GUI should handle:

- Missing required name
- Invalid email format
- Invalid date format
- Invalid phone format, if implemented
- Duplicate email
- File read/write errors
- Empty contact list
- No selected contact when pressing Edit or Delete

The GUI should not print errors to the terminal as the primary user feedback method.

---

## Data Model Compatibility

The current data model may not yet include all desired GUI fields.

### Required Fields

The GUI must support:

```text
name
address
phone_num
email
birth_date
```

### Optional Future Fields

The GUI should be designed so these can be added cleanly:

```text
category
favorite
notes
```

If implementing these fields now, update:

- `Contact.__init__`
- `Contact.to_dict()`
- `Contact.from_dict()`
- Any validation logic
- Existing tests
- README documentation

Do not break backward compatibility with existing JSON data. Existing contacts without these new keys should still load successfully.

Use `dict.get()` in `from_dict()` for optional fields.

---

## Backend Integration Rules

### Do

- Use the existing `Rolodex` class if available.
- Use existing storage functions indirectly through the Rolodex layer.
- Refresh the GUI after add, edit, or delete operations.
- Keep GUI state synchronized with backend state.
- Keep UI logic in `gui.py`.

### Do Not

- Do not duplicate JSON read/write logic in `gui.py`.
- Do not duplicate contact validation rules in `gui.py` except for small user-experience checks.
- Do not bypass `Rolodex` methods to mutate the contact list directly unless no backend method exists.
- Do not remove existing tests.
- Do not remove CLI functionality unless specifically instructed.

---

## Suggested Class Structure for `gui.py`

```python
class DigitalRolodexApp:
    def __init__(self, root):
        self.root = root
        self.rolodex = Rolodex(...)
        self.selected_contact = None
        self._build_ui()
        self._load_contacts()
        self._refresh_contact_list()
        self._refresh_birthday_summary()
```

Recommended methods:

```python
_build_ui()
_build_menu()
_build_left_panel()
_build_detail_panel()
_build_status_bar()
_load_contacts()
_refresh_contact_list()
_refresh_detail_panel(contact)
_clear_detail_panel()
_set_detail_fields_editable(is_editable)
_on_contact_selected(event)
_on_search_changed(event=None)
_on_sort_changed(event=None)
_on_add_contact()
_on_edit_contact()
_on_save_contact()
_on_cancel_edit()
_on_delete_contact()
_on_view_birthdays()
_refresh_birthday_summary()
_set_status(message)
```

Entry point function:

```python
def run_gui():
    root = tk.Tk()
    app = DigitalRolodexApp(root)
    root.mainloop()
```

---

## Suggested Widget Choices

Use:

```python
import tkinter as tk
from tkinter import ttk, messagebox
```

Recommended widgets:

| Purpose | Widget |
|---|---|
| Main window | `tk.Tk` |
| Panels | `ttk.Frame` |
| Contact list | `ttk.Treeview` or `tk.Listbox` |
| Text input | `ttk.Entry` |
| Multiline notes | `tk.Text` |
| Dropdowns | `ttk.Combobox` |
| Buttons | `ttk.Button` |
| Checkboxes | `ttk.Checkbutton` |
| Dialogs | `messagebox` or custom `tk.Toplevel` |
| Birthday popup | `tk.Toplevel` |

Prefer `ttk` widgets where possible for a cleaner native look.

---

## Acceptance Criteria

The GUI implementation is complete when:

1. Running `python main.py` launches the GUI.
2. The user can view all contacts in a scrollable list.
3. Selecting a contact displays full details.
4. The user can add a contact through a dialog.
5. The user can edit an existing contact.
6. The user can cancel an edit without saving changes.
7. The user can delete a contact after confirmation.
8. The user can search contacts.
9. The user can sort contacts by name.
10. The GUI displays upcoming birthdays.
11. The user can open a birthday reminder window.
12. Changes persist after closing and reopening the app.
13. Validation errors are shown in GUI dialogs, not as uncaught exceptions.
14. Existing backend tests continue to pass.
15. Existing CLI code is preserved if practical.

---

## Testing Recommendations

### Manual GUI Test Checklist

Test the following manually:

- Launch app.
- Add contact with name only.
- Add contact with all fields.
- Attempt to add invalid email.
- Attempt to add invalid birth date.
- Attempt to add duplicate email.
- Select contact and verify details populate.
- Edit contact and save.
- Edit contact and cancel.
- Delete contact and confirm.
- Attempt delete with no selected contact.
- Search by name.
- Search by email.
- Sort by name.
- Open upcoming birthdays window.
- Close and reopen app; confirm data persisted.

### Automated Testing

Do not over-focus on automated GUI testing yet.

Keep existing backend tests as the primary automated test suite.

If adding new backend birthday functions, add backend tests for:

- Birthday later this month
- Birthday next month
- Birthday across year boundary
- Missing birth date
- Invalid birth date
- Sorting by soonest birthday

---

## Implementation Priority

### Phase 1: Basic GUI Shell

- Create `gui.py`.
- Launch main window.
- Load contacts.
- Display contacts in list.
- Select contact and show details.

### Phase 2: CRUD Integration

- Add contact dialog.
- Edit selected contact.
- Save changes.
- Cancel edits.
- Delete contact with confirmation.

### Phase 3: Search and Sort

- Search box.
- Sort dropdown.
- Refresh list behavior.

### Phase 4: Birthday Reminder UI

- Bottom birthday summary.
- Birthday reminder popup window.

### Phase 5: Polish

- Status bar messages.
- Menu bar.
- Cleaner error handling.
- README update.

---

## README Update Required

After implementation, update `README.md` with:

- GUI launch instructions
- Screenshot placeholder or description
- Explanation that the CLI has been supplemented or replaced by a GUI
- Updated feature checklist
- Any new dependencies, if any

If Tkinter is used, note that it is included with most standard Python installations.

---

## Final Instruction to Codex

Implement the GUI incrementally and preserve the existing backend design. The goal is not to rewrite the Digital Rolodex. The goal is to provide a more user-friendly interface that calls the existing Rolodex, Contact, and storage functionality.

Prioritize correctness, maintainability, and simple user experience over visual complexity.
