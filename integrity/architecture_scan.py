"""T0 architecture scanner for repository-wide product-integrity invariants."""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Pattern

SDK_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SDK_ROOT.parent
SKIP_DIRS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", "node_modules", "dist", "build", ".venv", "venv"}


@dataclass(frozen=True)
class Evidence:
    path: Path
    line: int
    message: str

    def format(self) -> str:
        for root in (SDK_ROOT, WORKSPACE_ROOT):
            try:
                return f"{self.path.relative_to(root)}:{self.line}: {self.message}"
            except ValueError:
                continue
        return f"{self.path}:{self.line}: {self.message}"


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


@dataclass(frozen=True)
class LiteralCheck:
    code: str
    title: str
    pattern: Pattern[str]
    scan_dirs: tuple[str, ...]
    extensions: tuple[str, ...]
    skip_if_in_line: tuple[str, ...] = ()
    exempt_paths: tuple[str, ...] = ()
    message: str = "forbidden architecture pattern"


# Explicit legacy exemptions preserve visibility while making new occurrences fail.
MERGE_BASELINE_EXEMPTIONS = (
    "gen-ai-roi-demo-v4-v50/backend/app/data/alert_pool.py",
)
SQLITE_BASELINE_EXEMPTIONS = (
    "copilot-sdk/copilot_sdk/backend/signal_store.py",
    "copilot-sdk/copilot_sdk/evolution/variant_store.py",
    "copilot-sdk/copilot_sdk/graph/outbox.py",
    "copilot-sdk/copilot_sdk/graph/sqlite_store.py",
    "copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py",
    "copilot-sdk/copilot_sdk/migration/rehearsal.py",
    "copilot-sdk/copilot_sdk/outbox/store.py",
    "copilot-sdk/copilot_sdk/outcome/ledger.py",
    "copilot-sdk/copilot_sdk/pilot/transfer.py",
    "copilot-sdk/copilot_sdk/promotion/core.py",
    "copilot-sdk/copilot_sdk/scoring/persistence_outbox.py",
    "copilot-sdk/apps/dataops/backend/app/dataops_governance.py",
    "copilot-sdk/apps/dataops/backend/app/main.py",
    "copilot-sdk/apps/purchasing/backend/app/main.py",
    "copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py",
    "copilot-sdk/apps/trading/backend/app/main.py",
    "copilot-sdk/apps/trading/backend/app/cli_sdk.py",
    "s2p-copilot/backend/app/main.py",
    "s2p-copilot/backend/app/services/proposal_service.py",
    "gen-ai-roi-demo-v4-v50/backend/app/main.py",
    "gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py",
)
PURCHASING_LANGUAGE_BASELINE_EXEMPTIONS = (
    "copilot-sdk/apps/purchasing/backend/app/evidence_provider.py",
    "copilot-sdk/apps/purchasing/backend/app/investigation_config.py",
    "copilot-sdk/apps/purchasing/backend/app/inventory_router.py",
    "copilot-sdk/apps/purchasing/backend/app/vld_preseed.py",
    "copilot-sdk/apps/purchasing/frontend/src/App.tsx",
    "copilot-sdk/apps/purchasing/frontend/src/api.ts",
    "copilot-sdk/apps/purchasing/frontend/src/components/OrderContext.tsx",
    "copilot-sdk/apps/purchasing/frontend/src/components/ParLevelMonitor.tsx",
    "copilot-sdk/apps/purchasing/frontend/src/screens/DashboardScreen.tsx",
    "copilot-sdk/apps/purchasing/frontend/src/screens/InventoryScreen.tsx",
    "copilot-sdk/apps/purchasing/frontend/src/screens/OrderScreen.tsx",
)

