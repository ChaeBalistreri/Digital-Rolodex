"""CLI smoke test for Digital Rolodex.

Runs main.py non-interactively with scripted input. The subprocess uses the
Tests/_artifacts directory as its working directory so production contacts.json
is not touched.

Run:
    python Tests/cli_TestScript.py
"""

from __future__ import annotations

import os
import subprocess
import sys


CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)


def ensure_artifacts_dir() -> str:
    artifacts = os.path.join(CURRENT_DIR, "_artifacts")
    os.makedirs(artifacts, exist_ok=True)
    return artifacts


def main() -> None:
    artifacts = ensure_artifacts_dir()
    data_file = os.path.join(artifacts, "contacts.json")
    export_file = os.path.join(artifacts, "cli_export.csv")
    for path in (data_file, export_file):
        if os.path.exists(path):
            os.remove(path)

    scripted_input = "\n".join(
        [
            "1",
            "CLI Person",
            "cli.person@example.com",
            "",
            "123-456-7890",
            "2000-06-12",
            "Friends",
            "Met during CLI smoke test",
            "y",
            "friend, cli",
            "6",
            "name",
            "n",
            "5",
            "cli",
            "tags",
            "n",
            "9",
            export_file,
            "13",
            "14",
            "",
        ]
    )

    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_ROOT, "main.py"), "--cli"],
        input=scripted_input,
        text=True,
        capture_output=True,
        cwd=artifacts,
        timeout=15,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise AssertionError(f"CLI exited with {result.returncode}")

    assert "Contact added." in result.stdout
    assert "CLI Person <cli.person@example.com>" in result.stdout
    assert "Exported 1 contact(s)" in result.stdout
    assert "Favorite Contacts" in result.stdout
    assert os.path.exists(export_file)

    print("CLI add/list/search/export smoke test passed.")


if __name__ == "__main__":
    main()
