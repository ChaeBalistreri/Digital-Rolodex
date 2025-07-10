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
|Title| Purpose|
|-----|--------|
|main.py|entry point and UI handling|
|contact.py|defines Contact class|
|storage.py|handles saving/loading contacts from file (JSON or DB)|
|utils.py|for helper functions (input validation, formatting)|
|rolodex.py|core logic (add/edit/delete/search contacts)|
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
- Phone number should be in consistent format (e.g., (123) 456-7890 or 123-456-7890)
- Date of Birth must be in ISO format (YYYY-MM-DD)
- Name should not be empty
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
Select an option: _