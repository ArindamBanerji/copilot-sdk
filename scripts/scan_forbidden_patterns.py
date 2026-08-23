"""Scan SDK and copilot backend production code for forbidden patterns."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:
    from validate_age_unification import (
        ROOT,
        Finding,
        check_fstring_cypher,
        check_no_bare_except,
        check_no_empty_domain,
        check_no_hardcoded_dsn,
        check_no_inmemory_production,
        check_no_neo4j,
        check_no_type_ignore,
        check_unscoped_writes,
        rel,
        read_lines,
    )
except ImportError:  # pragma: no cover - supports direct module loading
    from scripts.validate_age_unification import (
        ROOT,
        Finding,
        check_fstring_cypher,
        check_no_bare_except,
        check_no_empty_domain,
        check_no_hardcoded_dsn,
        check_no_inmemory_production,
        check_no_neo4j,
        check_no_type_ignore,
        check_unscoped_writes,
        rel,
        read_lines,
    )


PatternCheck = Callable[[Path], list[Finding]]

WORKSPACE_ROOT = ROOT.parent
ACTIVE_SCAN_REPOSITORIES = frozenset(
    {"copilot-sdk", "ci-platform", "s2p-copilot", "gen-ai-roi-demo-v4-v50"}
)


@dataclass(frozen=True)
class DomainFinding:
    line: int
    category: str
    source: str


def iter_python_files(workspace_root: Path = WORKSPACE_ROOT) -> list[Path]:
    files: list[Path] = []
    for repository in ACTIVE_SCAN_REPOSITORIES:
        path = workspace_root / repository
        if path.exists():
            files.extend(item for item in path.rglob("*.py") if "__pycache__" not in item.parts)
    return sorted(set(files))


def load_allowlist(path: Path | None = None) -> dict[str, Any]:
    allowlist_path = path or (ROOT / "docs" / "design" / "age_unification_forbidden_patterns_allowlist.toml")
    if not allowlist_path.exists():
        return {}
    return tomllib.loads(allowlist_path.read_text(encoding="utf-8"))


def _relative_allowlist_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        pass
    try:
        return path.relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def _allowlisted(rule: str, path: Path, line_number: int, allowlist: dict[str, Any]) -> bool:
    rule_data = allowlist.get("rules", {}).get(rule, {})
    relative = _relative_allowlist_path(path)
    if any(relative.startswith(str(prefix)) for prefix in rule_data.get("paths", [])):
        return True
    if any(item.get("path") == relative for item in rule_data.get("files", [])):
        return True
    return any(
        item.get("path") == relative and int(item.get("line", -1)) == line_number
        for item in rule_data.get("lines", [])
    )


def scan_unscoped_decision_queries(
    path: Path,
    source: str,
    allowlist: dict[str, Any],
    _max_line: int,
) -> list[DomainFinding]:
    """Classify Decision reads as SCOPED, CALLER_SCOPED, or PRODUCTION."""
    lines = source.splitlines()
    findings: list[DomainFinding] = []
    for number, line in enumerate(lines, 1):
        if not re.search(r"MATCH\s*\([^\n]*:Decision\b", line, re.I):
            continue
        if _allowlisted("unscoped_decision_match", path, number, allowlist):
            category = "ALLOWLISTED"
        else:
            window = " ".join(lines[max(0, number - 5):min(len(lines), number + 5)])
            if re.search(r"where_clause|\{where_clause\}", line, re.I) and "d.domain" in source:
                category = "CALLER_SCOPED"
            elif re.search(r"d\.domain\s*=|\bdomain\s*=.*d\.domain", window, re.I):
                category = "SCOPED"
            else:
                category = "PRODUCTION"
        findings.append(DomainFinding(number, category, line.strip()))
    return findings


def scan_read_model_mutations(
    path: Path,
    source: str,
    allowlist: dict[str, Any],
) -> list[DomainFinding]:
    findings: list[DomainFinding] = []
    for number, line in enumerate(source.splitlines(), 1):
        if "SET d.archived" in line:
            continue
        if not re.search(r"(?:SET\s+d\.(?:correct|status)\b|d\[(?:'|\")(?:correct|status)(?:'|\")\]\s*=)", line, re.I):
            continue
        bracket_mutation = bool(re.search(r"d\[(?:'|\")(?:correct|status)(?:'|\")\]\s*=", line, re.I))
        category = "PRODUCTION" if bracket_mutation else (
            "ALLOWLISTED" if _allowlisted("correctness_read_model_write", path, number, allowlist) else "PRODUCTION"
        )
        findings.append(DomainFinding(number, category, line.strip()))
    return findings


def scan_domain_leaks(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    domains = ("trading", "purchasing", "dataops")
    for domain in domains:
        app_root = root / "apps" / domain / "backend" / "app"
        if not app_root.exists():
            continue
        other = [name for name in domains if name != domain]
        pattern = re.compile(r"(?:app\.domains\.|from\s+app\.|import\s+app\.).*(?:" + "|".join(other) + r")", re.I)
        for path in app_root.rglob("*.py"):
            for number, line in enumerate(read_lines(path), 1):
                if pattern.search(line):
                    findings.append(Finding(rel(path, root), number, line.strip()))
    return findings


FORBIDDEN_CHECKS: tuple[tuple[str, PatternCheck], ...] = (
    ("neo4j_import", check_no_neo4j),
    ("hardcoded_dsn", check_no_hardcoded_dsn),
    ("unscoped_write", check_unscoped_writes),
    ("unscoped_fstring_cypher", check_fstring_cypher),
    ("bare_except", check_no_bare_except),
    ("type_ignore", check_no_type_ignore),
    ("inmemory_graph_store", check_no_inmemory_production),
    ("empty_domain", check_no_empty_domain),
    ("cross_domain_reference", scan_domain_leaks),
)


def build_report(root: Path = ROOT) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    for name, check in FORBIDDEN_CHECKS:
        findings = check(root)
        groups.append({
            "pattern": name,
            "violations": [finding.as_dict() for finding in findings],
        })
    violations = [item for group in groups for item in group["violations"]]
    return {
        "schema_version": "sdk-forbidden-patterns-v1",
        "roots": ["copilot_sdk/", "apps/*/backend/app/"],
        "pattern_count": len(groups),
        "violation_count": len(violations),
        "all_clear": not violations,
        "patterns": groups,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan SDK production code for forbidden patterns")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    report = build_report(args.root.resolve())
    print(json.dumps(report, indent=2))
    return 0 if report["all_clear"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
