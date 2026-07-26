from __future__ import annotations

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.transfer_router import create_transfer_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.presets.dataops import DataOpsPreset
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.presets.soc import SOCPreset
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.transfer import SharedPatternRegistry, TransferPattern
from copilot_sdk.transfer.category_mappings import (
    CROSS_COPILOT_MAPPINGS,
    get_mapping,
    list_available_transfers,
)


def test_get_mapping_soc_dataops_returns_mapping_dict() -> None:
    mapping = get_mapping("soc", "dataops")

    assert isinstance(mapping, dict)
    assert mapping


def test_get_mapping_dataops_purchasing_returns_mapping_dict() -> None:
    mapping = get_mapping("dataops", "purchasing")

    assert isinstance(mapping, dict)
    assert mapping


def test_get_mapping_unknown_pair_returns_none() -> None:
    assert get_mapping("missing", "trading") is None


def test_get_mapping_reversed_is_directed() -> None:
    assert get_mapping("dataops", "soc") != get_mapping("soc", "dataops")


def test_list_available_returns_defined_pairs_with_counts() -> None:
    rows = list_available_transfers()

    assert rows
    assert {row["source"] for row in rows} >= {"soc", "dataops"}
    assert all(int(row["categories"]) > 0 for row in rows)


def test_mapping_categories_exist_in_source() -> None:
    presets = {
        "soc": SOCPreset(),
        "dataops": DataOpsPreset(),
        "purchasing": PurchasingPreset(),
        "trading": TradingPreset(),
    }

    for (source, _target), mapping in CROSS_COPILOT_MAPPINGS.items():
        valid = set(presets[source].shape.category_names)
        assert set(mapping).issubset(valid)


def test_mapping_categories_exist_in_target() -> None:
    presets = {
        "soc": SOCPreset(),
        "dataops": DataOpsPreset(),
        "purchasing": PurchasingPreset(),
        "trading": TradingPreset(),
    }

    for (_source, target), mapping in CROSS_COPILOT_MAPPINGS.items():
        valid = set(presets[target].shape.category_names)
        assert set(mapping.values()).issubset(valid)


def test_empty_mapping_rejected() -> None:
    assert all(mapping for mapping in CROSS_COPILOT_MAPPINGS.values())


def _trading_scorer(tmp_path) -> CompoundingScorer:
    scorer = CompoundingScorer.from_preset(
        "trading",
        db_path=str(tmp_path / "trading.db"),
        profile="test",
        graph_store=InMemoryGraphStore(domain="trading"),
    )
    scorer.source_conservation_states = {"dataops": "GREEN"}
    return scorer


