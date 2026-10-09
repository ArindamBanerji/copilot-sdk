"""Real-store integration coverage for the domain namespace adapter."""
from __future__ import annotations

import ast
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from copilot_sdk.graph import GraphStoreNamespace
from copilot_sdk.graph.enrichment import EnrichmentSourceSet, ProvenancedValue
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.protocol import GraphStore, ProductionReadyStore, ProtocolV2GraphStore

Pair = tuple[InMemoryGraphStore, GraphStoreNamespace, GraphStoreNamespace]


@pytest.fixture
def pair() -> Pair:
    store = InMemoryGraphStore(domain="test")
    return store, GraphStoreNamespace(store, "arm_a"), GraphStoreNamespace(store, "arm_b")


def decision(ns: GraphStoreNamespace, category: str = "risk") -> str:
    result: str = ns.write_decision("scoring", category, "accept", 0.8, {"cost": 0.5},
                             {"created_at": 100.0, "entity_group": "suppliers"})
    return result


@pytest.mark.parametrize("namespace", ["", " ", "a::b", "::", "a::"])
def test_invalid_namespace(namespace: str) -> None:
    with pytest.raises(ValueError, match="namespace"):
        GraphStoreNamespace(InMemoryGraphStore(), namespace)


def test_single_colons_and_domain_helpers(pair: Pair) -> None:
    store, _, _ = pair
    ns = GraphStoreNamespace(store, "s2p:run1:ci")
    assert ns._domain("scoring") == "s2p:run1:ci::scoring"
    assert ns._logical_domain(ns._domain("scoring")) == "scoring"
    assert ns._domain("other::scoring") == "s2p:run1:ci::other::scoring"
    for invalid in ("", " "):
        with pytest.raises(ValueError):
            ns._domain(invalid)
    for foreign in ("scoring", "s2p:run1:ci2::scoring", "s2p:run1:ci::"):
        with pytest.raises(ValueError):
            ns._logical_domain(foreign)


def test_row_rewrites_detached_structural_fields_only(pair: Pair) -> None:
    _, ns, _ = pair
    payload = {"domain": "business", "nested": [1]}
    row = {"domain": "arm_a::scoring", "metadata": payload, "factor_mapping": payload,
           "fingerprint": payload, "children": [{"source_domain": "arm_a::x", "target_domain": "arm_a::y"}]}
    rewritten = ns._row(row)
    assert rewritten["domain"] == "scoring"
    assert rewritten["children"] == [{"source_domain": "x", "target_domain": "y"}]
    for field in ("metadata", "factor_mapping", "fingerprint"):
        assert rewritten[field] == payload
    rewritten["metadata"]["nested"].append(2)
    assert payload["nested"] == [1]
    assert row["domain"] == "arm_a::scoring"


@pytest.mark.parametrize("row", [
    {}, {"domain": None}, {"domain": "arm_b::scoring"},
    {"metadata": {"domain": "arm_a::scoring"}},
    {"domain": "arm_a::scoring", "child": {"domain": "arm_b::scoring"}},
    {"source_domain": "arm_a::scoring", "target_domain": "arm_b::scoring"},
])
def test_foreign_or_unscoped_rows_fail_closed(pair: Pair, row: dict[str, Any]) -> None:
    _, ns, _ = pair
    assert not ns._belongs(row)
    assert ns._rows([row]) == []
    with pytest.raises(RuntimeError):
        ns._row(row)


def test_rows_preserve_order_and_nested_projection(pair: Pair) -> None:
    _, ns, _ = pair
    rows: list[dict[str, Any]] = [{"decision": {"domain": "arm_a::scoring", "id": "second"}},
            {"domain": "arm_b::scoring"}, {"domain": "arm_a::scoring", "id": "first"}]
    assert ns._rows(rows) == [{"decision": {"domain": "scoring", "id": "second"}},
                             {"domain": "scoring", "id": "first"}]


