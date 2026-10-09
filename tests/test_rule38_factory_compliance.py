"""Rule #38: SDK copilot startup paths construct stores through the factory."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from copilot_sdk.graph.factory import create_graph_store
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
def test_factory_preserves_sqlite_decision_id_prefix_rejected(tmp_path, domain: str, prefix: str) -> None:
    with pytest.raises(GraphConfigError, match="invalid graph backend"):
        create_graph_store(profile='test', backend='sqlite', domain=domain, db_path=tmp_path / f'{domain}.db', decision_id_prefix=prefix)
    assert not list(tmp_path.glob("*.db"))


def test_unsupported_backend_without_dsn_fails_closed_rejected(tmp_path) -> None:
    with pytest.raises(GraphConfigError, match="invalid graph backend"):
        create_graph_store(profile='test', backend='unsupported_backend', domain='trading', db_path=tmp_path / 'trading.db', decision_id_prefix='TRD-', env={})
    assert not list(tmp_path.glob("*.db"))


def test_sdk_copilot_main_helpers_call_create_graph_store(profile="test", ) -> None:
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
        call_names = [node.func.id for node in calls if isinstance(node.func, ast.Name)]
        assert "create_graph_store" in call_names, path
        assert "make_memory_store" not in call_names, path


@pytest.mark.parametrize(
    ("domain", "prefix"),
    (("trading", "TRD-"), ("purchasing", "PUR-"), ("dataops", "DOPS-")),
)
def test_factory_preserves_memory_decision_id_prefix(domain: str, prefix: str) -> None:
    store = create_graph_store(
        profile="test", backend="memory", domain=domain, decision_id_prefix=prefix, env={},
    )
    try:
        decision_id = store.write_decision(domain, "category", "approve", 0.9, {})
        assert decision_id.startswith(prefix)
        assert store.get_decision(decision_id, domain=domain) is not None
    finally:
        store.close()