def _client(scorer, registry: SharedPatternRegistry | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(create_transfer_router(scorer, pattern_registry=registry))
    return TestClient(app)


def _source_registry() -> SharedPatternRegistry:
    registry = SharedPatternRegistry()
    registry.register(
        TransferPattern(
            pattern_id="dataops-to-trading-test",
            source_copilot="dataops",
            pattern_type="centroid_delta",
            category="schema_change",
            action="strong_execution",
            win_rate=0.8,
            centroid_delta=[0.02 for _ in TradingPreset().shape.factor_names],
            confidence=0.9,
        )
    )
    return registry


def test_execute_dry_run_no_state_change(tmp_path) -> None:
    scorer = _trading_scorer(tmp_path)
    before = scorer.gae_scorer.centroids.copy()

    response = _client(scorer).post(
        "/api/transfer/execute",
        json={"source_domain": "dataops", "target_domain": "trading", "dry_run": True},
    )

    assert response.status_code == 200
    assert response.json()["dry_run"] is True
    assert np.array_equal(scorer.gae_scorer.centroids, before)


def test_execute_refuses_when_conservation_unknown(tmp_path) -> None:
    scorer = CompoundingScorer.from_preset(
        "trading",
        db_path=str(tmp_path / "trading.db"),
        profile="test",
        graph_store=InMemoryGraphStore(domain="trading"),
    )

    response = _client(scorer).post(
        "/api/transfer/execute",
        json={"source_domain": "dataops", "target_domain": "trading", "dry_run": False},
    )

    assert response.status_code == 503
    assert "verified GREEN" in response.json()["detail"]


def test_execute_copies_centroids(tmp_path) -> None:
    scorer = _trading_scorer(tmp_path)
    before = scorer.gae_scorer.centroids.copy()

    response = _client(scorer).post(
        "/api/transfer/execute",
        json={"source_domain": "dataops", "target_domain": "trading", "dry_run": False},
    )

    assert response.status_code == 200
    assert response.json()["patterns_applied"] > 0
    assert not np.array_equal(scorer.gae_scorer.centroids, before)


def test_execute_resets_conservation(tmp_path) -> None:
    scorer = _trading_scorer(tmp_path)
    scorer.graph_store.update_conservation_state(
        domain="trading",
        status="AMBER",
        alpha=0.5,
        q=0.5,
        V=8,
        theta_min=0.1,
        product=0.2,
        categories_total=3,
        categories_with_data=2,
        baseline_product=0.4,
        relative_threshold=0.5,
        complacency_flag="true",
    )

    response = _client(scorer).post(
        "/api/transfer/execute",
        json={"source_domain": "dataops", "target_domain": "trading", "dry_run": False},
    )

    assert response.json()["conservation_reset"] is True
    state = scorer.graph_store.get_conservation_state("trading")
    assert state is not None
    assert state["V"] == 0
    assert state["status"] == "GREEN"


def test_execute_requires_source_green(tmp_path) -> None:
    scorer = _trading_scorer(tmp_path)
    scorer.source_conservation_states = {"dataops": "AMBER"}

    response = _client(scorer).post(
        "/api/transfer/execute",
        json={"source_domain": "dataops", "target_domain": "trading", "dry_run": False},
    )

    assert response.status_code == 200
    assert response.json()["executed"] is False
    assert "GREEN" in response.json()["reason"]


def test_execute_dk_not_transferred(tmp_path) -> None:
    scorer = _trading_scorer(tmp_path)
    before = scorer.get_dk_weights()

    _client(scorer).post(
        "/api/transfer/execute",
        json={"source_domain": "dataops", "target_domain": "trading", "dry_run": False},
    )

    assert scorer.get_dk_weights() == before


def test_execute_log_in_target_store(tmp_path) -> None:
    scorer = _trading_scorer(tmp_path)
    source_store = InMemoryGraphStore(domain="dataops")
    scorer.source_stores = {"dataops": source_store}

    _client(scorer).post(
        "/api/transfer/execute",
        json={"source_domain": "dataops", "target_domain": "trading", "dry_run": False},
    )

    payload = _client(scorer).get("/api/transfer/status").json()
    target_logs = scorer.graph_store.get_centroid_checkpoints("trading", limit=20)
    source_logs = source_store.get_centroid_checkpoints("dataops", limit=20)
    assert payload["warm_started"] is True
    assert payload["source_copilot"] == "dataops"
    assert any(row.get("metadata", {}).get("source") == "transfer_event" for row in target_logs)
    assert any(row.get("metadata", {}).get("source") == "transfer_event" for row in source_logs)


def test_execute_uses_registered_patterns_when_available(tmp_path) -> None:
    scorer = _trading_scorer(tmp_path)

    response = _client(scorer, _source_registry()).post(
        "/api/transfer/execute",
        json={"source_domain": "dataops", "target_domain": "trading", "dry_run": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provenance"] == "transfer"
    assert payload["patterns_applied"] > 0


def test_full_flow_discover_dryrun_execute_validate(tmp_path) -> None:
    scorer = _trading_scorer(tmp_path)
    client = _client(scorer)

    opportunities = client.get("/api/transfer/opportunities").json()
    pair = next(item for item in opportunities["available_transfers"] if item["target"] == "trading")
    dry_run = client.post(
        "/api/transfer/execute",
        json={"source_domain": pair["source"], "target_domain": pair["target"], "dry_run": True},
    ).json()
    applied = client.post(
        "/api/transfer/execute",
        json={"source_domain": pair["source"], "target_domain": pair["target"], "dry_run": False},
    ).json()
    status = client.get("/api/transfer/status").json()

    assert dry_run["dry_run"] is True
    assert applied["conservation_reset"] is True
    assert status["warm_started"] is True