def test_complete_protocol_signatures_and_no_production_marker(pair: Pair) -> None:
    _, ns, _ = pair
    typed_store: ProtocolV2GraphStore = ns
    assert isinstance(typed_store, ProtocolV2GraphStore)
    assert not isinstance(ns, ProductionReadyStore)
    methods = {name: method for cls in (GraphStore, ProtocolV2GraphStore)
               for name, method in vars(cls).items() if not name.startswith("_") and callable(method)}
    assert len(methods) == 66
    for name, method in methods.items():
        assert name in vars(GraphStoreNamespace)
        assert inspect.signature(vars(GraphStoreNamespace)[name]) == inspect.signature(method), name
    source = ast.parse(Path(inspect.getfile(GraphStoreNamespace)).read_text())
    assert not any(isinstance(node, ast.FunctionDef) and node.name == "__getattr__" for node in ast.walk(source))
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in {"getattr", "hasattr", "setattr"} for node in ast.walk(source))


def test_unsupported_store_rejected() -> None:
    # Runtime rejection is intentionally exercised with an invalid object.
    with pytest.raises(RuntimeError, match="ProtocolV2GraphStore"):
        GraphStoreNamespace(cast(ProtocolV2GraphStore, object()), "arm")


def test_decision_isolation_and_physical_domain(pair: Pair) -> None:
    store, a, b = pair
    first = decision(a)
    second = decision(b)
    assert first != second
    own = a.get_decision(first, "scoring")
    assert own is not None and own["domain"] == "scoring"
    assert b.get_decision(first, "scoring") is None
    assert store.get_decision(first, "arm_a::scoring")["domain"] == "arm_a::scoring"
    assert a.count_decisions("scoring") == b.count_decisions("scoring") == 1
    assert [r["decision_id"] for r in a.get_all_decisions("scoring")] == [first]
    assert [r["decision_id"] for r in b.get_decisions("scoring", category="risk", limit=1)] == [second]
    assert a.get_decisions("scoring", category="other") == []
    assert a.get_decisions("scoring", limit=0) == []
    assert a.get_decision(second, "arm_b::scoring") is None


def test_outcomes_and_counts_are_isolated(pair: Pair) -> None:
    _, a, b = pair
    key = decision(a)
    decision(b)
    with pytest.raises(KeyError):
        b.write_outcome(key, "accept", True, domain="scoring")
    a.write_outcome(key, "accept", True, {"verified_at": 110.0, "domain": "business", "context": {"domain": "business"}}, domain="scoring",
                    outcome="correct", verified_at_epoch=110.0, quality_signal=0.9,
                    override_comment="checked", verified_by="analyst", analyst_action="accept",
                    final_action="accept", recommended_action="accept", was_override=False)
    row = a.get_decision(key, "scoring", include_outcome=True)
    assert row is not None
    assert row["verified_by"] == "analyst"
    assert row["quality_signal"] == 0.9
    assert a.count_verified("scoring") == a.count_verified_decisions("scoring") == a.count_correct("scoring") == 1
    assert b.count_verified("scoring") == b.count_correct("scoring") == 0
    verified = a.get_verified_decisions("scoring")
    assert len(verified) == 1
    assert verified[0]["outcome_metadata"]["domain"] == "business"
    assert b.get_verified_decisions("scoring") == []


def test_legacy_id_override_is_delegated(pair: Pair) -> None:
    store, a, _ = pair
    key = a.write_decision(
        "scoring", "risk", "reject", 0.2, {}, {"decision_id": "explicit-id"}
    )
    assert key == "explicit-id"
    assert store.get_decision(key, "arm_a::scoring") is not None


