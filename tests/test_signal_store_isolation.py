"""Fact delivery must stay separate from domain decisions, including app mounts."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from copilot_sdk.backend.graph_signals import GraphSignalEvents
from copilot_sdk.graph.memory_store import InMemoryGraphStore


def _signal(entity_id: str = "vendor-1") -> dict[str, Any]:
    return {
        "source_copilot": "trading",
        "target_copilot": "purchasing",
        "signal_type": "supplier_risk",
        "entity_id": entity_id,
        "confidence": 0.8,
        "detail": "Verified delivery delay",
    }


def _decision(store: InMemoryGraphStore) -> str:
    return str(store.write_decision(
        domain="trading", category="position_entry", action="hold",
        confidence=0.8, factors={"timing_quality": 0.6},
    ))


def test_graph_signals_publish_does_not_pollute_decisions() -> None:
    graph = InMemoryGraphStore(domain="trading")
    _decision(graph)
    before = graph.get_all_decisions(domain="trading")
    store = GraphSignalEvents(graph)

    signal_id = store.publish(_signal())

    assert graph.count_decisions("trading") == len(before) == 1
    assert graph.get_all_decisions(domain="trading") == before
    record = store.get(signal_id)
    assert record is not None
    assert record["entity_id"] == "vendor-1"


def test_graph_signals_reads_only_own_events() -> None:
    graph = InMemoryGraphStore(domain="trading")
    decision_id = _decision(graph)
    store = GraphSignalEvents(graph)
    ids = [store.publish(_signal(f"vendor-{index}")) for index in range(3)]

    rows, total = store.page()

    assert total == len(rows) == 3
    assert [row["signal_id"] for row in rows] == ids
    assert store.get(decision_id) is None


def test_graph_store_decisions_not_visible_as_signals() -> None:
    graph = InMemoryGraphStore(domain="trading")
    decision_ids = [_decision(graph) for _ in range(3)]
    store = GraphSignalEvents(graph)

    assert graph.count_decisions("trading") == 3
    assert store.page() == ([], 0)
    assert all(store.get(decision_id) is None for decision_id in decision_ids)


@pytest.mark.parametrize("domain", ["trading", "purchasing", "dataops"])
def test_app_signal_mount_is_isolated_and_shared(tmp_path: Path, domain: str) -> None:
    """Exercise each real mount in isolation from other apps' module namespaces."""
    root = Path(__file__).resolve().parents[1]
    config = tmp_path / "graph.toml"
    config.write_text(
        '[defaults]\nbackend="memory"\nexpected_backend="memory"\n'
        'graph="test_graph"\ndsn=""\n', encoding="utf-8",
    )
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("GRAPH_", "AGE_", "TRADING_ACTIVE_", "PURCHASING_ACTIVE_", "DATAOPS_ACTIVE_"))
    }
    env.update({
        "GRAPH_CONFIG_PATH": str(config),
        f"{domain.upper()}_PROFILE": "test",
        f"{domain.upper()}_ACTIVE_GRAPH_BACKEND": "memory",
        "CI_DATA_DIR": str(tmp_path),
        "DEMO_NO_RESEED": "1",
    })
    script = """
import importlib
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
from copilot_sdk.backend.cross_signal_router import create_cross_signal_router

domain = sys.argv[1]
sys.path.insert(0, sys.argv[2])
app = importlib.import_module('app.main').app
graph = app.state.graph_store
decision_id = graph.write_decision(
    domain=domain, category='ordinary_decision', action='hold', confidence=0.8,
    factors={'test_factor': 0.6},
)
before = graph.count_decisions(domain)
client = TestClient(app)
path = '/api/platform/cross-signals'
assert client.get(path).json()['count'] == 0
assert client.get(path + '/' + decision_id).status_code == 404
response = client.post(path, json={
    'source_copilot': domain, 'target_copilot': 's2p', 'signal_type': 'supplier_risk',
    'entity_id': 'vendor-1', 'confidence': 0.8, 'detail': 'Verified delivery delay',
})
assert response.status_code == 201, response.text
signal_id = response.json()['signal_id']
assert graph.count_decisions(domain) == before
assert client.get(path).json()['count'] == 1

# A separately constructed receiver uses the same graph in this memory profile.
receiver_app = FastAPI()
receiver_app.include_router(
    create_cross_signal_router(graph), prefix='/api',
)
receiver = TestClient(receiver_app)
record = receiver.get(path + '/' + signal_id)
assert record.status_code == 200, record.text
assert record.json()['source_copilot'] == domain
assert receiver.get(path, params={'target_copilot': 's2p'}).json()['count'] == 1
assert receiver.get(path, params={'target_copilot': 'soc'}).json()['count'] == 0
assert receiver.get(path + '/' + decision_id).status_code == 404
assert graph.count_decisions(domain) == before
print('ISOLATED_AND_SHARED:' + domain)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, domain, str(root / "apps" / domain / "backend")],
        cwd=root, env=env, capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"ISOLATED_AND_SHARED:{domain}" in result.stdout
