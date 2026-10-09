"""Graph-only authority contracts, exercised against real graph backends."""
from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from gae.learning import CalibrationProfile, WeightUpdate

from copilot_sdk.backend.transfer import load_fingerprints, save_fingerprint
from copilot_sdk.evolution import GraphProofLedger, GraphVariantStore, VariantSpec
from copilot_sdk.framework.learning_state import (
    load_from_graph, make_state, read_checkpoint_metadata, save_state,
)
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.outcome import OutcomeLedger
from copilot_sdk.pilot import MeasuredTransferStore
from copilot_sdk.promotion import PromotionRecord, PromotionStore
from copilot_sdk.transfer import SharedPatternRegistry
from copilot_sdk.twin import FrozenSnapshot, FrozenTwinStore
from tests.test_outcome_protocol import _outcome
from tests.transfer.test_registry import _pattern


@pytest.fixture(params=["memory", "age"])
def graph(request: pytest.FixtureRequest) -> Any:
    if request.param == "age":
        return request.getfixturevalue("age_graph_store")("trading")
    return InMemoryGraphStore()


def test_outcome_receipts_are_live_deduplicated_and_newest_first(graph: Any) -> None:
    writer = OutcomeLedger(graph, "trading")
    reader = OutcomeLedger(graph, "trading")
    assert reader.count("test") == 0
    old = _outcome(decision_id="old", timestamp="2026-01-01T00:00:00Z")
    new = _outcome(decision_id="new", timestamp="2026-02-01T00:00:00Z")
    assert writer.append(new)
    assert writer.append(old)
    assert not writer.append(new)
    assert reader.count("test") == 2
    assert reader.list_recent("test", 1) == [new]
    assert reader.list_recent("test", 0) == []
    assert OutcomeLedger(graph, "purchasing").count("test") == 0


def test_promotion_updates_preserve_keys_and_isolate_domains(graph: Any) -> None:
    store = PromotionStore(graph, "trading")
    for identifier in ("z", "a"):
        store.save(PromotionRecord(identifier, "trading", "trend"))
    graph.save_promotion("trading", "unrelated", {"snapshot": {}})
    reader = PromotionStore(graph, "trading")
    assert [row.record_id for row in reader.list_all("trading")] == ["a", "z"]
    assert reader.load_by_class("trading", "trend").record_id == "a"
    assert PromotionStore(graph, "purchasing").load("a") is None
    updated = PromotionRecord("a", "trading", "trend", shadow_decisions=12)
    store.save(updated)
    assert reader.load("a") == updated


def test_proof_event_deduplication_and_recent_window(graph: Any) -> None:
    ledger = GraphProofLedger(graph, "trading")
    ledger.record("decision", {"id": "old"})
    ledger.record("decision", {"id": "old"})
    ledger.record("decision", {"id": "new"})
    rows = GraphProofLedger(graph, "trading").list_entries()
    assert len(rows) == 2
    assert all(isinstance(row["created_at"], float) for row in rows)
    events = graph.get_evolution_events("trading", event_type="proof_record", limit=1)
    assert ledger.list_entries(1)[0]["payload"] == events[0]["metadata"]["payload"]
    assert ledger.list_entries(0) == []


def test_twin_reopen_refuses_overwrite_and_detects_tampering(graph: Any) -> None:
    snapshot = FrozenSnapshot.create(scorer_state={}, kernel_state={},
                                     conservation_state={}, iks_value=0.0,
                                     metadata={"copilot": "trading"})
    FrozenTwinStore(graph, "trading").save(snapshot)
    reader = FrozenTwinStore(graph, "trading")
    assert reader.load("trading").checksum == snapshot.checksum
    with pytest.raises(FileExistsError):
        reader.save(snapshot)
    raw = graph.get_promotion("trading", "frozen_twin:trading")
    raw["snapshot"]["iks_value"] = 99.0
    graph.save_promotion("trading", "frozen_twin:trading", raw)
    with pytest.raises(ValueError, match="checksum"):
        reader.load("trading")


def test_pilot_observation_upsert_and_domain_isolation(graph: Any) -> None:
    row = {"session_id": "session", "decision_id": "decision", "category": "trend",
           "live_correct": False, "frozen_correct": True, "value": 10.0,
           "recorded_at": "2026-01-01T00:00:00Z"}
    writer = MeasuredTransferStore(graph, "trading")
    reader = MeasuredTransferStore(graph, "trading")
    writer.save_observation(row)
    row["live_correct"] = True
    writer.save_observation(row)
    assert reader.observations("session") == [row]
    assert MeasuredTransferStore(graph, "purchasing").observations("session") == []