@pytest.mark.parametrize("family", ["evolution", "posterior", "promotion", "ledger", "governance"])
def test_platform_state_families_preserve_opaque_payloads(pair: Pair, family: str) -> None:
    _, a, b = pair
    def operations(ns: GraphStoreNamespace) -> tuple[Callable[..., None], Callable[..., Any], Callable[..., Any], Callable[..., None]]:
        return {
            "evolution": (ns.save_evolution, ns.get_evolution, ns.list_evolutions, ns.delete_evolution),
            "posterior": (ns.save_posterior, ns.get_posterior, ns.list_posteriors, ns.delete_posterior),
            "promotion": (ns.save_promotion, ns.get_promotion, ns.list_promotions, ns.delete_promotion),
            "ledger": (ns.save_ledger, ns.get_ledger, ns.list_ledgers, ns.delete_ledger),
            "governance": (ns.save_governance, ns.get_governance, ns.list_governance, ns.delete_governance),
        }[family]
    save_a, get_a, list_a, delete_a = operations(a)
    save_b, get_b, list_b, _ = operations(b)
    payload = {"domain": "business", "value": [1]}
    save_a("scoring", "same-key", payload)
    assert get_b("scoring", "same-key") is None
    assert list_b("scoring") == []
    save_b("scoring", "same-key", {"value": [2]})
    assert get_a("scoring", "same-key") == payload
    assert list_a("scoring") == [{"key": "same-key", **payload}]
    delete_a("scoring", "same-key")
    assert get_a("scoring", "same-key") is None
    assert get_b("scoring", "same-key") == {"value": [2]}


def test_evolution_state_aliases(pair: Pair) -> None:
    _, a, b = pair
    a.save_evolution_state("scoring", "variant", {"generation": 2})
    assert a.get_evolution_state("scoring", "variant") == {"generation": 2}
    assert b.get_evolution_state("scoring", "variant") is None


def test_centroids_and_checkpoint_results(pair: Pair) -> None:
    store, a, b = pair
    a.save_centroids("scoring", "risk", [[1.0, 2.0]], {"regime_tag": "normal"}, decisions_count=7)
    np.testing.assert_array_equal(a.load_latest_centroids("scoring"), [[1.0, 2.0]])
    assert b.load_latest_centroids("scoring") is None
    assert b.get_centroid_checkpoints("scoring") == []
    row = a.get_centroid_checkpoints("scoring", limit=1)[0]
    assert row["domain"] == "scoring"
    assert row["decisions_count"] == 7
    latest = a.load_latest_checkpoint_for_regime("scoring", "normal")
    assert latest is not None and latest["domain"] == "scoring"
    assert store.get_centroid_checkpoints("arm_a::scoring")[0]["domain"] == "arm_a::scoring"


def test_governed_ids_and_conflicts(pair: Pair) -> None:
    _, a, b = pair
    key = a.generate_decision_id("scoring")
    assert isinstance(key, str) and key
    a.write_governed_decision(key, "scoring", "risk", 1, "accept", 0, 0.8, [0.8, 0.2], [0.5], ["cost"])
    row = a.get_decision(key, "scoring")
    assert row is not None and row["domain"] == "scoring"
    assert row["factor_names"] == ["cost"]
    assert b.get_decision(key, "scoring") is None
    with pytest.raises(ValueError, match="conflicting"):
        b.write_governed_decision(key, "scoring", "risk", 1, "accept", 0, 0.8, [0.8, 0.2], [0.5], ["cost"])
    assert a.get_decision(key, "scoring") == row


def test_observation_and_entity_writes(pair: Pair) -> None:
    store, a, b = pair
    a.write_observation("observation-a", "scoring", "risk", "accept", 0.8, "/score", "v1", "v1", "supplier", [0.5], ["cost"])
    assert store._observations["observation-a"]["domain"] == "arm_a::scoring"
    assert a.count_decisions("scoring") == b.count_decisions("scoring") == 0
    key = decision(a)
    a.link_entity(key, "supplier", "Supplier", "scoring")
    assert store._edges[-1]["domain"] == "arm_a::scoring"
    assert a.contextual_judgment("scoring", "suppliers", "risk")[0]["decision"]["domain"] == "scoring"
    assert b.contextual_judgment("scoring", "suppliers", "risk") == []
    assert b.decision_movement("scoring", key) == []
    assert a.decision_movement("scoring", key)


