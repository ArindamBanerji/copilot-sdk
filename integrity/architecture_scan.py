"""T0 architecture scanner for product-integrity invariants.

The scanner is intentionally stdlib-only so it can run before dependency
installation. Enforced checks return a non-zero exit code in ``--check`` mode;
inventory checks always report and do not fail the run.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SDK_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SDK_ROOT.parent
REPO_NAMES = (
    "copilot-sdk",
    "s2p-copilot",
    "gen-ai-roi-demo-v4-v50",
    "ci-platform",
    "graph-attention-engine-v50",
)
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
}


@dataclass(frozen=True)
class Evidence:
    path: Path
    line: int
    message: str

    def format(self) -> str:
        try:
            display_path = self.path.relative_to(SDK_ROOT)
        except ValueError:
            display_path = self.path.relative_to(WORKSPACE_ROOT)
        return f"{display_path}:{self.line}: {self.message}"


@dataclass(frozen=True)
class CheckResult:
    code: str
    title: str
    enforced: bool
    evidence: tuple[Evidence, ...]
    note: str = ""
    exempt_message: str = ""

    @property
    def passed(self) -> bool:
        return not self.evidence

    @property
    def exempted(self) -> bool:
        return bool(self.exempt_message) and self.passed


# AGE migration utilities intentionally use direct psycopg SQL wrappers because
# they create, verify, and copy between graphs before the target GraphStore or
# AGEClient graph abstraction is safe to assume available.
AGE_01_EXEMPT_PATHS: dict[str, str] = {
    "copilot_sdk/migrate/scratch_graph.py": "migration module - direct psycopg required while creating scratch graphs",
    "copilot_sdk/migrate/sqlite_to_age.py": "migration module - direct psycopg required during cross-db migration",
    "copilot_sdk/migrate/verify_state.py": "migration module - direct psycopg required for replay verification against AGE",
}


AGE_01_EXEMPT_MESSAGE = (
    "migration module - direct psycopg required, AGEClient unavailable during cross-db migration"
)


def _iter_py_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _iter_tsx_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for path in root.rglob("*.tsx"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _parse(path: Path) -> ast.AST | None:
    try:
        return ast.parse(_read(path), filename=str(path))
    except SyntaxError:
        return None


def _docstring_lines(tree: ast.AST) -> set[int]:
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.body:
                continue
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                lines.add(int(getattr(first, "lineno", 0)))
    return lines


def _string_literals(path: Path) -> Iterable[tuple[int, str]]:
    tree = _parse(path)
    if tree is None:
        return
    docstring_lines = _docstring_lines(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            line = int(getattr(node, "lineno", 1))
            if line in docstring_lines:
                continue
            yield line, node.value


def check_age_raw_sql() -> CheckResult:
    evidence: list[Evidence] = []
    for path in _iter_py_files(SDK_ROOT / "copilot_sdk"):
        rel = path.relative_to(SDK_ROOT).as_posix()
        if rel in AGE_01_EXEMPT_PATHS:
            continue
        if path.name == "age_client.py":
            continue
        for line, value in _string_literals(path):
            upper = value.upper()
            lower = value.lower()
            if "SELECT * FROM" in upper and ("cypher" in lower or "ag_catalog" in lower):
                evidence.append(Evidence(path, line, "raw AGE SQL string should use the AGE client two-step pattern"))
    return CheckResult(
        "AGE-01",
        "No raw SQL in Cypher queries",
        True,
        tuple(evidence),
        exempt_message=AGE_01_EXEMPT_MESSAGE,
    )


def check_age_merge() -> CheckResult:
    evidence: list[Evidence] = []
    for path in _iter_py_files(SDK_ROOT / "copilot_sdk"):
        for line, value in _string_literals(path):
            upper = value.upper()
            lower = value.lower()
            if "MERGE" in upper and ("cypher" in lower or "match" in lower or "create" in lower):
                evidence.append(Evidence(path, line, "Cypher MERGE is forbidden; use MATCH-then-CREATE"))
    return CheckResult("AGE-02", "No MERGE in Cypher", True, tuple(evidence))


def check_purchasing_kitchen_language() -> CheckResult:
    raw_ids = ("coverage_depth", "cost_trend_alignment")
    evidence: list[Evidence] = []
    root = SDK_ROOT / "apps" / "purchasing"
    for path in _iter_py_files(root):
        if "tests" in path.parts:
            continue
        for line, value in _string_literals(path):
            lowered = value.lower()
            for raw_id in raw_ids:
                if raw_id in lowered:
                    evidence.append(Evidence(path, line, f"raw factor id {raw_id!r} appears in a string literal"))
    return CheckResult("LANG-01", "Kitchen language in Purchasing", True, tuple(evidence))


def check_learning_names() -> CheckResult:
    evidence: list[Evidence] = []
    prefixes = ("rl_", "reward_", "policy_")
    for base in (SDK_ROOT / "copilot_sdk" / "scoring", SDK_ROOT / "copilot_sdk" / "evolution"):
        for path in _iter_py_files(base):
            tree = _parse(path)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = node.name.lower()
                    if name.startswith(prefixes):
                        evidence.append(Evidence(path, int(node.lineno), f"core learning symbol uses reserved prefix: {node.name}"))
    return CheckResult("F-25", "No RL naming on core learning path", True, tuple(evidence))


def check_mu_access() -> CheckResult:
    pattern = re.compile(r"(\b\w+\.mu\s*\[|\bstate\s*\[\s*['\"]mu['\"]\s*\]\s*\[)")
    evidence: list[Evidence] = []
    for repo_name in REPO_NAMES:
        repo = WORKSPACE_ROOT / repo_name
        for path in _iter_py_files(repo):
            text = _read(path)
            for index, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    evidence.append(Evidence(path, index, "direct mu indexing found"))
    return CheckResult(
        "ARCH-20",
        "No raw centroid indexing",
        False,
        tuple(evidence),
        "inventory only until C-REGIME P1",
    )


def check_provenance_badges() -> CheckResult:
    evidence: list[Evidence] = []
    apps_root = SDK_ROOT / "apps"
    if not apps_root.exists():
        return CheckResult("PROV-01", "ProvenanceBadge on key frontend surfaces", False, ())
    for app_dir in sorted(path for path in apps_root.iterdir() if path.is_dir()):
        frontend = app_dir / "frontend" / "src"
        if not frontend.exists():
            continue
        has_badge = any("ProvenanceBadge" in _read(path) for path in _iter_tsx_files(frontend))
        if not has_badge:
            evidence.append(Evidence(frontend, 1, f"{app_dir.name} frontend has no ProvenanceBadge usage"))
    return CheckResult("PROV-01", "ProvenanceBadge on key frontend surfaces", False, tuple(evidence))


def run_checks() -> list[CheckResult]:
    return [
        check_age_raw_sql(),
        check_age_merge(),
        check_purchasing_kitchen_language(),
        check_learning_names(),
        check_mu_access(),
        check_provenance_badges(),
    ]


def print_results(results: list[CheckResult], verbose: bool) -> None:
    for result in results:
        if result.exempted:
            status = "EXEMPT"
        else:
            status = "PASS" if result.passed else ("FAIL" if result.enforced else "REPORT")
        suffix = f" ({result.note})" if result.note else ""
        message = f" - {result.exempt_message}" if result.exempted else f" - {result.title}{suffix}"
        print(f"{result.code}: {status}{message}")
        if verbose or not result.passed:
            for item in result.evidence:
                print(f"  - {item.format()}")
        if result.code == "ARCH-20":
            print(f"  direct_mu_access_count={len(result.evidence)}")
    enforced_failures = [result for result in results if result.enforced and not result.passed]
    if enforced_failures:
        print(f"ENFORCED_FAILURES={len(enforced_failures)}")
    else:
        print("ENFORCED_FAILURES=0")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run T0 architecture integrity checks.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Run enforced checks and return 1 on failure.")
    mode.add_argument("--report", action="store_true", help="Print verbose report and always return 0.")
    args = parser.parse_args(argv)

    results = run_checks()
    print_results(results, verbose=bool(args.report))
    if args.report:
        return 0
    return 1 if any(result.enforced and not result.passed for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
