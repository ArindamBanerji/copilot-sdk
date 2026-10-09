from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import re
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from copilot_sdk.backend.graph_signals import GraphSignalEvents
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.testing.fixtures import age_test_dsn

from copilot_sdk.backend.cross_signal_router import (
    EVICTION_BATCH,
    MAX_SIGNALS,
    create_cross_signal_router,
)


SIGNAL = {
    "source_copilot": "soc",
    "signal_type": "vendor_credential_compromised",
    "entity_id": "vendor-acme-corp",
    "confidence": 0.92,
    "detail": "Credential found in leak-forum toolkit",
}


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_cross_signal_router(InMemoryGraphStore()), prefix="/api")
    return TestClient(app)


def test_publish_signal_201() -> None:
    response = _client().post("/api/platform/cross-signals", json=SIGNAL)
    assert response.status_code == 201
    assert response.json()["status"] == "published"


def test_get_signals_empty() -> None:
    response = _client().get("/api/platform/cross-signals")
    assert response.status_code == 200
    assert response.json()["signals"] == []


def test_get_signals_after_publish() -> None:
    client = _client()
    client.post("/api/platform/cross-signals", json=SIGNAL)
    payload = client.get("/api/platform/cross-signals").json()
    assert payload["count"] == 1
    assert payload["signals"][0]["entity_id"] == SIGNAL["entity_id"]


def test_get_signal_by_id() -> None:
    client = _client()
    signal_id = client.post("/api/platform/cross-signals", json=SIGNAL).json()["signal_id"]
    response = client.get(f"/api/platform/cross-signals/{signal_id}")
    assert response.status_code == 200
    assert response.json()["signal_id"] == signal_id


def test_signal_shape() -> None:
    client = _client()
    signal_id = client.post("/api/platform/cross-signals", json=SIGNAL).json()["signal_id"]
    payload = client.get(f"/api/platform/cross-signals/{signal_id}").json()
    assert set(SIGNAL).issubset(payload)
    assert {"signal_id", "honesty_note"}.issubset(payload)


def test_f26_honesty() -> None:
    payload = _client().post("/api/platform/cross-signals", json=SIGNAL).json()
    assert "transfer facts" in payload["honesty_note"]
    assert "per-copilot" in payload["honesty_note"]


def test_signal_id_uses_uuid_format() -> None:
    signal_id = _client().post("/api/platform/cross-signals", json=SIGNAL).json()["signal_id"]
    assert re.fullmatch(r"sig-[0-9a-f]{32}", signal_id)


def test_concurrent_publish_unique_ids() -> None:
    client = _client()
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda index: client.post(
                    "/api/platform/cross-signals",
                    json={**SIGNAL, "entity_id": f"concurrent-{index}"},
                ),
                range(2),
            )
        )
    assert all(response.status_code == 201 for response in responses)
    assert len({response.json()["signal_id"] for response in responses}) == 2


def test_cap_enforced_with_oldest_batch_evicted() -> None:
    client = _client()
    signal_ids = []
    for index in range(MAX_SIGNALS + 1):
        response = client.post(
            "/api/platform/cross-signals",
            json={**SIGNAL, "entity_id": f"entity-{index}"},
        )
        assert response.status_code == 201
        signal_ids.append(response.json()["signal_id"])

    payload = client.get(
        "/api/platform/cross-signals",
        params={"limit": MAX_SIGNALS},
    ).json()
    assert payload["count"] == MAX_SIGNALS - EVICTION_BATCH + 1
    assert client.get(f"/api/platform/cross-signals/{signal_ids[0]}").status_code == 404
    assert client.get(f"/api/platform/cross-signals/{signal_ids[-1]}").status_code == 200


def test_list_pagination() -> None:
    client = _client()
    for index in range(5):
        client.post(
            "/api/platform/cross-signals",
            json={**SIGNAL, "entity_id": f"paged-{index}"},
        )
    payload = client.get(
        "/api/platform/cross-signals",
        params={"limit": 2, "offset": 1},
    ).json()
    assert payload["count"] == 5
    assert payload["limit"] == 2
    assert payload["offset"] == 1
    assert [item["entity_id"] for item in payload["signals"]] == ["paged-1", "paged-2"]


def test_old_signals_excluded() -> None:
    client = _client()
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    signal_id = client.post(
        "/api/platform/cross-signals",
        json={**SIGNAL, "timestamp": old_timestamp},
    ).json()["signal_id"]
    assert client.get("/api/platform/cross-signals").json()["count"] == 0
    assert client.get(f"/api/platform/cross-signals/{signal_id}").status_code == 404


def test_invalid_pagination_rejected() -> None:
    client = _client()
    assert client.get("/api/platform/cross-signals", params={"limit": 0}).status_code == 422
    assert client.get("/api/platform/cross-signals", params={"offset": -1}).status_code == 422


def test_signal_empty_type_rejected() -> None:
    response = _client().post(
        "/api/platform/cross-signals",
        json={**SIGNAL, "signal_type": ""},
    )
    assert response.status_code == 422


def test_signal_empty_entity_rejected() -> None:
    response = _client().post(
        "/api/platform/cross-signals",
        json={**SIGNAL, "entity_id": ""},
    )
    assert response.status_code == 422


