"""Fail on graph-access patterns that bypass the shared AGE architecture.

The scanner is intentionally lexical. It enforces the architectural boundary in
source code before a runtime configuration can mask an unsupported access path.
Exceptions are explicit and rule-specific in the companion TOML allowlist.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import tomllib
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
ALLOWLIST_PATH = ROOT / "docs" / "design" / "age_unification_forbidden_patterns_allowlist.toml"
EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


@dataclass(frozen=True)
class PatternRule:
    key: str
    description: str
    pattern: re.Pattern[str]


PATTERN_RULES = (
    PatternRule("neo4j_driver", "direct GraphDatabase.driver", re.compile(r"\bGraphDatabase\.driver\s*\(")),
    PatternRule("psycopg_connect", "direct psycopg.connect", re.compile(r"\bpsycopg\.connect\s*\(")),
    PatternRule("sqlite_graph_store", "SQLiteGraphStore construction", re.compile(r"\bSQLiteGraphStore\s*\(")),
    PatternRule("in_memory_graph_store", "InMemoryGraphStore construction", re.compile(r"\bInMemoryGraphStore\s*\(")),
    PatternRule(
        "graph_environment",
        "direct GRAPH_* environment access",
        re.compile(
            r"\bos\.environ(?:\s*\[\s*['\"]GRAPH_[A-Za-z0-9_]+['\"]\s*\]|"
            r"\.get\s*\(\s*['\"]GRAPH_[A-Za-z0-9_]+['\"]\s*\))"
        ),
    ),
)
DECISION_MATCH = re.compile(r"\bMATCH\s*\(\s*d\s*:\s*Decision\b", re.IGNORECASE)
DECISION_DOMAIN_PREDICATE = re.compile(
    r"\bd\s*\.\s*domain\b|\bd\s*:\s*Decision\s*\{+\s*domain\s*:",
    re.IGNORECASE,
)
TRIPLE_QUOTED_STRING = re.compile(r"(?P<quote>'''|\"\"\").*?(?P=quote)", re.DOTALL)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    rule: str
    source: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        help="Repository directory to scan, relative to the shared workspace (for example copilot-sdk).",
    )
    return parser.parse_args()


def load_allowlist() -> dict[str, tuple[str, ...]]:
    with ALLOWLIST_PATH.open("rb") as handle:
        raw = tomllib.load(handle)
    rules = raw.get("rules")
    if not isinstance(rules, dict):
        raise ValueError(f"{ALLOWLIST_PATH} must contain a [rules] table")

    allowlist: dict[str, tuple[str, ...]] = {}
    for key, entries in rules.items():
        if not isinstance(entries, list) or not all(isinstance(entry, str) for entry in entries):
            raise ValueError(f"allowlist rule {key!r} must be an array of paths")
        allowlist[key] = tuple(entries)
    return allowlist


def resolve_scan_root(repo: str | None) -> Path:
    if repo is None:
        return WORKSPACE_ROOT
    candidate = (WORKSPACE_ROOT / repo).resolve()
    try:
        candidate.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError("--repo must stay within the shared workspace") from exc
    if not candidate.is_dir():
        raise ValueError(f"repository does not exist: {candidate}")
    return candidate


def iter_python_files(scan_root: Path) -> Iterable[Path]:
    for directory, subdirectories, filenames in os.walk(scan_root):
        subdirectories[:] = [
            name for name in subdirectories if name not in EXCLUDED_DIRECTORIES
        ]
        for filename in filenames:
            if filename.endswith(".py"):
                yield Path(directory) / filename


def normalized_path(path: Path) -> str:
    return path.resolve().as_posix()


def is_test_file(path: Path) -> bool:
    path_text = normalized_path(path)
    return path.name == "conftest.py" or path.name.startswith("test_") or "/tests/" in path_text


def is_allowlisted(path: Path, rule: str, allowlist: dict[str, tuple[str, ...]]) -> bool:
    if is_test_file(path):
        return True
    path_text = normalized_path(path)
    for entry in allowlist.get(rule, ()):
        is_directory = entry.endswith("/")
        normalized_entry = entry.strip("/")
        if path_text.endswith(f"/{normalized_entry}"):
            return True
        if is_directory and f"/{normalized_entry}/" in path_text:
            return True
    return False


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def source_line(source: str, line: int) -> str:
    return source.splitlines()[line - 1].strip()


def code_only_source(source: str) -> str:
    """Mask comments and string literals while preserving offsets and line numbers."""
    offsets = [0]
    for match in re.finditer("\n", source):
        offsets.append(match.end())
    masked = list(source)
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type not in {tokenize.COMMENT, tokenize.STRING}:
                continue
            start = offsets[token.start[0] - 1] + token.start[1]
            end = offsets[token.end[0] - 1] + token.end[1]
            for index in range(start, end):
                if masked[index] != "\n":
                    masked[index] = " "
    except tokenize.TokenError:
        return source
    return "".join(masked)


def scan_pattern_rules(path: Path, source: str, allowlist: dict[str, tuple[str, ...]]) -> list[Violation]:
    violations: list[Violation] = []
    code_source = code_only_source(source)
    for rule in PATTERN_RULES:
        if is_allowlisted(path, rule.key, allowlist):
            continue
        search_source = source if rule.key == "graph_environment" else code_source
        for match in rule.pattern.finditer(search_source):
            line = line_number(search_source, match.start())
            violations.append(Violation(path, line, rule.description, source_line(source, line)))
    return violations


def scan_unscoped_decision_queries(path: Path, source: str, allowlist: dict[str, tuple[str, ...]]) -> list[Violation]:
    if is_allowlisted(path, "unscoped_decision_match", allowlist):
        return []

    violations: list[Violation] = []
    triple_spans: list[tuple[int, int]] = []
    for literal in TRIPLE_QUOTED_STRING.finditer(source):
        triple_spans.append((literal.start(), literal.end()))
        content = literal.group(0)
        if DECISION_DOMAIN_PREDICATE.search(content):
            continue
        for match in DECISION_MATCH.finditer(content):
            offset = literal.start() + match.start()
            line = line_number(source, offset)
            violations.append(Violation(path, line, "unscoped Decision query", source_line(source, line)))

    for match in DECISION_MATCH.finditer(source):
        if any(start <= match.start() < end for start, end in triple_spans):
            continue
        line = line_number(source, match.start())
        text = source_line(source, line)
        query_window = source[match.start() : match.start() + 1200]
        if not DECISION_DOMAIN_PREDICATE.search(query_window):
            violations.append(Violation(path, line, "unscoped Decision query", text))
    return violations


def scan_file(path: Path, allowlist: dict[str, tuple[str, ...]]) -> list[Violation]:
    source = read_source(path)
    return scan_pattern_rules(path, source, allowlist) + scan_unscoped_decision_queries(path, source, allowlist)


def main() -> int:
    try:
        args = parse_args()
        scan_root = resolve_scan_root(args.repo)
        allowlist = load_allowlist()
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    violations = [
        violation
        for path in sorted(iter_python_files(scan_root))
        for violation in scan_file(path, allowlist)
    ]
    if violations:
        for violation in violations:
            try:
                display_path = violation.path.relative_to(WORKSPACE_ROOT).as_posix()
            except ValueError:
                display_path = violation.path.as_posix()
            print(f"{display_path}:{violation.line}: {violation.rule}: {violation.source}")
        print(f"FAIL: {len(violations)} forbidden graph-access pattern(s) found")
        return 1

    print("PASS: no forbidden graph-access patterns found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
