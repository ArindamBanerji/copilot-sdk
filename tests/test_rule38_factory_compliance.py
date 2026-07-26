"""Rule #38: SDK copilot startup paths construct stores through the factory."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.config import GraphConfigError


REPO_ROOT = Path(__file__).resolve().parents[1]
COPILOT_MAINS = (
    REPO_ROOT / "apps" / "trading" / "backend" / "app" / "main.py",
    REPO_ROOT / "apps" / "purchasing" / "backend" / "app" / "main.py",
    REPO_ROOT / "apps" / "dataops" / "backend" / "app" / "main.py",
)


@pytest.mark.parametrize(
    ("domain", "prefix"),
    (("trading", "TRD-"), ("purchasing", "PUR-"), ("dataops", "DOPS-")),
)
def test_factory_preserves_sqlite_decision_id_prefix(tmp_path, domain: str, prefix: str) -> None:
    store = create_graph_store(
        backend="sqlite",
        domain=domain,
        db_path=tmp_path / f"{domain}.db",
        decision_id_prefix=prefix,
    )
    assert isinstance(store, SQLiteGraphStore)
    assert store.write_decision(domain, "category", "approve", 0.9, {}).startswith(prefix)
    store.close()


def test_dual_write_without_dsn_fails_closed(tmp_path) -> None:
    with pytest.raises(GraphConfigError):
        create_graph_store(
            backend="dual_write",
            domain="trading",
            db_path=tmp_path / "trading.db",
            decision_id_prefix="TRD-",
            env={},
        )


def test_sdk_copilot_main_helpers_call_create_graph_store() -> None:
    for path in COPILOT_MAINS:
        module = ast.parse(path.read_text(encoding="utf-8"))
        helper = next(
            node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_graph_store"
        )
        calls = [
            node
            for node in ast.walk(helper)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        assert any(node.func.id == "create_graph_store" for node in calls), path
        assert not any(node.func.id == "SQLiteGraphStore" for node in calls), path