def test_signal_invalid_timestamp_rejected() -> None:
    response = _client().post(
        "/api/platform/cross-signals",
        json={**SIGNAL, "timestamp": "not-a-date"},
    )
    assert response.status_code == 422


def test_signal_valid_timestamp_accepted() -> None:
    response = _client().post(
        "/api/platform/cross-signals",
        json={**SIGNAL, "timestamp": "2026-09-19T12:00:00Z"},
    )
    assert response.status_code == 201

def _shared_client(graph: GraphStore) -> TestClient:
    app = FastAPI()
    app.include_router(create_cross_signal_router(graph), prefix="/api")
    return TestClient(app)


def test_independent_apps_deliver_signal_through_shared_graph() -> None:
    graph = InMemoryGraphStore()
    with _shared_client(graph) as publisher, _shared_client(graph) as receiver:
        result = publisher.post("/api/platform/cross-signals", json=SIGNAL)
        assert result.status_code == 201
        signal_id = result.json()["signal_id"]
        assert receiver.get("/api/platform/cross-signals").json()["count"] == 1
        assert receiver.get(f"/api/platform/cross-signals/{signal_id}").json()["entity_id"] == SIGNAL["entity_id"]
    with _shared_client(graph) as reopened:
        assert reopened.get(f"/api/platform/cross-signals/{signal_id}").status_code == 200


def test_publish_in_another_process(age_graph_store: Callable[[str], Any]) -> None:
    graph = age_graph_store("trading")
    with _shared_client(graph) as receiver:
        command = (
            "import json,sys; from ci_platform.graph import AGEGraphStoreAdapter; "
            "from copilot_sdk.backend.graph_signals import GraphSignalEvents; "
            "graph = AGEGraphStoreAdapter(dsn=sys.stdin.readline().strip(), graph_name=sys.argv[1]); "
            "print(GraphSignalEvents(graph).publish(json.loads(sys.argv[2]))); graph.close()"
        )
        result = subprocess.run(
            [sys.executable, "-c", command, graph._store._client._graph, json.dumps(SIGNAL)],
            input=age_test_dsn() + "\n", check=True, capture_output=True, text=True, timeout=60,
        )
        signal_id = result.stdout.strip()
        assert receiver.get(f"/api/platform/cross-signals/{signal_id}").status_code == 200


def test_shared_graph_concurrent_publish_and_cap() -> None:
    graph = InMemoryGraphStore()
    stores = [GraphSignalEvents(graph), GraphSignalEvents(graph)]
    for _ in range(MAX_SIGNALS - 1):
        stores[0].publish(SIGNAL)
    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(lambda index: stores[index % 2].publish(SIGNAL), range(20)))
    assert len(set(ids)) == 20
    assert stores[1].count() == MAX_SIGNALS - 1 + 20 - EVICTION_BATCH
    assert all(stores[0].get(signal_id) is not None for signal_id in ids)


def test_shared_filters_and_pagination() -> None:
    with _shared_client(InMemoryGraphStore()) as client:
        for target in (None, "trading", "purchasing"):
            client.post("/api/platform/cross-signals", json={**SIGNAL, "target_copilot": target})
        payload = client.get("/api/platform/cross-signals",
                             params={"target_copilot": "trading", "limit": 1, "offset": 1}).json()
        assert payload["count"] == 2
        assert payload["signals"][0]["target_copilot"] == "trading"
        assert client.get("/api/platform/cross-signals",
                          params={"source_copilot": "missing"}).json()["count"] == 0


def test_shared_ttl_applies_to_other_apps() -> None:
    graph = InMemoryGraphStore()
    with _shared_client(graph) as publisher, _shared_client(graph) as receiver:
        response = publisher.post("/api/platform/cross-signals", json={
            **SIGNAL, "timestamp": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
        })
        assert response.status_code == 201
        assert receiver.get("/api/platform/cross-signals").json()["count"] == 0
        assert receiver.get("/api/platform/cross-signals/" + response.json()["signal_id"]).status_code == 404


def test_shared_graph_preserves_untrusted_text() -> None:
    store = GraphSignalEvents(InMemoryGraphStore())
    entity = "'; DROP TABLE signals; --"
    signal_id = store.publish({**SIGNAL, "entity_id": entity})
    record = store.get(signal_id)
    assert record is not None and record["entity_id"] == entity
    assert store.count() == 1


def test_shared_graph_independent_of_working_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    graph = InMemoryGraphStore()
    signal_id = GraphSignalEvents(graph).publish(SIGNAL)
    monkeypatch.chdir(tmp_path)
    assert GraphSignalEvents(graph).get(signal_id) is not None
    assert list(tmp_path.iterdir()) == []


def test_explicit_graph_adapter_reads_written_event() -> None:
    graph = InMemoryGraphStore()
    store = GraphSignalEvents(graph)
    signal_id = store.publish(SIGNAL)

    record = store.get(signal_id)
    assert record is not None
    assert record["source_copilot"] == SIGNAL["source_copilot"]
    events = graph.get_evolution_events("cross_signals_ZGVmYXVsdA", limit=None)
    assert len(events) == 1
    assert events[0]["metadata"]["payload"] == record
