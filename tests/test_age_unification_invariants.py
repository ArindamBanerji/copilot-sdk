"""Executable gates for the AGE-unification architecture.

These tests deliberately describe the target state.  They are expected to
surface the currently reachable SQLite, direct-client, and swallowed-error
paths until the migration plan in the design document is complete.
"""

from __future__ import annotations

import inspect
import ast
import os
import re
from pathlib import Path
from typing import Iterable

import pytest

from copilot_sdk.config import GraphConfig
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.protocol import GraphStore
from tests.graph_store_test_helpers import make_memory_store
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.testing.fixtures import requires_age


ROOT = Path(__file__).resolve().parents[1]
REPOS = (
    ROOT,
    ROOT.parent / "s2p-copilot",
    ROOT.parent / "gen-ai-roi-demo-v4-v50",
    ROOT.parent / "ci-platform",
    ROOT.parent / "graph-attention-engine-v50",
)
DOMAINS = ("trading", "purchasing", "dataops", "s2p", "soc")
CONFIG_TEST_DSN = "postgresql://test:test@127.0.0.1:1/test?connect_timeout=1"


def _forbidden_store_imports(symbol: str, module: str) -> list[str]:
    hits = []
    for folder in (ROOT / "copilot_sdk", ROOT / "apps"):
        for path in folder.rglob("*.py"):
            if "node_modules" in path.parts:
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
                if isinstance(node, ast.ImportFrom):
                    if node.module == module or any(alias.name == symbol for alias in node.names):
                        hits.append(f"{path.relative_to(ROOT)}:{node.lineno}")
                    elif any(f"{node.module}.{alias.name}" == module for alias in node.names):
                        hits.append(f"{path.relative_to(ROOT)}:{node.lineno}")
                elif isinstance(node, ast.Import) and any(alias.name == module for alias in node.names):
                    hits.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    return hits


def test_no_decision_store_class_exists() -> None:
    path = ROOT / "copilot_sdk/scoring/storage.py"
    assert not path.exists() or "class DecisionStore" not in path.read_text(encoding="utf-8")


def test_no_decision_store_import_anywhere() -> None:
    assert not _forbidden_store_imports("DecisionStore", "copilot_sdk.scoring.storage")


def test_no_direct_backend_references_in_production() -> None:
    """Step 10 guard: production code must use GraphStore protocol, not concrete backends."""
    hits = []
    for root, dirs, files in os.walk(ROOT / "copilot_sdk"):
        for filename in files:
            if not filename.endswith(".py"):
                continue
            path = Path(root) / filename
            rel = path.relative_to(ROOT).as_posix()
            if "/storage.py" in rel or "/tests/" in rel or rel.startswith("tests/"):
                continue
            with path.open(encoding="utf-8") as source:
                for line_number, line in enumerate(source, 1):
                    if re.search(r"\bSQLiteGraphStore\b|\bDualWriteStore\b", line):
                        hits.append(f"{rel}:{line_number}: {line.rstrip()}")
    assert hits == [], f"Direct backend references in production code: {hits}"


@pytest.mark.xfail(strict=True, reason="DSTORE-MIGRATE-2: durable failure outbox must survive AGE outages and process restarts")
def test_no_raw_sqlite3_in_scoring() -> None:
    hits = [str(path.relative_to(ROOT)) for path in (ROOT / "copilot_sdk/scoring").rglob("*.py")
            if re.search(r"import sqlite3|sqlite3\.connect", path.read_text(encoding="utf-8"))]
    assert not hits


def _age_config(domain: str) -> GraphConfig:
    """Resolve AGE policy with a syntactic DSN; these checks never connect."""
    env = dict(os.environ)
    env.update({"GRAPH_BACKEND": "age", "GRAPH_DSN": CONFIG_TEST_DSN})
    return GraphConfig.load(domain, env=env)


def _production_python_files() -> Iterable[Path]:
    excluded_parts = {"tests", "scripts", "migration", "migrations", "__pycache__"}
    for repo in REPOS:
        if not repo.is_dir():
            continue
        for path in repo.rglob("*.py"):
            if excluded_parts.intersection(path.parts):
                continue
            yield path


