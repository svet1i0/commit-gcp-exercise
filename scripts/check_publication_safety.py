#!/usr/bin/env python3
"""Scan tracked public files for personal Gmail-style addresses.

Reports only path, line number, and violation class. Never prints matched values.
Exit non-zero on any violation.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Case-insensitive personal Gmail-style addresses.
PATTERN = re.compile(r"(?i)[a-z0-9._%+\-]+@gmail\.com")
# Allowed GitHub noreply author identity (tracked docs may mention it).
ALLOWED = {
    "75417040+svet1i0@users.noreply.github.com",
}


def tracked_files(repo_root: Path) -> list[Path]:
    out = subprocess.check_output(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        text=False,
    )
    files: list[Path] = []
    for raw in out.split(b"\0"):
        if not raw:
            continue
        files.append(repo_root / raw.decode())
    return files


def main() -> int:
    # scripts/ is under repository/; repo root is parent of scripts/
    repo_root = Path(__file__).resolve().parents[1]
    violations = 0
    for path in tracked_files(repo_root):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in PATTERN.finditer(line):
                value = match.group(0)
                if value.lower() in {a.lower() for a in ALLOWED}:
                    continue
                # Do not print the matched value — only path/line/class.
                print(f"{path.relative_to(repo_root)}:{lineno}: personal_gmail_address")
                violations += 1
    if violations:
        print(f"publication_safety_violations={violations}", file=sys.stderr)
        return 1
    print("publication_safety_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
