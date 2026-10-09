from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.transfer_router import create_self_transfer_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.transfer import SharedPatternRegistry, TransferPattern
from tests.graph_store_test_helpers import make_memory_store


SOURCE_ARTIFACT_ID = "artifact:dataops:cross-copilot"


def _green(store: InMemoryGraphStore, domain: str) -> None:
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
    _green(store, "dataops")
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
    store.save_governance("dataops", SOURCE_ARTIFACT_ID, {"kind": "judgment_artifact"})
    SharedPatternRegistry(store, "dataops").register(
        TransferPattern(
            pattern_id="dataops-to-trading-governed",
            source_copilot="dataops",
            pattern_type="centroid_delta",
            category="schema_change",
            action="strong_execution",
            win_rate=0.8,
            centroid_delta=[0.02 for _ in TradingPreset().shape.factor_names],
            confidence=0.9,
            metadata={
                "source_artifact_id": SOURCE_ARTIFACT_ID,
                "source_fingerprint_id": "fingerprint:dataops:governed",
                "factor_mapping": {"volume_anomaly": "event_driven"},
            },
        )
    )
    app = FastAPI()
    app.include_router(create_self_transfer_router(scorer))
    return TestClient(app), scorer


def _transfer_payload(*, source: str = "dataops", target: str = "trading") -> dict[str, object]:
    return {
        "source_domain": source,
        "target_domain": target,
        "source_artifact_ids": [SOURCE_ARTIFACT_ID],
    }


def test_transfer_records_pattern_and_is_idempotent(tmp_path) -> None:
    client, scorer = _trading_client(tmp_path)

    first = client.post(
        "/api/self/transfer",
        json=_transfer_payload(),
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
        json=_transfer_payload(),
    )
    assert second.status_code == 200
    assert second.json()["status"] == "skipped"
    assert second.json()["reason"] == "transfer_already_recorded"
    assert len(scorer.graph_store.get_transfer_patterns()) == len(rows)


def test_transfer_pattern_queryable_by_direction(tmp_path) -> None:
    client, _scorer = _trading_client(tmp_path)
    client.post(
        "/api/self/transfer",
        json=_transfer_payload(),
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
        json=_transfer_payload(),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "skipped"
    assert response.json()["reason"] == "learned_checkpoint_exists"


def test_transfer_blocks_amber_target(tmp_path) -> None:
    client, scorer = _trading_client(tmp_path, target_status="AMBER")

    response = client.post(
        "/api/self/transfer",
        json=_transfer_payload(),
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Conservation threshold not met for trading"
    assert scorer.graph_store.get_transfer_patterns() == []


def test_transfer_unknown_source_returns_404(tmp_path) -> None:
    client, _scorer = _trading_client(tmp_path)

    response = client.post(
        "/api/self/transfer",
        json=_transfer_payload(source="missing"),
    )
    assert response.status_code == 404


@pytest.mark.parametrize("store_kind", ["memory", "sqlite"])
def test_transfer_pattern_store_parity(tmp_path, store_kind: str) -> None:
    if store_kind == "memory":
        store = InMemoryGraphStore(domain="trading")
    else:
        store = make_memory_store(tmp_path / "transfer.sqlite", domain="trading")

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