def test_receipt_chains_are_domain_scoped(pair: Pair) -> None:
    store, a, b = pair
    first = decision(a)
    second = decision(b)
    idx_a, hash_a = a.append_evidence_receipt("same-intent", "scoring", first, {"value": 1}, "analyst", "/learn")
    idx_b, hash_b = b.append_evidence_receipt("same-intent", "scoring", second, {"value": 2}, "analyst", "/learn")
    assert idx_a == idx_b == 0
    assert hash_a != hash_b
    assert store._evidence_receipts[("arm_a::scoring", "same-intent")]["decision_id"] == first
    assert a.append_evidence_receipt("next", "scoring", first, {}, "analyst", "/learn")[0] == 1


def test_v2_checkpoint_lineage_and_trajectory(pair: Pair) -> None:
    _, a, b = pair
    key = decision(a)
    a.write_centroid_checkpoint("checkpoint-a", "scoring", "risk", "accept", [[0.5]], 1, 0, 0.4, [1, 1], "hash",
                                quality_window_size=1, quality_verified_count=0, quality_correct_count=0,
                                metadata={"regime_tag": "normal"}, decision_id=key)
    lineage = a.get_checkpoint_lineage("scoring", "checkpoint-a")
    assert lineage is not None and lineage["decision_id"] == key
    assert b.get_checkpoint_lineage("scoring", "checkpoint-a") is None
    assert a.get_decision_checkpoints("scoring", key)[0]["domain"] == "scoring"
    assert b.get_decision_checkpoints("scoring", key) == []
    assert a.get_iks_trajectory(["scoring"])[0]["domain"] == "scoring"
    assert b.get_iks_trajectory(["scoring"]) == []
    assert a.get_iks_trajectory(["scoring"], start=0.0, end=1.0) == []


def test_conservation_and_fingerprint_discovery(pair: Pair) -> None:
    _, a, b = pair
    a.write_conservation_status("status-a", "scoring", 0, 0.0, 0.05, 0.5, 0, 0, "RED", "v1")
    assert a.get_latest_conservation_statuses(["scoring"])[0]["domain"] == "scoring"
    assert b.get_latest_conservation_statuses(["scoring"]) == []
    a.write_fingerprint("fingerprint-a", "scoring", ["cost"], {"domain": "business", "cost": 0.5}, 0, 10)
    row = a.list_fingerprints("scoring")[0]
    assert row["domain"] == "scoring"
    assert row["fingerprint"]["domain"] == "business"
    assert b.list_fingerprints("scoring") == []


def test_evolution_events_and_promotion_projections(pair: Pair) -> None:
    _, a, b = pair
    a.write_evolution_event("event-a", "scoring", "promotion", "rule", "variant", metric=0.9, shadow_batch_size=4)
    rows = a.get_evolution_events("scoring", event_type="promotion", limit=1)
    assert rows[0]["domain"] == "scoring" and rows[0]["shadow_batch_size"] == 4
    assert a.get_evolution_events("scoring", event_type="other") == []
    assert b.get_evolution_events("scoring") == []
    assert a.promotion_basis("scoring", "rule")[0]["evolution_event"]["domain"] == "scoring"
    assert b.promotion_basis("scoring", "rule") == []


def test_transfer_filters_and_witness(pair: Pair) -> None:
    store, a, b = pair
    a.write_transfer_pattern("transfer-a", "source", "target", "mapping", {"domain": "business"}, 0.8, "valid", "GREEN")
    for rows in (a.get_transfer_patterns(source_domain="source"), a.get_transfer_patterns(target_domain="target"),
                 a.get_transfer_patterns("source", "target")):
        assert rows[0]["source_domain"] == "source" and rows[0]["target_domain"] == "target"
        assert rows[0]["factor_mapping"] == {"domain": "business"}
        assert rows[0]["domain"] == "test"  # Store catalogue, not transfer endpoint.
    assert b.get_transfer_patterns("source", "target") == []
    assert a.transfer_witness("source", "target", "transfer-a")[0]["transfer_pattern"]["target_domain"] == "target"
    store.write_transfer_pattern("foreign", "arm_a::source", "arm_b::target", "mapping", {}, 0.8, "valid", "GREEN")
    assert len(a.get_transfer_patterns(source_domain="source")) == 1
    assert b.get_transfer_patterns(target_domain="target") == []