LITERAL_CHECKS = (
    LiteralCheck(
        code="AGE-01",
        title="No MERGE in production Cypher",
        pattern=re.compile(r"\bMERGE\s*\(", re.IGNORECASE),
        scan_dirs=("ci-platform/ci_platform", "gen-ai-roi-demo-v4-v50/backend/app", "copilot-sdk/copilot_sdk", "s2p-copilot/backend/app"),
        extensions=(".py",),
        skip_if_in_line=("MERGE is forbidden", "MATCH-then-CREATE"),
        exempt_paths=MERGE_BASELINE_EXEMPTIONS,
        message="Cypher MERGE is forbidden; use MATCH-then-CREATE",
    ),
    LiteralCheck(
        code="AGE-02",
        title="No raw sqlite3.connect in production",
        pattern=re.compile(r"\bsqlite3\.connect\s*\("),
        scan_dirs=("copilot-sdk/copilot_sdk", "copilot-sdk/apps/dataops/backend/app", "copilot-sdk/apps/purchasing/backend/app", "copilot-sdk/apps/trading/backend/app", "s2p-copilot/backend/app", "gen-ai-roi-demo-v4-v50/backend/app"),
        extensions=(".py",),
        skip_if_in_line=("migration", "preseed"),
        exempt_paths=SQLITE_BASELINE_EXEMPTIONS,
        message="raw sqlite3.connect bypasses the GraphStore boundary",
    ),
    LiteralCheck(
        code="LANG-01",
        title="Purchasing language boundary",
        pattern=re.compile(r"\b(inventory|customers|shrinkage|SKU)\b", re.IGNORECASE),
        scan_dirs=("copilot-sdk/apps/purchasing/frontend", "copilot-sdk/apps/purchasing/backend/app"),
        extensions=(".py", ".tsx", ".ts"),
        skip_if_in_line=("migration",),
        exempt_paths=PURCHASING_LANGUAGE_BASELINE_EXEMPTIONS,
        message="legacy purchasing-language term found",
    ),
)


def _iter_files(root: Path, extensions: tuple[str, ...]) -> Iterable[Path]:
    if not root.exists():
        return
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in extensions:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if "tests" in path.parts or path.name.startswith("test_"):
            continue
        yield path


def _iter_py_files(root: Path) -> Iterable[Path]:
    yield from _iter_files(root, (".py",))


def _iter_tsx_files(root: Path) -> Iterable[Path]:
    yield from _iter_files(root, (".tsx",))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _parse(path: Path) -> ast.AST | None:
    try:
        return ast.parse(_read(path), filename=str(path))
    except SyntaxError:
        return None


def _docstring_line_numbers(path: Path) -> set[int]:
    if path.suffix != ".py":
        return set()
    tree = _parse(path)
    if tree is None:
        return set()
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) or not node.body:
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            start = int(getattr(first, "lineno", 0))
            end = int(getattr(first, "end_lineno", start))
            lines.update(range(start, end + 1))
    return lines


def _workspace_relative(path: Path, repos_root: Path) -> str:
    try:
        return path.relative_to(repos_root).as_posix()
    except ValueError:
        return path.as_posix()


def scan_file(path: Path, check: LiteralCheck) -> tuple[Evidence, ...]:
    """Scan one source file line-by-line for one literal architecture check."""
    docstrings = _docstring_line_numbers(path)
    evidence: list[Evidence] = []
    for line_number, line in enumerate(_read(path).splitlines(), start=1):
        stripped = line.lstrip()
        if line_number in docstrings or stripped.startswith(("#", "//")):
            continue
        if any(token.lower() in line.lower() for token in check.skip_if_in_line):
            continue
        if check.pattern.search(line):
            evidence.append(Evidence(path, line_number, check.message))
    return tuple(evidence)


def run_literal_check(check: LiteralCheck, repos_root: Path = WORKSPACE_ROOT) -> CheckResult:
    evidence: list[Evidence] = []
    missing: list[str] = []
    exemptions = set(check.exempt_paths)
    for relative_dir in check.scan_dirs:
        root = repos_root / relative_dir
        if not root.exists():
            missing.append(relative_dir)
            continue
        for path in _iter_files(root, check.extensions):
            if _workspace_relative(path, repos_root) in exemptions:
                continue
            evidence.extend(scan_file(path, check))
    note = "missing directories skipped: " + ", ".join(missing) if missing else ""
    return CheckResult(check.code, check.title, True, tuple(evidence), note=note)


def check_age_merge() -> CheckResult:
    return run_literal_check(LITERAL_CHECKS[0])


def check_raw_sqlite() -> CheckResult:
    return run_literal_check(LITERAL_CHECKS[1])


def check_purchasing_kitchen_language() -> CheckResult:
    return run_literal_check(LITERAL_CHECKS[2])