def test_transfer_patterns_are_live_and_detached(graph: Any) -> None:
    writer = SharedPatternRegistry(graph, "trading")
    reader = SharedPatternRegistry(graph, "trading")
    assert reader.count == 0
    stored = writer.register(_pattern())
    assert reader.get_patterns() == [stored]
    reader.get_patterns()[0].centroid_delta[0] = 999.0
    assert reader.get_patterns()[0].centroid_delta[0] == 0.1
    assert SharedPatternRegistry(graph, "purchasing").count == 0


def test_fingerprint_repeated_exports_accept_changed_data(
    graph: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Coarse clocks can give sequential exports identical epoch timestamps.
    monkeypatch.setattr("copilot_sdk.backend.transfer.time.time", lambda: 1705312200.0)
    first = save_fingerprint("trading", {"factors": []}, graph_store=graph)
    latest = {"factors": [{"name": "x", "sigma": 0.2}]}
    second = save_fingerprint("trading", latest, graph_store=graph)
    assert first != second
    assert load_fingerprints(graph_store=graph)["trading"]["fingerprint"] == latest


def test_learning_checkpoint_round_trip_preserves_weights_and_history(graph: Any) -> None:
    profile = CalibrationProfile()
    state = make_state(np.ones((2, 2)), ["a", "b"], profile, decision_count=7)
    state.history = [WeightUpdate(7, 1705312200.0, 0, "approve", 1,
        np.array([0.1, 0.2]), np.array([0.01, 0.02]), np.zeros((2, 2)),
        np.ones((2, 2)), 0.1, 0.8)]
    save_state(state, {"source": "observations"}, graph, "trading")
    loaded = load_from_graph(graph, "trading", profile)
    assert np.array_equal(loaded.W, state.W)
    assert loaded.decision_count == 7
    assert len(loaded.history) == 1
    assert np.array_equal(loaded.history[0].delta_applied, state.history[0].delta_applied)
    assert read_checkpoint_metadata(graph, "trading") == {"source": "observations"}
    with pytest.raises(KeyError, match="No learning checkpoint"):
        load_from_graph(graph, "purchasing", profile)


def test_fingerprint_equal_epochs_use_publication_order(graph: Any) -> None:
    # Deliberately reverse ID order so ID sorting cannot select the latest export.
    for identifier, tick, value in (("z-older", 1, 0.4), ("a-newer", 2, 0.2)):
        graph.write_fingerprint(
            fingerprint_id=identifier, domain="trading", factor_names=["x"],
            factor_stats={"factors": [{"name": "x", "sigma": value}]},
            skipped_incompatible=0, window=0,
            metadata={"exported_at": 1705312200.0, "export_tick": tick},
        )
    assert load_fingerprints(graph_store=graph)["trading"]["fingerprint_id"] == "a-newer"


def test_fingerprint_catalog_does_not_hide_exports_after_five_hundred(graph: Any) -> None:
    for index in range(501):
        graph.write_fingerprint(
            fingerprint_id=f"export-{index:04d}", domain="trading", factor_names=[],
            factor_stats={"revision": index}, skipped_incompatible=0, window=0,
            metadata={"exported_at": float(index)},
        )
    assert len(graph.list_fingerprints("trading")) == 501
    assert load_fingerprints(graph_store=graph)["trading"]["fingerprint"]["revision"] == 500


def test_variant_history_survives_adapter_recreation(graph: Any) -> None:
    store = GraphVariantStore(graph, "trading")
    store.register_variant(VariantSpec("v", "family"))
    store.record_outcome("v", True, "trend")
    reader = GraphVariantStore(graph, "trading")
    assert reader.get_global_stats("v").total == 1
    assert reader.get_category_stats("trend", "v").successes == 1
    assert GraphVariantStore(graph, "purchasing").get_all_variants() == []


def test_outcome_history_is_not_truncated_at_ten_thousand() -> None:
    graph = InMemoryGraphStore()
    for index in range(10_001):
        receipt = _outcome(decision_id=f"decision-{index}")
        graph.write_evolution_event(f"receipt-{index}", "trading", "verified_outcome",
                                    "operations", receipt.decision_id,
                                    metadata={"receipt": receipt.to_dict()})
    assert OutcomeLedger(graph, "trading").count("test") == 10_001
