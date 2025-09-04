import json
import os
import logging
from typing import List

from contact import Contact

"""Storage utilities for Digital Rolodex (DR).

This module focuses solely on persistence (saving/loading), keeping storage
concerns separate from UI and business logic. The caller (e.g., main.py) is
responsible for deciding and passing the path to the contacts file. We do NOT
keep any global file path here to avoid hidden state and to make testing
easier.
"""


logger = logging.getLogger(__name__)


def load_contacts(file_path: str) -> List[Contact]:
    """Load contacts from a JSON file.

    - Returns a list of Contact objects.
    - Returns an empty list when the file does not exist, is empty, or
      contains invalid JSON. This is intentional so the app can start with
      a clean state on first run without raising an error.

    Args:
        file_path: Path to the JSON file (e.g., "contacts.json").

    Notes:
        We open the file using UTF-8 to safely handle non-ASCII characters
        (names, addresses, etc.).
    """
    try:
        # Use the path provided by the caller; no globals.
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Be defensive: if the decoded JSON is not a list, treat it as empty.
        if not isinstance(data, list):
            # Defensive: if JSON root isn't a list, treat as empty but notify.
            logger.warning(
                "Expected a list in '%s', got %s. Returning empty list.",
                file_path,
                type(data).__name__,
            )
            return []

        # Convert each dictionary back into a Contact, robustly skipping
        # malformed entries instead of failing the entire load.
        contacts: List[Contact] = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                logger.warning(
                    "Skipping non-dict item at index %d in '%s'", idx, file_path
                )
                continue
            try:
                c = Contact.from_dict(item)

                # Soft warning: record is present but may be of low quality
                # (missing email and phone). This does not block loading.
                if not c.is_minimally_complete():
                    logger.warning(
                        "Contact '%s' is incomplete (missing email and/or phone).",
                        c.name,
                    )

                # Stricter policy: require name + email; skip otherwise.
                if not getattr(c, "email", None):
                    logger.warning(
                        "Skipping contact '%s' due to missing required field: email.",
                        c.name or "<unknown>",
                    )
                    continue

                contacts.append(c)
            except Exception as e:
                logger.warning(
                    "Skipping invalid contact at index %d in '%s': %s",
                    idx,
                    file_path,
                    e,
                )
        return contacts

    except FileNotFoundError:
        # File doesn't exist yet — likely first run; return empty list gracefully.
        return []
    except json.JSONDecodeError:
        # File exists but is empty or corrupted — return empty safely.
        logger.warning(
            "Could not decode JSON from '%s'. Returning empty list.", file_path
        )
        return []
    except Exception as e:
        # Catch-all for unexpected errors to avoid crashing the app due to I/O.
        logger.error("Unexpected error while loading '%s': %s", file_path, e)
        return []


def save_contacts(file_path: str, contacts: List[Contact]) -> None:
    """Save contacts to a JSON file in a robust, UTF-8 encoded manner.

    - Ensures the parent directory exists (if a directory component is present).
    - Serializes Contact instances via `to_dict()`.
    - Writes human-readable JSON (indent=4) with non-ASCII preserved.

    Args:
        file_path: Destination JSON file path.
        contacts: List of Contact objects to serialize and save.
    """
    try:
        # Create the parent directory if one is specified and does not exist.
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        # Prepare data allowing mixed inputs: Contact instances or pre-serialized dicts.
        # This makes the function tolerant to callers that already converted objects.
        data = [c.to_dict() if isinstance(c, Contact) else c for c in contacts]

        # Write atomically to avoid partial/corrupt files in case of crashes.
        # 1) Write JSON to a temporary file next to the target.
        # 2) Atomically replace the destination with the temp file.
        tmp_path = f"{file_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        os.replace(tmp_path, file_path)
    except Exception as e:
        # Best-effort cleanup of temp file if something went wrong mid-write.
        try:
            tmp_path = f"{file_path}.tmp"
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            # Swallow cleanup errors; original error is more important.
            pass
        logger.error("Failed to save contacts to '%s': %s", file_path, e)
