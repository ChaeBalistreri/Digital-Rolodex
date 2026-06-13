"""Tkinter desktop GUI for the Digital Rolodex."""

from __future__ import annotations

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from contact import Contact
from rolodex import Rolodex


CONTACTS_FILE = "contacts.json"
DEFAULT_CONTACT_CATEGORIES = ["Family", "Friends", "Work", "School", "Veteran", "Other"]
DEFAULT_CATEGORIES = ["All"] + DEFAULT_CONTACT_CATEGORIES
CATEGORIES_FILE = "categories.json"


def format_phone_for_entry(value: str) -> str:
    """Format partial U.S. phone digits as the user types."""
    if value.strip().startswith("+"):
        return value
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) > 10 and digits.startswith("1"):
        digits = digits[1:]
    digits = digits[:10]
    if len(digits) <= 3:
        return digits
    if len(digits) <= 6:
        return f"({digits[:3]}) {digits[3:]}"
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def iso_to_display_date(value: object) -> str:
    """Convert backend YYYY-MM-DD dates to GUI slash dates."""
    text = str(value or "").strip()
    parts = text.split("-")
    if len(parts) == 3 and all(parts):
        year, month, day = parts
        return f"{month}/{day}/{year}"
    return text


def format_birthday_for_entry(value: str, separator: str = "/") -> str:
    """Format partial birthday digits as DD/MM/YYYY or DD-MM-YYYY while typing."""
    digits = "".join(ch for ch in value if ch.isdigit())[:8]
    if len(digits) <= 2:
        return digits
    if len(digits) <= 4:
        return f"{digits[:2]}{separator}{digits[2:]}"
    return f"{digits[:2]}{separator}{digits[2:4]}{separator}{digits[4:]}"


def display_to_iso_date(value: object) -> Optional[str]:
    """Convert GUI slash dates to backend YYYY-MM-DD dates.

    The GUI displays month/day/year. For compatibility, day/month/year input is
    also accepted when it is unambiguous, such as 20/06/2000.
    """
    text = str(value or "").strip()
    if not text:
        return None
    if "-" in text and len(text.split("-")[0]) == 4:
        return text
    separator = "/" if "/" in text else "-"
    parts = text.split(separator)
    if len(parts) != 3:
        return text
    first, second, year = [part.strip() for part in parts]
    if not (first and second and year):
        return text
    first_num = int(first) if first.isdigit() else 0
    second_num = int(second) if second.isdigit() else 0
    if first_num > 12 and second_num <= 12:
        day, month = first, second
    else:
        month, day = first, second
    return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"


def load_custom_categories(file_path: str = CATEGORIES_FILE) -> list[str]:
    """Load custom GUI category choices."""
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return sorted({str(item).strip() for item in data if str(item).strip()})


def save_custom_categories(categories: list[str], file_path: str = CATEGORIES_FILE) -> None:
    """Persist custom GUI category choices."""
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(sorted(set(categories)), handle, indent=4, ensure_ascii=False)


def categories_from_contacts(contacts: list[Contact]) -> list[str]:
    """Return sorted non-empty category names from contacts."""
    return sorted({contact.category for contact in contacts if getattr(contact, "category", None)})


