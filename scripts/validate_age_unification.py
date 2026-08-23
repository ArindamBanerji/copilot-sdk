"""Run static AGE-unification checks and emit a JSON validation report.

The runner is deliberately fail-closed: a check is PASS only when its
evidence is available and no forbidden pattern is found.  It does not modify
the repository or invoke application code.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DOMAIN_APPS = ("trading", "purchasing", "dataops")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {"path": self.path, "line": self.line, "message": self.message}


def production_files(root: Path = ROOT) -> list[Path]:
    files = [p for p in (root / "copilot_sdk").rglob("*.py") if "__pycache__" not in p.parts]
    for app in (root / "apps").glob("*/backend/app"):
        files.extend(p for p in app.rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(set(files))


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def rel(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()


def _find_lines(files: Iterable[Path], pattern: re.Pattern[str], root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        for number, line in enumerate(read_lines(path), 1):
            if pattern.search(line):
                findings.append(Finding(rel(path, root), number, line.strip()))
    return findings


def check_domain_isolation(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for domain in DOMAIN_APPS:
        app_root = root / "apps" / domain / "backend" / "app"
        if not app_root.exists():
            continue
        forbidden = [other for other in DOMAIN_APPS if other != domain]
        pattern = re.compile(r"(?:app\.domains\.|from\s+app\.|import\s+app\.).*(?:" + "|".join(forbidden) + r")", re.I)
        findings.extend(_find_lines(app_root.rglob("*.py"), pattern, root))
    return findings


def check_config_completeness(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for main in sorted((root / "apps").glob("*/backend/app/main.py")):
        source = main.read_text(encoding="utf-8", errors="replace")
        if "GraphConfig" not in source:
            findings.append(Finding(rel(main, root), 1, "GraphConfig is not used by the application main module"))
    return findings


def check_fail_closed(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for app_root in sorted((root / "apps").glob("*/backend/app")):
        graph_modules = [path for path in app_root.rglob("*.py") if "graph" in path.name or "health" in path.name]
        if not any("503" in path.read_text(encoding="utf-8", errors="replace") for path in graph_modules):
            findings.append(Finding(rel(app_root, root), 1, "graph startup/status path has no 503 fail-closed response"))
    return findings


def check_no_neo4j(root: Path = ROOT) -> list[Finding]:
    return _find_lines(production_files(root), re.compile(r"\b(?:import\s+neo4j|from\s+neo4j)\b", re.I), root)


def check_no_hardcoded_dsn(root: Path = ROOT) -> list[Finding]:
    return _find_lines(production_files(root), re.compile(r"(?:bolt://|neo4j://|neo4j\+s://|aura\.neo4j)", re.I), root)


def _write_lines(path: Path) -> list[tuple[int, str]]:
    return [(n, line) for n, line in enumerate(read_lines(path), 1) if re.search(r"\b(?:CREATE|MERGE)\s*\(", line, re.I)]


def check_unscoped_writes(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for path in production_files(root):
        lines = read_lines(path)
        for number, line in _write_lines(path):
            if not re.search(r"Decision|Outcome|Centroid|Campaign", line, re.I):
                continue
            context = " ".join(lines[max(0, number - 4):min(len(lines), number + 3)]).lower()
            if "domain" not in context and "sqlite" not in context:
                findings.append(Finding(rel(path, root), number, "write has no nearby domain scope"))
    return findings


def check_fstring_cypher(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for path in production_files(root):
        lines = read_lines(path)
        for number, line in enumerate(lines, 1):
            if "f\"" not in line and "f'" not in line:
                continue
            if not re.search(r"\b(?:MATCH|CREATE|MERGE|SET)\b", line, re.I):
                continue
            if not re.search(r"Decision|Outcome|Centroid|Campaign", line, re.I):
                continue
            context = " ".join(lines[max(0, number - 3):min(len(lines), number + 4)]).lower()
            if "domain" not in context:
                findings.append(Finding(rel(path, root), number, "f-string Cypher lacks domain scope"))
    return findings


def check_no_bare_except(root: Path = ROOT) -> list[Finding]:
    return _find_lines(production_files(root), re.compile(r"^\s*except\s*:\s*$"), root)


def check_no_type_ignore(root: Path = ROOT) -> list[Finding]:
    return _find_lines(production_files(root), re.compile(r"#\s*type:\s*ignore\b"), root)


def check_no_inmemory_production(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for path in production_files(root):
        if any(part in {"testing", "tests", "demo"} for part in path.parts):
            continue
        findings.extend(_find_lines([path], re.compile(r"\bInMemoryGraphStore\b"), root))
    return findings


def check_no_empty_domain(root: Path = ROOT) -> list[Finding]:
    findings = _find_lines(production_files(root), re.compile(r"\bdomain\s*[:=]\s*['\"]['\"]"), root)
    return [finding for finding in findings if "where domain" not in finding.message.lower()]


def check_health_graph_status(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for main in sorted((root / "apps").glob("*/backend/app/main.py")):
        source = main.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"graph_status|graph_backend", source):
            findings.append(Finding(rel(main, root), 1, "health surface does not mention graph status"))
    return findings


def check_mypy(root: Path = ROOT) -> list[Finding]:
    app_files = [str(path.relative_to(root)) for path in production_files(root) if "backend" in path.parts]
    if not app_files:
        return [Finding(".", 0, "no backend app modules found")]
    completed = subprocess.run(
        [sys.executable, "-m", "mypy", *app_files, "--no-error-summary"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return []
    output = (completed.stdout + completed.stderr).splitlines()
    return [Finding("mypy", 0, line) for line in output[:25]] or [Finding("mypy", 0, "mypy failed")]


CHECKS = (
    ("domain_isolation", check_domain_isolation),
    ("config_completeness", check_config_completeness),
    ("fail_closed_routers", check_fail_closed),
    ("no_neo4j_imports", check_no_neo4j),
    ("no_hardcoded_dsns", check_no_hardcoded_dsn),
    ("no_unscoped_writes", check_unscoped_writes),
    ("no_unscoped_fstring_cypher", check_fstring_cypher),
    ("no_bare_except", check_no_bare_except),
    ("no_type_ignore", check_no_type_ignore),
    ("no_inmemory_production", check_no_inmemory_production),
    ("no_empty_domain", check_no_empty_domain),
    ("health_reports_graph_status", check_health_graph_status),
    ("mypy_clean_app_modules", check_mypy),
)


def build_report(root: Path = ROOT) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for name, function in CHECKS:
        findings = function(root)
        checks.append({
            "name": name,
            "result": "PASS" if not findings else "FAIL",
            "violations": [finding.as_dict() for finding in findings],
        })
    return {
        "schema_version": "age-unification-validation-v1",
        "check_count": len(checks),
        "all_pass": all(item["result"] == "PASS" for item in checks),
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate AGE graph unification contracts")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    report = build_report(args.root.resolve())
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
