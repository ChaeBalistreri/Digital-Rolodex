import json
import os
from contact import Contact

CONTACTS_FILE = "contacts.json" # Set hard-coded file name here
# **The CONTACTS_FILE variable should be moved to MAIN.PY upon creation**

def load_contacts(file_path):
    """Load contacts from a JSON file and return a list of Contact objects.
    Returns an empty list if file is missing or unreadable.
    """
    try:
        with open(CONTACTS_FILE, 'r') as file:
            data = json.load(file)
            return [Contact.from_dict(item) for item in data]
    except FileNotFoundError:
        # File doesn't exist yet — no contacts to load
        return []
    except json.JSONDecodeError:
        # File exists but is empty or corrupted — return empty safely
        print(f"Warning: Could not decode JSON from '{file_path}'. Returning empty list.")
        return []
    except Exception as e:
        # Catch all other unexpected errors
        print(f"Unexpected error while loading contacts: {e}")
        return []


def save_contacts(file_path, contacts):
    """Save a list of Contact objects to a JSON file."""
    try:
        with open(file_path, 'w') as file:
            json.dump([contact.to_dict() for contact in contacts], file, indent=4)
    except Exception as e:
        print(f"Failed to save contacts to {file_path}: {e}")