class DigitalRolodexApp:
    """Main Tkinter application for browsing and editing contacts."""

    def __init__(self, root: tk.Tk, contacts_file: str = CONTACTS_FILE) -> None:
        self.root = root
        self.contacts_file = contacts_file
        self.rolodex = Rolodex(contacts_file)
        self.selected_contact: Optional[Contact] = None
        self.is_editing = False
        self.custom_categories = (
            load_custom_categories()
            if os.path.exists(CATEGORIES_FILE)
            else DEFAULT_CONTACT_CATEGORIES.copy()
        )

        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="Name")
        self.sort_descending = False
        self.category_filter_var = tk.StringVar(value="All")
        self.status_var = tk.StringVar()

        self.name_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.birth_date_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.favorite_var = tk.BooleanVar(value=False)

        self.root.title("Digital Rolodex")
        self.root.geometry("900x600")
        self.root.minsize(750, 500)

        self._build_ui()
        self._set_detail_fields_editable(False)
        self._refresh_category_choices()
        self._refresh_contact_list()
        self._refresh_birthday_summary()
        self._set_status(f"Loaded {len(self.rolodex.list_contacts())} contacts.")

    def _build_ui(self) -> None:
        self._build_menu()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_pane.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.main_pane.bind("<Configure>", self._keep_contact_browser_half_width)

        self.left_panel = ttk.Frame(self.main_pane, padding=8)
        self.right_panel = ttk.Frame(self.main_pane, padding=8)
        self.main_pane.add(self.left_panel, weight=1)
        self.main_pane.add(self.right_panel, weight=1)

        self._build_left_panel()
        self._build_detail_panel()
        self._build_bottom_panel()
        self.root.after_idle(self._set_initial_pane_sizes)

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Export CSV", command=self._on_export_csv)
        file_menu.add_command(label="Import CSV", command=self._on_import_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menu_bar.add_cascade(label="File", menu=file_menu)

        contacts_menu = tk.Menu(menu_bar, tearoff=False)
        contacts_menu.add_command(label="Add Contact", command=self._on_add_contact)
        contacts_menu.add_command(label="Edit Selected Contact", command=self._on_edit_contact)
        contacts_menu.add_command(label="Delete Selected Contact", command=self._on_delete_contact)
        contacts_menu.add_command(label="Refresh List", command=self._refresh_all)
        menu_bar.add_cascade(label="Contacts", menu=contacts_menu)

        birthdays_menu = tk.Menu(menu_bar, tearoff=False)
        birthdays_menu.add_command(label="View Upcoming Birthdays", command=self._on_view_birthdays)
        menu_bar.add_cascade(label="Birthdays", menu=birthdays_menu)

        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="About", command=self._on_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def _build_left_panel(self) -> None:
        self.left_panel.columnconfigure(0, weight=1)
        self.left_panel.rowconfigure(5, weight=1)

        ttk.Label(self.left_panel, text="Search").grid(row=0, column=0, sticky="w")
        search_entry = ttk.Entry(self.left_panel, textvariable=self.search_var)
        search_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        search_entry.bind("<KeyRelease>", self._on_search_changed)
        search_entry.bind("<Return>", self._on_search_changed)

        controls = ttk.Frame(self.left_panel)
        controls.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(3, weight=1)

        ttk.Label(controls, text="Sort").grid(row=0, column=0, sticky="w", padx=(0, 4))
        sort_box = ttk.Combobox(
            controls,
            textvariable=self.sort_var,
            values=["Name", "Email", "Birthday", "Category", "Favorite"],
            state="readonly",
            width=12,
        )
        sort_box.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        sort_box.bind("<<ComboboxSelected>>", self._on_sort_changed)

        ttk.Label(controls, text="Category").grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.category_filter_box = ttk.Combobox(
            controls,
            textvariable=self.category_filter_var,
            values=DEFAULT_CATEGORIES,
            state="readonly",
            width=14,
        )
        self.category_filter_box.grid(row=0, column=3, sticky="ew")
        self.category_filter_box.bind("<<ComboboxSelected>>", self._on_category_filter_changed)

        ttk.Button(
            controls,
            text="Manage Categories",
            command=self._on_manage_categories,
        ).grid(row=1, column=2, columnspan=2, sticky="ew", pady=(6, 0))

        ttk.Label(self.left_panel, text="Contacts").grid(row=3, column=0, sticky="w")

        tree_frame = ttk.Frame(self.left_panel)
        tree_frame.grid(row=5, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("name", "email", "phone", "birthday", "category", "favorite", "address", "notes")
        self.contact_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.sortable_contact_columns = {
            "name": "Name",
            "email": "Email",
            "birthday": "Birthday",
            "category": "Category",
            "favorite": "Favorite",
        }
        self.contact_tree.heading("name", text="Name")
        self.contact_tree.heading("email", text="Email")
        self.contact_tree.heading("phone", text="Phone")
        self.contact_tree.heading("birthday", text="Birthday")
        self.contact_tree.heading("category", text="Category")
        self.contact_tree.heading("favorite", text="Favorite")
        self.contact_tree.heading("address", text="Address")
        self.contact_tree.heading("notes", text="Notes")
        self.contact_tree.column("name", width=160, minwidth=120, anchor="w", stretch=False)
        self.contact_tree.column("email", width=220, minwidth=160, anchor="w", stretch=False)
        self.contact_tree.column("phone", width=130, minwidth=110, anchor="w", stretch=False)
        self.contact_tree.column("birthday", width=110, minwidth=100, anchor="w", stretch=False)
        self.contact_tree.column("category", width=130, minwidth=100, anchor="w", stretch=False)
        self.contact_tree.column("favorite", width=80, minwidth=70, anchor="center", stretch=False)
        self.contact_tree.column("address", width=260, minwidth=180, anchor="w", stretch=False)
        self.contact_tree.column("notes", width=320, minwidth=180, anchor="w", stretch=False)
        self.contact_tree.grid(row=0, column=0, sticky="nsew")
        self.contact_tree.bind("<<TreeviewSelect>>", self._on_contact_selected)
        self.contact_tree.bind("<Double-1>", self._on_contact_heading_double_click)

        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.contact_tree.yview)
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.contact_tree.xview)
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        self.contact_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        buttons = ttk.Frame(self.left_panel)
        buttons.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(buttons, text="Add", command=self._on_add_contact).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Delete", command=self._on_delete_contact).pack(side=tk.LEFT, padx=(8, 0))

    def _build_detail_panel(self) -> None:
        self.right_panel.columnconfigure(1, weight=1)
        self.right_panel.rowconfigure(7, weight=1)

        fields = [
            ("Name", self.name_var),
            ("Address", self.address_var),
            ("Phone", self.phone_var),
            ("Email", self.email_var),
            ("Birthday", self.birth_date_var),
            ("Category", self.category_var),
        ]
        self.detail_entries: list[ttk.Entry] = []
        for row, (label, variable) in enumerate(fields):
            ttk.Label(self.right_panel, text=label).grid(row=row, column=0, sticky="w", pady=3)
            entry = ttk.Entry(self.right_panel, textvariable=variable)
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            if label == "Phone":
                self.detail_phone_entry = entry
                entry.bind("<KeyRelease>", self._format_detail_phone)
            if label == "Birthday":
                self.detail_birthday_entry = entry
                entry.bind("<KeyRelease>", self._format_detail_birthday)
            self.detail_entries.append(entry)

        ttk.Label(self.right_panel, text="Favorite").grid(row=6, column=0, sticky="w", pady=3)
        self.favorite_check = ttk.Checkbutton(self.right_panel, variable=self.favorite_var)
        self.favorite_check.grid(row=6, column=1, sticky="w", pady=3)

        ttk.Label(self.right_panel, text="Notes").grid(row=7, column=0, sticky="nw", pady=3)
        self.notes_text = tk.Text(self.right_panel, height=8, wrap="word")
        self.notes_text.grid(row=7, column=1, sticky="nsew", pady=3)

        buttons = ttk.Frame(self.right_panel)
        buttons.grid(row=8, column=1, sticky="e", pady=(8, 0))
        self.edit_button = ttk.Button(buttons, text="Edit", command=self._on_edit_contact)
        self.save_button = ttk.Button(buttons, text="Save", command=self._on_save_contact)
        self.cancel_button = ttk.Button(buttons, text="Cancel", command=self._on_cancel_edit)
        self.edit_button.pack(side=tk.LEFT)
        self.save_button.pack(side=tk.LEFT, padx=(8, 0))
        self.cancel_button.pack(side=tk.LEFT, padx=(8, 0))

    def _build_bottom_panel(self) -> None:
        bottom = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        bottom.grid(row=1, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)

        self.birthday_summary_var = tk.StringVar()
        ttk.Label(bottom, textvariable=self.birthday_summary_var).grid(row=0, column=0, sticky="w")
        ttk.Button(bottom, text="View Upcoming Birthdays", command=self._on_view_birthdays).grid(
            row=0, column=1, padx=(8, 0)
        )

        status = ttk.Label(bottom, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    def _refresh_all(self) -> None:
        self._refresh_category_choices()
        self._refresh_contact_list()
        self._refresh_birthday_summary()

    def _set_initial_pane_sizes(self) -> None:
        """Place the contact browser and detail panel in an even split."""
        self._set_contact_browser_half_width()

    def _keep_contact_browser_half_width(self, _event=None) -> None:
        """Keep the contact browser at half the main pane width as the window resizes."""
        self.root.after_idle(self._set_contact_browser_half_width)

    def _set_contact_browser_half_width(self) -> None:
        try:
            width = self.main_pane.winfo_width()
            if width > 1:
                self.main_pane.sashpos(0, width // 2)
        except tk.TclError:
            pass

    def _refresh_category_choices(self) -> None:
        categories = {
            contact.category
            for contact in self.rolodex.list_contacts()
            if getattr(contact, "category", None)
        }
        values = ["All"] + sorted(
            c
            for c in set(categories).union(self.custom_categories)
            if c
        )
        self.category_filter_box.configure(values=values)
        if self.category_filter_var.get() not in values:
            self.category_filter_var.set("All")

    def _refresh_contact_list(self, select_email: Optional[str] = None) -> None:
        self._update_contact_sort_headings()
        for row in self.contact_tree.get_children():
            self.contact_tree.delete(row)

        contacts = self._get_filtered_contacts()
        for contact in contacts:
            email = contact.email or ""
            self.contact_tree.insert(
                "",
                tk.END,
                iid=email,
                values=(
                    contact.name or "",
                    email,
                    contact.phone_num or "",
                    iso_to_display_date(contact.birth_date),
                    contact.category or "",
                    "Yes" if contact.favorite else "No",
                    contact.address or "",
                    contact.notes or "",
                ),
            )

        if select_email and self.contact_tree.exists(select_email):
            self.contact_tree.selection_set(select_email)
            self.contact_tree.focus(select_email)
            self.contact_tree.see(select_email)
        self._set_status(f"Showing {len(contacts)} contacts.")

    def _get_filtered_contacts(self) -> list[Contact]:
        query = self.search_var.get().strip()
        if query:
            contacts = self.rolodex.search_contacts(
                query,
                fields=("name", "email", "phone_num", "address", "birth_date", "category", "notes", "tags"),
            )
        else:
            contacts = self.rolodex.list_contacts()

        category = self.category_filter_var.get()
        if category and category != "All":
            key = category.lower()
            contacts = [c for c in contacts if (c.category or "").lower() == key]
        return self._sort_contacts(contacts)

    def _sort_contacts(self, contacts: list[Contact]) -> list[Contact]:
        sort_by = self._current_sort_attribute()

        def has_sort_value(contact: Contact) -> bool:
            if sort_by == "favorite":
                return True
            return bool(getattr(contact, sort_by, None))

        def sort_key(contact: Contact):
            if sort_by == "favorite":
                return 1 if contact.favorite else 0
            value = getattr(contact, sort_by, None)
            return (value or "").lower() if isinstance(value, str) else (value or "")

        present = [contact for contact in contacts if has_sort_value(contact)]
        missing = [contact for contact in contacts if not has_sort_value(contact)]
        return sorted(present, key=sort_key, reverse=self.sort_descending) + missing

    def _current_sort_attribute(self) -> str:
        sort_map = {
            "Name": "name",
            "Email": "email",
            "Birthday": "birth_date",
            "Category": "category",
            "Favorite": "favorite",
        }
        return sort_map.get(self.sort_var.get(), "name")

    def _update_contact_sort_headings(self) -> None:
        for column, label in self.sortable_contact_columns.items():
            self.contact_tree.heading(column, text=label)

    def _sort_column_from_label(self, label: str) -> str:
        column_map = {
            "Name": "name",
            "Email": "email",
            "Birthday": "birthday",
            "Category": "category",
            "Favorite": "favorite",
        }
        return column_map.get(label, "name")

    def _populate_detail_panel(self, contact: Optional[Contact]) -> None:
        self.selected_contact = contact
        if contact is None:
            self.name_var.set("")
            self.address_var.set("")
            self.phone_var.set("")
            self.email_var.set("")
            self.birth_date_var.set("")
            self.category_var.set("")
            self.favorite_var.set(False)
            self._set_notes("")
            self._set_detail_fields_editable(False)
            return

        self.name_var.set(contact.name or "")
        self.address_var.set(contact.address or "")
        self.phone_var.set(contact.phone_num or "")
        self.email_var.set(contact.email or "")
        self.birth_date_var.set(iso_to_display_date(contact.birth_date))
        self.category_var.set(contact.category or "")
        self.favorite_var.set(bool(contact.favorite))
        self._set_notes(contact.notes or "")
        self._set_detail_fields_editable(False)

    def _set_notes(self, value: str) -> None:
        self.notes_text.configure(state=tk.NORMAL)
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", value)
        if not self.is_editing:
            self.notes_text.configure(state=tk.DISABLED)

    def _set_detail_fields_editable(self, is_editable: bool) -> None:
        self.is_editing = is_editable
        entry_state = tk.NORMAL if is_editable else "readonly"
        for entry in self.detail_entries:
            entry.configure(state=entry_state)
        self.favorite_check.configure(state=tk.NORMAL if is_editable else tk.DISABLED)
        self.notes_text.configure(state=tk.NORMAL if is_editable else tk.DISABLED)
        self.edit_button.configure(state=tk.NORMAL if self.selected_contact and not is_editable else tk.DISABLED)
        self.save_button.configure(state=tk.NORMAL if is_editable else tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL if is_editable else tk.DISABLED)

    def _on_contact_selected(self, _event=None) -> None:
        selected = self.contact_tree.selection()
        if not selected:
            return
        contact = self.rolodex.view_contact(selected[0])
        self._populate_detail_panel(contact)

    def _on_search_changed(self, _event=None) -> None:
        self._refresh_contact_list()

    def _on_sort_changed(self, _event=None) -> None:
        self.sort_descending = False
        self._refresh_contact_list()

    def _on_contact_heading_double_click(self, event) -> None:
        if self.contact_tree.identify_region(event.x, event.y) != "heading":
            return
        column_id = self.contact_tree.identify_column(event.x)
        try:
            column = self.contact_tree["columns"][int(column_id.replace("#", "")) - 1]
        except (IndexError, ValueError):
            return
        if column not in self.sortable_contact_columns:
            return

        label = self.sortable_contact_columns[column]
        if self.sort_var.get() == label:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_var.set(label)
            self.sort_descending = False
        self._refresh_contact_list()

    def _on_category_filter_changed(self, _event=None) -> None:
        self._refresh_contact_list()

    def _format_detail_phone(self, _event=None) -> None:
        if not self.is_editing:
            return
        current = self.phone_var.get()
        formatted = format_phone_for_entry(current)
        if formatted != current:
            self.phone_var.set(formatted)
            self.root.after_idle(lambda: self.detail_phone_entry.icursor(tk.END))

    def _format_detail_birthday(self, _event=None) -> None:
        if not self.is_editing:
            return
        current = self.birth_date_var.get()
        formatted = format_birthday_for_entry(current)
        if formatted != current:
            self.birth_date_var.set(formatted)
            self.root.after_idle(lambda: self.detail_birthday_entry.icursor(tk.END))

    def _on_add_contact(self) -> None:
        ContactDialog(
            self.root,
            "Add Contact",
            self._add_contact_from_dialog,
            categories=self._contact_category_choices(),
        )

    def _add_contact_from_dialog(self, data: dict) -> bool:
        try:
            contact = Contact(**data)
            added = self.rolodex.add_contact(contact)
        except Exception as error:
            messagebox.showerror("Invalid Contact", str(error), parent=self.root)
            return False
        self._refresh_category_choices()
        self._refresh_contact_list(select_email=added.email)
        self._refresh_birthday_summary()
        self._set_status("Contact added.")
        return True

    def _on_edit_contact(self) -> None:
        if not self.selected_contact:
            messagebox.showwarning("No Contact Selected", "Select a contact to edit.", parent=self.root)
            return
        self._set_detail_fields_editable(True)
        self._set_status("Editing contact.")

    def _on_save_contact(self) -> None:
        if not self.selected_contact:
            return
        current_email = self.selected_contact.email
        try:
            updated = self.rolodex.edit_contact(current_email, **self._get_detail_data())
        except Exception as error:
            messagebox.showerror("Invalid Contact", str(error), parent=self.root)
            return
        self._refresh_category_choices()
        self._refresh_contact_list(select_email=updated.email)
        self._populate_detail_panel(updated)
        self._refresh_birthday_summary()
        self._set_status("Contact saved.")

    def _on_cancel_edit(self) -> None:
        self._populate_detail_panel(self.selected_contact)
        self._set_status("Edit cancelled.")

    def _on_delete_contact(self) -> None:
        if not self.selected_contact:
            messagebox.showwarning("No Contact Selected", "Select a contact to delete.", parent=self.root)
            return
        name = self.selected_contact.name or self.selected_contact.email
        if not messagebox.askyesno(
            "Delete Contact",
            f"Delete {name}?\n\nThis action cannot be undone.",
            parent=self.root,
        ):
            return
        email = self.selected_contact.email
        try:
            deleted = self.rolodex.delete_contact(email)
        except Exception as error:
            messagebox.showerror("Delete Failed", str(error), parent=self.root)
            return
        if deleted:
            self._populate_detail_panel(None)
            self._refresh_category_choices()
            self._refresh_contact_list()
            self._refresh_birthday_summary()
            self._set_status("Contact deleted.")

    def _on_export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Contacts to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            count = self.rolodex.export_contacts(path, file_format="csv")
        except Exception as error:
            messagebox.showerror("Export Failed", str(error), parent=self.root)
            return
        self._set_status(f"Exported {count} contacts to {os.path.basename(path)}.")

    def _on_import_csv(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Import Contacts from CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        merge = messagebox.askyesno(
            "Import Contacts",
            "Merge imported contacts into the current Rolodex?\n\nChoose No to replace current contacts.",
            parent=self.root,
        )
        try:
            result = self.rolodex.import_contacts(path, merge=merge)
        except Exception as error:
            messagebox.showerror("Import Failed", str(error), parent=self.root)
            return
        imported_categories = categories_from_contacts(self.rolodex.list_contacts())
        self.custom_categories = sorted(set(self.custom_categories).union(imported_categories))
        try:
            save_custom_categories(self.custom_categories)
        except OSError as error:
            messagebox.showwarning(
                "Categories",
                f"Contacts imported, but category choices could not be saved: {error}",
                parent=self.root,
            )
        self._refresh_all()
        message = f"Imported {result['imported']} contacts; skipped {result['skipped']}."
        if result["errors"]:
            message += f"\n\nFirst issue: {result['errors'][0]}"
        self._set_status(message.splitlines()[0])
        if result["errors"]:
            messagebox.showwarning("Import Completed with Warnings", message, parent=self.root)

    def _on_manage_categories(self) -> None:
        CategoryManagerWindow(
            self.root,
            categories=self._contact_category_choices(),
            on_save=self._save_managed_categories,
        )

    def _on_view_birthdays(self) -> None:
        BirthdayWindow(self.root, self.rolodex)

    def _on_about(self) -> None:
        messagebox.showinfo(
            "About Digital Rolodex",
            "Digital Rolodex\nA local contact manager built with Python and Tkinter.",
            parent=self.root,
        )

    def _get_detail_data(self) -> dict:
        return {
            "name": self.name_var.get(),
            "address": self.address_var.get(),
            "phone_num": self.phone_var.get(),
            "email": self.email_var.get(),
            "birth_date": display_to_iso_date(self.birth_date_var.get()),
            "category": self.category_var.get(),
            "favorite": self.favorite_var.get(),
            "notes": self.notes_text.get("1.0", tk.END).strip(),
        }

    def _contact_category_choices(self) -> list[str]:
        contact_categories = {
            contact.category
            for contact in self.rolodex.list_contacts()
            if getattr(contact, "category", None)
        }
        return sorted(set(self.custom_categories).union(contact_categories))

    def _save_managed_categories(self, categories: list[str]) -> None:
        self.custom_categories = sorted({c for c in categories if c})
        try:
            save_custom_categories(self.custom_categories)
        except OSError as error:
            messagebox.showerror("Categories", f"Could not save categories: {error}", parent=self.root)
            return
        self._refresh_category_choices()
        self._set_status("Categories updated.")

    def _refresh_birthday_summary(self) -> None:
        upcoming = self.rolodex.upcoming_birthdays(days=30)[:3]
        if not upcoming:
            self.birthday_summary_var.set("No birthdays in the next 30 days.")
            return
        parts = []
        for contact, days in upcoming:
            label = "today" if days == 0 else f"in {days} days"
            parts.append(f"{contact.name} {label}")
        self.birthday_summary_var.set("Upcoming Birthdays: " + " | ".join(parts))

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)


class ContactDialog:
    """Modal contact creation dialog."""

    def __init__(self, parent: tk.Tk, title: str, on_save, categories: list[str]) -> None:
        self.parent = parent
        self.on_save = on_save
        self.categories = categories
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)

        self.name_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.birth_date_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.favorite_var = tk.BooleanVar(value=False)

        self._build()
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        self.window.wait_window()

    def _build(self) -> None:
        frame = ttk.Frame(self.window, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        fields = [
            ("Name", self.name_var),
            ("Address", self.address_var),
            ("Phone", self.phone_var),
            ("Email", self.email_var),
            ("Birthday", self.birth_date_var),
        ]
        for row, (label, variable) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=3)
            entry = ttk.Entry(frame, textvariable=variable, width=42)
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            if label == "Phone":
                entry.bind("<KeyRelease>", self._format_phone)
            if label == "Birthday":
                entry.bind("<KeyRelease>", self._format_birthday)

        ttk.Label(frame, text="Category").grid(row=5, column=0, sticky="w", pady=3)
        ttk.Combobox(
            frame,
            textvariable=self.category_var,
            values=self.categories,
            width=40,
        ).grid(row=5, column=1, sticky="ew", pady=3)

        ttk.Label(frame, text="Favorite").grid(row=6, column=0, sticky="w", pady=3)
        ttk.Checkbutton(frame, variable=self.favorite_var).grid(row=6, column=1, sticky="w", pady=3)

        ttk.Label(frame, text="Notes").grid(row=7, column=0, sticky="nw", pady=3)
        self.notes_text = tk.Text(frame, height=5, width=32, wrap="word")
        self.notes_text.grid(row=7, column=1, sticky="ew", pady=3)

        buttons = ttk.Frame(frame)
        buttons.grid(row=8, column=1, sticky="e", pady=(8, 0))
        ttk.Button(buttons, text="Save", command=self._save).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT, padx=(8, 0))

    def _save(self) -> None:
        data = {
            "name": self.name_var.get(),
            "address": self.address_var.get(),
            "phone_num": self.phone_var.get(),
            "email": self.email_var.get(),
            "birth_date": display_to_iso_date(self.birth_date_var.get()),
            "category": self.category_var.get(),
            "favorite": self.favorite_var.get(),
            "notes": self.notes_text.get("1.0", tk.END).strip(),
        }
        if self.on_save(data):
            self.window.destroy()

    def _format_phone(self, _event=None) -> None:
        current = self.phone_var.get()
        formatted = format_phone_for_entry(current)
        if formatted != current:
            self.phone_var.set(formatted)
            self.window.after_idle(self._move_phone_cursor_to_end)

    def _format_birthday(self, _event=None) -> None:
        current = self.birth_date_var.get()
        formatted = format_birthday_for_entry(current)
        if formatted != current:
            self.birth_date_var.set(formatted)
            self.window.after_idle(self._move_phone_cursor_to_end)

    def _move_phone_cursor_to_end(self) -> None:
        focused = self.window.focus_get()
        if isinstance(focused, ttk.Entry):
            focused.icursor(tk.END)