def test_enrichment_records_keep_metric_namespace(pair: Pair) -> None:
    store, a, b = pair
    metric = ProvenancedValue.from_fixture(0.5)
    receipt = a.write_entity_enrichment(domain="scoring", entity_type="Supplier", entity_id="supplier",
                  namespace="metrics", metrics={"risk": metric}, computed_from=EnrichmentSourceSet(fixture_sources=["fixture"]))
    assert receipt.persisted and receipt.domain == "scoring" and receipt.namespace == "metrics"
    rows = a.list_entity_enrichments(domain="scoring", namespace="metrics")
    assert len(rows) == 1 and rows[0].domain == "scoring" and rows[0].value == metric
    assert a.read_entity_enrichment(domain="scoring", entity_type="Supplier", entity_id="supplier", namespace="metrics") == {"risk": metric}
    assert b.read_entity_enrichment(domain="scoring", entity_type="Supplier", entity_id="supplier") == {}
    assert b.list_entity_enrichments(domain="scoring") == []
    assert store.list_entity_enrichments(domain="arm_a::scoring")[0].domain == "arm_a::scoring"


def test_archival_is_domain_bounded(pair: Pair) -> None:
    _, a, b = pair
    first, second = decision(a), decision(b)
    assert a.archive_decisions("scoring", before=101.0) == 1
    assert a.get_decision(first, "scoring") is None
    assert b.get_decision(second, "scoring") is not None
    assert a.count_archived("scoring") == 1 and b.count_archived("scoring") == 0
    assert a.get_archived_decisions("scoring")[0]["domain"] == "scoring"
    assert b.get_archived_decisions("scoring") == []
    decision(a)
    assert a.archive_old_decisions("scoring", keep_recent=0) == 1
    assert b.count_decisions("scoring") == 1


@pytest.mark.parametrize("operation", ["reset", "fingerprints", "transfers", "conservation", "trajectory"])
def test_inventory_and_reset_operations_remain_namespace_bounded(pair: Pair, operation: str) -> None:
    _, a, b = pair
    key = decision(b)
    operations: dict[str, Callable[[], object]] = {
        "reset": lambda: a.domain_scoped_reset("scoring"), "fingerprints": a.list_fingerprints,
        "transfers": a.get_transfer_patterns, "conservation": a.get_latest_conservation_statuses,
        "trajectory": a.get_iks_trajectory,
    }
    assert operations[operation]() in (None, [])
    assert b.get_decision(key, "scoring") is not None


def test_empty_domain_selection_returns_nothing(pair: Pair) -> None:
    _, a, _ = pair
    a.write_conservation_status("status-a", "scoring", 0, 0.0, 0.05, 0.5, 0, 0, "RED", "v1")
    assert a.get_latest_conservation_statuses([]) == []
    assert a.get_iks_trajectory([]) == []


def test_close_does_not_own_shared_lifecycle(pair: Pair) -> None:
    store, a, b = pair
    a.close()
    key = decision(b)
    assert b.get_decision(key, "scoring") is not None
    assert store.count_decisions("arm_b::scoring") == 1
    # Memory close is also a no-op; inspect the adapter to prove it never delegates.
    assert "self._store" not in inspect.getsource(GraphStoreNamespace.close)


def test_single_colon_boundary_cannot_alias_another_namespace(pair: Pair) -> None:
    store, a, _ = pair
    adjacent = GraphStoreNamespace(store, "arm_a:")
    key = decision(adjacent)
    assert adjacent.get_decision(key, "scoring") is not None
    assert a.get_decision(key, "scoring") is None
    assert not a._belongs({"domain": "arm_a:::scoring"})
    with pytest.raises(ValueError, match="colon"):
        a.get_decision(key, ":scoring")