def _string_literals(path: Path) -> Iterable[tuple[int, str]]:
    tree = _parse(path)
    if tree is None:
        return
    docstrings = _docstring_line_numbers(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            line = int(getattr(node, "lineno", 1))
            if line not in docstrings:
                yield line, node.value


AGE_RAW_SQL_EXEMPT_PATHS = {"copilot_sdk/migrate/scratch_graph.py", "copilot_sdk/migrate/sqlite_to_age.py", "copilot_sdk/migrate/verify_state.py"}


def check_age_raw_sql() -> CheckResult:
    """Retained compatibility audit for direct AGE SQL wrappers."""
    evidence: list[Evidence] = []
    for path in _iter_py_files(SDK_ROOT / "copilot_sdk"):
        rel = path.relative_to(SDK_ROOT).as_posix()
        if rel in AGE_RAW_SQL_EXEMPT_PATHS or path.name == "age_client.py":
            continue
        for line, value in _string_literals(path):
            upper = value.upper()
            lower = value.lower()
            if "SELECT * FROM" in upper and ("cypher" in lower or "ag_catalog" in lower):
                evidence.append(Evidence(path, line, "raw AGE SQL string should use the AGE client two-step pattern"))
    return CheckResult("AGE-RAW", "No raw SQL in Cypher queries", True, tuple(evidence))


def check_learning_names() -> CheckResult:
    evidence: list[Evidence] = []
    prefixes = ("rl_", "reward_", "policy_")
    for base in (SDK_ROOT / "copilot_sdk" / "scoring", SDK_ROOT / "copilot_sdk" / "evolution"):
        for path in _iter_py_files(base):
            tree = _parse(path)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name.lower().startswith(prefixes):
                    evidence.append(Evidence(path, int(node.lineno), f"core learning symbol uses reserved prefix: {node.name}"))
    return CheckResult("F-25", "No RL naming on core learning path", True, tuple(evidence))


def check_mu_access() -> CheckResult:
    pattern = re.compile(r"(\b\w+\.mu\s*\[|\bstate\s*\[\s*['\"]mu['\"]\s*\]\s*\[)")
    evidence: list[Evidence] = []
    for repo_name in ("copilot-sdk", "s2p-copilot", "gen-ai-roi-demo-v4-v50", "ci-platform"):
        for path in _iter_py_files(WORKSPACE_ROOT / repo_name):
            for index, line in enumerate(_read(path).splitlines(), start=1):
                if pattern.search(line):
                    evidence.append(Evidence(path, index, "direct mu indexing found"))
    return CheckResult("ARCH-20", "No raw centroid indexing", False, tuple(evidence), "inventory only until C-REGIME P1")


def check_provenance_badges() -> CheckResult:
    evidence: list[Evidence] = []
    apps_root = SDK_ROOT / "apps"
    if not apps_root.exists():
        return CheckResult("PROV-01", "ProvenanceBadge on key frontend surfaces", False, ())
    for app_dir in sorted(path for path in apps_root.iterdir() if path.is_dir()):
        frontend = app_dir / "frontend" / "src"
        if frontend.exists() and not any("ProvenanceBadge" in _read(path) for path in _iter_tsx_files(frontend)):
            evidence.append(Evidence(frontend, 1, f"{app_dir.name} frontend has no ProvenanceBadge usage"))
    return CheckResult("PROV-01", "ProvenanceBadge on key frontend surfaces", False, tuple(evidence))


def run_checks() -> list[CheckResult]:
    return [*(run_literal_check(check) for check in LITERAL_CHECKS), check_age_raw_sql(), check_learning_names(), check_mu_access(), check_provenance_badges()]


def print_results(results: list[CheckResult], verbose: bool) -> None:
    for result in results:
        status = "PASS" if result.passed else ("FAIL" if result.enforced else "REPORT")
        suffix = f" ({result.note})" if result.note else ""
        print(f"{result.code}: {status} - {result.title}{suffix}")
        if verbose or not result.passed:
            for item in result.evidence:
                print(f"  - {item.format()}")
        if result.code == "ARCH-20":
            print(f"  direct_mu_access_count={len(result.evidence)}")
    failures = [result for result in results if result.enforced and not result.passed]
    print(f"ENFORCED_FAILURES={len(failures)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run T0 architecture integrity checks.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Return 1 when an enforced check fails.")
    mode.add_argument("--report", action="store_true", help="Print all evidence and always return 0.")
    args = parser.parse_args(argv)
    results = run_checks()
    print_results(results, verbose=bool(args.report))
    if args.report:
        return 0
    return 1 if any(result.enforced and not result.passed for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
