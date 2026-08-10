from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.transfer_router import create_self_transfer_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def _green(store: InMemoryGraphStore | SQLiteGraphStore, domain: str) -> None:
    store.update_conservation_state(
        domain=domain,
        status="GREEN",
        alpha=0.9,
        q=0.9,
        V=20,
        theta_min=0.1,
        product=0.7,
        categories_total=3,
        categories_with_data=3,
        baseline_product=0.6,
        relative_threshold=0.1,
        complacency_flag="false",
    )


def _trading_client(tmp_path, *, target_status: str = "GREEN") -> tuple[TestClient, CompoundingScorer]:
    store = InMemoryGraphStore(domain="trading")
    _green(store, "trading")
    if target_status != "GREEN":
        store.update_conservation_state(
            domain="trading",
            status=target_status,
            alpha=0.2,
            q=0.2,
            V=2,
            theta_min=0.1,
            product=0.02,
            categories_total=3,
            categories_with_data=1,
            baseline_product=0.6,
            relative_threshold=0.1,
            complacency_flag="false",
        )
    scorer = CompoundingScorer.from_preset(
        "trading",
        profile="test",
        graph_store=store,
    )
    scorer.source_conservation_states = {"dataops": "GREEN"}
    app = FastAPI()
    app.include_router(create_self_transfer_router(scorer))
    return TestClient(app), scorer


def test_transfer_records_pattern_and_is_idempotent(tmp_path) -> None:
    client, scorer = _trading_client(tmp_path)

    first = client.post(
        "/api/self/transfer",
        json={"source_domain": "dataops", "target_domain": "trading"},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "applied"
    assert first.json()["shape_safe"] is True

    rows = scorer.graph_store.get_transfer_patterns(
        source_domain="dataops",
        target_domain="trading",
    )
    assert rows
    assert all(row["domain"] == "trading" for row in rows)

    second = client.post(
        "/api/self/transfer",
        json={"source_domain": "dataops", "target_domain": "trading"},
    )
    assert second.status_code == 200
    assert second.json()["status"] == "skipped"
    assert second.json()["reason"] == "transfer_already_recorded"
    assert len(scorer.graph_store.get_transfer_patterns()) == len(rows)


def test_transfer_pattern_queryable_by_direction(tmp_path) -> None:
    client, _scorer = _trading_client(tmp_path)
    client.post(
        "/api/self/transfer",
        json={"source_domain": "dataops", "target_domain": "trading"},
    )

    incoming = client.get("/api/self/transfers?direction=incoming").json()
    outgoing = client.get("/api/self/transfers?direction=outgoing").json()
    assert incoming["total"] > 0
    assert all(row["target_domain"] == "trading" for row in incoming["transfers"])
    assert outgoing["total"] == 0


def test_transfer_skips_when_target_has_learned_checkpoint(tmp_path) -> None:
    client, scorer = _trading_client(tmp_path)
    scorer.graph_store.save_centroids(
        "trading",
        "learned",
        scorer.gae_scorer.centroids,
    )

    response = client.post(
        "/api/self/transfer",
        json={"source_domain": "dataops", "target_domain": "trading"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "skipped"
    assert response.json()["reason"] == "learned_checkpoint_exists"


def test_transfer_blocks_amber_target(tmp_path) -> None:
    client, scorer = _trading_client(tmp_path, target_status="AMBER")

    response = client.post(
        "/api/self/transfer",
        json={"source_domain": "dataops", "target_domain": "trading"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "blocked"
    assert response.json()["target_conservation"] == "AMBER"
    assert scorer.graph_store.get_transfer_patterns() == []


def test_transfer_unknown_source_returns_404(tmp_path) -> None:
    client, _scorer = _trading_client(tmp_path)

    response = client.post(
        "/api/self/transfer",
        json={"source_domain": "missing", "target_domain": "trading"},
    )
    assert response.status_code == 404


@pytest.mark.parametrize("store_kind", ["memory", "sqlite"])
def test_transfer_pattern_store_parity(tmp_path, store_kind: str) -> None:
    if store_kind == "memory":
        store = InMemoryGraphStore(domain="trading")
    else:
        store = SQLiteGraphStore(tmp_path / "transfer.sqlite", domain="trading")

    kwargs = {
        "pattern_id": "TR-parity",
        "source_domain": "dataops",
        "target_domain": "trading",
        "pattern_type": "semantic_pattern_transfer",
        "factor_mapping": {"volume_anomaly": "event_driven"},
        "confidence": 0.8,
        "validation_status": "validated",
        "conservation_status": "GREEN",
        "metadata": {"test": True},
    }
    store.write_transfer_pattern(**kwargs)
    store.write_transfer_pattern(**kwargs)
    row = store.get_transfer_patterns()[0]
    assert {
        key: row[key]
        for key in ("domain", "source_domain", "target_domain", "pattern_type", "factor_mapping")
    } == {
        "domain": "trading",
        "source_domain": "dataops",
        "target_domain": "trading",
        "pattern_type": "semantic_pattern_transfer",
        "factor_mapping": {"volume_anomaly": "event_driven"},
    }
