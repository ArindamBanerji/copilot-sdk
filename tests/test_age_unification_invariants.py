"""Executable gates for the AGE-unification architecture.

These tests deliberately describe the target state.  They are expected to
surface the currently reachable SQLite, direct-client, and swallowed-error
paths until the migration plan in the design document is complete.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from typing import Iterable

import pytest

from copilot_sdk.config import GraphConfig
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.dual_write_store import DualWriteStore
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


ROOT = Path(__file__).resolve().parents[1]
REPOS = (
    ROOT,
    ROOT.parent / "s2p-copilot",
    ROOT.parent / "gen-ai-roi-demo-v4-v50",
    ROOT.parent / "ci-platform",
    ROOT.parent / "graph-attention-engine-v50",
)
DOMAINS = ("trading", "purchasing", "dataops", "s2p", "soc")


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
            config = GraphConfig.load(domain)
            assert config.backend == "age", domain
            assert config.graph == "soc_graph", domain

    def test_scorer_rejects_sqlite_store(self) -> None:
        store = SQLiteGraphStore(":memory:", domain="trading")
        try:
            with pytest.raises(RuntimeError, match="AGE-backed"):
                CompoundingScorer.from_preset(
                    "trading", graph_store=store, profile="production"
                )
        finally:
            store.close()

    def test_scorer_rejects_sqlite_primary_dual_write_store(self) -> None:
        primary = SQLiteGraphStore(":memory:", domain="trading")
        secondary = SQLiteGraphStore(":memory:", domain="trading")
        try:
            with pytest.raises(TypeError, match="ProtocolV2GraphStore"):
                DualWriteStore(primary, secondary)
        finally:
            primary.close()
            secondary.close()

    def test_factory_creates_age_store_for_all_domains(self) -> None:
        stores = []
        try:
            for domain in DOMAINS:
                config = GraphConfig.load(domain)
                store = create_graph_store(
                    backend=config.backend,
                    domain=config.domain,
                    dsn=config.dsn,
                    graph_name=config.graph,
                    shared_graph_authorization=config.authorized,
                )
                stores.append(store)
                assert "AGE" in type(store).__name__, domain
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
            config = GraphConfig.load(domain)
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

    def test_no_evolution_sqlite_stores(self) -> None:
        offenders = []
        for path in _runtime_application_files():
            source = _source(path)
            if "SQLiteVariantStore(" in source and "create_variant_store" not in source:
                offenders.append(str(path))
        assert not offenders, "SQLite evolution stores remain: " + ", ".join(offenders)

    def test_no_promotion_sqlite_stores(self) -> None:
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