def _runtime_application_files() -> Iterable[Path]:
    """Yield copilot application modules, excluding SDK test backends/tools."""
    roots = (
        ROOT / "apps" / "trading" / "backend" / "app",
        ROOT / "apps" / "purchasing" / "backend" / "app",
        ROOT / "apps" / "dataops" / "backend" / "app",
        ROOT.parent / "s2p-copilot" / "backend" / "app",
        ROOT.parent / "gen-ai-roi-demo-v4-v50" / "backend" / "app",
    )
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            if "tests" in path.parts or "__pycache__" in path.parts:
                continue
            if path.name in {"cli_sdk.py"}:
                continue
            yield path


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestINV1GraphStoreProtocol:
    """Every production Decision path must be AGE-backed GraphStore."""

    def test_no_sqlite_decision_store_in_production_config(self) -> None:
        for domain in DOMAINS:
            config = _age_config(domain)
            assert config.backend == "age", domain
            assert config.graph == "soc_graph", domain

    def test_scorer_rejects_memory_store(self) -> None:
        store = make_memory_store(":memory:", domain="trading")
        try:
            with pytest.raises(RuntimeError, match="AGE-backed"):
                CompoundingScorer.from_preset(
                    "trading", graph_store=store, profile="production"
                )
        finally:
            store.close()

    @requires_age
    def test_factory_creates_age_store_for_all_domains(self) -> None:
        stores = []
        try:
            for domain in DOMAINS:
                env = dict(os.environ)
                if not env.get("GRAPH_DSN"):
                    env["GRAPH_DSN"] = env.get("AGE_TEST_DSN", "")
                config = GraphConfig.load(domain, env=env)
                store = create_graph_store(
                    backend=config.backend,
                    domain=config.domain,
                    dsn=config.dsn,
                    graph_name=config.graph,
                    shared_graph_authorization=config.authorized,
                )
                stores.append(store)
                assert "AGE" in type(store.graph_primary).__name__, domain
        finally:
            for store in stores:
                store.close()

    def test_no_sqlite_import_in_scoring_router_path(self) -> None:
        for path in (
            ROOT / "copilot_sdk" / "backend" / "scoring_router.py",
            ROOT / "copilot_sdk" / "backend" / "conservation_router.py",
            ROOT / "copilot_sdk" / "backend" / "evolution_router.py",
            ROOT / "copilot_sdk" / "backend" / "self_computation_router.py",
            ROOT / "copilot_sdk" / "backend" / "transfer_router.py",
        ):
            if path.exists():
                assert "sqlite3" not in _source(path), str(path)


class TestINV2GraphConfig:
    """Every graph connection and graph name must be GraphConfig-owned."""

    def test_no_raw_graph_env_reads_in_production(self) -> None:
        forbidden = re.compile(
            r"(?:os\.environ|os\.getenv)\s*\.?(?:get)?\s*\(\s*"
            r"[\"'](?:AGE_GRAPH_NAME|GRAPH_NAME|GRAPH_DSN|AGE_DSN|GRAPH_BACKEND)"
        )
        offenders = []
        for path in _runtime_application_files():
            if path.name in {"campaigns.py", "triage.py"} and "AGE_GRAPH_NAME" in _source(path):
                offenders.append(str(path))
                continue
            if forbidden.search(_source(path)):
                offenders.append(str(path))
        assert not offenders, "raw graph configuration reads: " + ", ".join(offenders)

    def test_graphconfig_rejects_invalid_domain(self) -> None:
        with pytest.raises(ValueError, match="unknown graph config domain"):
            GraphConfig.load("not-a-copilot")


class TestINV3NoSilentSubstitution:
    """AGE errors must surface instead of becoming fabricated absence."""

    def test_no_known_graph_error_to_empty_or_absent_substitution(self) -> None:
        forbidden = {
            "gae_state.py": ("return None", "return False"),
            "purchasing_control.py": ("return []",),
            "s2p_graph_reader.py": ("return []",),
        }
        offenders = []
        for path in _production_python_files():
            needles = forbidden.get(path.name)
            if needles and any(needle in _source(path) for needle in needles):
                offenders.append(str(path))
        assert not offenders, "graph error substitution remains: " + ", ".join(offenders)


class TestINV4DomainScoped:
    """Regression gate for required domain arguments on Decision reads."""

    def test_protocol_requires_domain_on_reads(self) -> None:
        for name in ("get_decision", "get_decisions", "get_all_decisions", "get_verified_decisions"):
            signature = inspect.signature(getattr(GraphStore, name))
            assert "domain" in signature.parameters, name
            assert signature.parameters["domain"].default is inspect.Parameter.empty, name


class TestINV5DomainStamped:
    """Regression gate for required domain arguments on Decision writes."""

    def test_protocol_requires_domain_on_writes(self) -> None:
        for name in ("write_decision", "write_outcome"):
            signature = inspect.signature(getattr(GraphStore, name))
            assert "domain" in signature.parameters, name
            assert signature.parameters["domain"].default is inspect.Parameter.empty, name


class TestINV6SharedGraph:
    """All five copilot configurations must resolve the shared graph."""

    def test_all_domains_resolve_to_soc_graph(self) -> None:
        for domain in DOMAINS:
            config = _age_config(domain)
            assert config.graph == "soc_graph", domain
            assert config.authorized == f"{domain}:soc_graph", domain


