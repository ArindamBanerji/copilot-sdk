"""Static checks for the correctness-unification write and count invariants."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    rule: str
    text: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.rule}: {self.text.strip()}"


_RAW_CORRECT_SET = re.compile(r"\bSET\s+[A-Za-z_]\w*\.correct\s*=", re.IGNORECASE)
_COUNT_PATTERNS = (
    re.compile(r"HAS_OUTCOME", re.IGNORECASE),
    re.compile(r"\bJOIN\s+outcomes\b", re.IGNORECASE),
    re.compile(r"\bo\.is_correct\b", re.IGNORECASE),
)
_COUNT_NAMES = {"count_correct", "count_verified", "count_verified_decisions"}
# The check targets active runtime paths. One-time seed/backfill utilities are
# intentionally outside this runtime gate because they operate before the
# write_outcome contract exists in a deployment.
_EXCLUDED_PARTS = {"tests", "test", "__pycache__", "scripts", "support"}
_EXCLUDED_FILENAMES = {
    "backfill_correct.py",
    "backfill_d_correct.py",
    "inject_errors.py",
    "seed_zero_day.py",
}
_DEFAULT_REPOSITORIES = ("copilot-sdk", "ci-platform", "gen-ai-roi-demo-v4-v50", "s2p-copilot")


def _function_ranges(tree: ast.AST) -> list[tuple[int, int, str]]:
    ranges: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ranges.append((node.lineno, getattr(node, "end_lineno", node.lineno), node.name))
    return ranges


def _function_at_line(ranges: list[tuple[int, int, str]], line: int) -> str | None:
    matches: list[tuple[int, int, str]] = []
    for start, end, name in ranges:
        if start <= line <= end:
            matches.append((start, end, name))
    if not matches:
        return None
    return max(matches, key=lambda item: item[0])[2]


def _is_excluded(path: Path) -> bool:
    return (
        bool(_EXCLUDED_PARTS.intersection(path.parts))
        or path.name.startswith("test_")
        or path.name in _EXCLUDED_FILENAMES
    )


def scan_file(path: Path) -> list[Violation]:
    if _is_excluded(path):
        return []
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    function_ranges = _function_ranges(tree)
    violations: list[Violation] = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if not _RAW_CORRECT_SET.search(line) and not any(
            pattern.search(line) for pattern in _COUNT_PATTERNS
        ):
            continue
        function_name = _function_at_line(function_ranges, line_number)
        if function_name != "write_outcome" and _RAW_CORRECT_SET.search(line):
            violations.append(
                Violation(path, line_number, "C2", "raw Decision.correct write outside write_outcome")
            )
        if function_name in _COUNT_NAMES:
            for pattern in _COUNT_PATTERNS:
                if pattern.search(line):
                    violations.append(
                        Violation(path, line_number, "C3", "counting query traverses outcome correctness")
                    )
                    break
    return violations


def scan(root: Path) -> list[Violation]:
    """Scan the four repositories under *root* and return sorted violations."""
    paths: list[Path] = []
    for repository in _DEFAULT_REPOSITORIES:
        repository_path = root / repository
        if repository_path.exists():
            paths.extend(repository_path.rglob("*.py"))
    violations: list[Violation] = []
    for path in paths:
        violations.extend(scan_file(path))
    return sorted(violations, key=lambda item: (str(item.path), item.line, item.rule))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="scan and return non-zero on violations")
    parser.add_argument("--verbose", action="store_true", help="print the scanned root")
    parser.add_argument("--root", type=Path, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = (args.root or Path(__file__).resolve().parents[2]).resolve()
    violations = scan(root)
    if args.verbose:
        print(f"correctness scanner root: {root}")
    for violation in violations:
        print(violation)
    if violations:
        print(f"{len(violations)} correctness violation(s) found", file=sys.stderr)
        return 1
    print("correctness scanner: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