class CategoryManagerWindow:
    """Window for adding and deleting category choices."""

    def __init__(self, parent: tk.Tk, categories: list[str], on_save) -> None:
        self.parent = parent
        self.on_save = on_save
        self.categories = sorted({category for category in categories if category})
        self.new_category_var = tk.StringVar()

        self.window = tk.Toplevel(parent)
        self.window.title("Manage Categories")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)

        self._build()
        self._refresh_list()

    def _build(self) -> None:
        frame = ttk.Frame(self.window, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Manage Categories", anchor="center").grid(
            row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8)
        )

        self.listbox = tk.Listbox(frame, height=10, width=34)
        self.listbox.grid(row=1, column=0, columnspan=3, sticky="ew")

        ttk.Entry(frame, textvariable=self.new_category_var).grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(frame, text="Add", command=self._add_category).grid(row=2, column=1, padx=(8, 0), pady=(8, 0))
        ttk.Button(frame, text="Delete", command=self._delete_selected).grid(row=2, column=2, padx=(8, 0), pady=(8, 0))

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=3, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Save", command=self._save).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT, padx=(8, 0))

    def _refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for category in self.categories:
            self.listbox.insert(tk.END, category)

    def _add_category(self) -> None:
        category = self.new_category_var.get().strip()
        if not category:
            return
        if category.lower() not in {existing.lower() for existing in self.categories}:
            self.categories.append(category)
            self.categories.sort()
            self._refresh_list()
        self.new_category_var.set("")

    def _delete_selected(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        category = self.listbox.get(selection[0])
        if messagebox.askyesno(
            "Delete Category",
            f"Delete category '{category}' from the category list?\n\nContacts already using it will keep their value.",
            parent=self.window,
        ):
            self.categories = [item for item in self.categories if item != category]
            self._refresh_list()

    def _save(self) -> None:
        self.on_save(self.categories)
        self.window.destroy()


class BirthdayWindow:
    """Popup window for upcoming birthday reminders."""

    def __init__(self, parent: tk.Tk, rolodex: Rolodex) -> None:
        self.parent = parent
        self.rolodex = rolodex
        self.days_var = tk.StringVar(value="30")
        self.window = tk.Toplevel(parent)
        self.window.title("Upcoming Birthdays")
        self.window.geometry("520x360")
        self.window.transient(parent)
        self._build()
        self._refresh()

    def _build(self) -> None:
        frame = ttk.Frame(self.window, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        controls = ttk.Frame(frame)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(controls, text="Show birthdays within").pack(side=tk.LEFT)
        ttk.Entry(controls, textvariable=self.days_var, width=6).pack(side=tk.LEFT, padx=6)
        ttk.Label(controls, text="days").pack(side=tk.LEFT)
        ttk.Button(controls, text="Refresh", command=self._refresh).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(controls, text="Close", command=self.window.destroy).pack(side=tk.RIGHT)

        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("name", "birthday", "days")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.tree.heading("name", text="Name")
        self.tree.heading("birthday", text="Birthday")
        self.tree.heading("days", text="Days Away")
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("birthday", width=140, anchor="w")
        self.tree.column("days", width=90, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")

        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=y_scrollbar.set)

    def _refresh(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            days = int(self.days_var.get())
            upcoming = self.rolodex.upcoming_birthdays(days=days)
        except Exception as error:
            messagebox.showerror("Birthday Report", str(error), parent=self.window)
            return
        for contact, days_away in upcoming:
            self.tree.insert("", tk.END, values=(contact.name, contact.birth_date or "", days_away))


def run_gui(contacts_file: str = CONTACTS_FILE) -> None:
    """Launch the Digital Rolodex GUI."""
    root = tk.Tk()
    DigitalRolodexApp(root, contacts_file=contacts_file)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