class TestINV7NoNonUnifiedPaths:
    """Meta-gates for the remaining concrete P1-P7 paths."""

    def test_no_sqlite3_import_in_production(self) -> None:
        active_paths = (
            ROOT / "copilot_sdk" / "graph" / "factory.py",
            ROOT / "copilot_sdk" / "backend" / "scoring_router.py",
            ROOT / "copilot_sdk" / "backend" / "conservation_router.py",
            ROOT / "copilot_sdk" / "backend" / "evolution_router.py",
            ROOT / "copilot_sdk" / "backend" / "self_computation_router.py",
            ROOT / "copilot_sdk" / "backend" / "transfer_router.py",
        )
        offenders = [
            str(path)
            for path in active_paths
            if path.exists() and ("import sqlite3" in _source(path) or "import aiosqlite" in _source(path))
        ]
        assert not offenders, "SQLite imports remain: " + ", ".join(offenders)

    def test_no_sqlite_file_paths_in_production(self) -> None:
        active_paths = (
            ROOT / "copilot_sdk" / "backend" / "scoring_router.py",
            ROOT / "copilot_sdk" / "backend" / "conservation_router.py",
            ROOT / "copilot_sdk" / "backend" / "evolution_router.py",
            ROOT / "copilot_sdk" / "backend" / "self_computation_router.py",
            ROOT / "copilot_sdk" / "backend" / "transfer_router.py",
        )
        offenders = [
            str(path)
            for path in active_paths
            if path.exists() and ".sqlite3" in _source(path)
        ]
        assert not offenders, "SQLite paths remain: " + ", ".join(offenders)

    def test_no_evolution_memory_stores(self) -> None:
        offenders = []
        for path in _runtime_application_files():
            source = _source(path)
            if "SQLiteVariantStore(" in source and "create_variant_store" not in source:
                offenders.append(str(path))
        assert not offenders, "SQLite evolution stores remain: " + ", ".join(offenders)

    def test_no_promotion_memory_stores(self) -> None:
        active_paths = (
            ROOT / "apps" / "trading" / "backend" / "app" / "main.py",
            ROOT / "apps" / "purchasing" / "backend" / "app" / "main.py",
            ROOT / "apps" / "dataops" / "backend" / "app" / "main.py",
        )
        forbidden_patterns = ("SQLitePromotionStore(", "PromotionStore(data_dir")
        offenders = [
            str(path)
            for path in active_paths
            if path.exists() and any(pattern in _source(path) for pattern in forbidden_patterns)
        ]
        assert not offenders, "SQLite promotion stores remain: " + ", ".join(offenders)


class TestINV8RetiredBackendGates:
    """Prevent re-introduction of deleted SQLite/DualWrite infrastructure (P6 CI guards)."""

    def test_no_sqlite_graph_store_module(self) -> None:
        """copilot_sdk/graph/sqlite_store.py must stay deleted."""
        path = ROOT / "copilot_sdk/graph/sqlite_store.py"
        assert not path.exists(), (
            "RETIRED: sqlite_store.py was deleted in Step 7 (F-03). "
            "Do not recreate. Use InMemoryGraphStore (test) or AGEGraphStore (prod)."
        )

    def test_no_dual_write_store_module(self) -> None:
        """copilot_sdk/graph/dual_write_store.py must stay deleted."""
        path = ROOT / "copilot_sdk/graph/dual_write_store.py"
        assert not path.exists(), (
            "RETIRED: dual_write_store.py was deleted in Step 7 (F-03). "
            "Do not recreate. AGE is the sole production backend."
        )

    def test_no_sqlite_graph_store_import_anywhere(self) -> None:
        """No production or test code may import SQLiteGraphStore."""
        hits = _forbidden_store_imports("SQLiteGraphStore", "copilot_sdk.graph.sqlite_store")
        assert not hits, (
            "RETIRED: SQLiteGraphStore imports found. "
            f"Violations: {hits}"
        )

    def test_no_dual_write_store_import_anywhere(self) -> None:
        """No production or test code may import DualWriteStore."""
        hits = _forbidden_store_imports("DualWriteStore", "copilot_sdk.graph.dual_write_store")
        assert not hits, (
            "RETIRED: DualWriteStore imports found. "
            f"Violations: {hits}"
        )

    def test_factory_valid_backends_locked(self) -> None:
        """Factory must only accept memory and age backends."""
        source = (ROOT / "copilot_sdk/graph/factory.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_VALID_BACKENDS":
                        if isinstance(node.value, ast.Set):
                            values = set()
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    values.add(elt.value)
                            assert values == {"memory", "age"}, (
                                f"_VALID_BACKENDS must be exactly {{memory, age}}, got {values}"
                            )
                            return
        pytest.fail("_VALID_BACKENDS not found in factory.py")


def test_scoring_sqlite_exception_bounded() -> None:
    allowed = ROOT / "copilot_sdk/scoring/persistence_outbox.py"
    importers: set[Path] = set()
    for path in sorted((ROOT / "copilot_sdk/scoring").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name.split(".", 1)[0] == "sqlite3" for alias in node.names
            ):
                importers.add(path)
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and node.module.split(".", 1)[0] == "sqlite3"
            ):
                importers.add(path)

    violators = sorted(
        path.relative_to(ROOT).as_posix() for path in importers if path != allowed
    )
    assert not violators, (
        "Rule #89: Only persistence_outbox.py may import sqlite3 in scoring. "
        f"Violations: {violators}"
    )
    assert importers == {allowed}, (
        "Rule #89: persistence_outbox.py must remain scoring's sole sqlite3 importer"
    )

