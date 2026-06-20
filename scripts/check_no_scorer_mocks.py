"""Scan test files for forbidden scorer/store mock patterns.

Exit 1 if any forbidden pattern is found. Allowed exceptions must include
"# MOCK-OK: reason" on the same line.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOTS = [
    ROOT / "tests",
    *(ROOT / "apps").glob("*/backend/tests"),
]

FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "fake scorer/store class",
        re.compile(r"\bclass\s+(FakeScorer|FakeStore|PauseScorer|FakeAGEStore)\b"),
    ),
    (
        "mock.patch targeting scorer/store",
        re.compile(r"\bmock\.patch\([^#\n]*(scorer|store)", re.IGNORECASE),
    ),
    (
        "monkeypatch conservation status",
        re.compile(r"\bmonkeypatch\.setattr\([^#\n]*_conservation_status\b"),
    ),
    (
        "monkeypatch scorer score/learn",
        re.compile(r"\bmonkeypatch\.setattr\([^#\n]*(scorer|Scorer)[^#\n]*(score|learn)", re.IGNORECASE),
    ),
    (
        "MagicMock assigned to scorer/store",
        re.compile(r"\b(scorer|store)\s*=\s*MagicMock\(", re.IGNORECASE),
    ),
)


def iter_test_files() -> list[Path]:
    files: list[Path] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        files.extend(path for path in root.rglob("*.py") if path.is_file())
    return sorted(set(files))


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    violations: list[tuple[int, str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    for line_number, line in enumerate(lines, start=1):
        if "# MOCK-OK:" in line:
            continue
        for label, pattern in FORBIDDEN_PATTERNS:
            if pattern.search(line):
                violations.append((line_number, label, line.strip()))
                break
    return violations


def main() -> int:
    all_violations: list[tuple[Path, int, str, str]] = []
    for path in iter_test_files():
        for line_number, label, line in scan_file(path):
            all_violations.append((path, line_number, label, line))

    if all_violations:
        print("Forbidden scorer/store mock patterns found:")
        for path, line_number, label, line in all_violations:
            rel = path.relative_to(ROOT)
            print(f"{rel}:{line_number}: {label}: {line}")
        return 1

    print("PASS: no forbidden scorer/store mock patterns found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
