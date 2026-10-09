"""Portable readback expectations; construction is the only backend-specific step."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, cast
from unittest.mock import patch

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.protocol import (
    EnrichmentSourceSet, GraphTraversalStore, L5LearningStore, ProtocolV2GraphStore,
    ProvenancedValue, ScoringPersistenceStore,
)


class ConformanceStore(ProtocolV2GraphStore, L5LearningStore, GraphTraversalStore, ScoringPersistenceStore, Protocol):
    pass


@pytest.fixture
def store() -> ConformanceStore:
    return cast(ConformanceStore, InMemoryGraphStore(domain="contract"))


DECISION_KEYS = set("""decision_id domain entity_id category category_index recommended_action
recommended_index confidence factors factor_vector probabilities status metadata created_at
factor_names source scorer_version preset_version factor_schema_version correct outcome
verified_at_epoch quality_signal override_comment verified_by analyst_action final_action was_override""".split())
OUTCOME_KEYS = {"actual_action", "actual_index", "is_correct", "verified_at", "outcome_metadata"}
CHECKPOINT_KEYS = set("""checkpoint_id domain decision_id category action centroids decisions_count
verified_count iks shape factor_names_hash quality_window_size quality_verified_count quality_correct_count
rolling_accuracy quality_window_end quality_policy_version metadata created_at decision_time_start
decision_time_end checkpoint_time""".split())
EVENT_KEYS = set("""event_id domain event_type rule_name variant_id source_copilot source_rule metric
shadow_batch_size min_shadow_batches metadata timestamp""".split())


def decision(store: ProtocolV2GraphStore, identifier: str = "d", *, timestamp: float = 10.0,
             domain: str = "contract", category: str = "risk") -> None:
    store.write_governed_decision(
        identifier, domain, category, 0, "approve", 0, 0.8, [0.8, 0.2], [0.5], ["risk"],
        source="score", scorer_version="s1", preset_version="p1", factor_schema_version="f1",
        metadata={"created_at": timestamp, "entity_id": "entity", "entity_group": "group"},
    )


def checkpoint(store: ProtocolV2GraphStore, identifier: str = "cp", *, category: str = "risk",
               domain: str = "contract", decision_id: str | None = None, **kwargs: Any) -> None:
    store.write_centroid_checkpoint(identifier, domain, category, "approve", [[0.5]], 3, 2,
                                    0.7, [1, 1], "hash", decision_id=decision_id, **kwargs)


def event(store: ProtocolV2GraphStore, identifier: str = "ev", *, timestamp: float = 10.0,
          domain: str = "contract", event_type: str = "promoted", rule_name: str = "rule",
          variant_id: str = "v") -> None:
    store.write_evolution_event(identifier, domain, event_type, rule_name, variant_id,
                               metadata={"timestamp": timestamp})


def conservation(store: L5LearningStore) -> str:
    return cast(str, store.update_conservation_state("contract", "GREEN", 0.2, 0.8, 10, 1.0, 1.6,
                                            2, 1, 1.0, 0.9, "false"))


class TestReadbackShapes:
    def test_archived_decision(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        decision(store)
        store.archive_decisions("contract", before=20.0)
        row = store.get_archived_decisions("contract")[0]
        assert set(row) == set("""decision_id domain category category_index recommended_action recommended_index
            confidence factor_vector probabilities created_at actual_action actual_index is_correct verified_at archived_at archive_reason metadata""".split())
        for field in ("actual_action", "actual_index", "is_correct", "verified_at"):
            assert row[field] is None
        assert type(row["archived_at"]) is float and type(row["created_at"]) is float
        assert store.get_all_decisions("contract") == []

    def test_transfer_pattern(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        store.write_transfer_pattern("p", "contract", "target", "rule", {"risk": "cost"}, 0.8, "valid", "GREEN")
        row = store.get_transfer_patterns("contract", "target")[0]
        assert set(row) == set("""pattern_id domain source_domain target_domain pattern_type source_rule target_rule
            factor_mapping confidence validation_status conservation_status source_fingerprint_id evolution_event_id metadata created_at similarity_score""".split())
        assert row["factor_mapping"] == {"risk": "cost"} and row["similarity_score"] == 0.8
        assert type(row["created_at"]) is float
        for field in ("source_rule", "target_rule", "source_fingerprint_id", "evolution_event_id"):
            assert row[field] is None
        assert store.transfer_witness("contract", "target", "p") == [{"transfer_pattern": row}]

    def test_governed_decision(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        decision(store)
        row = store.get_decision("d", "contract")
        assert row is not None and set(row) == DECISION_KEYS
        assert row["factor_names"] == ["risk"] and row["factor_vector"] == [0.5]
        assert row["factors"] == {"risk": 0.5}
        assert (row["source"], row["scorer_version"], row["preset_version"], row["factor_schema_version"]) == ("score", "s1", "p1", "f1")
        assert row["metadata"]["entity_id"] == "entity"
        assert store.get_decisions("contract") == store.get_all_decisions("contract") == [row]

    def test_basic_decision(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        identifier = store.write_decision("contract", "risk", "approve", 0.8, {"risk": 0.5})
        row = store.get_decision(identifier, "contract")
        assert row is not None and set(row) == DECISION_KEYS
        assert type(identifier) is str and row["decision_id"] == identifier
        assert row["factors"] == {"risk": 0.5}

    def test_outcome(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        decision(store)
        store.write_outcome("d", "review", False, {"actual_index": 1, "verified_at": 20.0,
                                                   "context": {"reason": "risk"}}, domain="contract")
        row = store.get_decision("d", "contract", include_outcome=True)
        assert row is not None and set(row) == DECISION_KEYS | OUTCOME_KEYS
        assert row["actual_index"] == 1 and row["is_correct"] is False
        assert row["outcome_metadata"]["context"] == {"reason": "risk"}
        assert store.get_verified_decisions("contract") == [row]

    @pytest.mark.parametrize("v2", [False, True])
    def test_checkpoints(self, store: ConformanceStore, v2: bool) -> None:
        # Conformance: AGE must also pass this test
        if v2:
            checkpoint(store)
        else:
            store.save_centroids("contract", "risk", [[0.5]])
        row = store.get_centroid_checkpoints("contract", include_v2=True)[0]
        assert set(row) == CHECKPOINT_KEYS
        assert row["centroids"] == [[0.5]] and row["metadata"] == {}

    def test_checkpoint_readers_agree(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        decision(store)
        checkpoint(store, decision_id="d", metadata={"regime_tag": "steady"})
        rows = store.get_centroid_checkpoints("contract", include_v2=True)
        assert store.get_decision_checkpoints("contract", "d") == rows
        assert store.get_iks_trajectory(["contract"]) == rows
        assert store.load_latest_checkpoint_for_regime("contract", "steady") == rows[0]
        assert store.get_checkpoint_lineage("contract", "cp") == store.get_decision("d", "contract")

    def test_centroids(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        store.update_centroid("contract", "risk", "approve", [0.5], 0.1)
        row = store.get_centroids("contract")[0]
        assert set(row) == {"category", "action", "vector_json", "delta_norm", "caused_by_decision_id", "updated_at"}
        assert row["vector_json"] == [0.5] and row["delta_norm"] == 0.1

    def test_dk_weights(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        store.update_dk_weights("contract", [[0.5]], 2, 10.0)
        row = store.get_dk_weights("contract")
        assert row is not None and set(row) == {"domain", "weight_json", "n_decisions_used", "computed_at",
            "supersedes_id", "created_at", "welford_state", "n_confirmed", "n_overridden", "entity_group"}
        assert row["weight_json"] == [[0.5]]

    def test_conservation(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        identifier = conservation(store)
        row = store.get_conservation_state("contract")
        assert row is not None and set(row) == set("""id domain status alpha q V theta_min product categories_total
            categories_with_data baseline_product relative_threshold complacency_flag caused_by_decision_id old_status updated_at""".split())
        assert type(identifier) is str and row["id"] == identifier

    def test_conservation_snapshots(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        store.write_conservation_status("status", "contract", 10, 0.8, 0.2, 1.0, 10, 8, "GREEN", "v1")
        row = store.get_latest_conservation_statuses(["contract"])[0]
        assert set(row) == set("status_id snapshot_id counts_scope domain V q alpha theta_min verified_count correct_count status policy_version computed_at".split())
        assert row["status_id"] == row["snapshot_id"] == "status" and row["counts_scope"] == "verified_only"

    @pytest.mark.parametrize("legacy", [False, True])
    def test_events(self, store: ConformanceStore, legacy: bool) -> None:
        # Conformance: AGE must also pass this test
        if legacy:
            store.save_evolution_event("contract", "promoted", "rule", "v")
        else:
            event(store)
        row = store.get_evolution_events("contract")[0]
        assert set(row) == EVENT_KEYS and row["event_type"] == "promoted"

    def test_entity_links(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        decision(store)
        store.link_entity("d", "entity", "supplier", domain="contract")
        row = store.get_decision_links("d", domain="contract")[0]
        assert set(row) == {"decision_id", "entity_id", "edge_type", "created_at"}
        assert row["decision_id"] == "d" and row["entity_id"] == "entity"

    def test_fingerprints(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        store.write_fingerprint("fp", "contract", ["risk"], {"risk": {"mean": 0.5}}, 0, 10)
        row = store.list_fingerprints("contract")[0]
        assert set(row) == {"domain", "fingerprint_id", "fingerprint", "factor_names", "metadata"}
        assert row["fingerprint"] == {"risk": {"mean": 0.5}}

    @pytest.mark.parametrize("kind", ["evolution", "posterior", "promotion", "ledger", "governance"])
    def test_opaque_state(self, store: ConformanceStore, kind: str) -> None:
        # Conformance: AGE must also pass this test
        payload = {"optional": None, "nested": {"created_at": "caller-owned"}}
        getattr(store, f"save_{kind}")("contract", "key", payload)
        assert getattr(store, f"get_{kind}")("contract", "key") == payload
        plural = "governance" if kind == "governance" else kind + "s"
        assert getattr(store, f"list_{plural}")("contract") == [{"key": "key", **payload}]

    def test_read_copies_preserve_replay(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        decision(store)
        checkpoint(store)
        row = store.get_decision("d", "contract")
        assert row is not None
        row["factor_names"].append("mutated")
        row["metadata"]["factor_names"].append("mutated")
        store.get_centroid_checkpoints("contract", include_v2=True)[0]["centroids"][0][0] = 99
        decision(store)
        checkpoint(store)
        assert store.get_decision("d", "contract")["factor_names"] == ["risk"]  # type: ignore[index]
        assert store.get_centroid_checkpoints("contract", include_v2=True)[0]["centroids"] == [[0.5]]


class TestTimestamps:
    def test_decision_and_outcome(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        decision(store, timestamp=10.0)
        store.write_outcome("d", "approve", True, {"verified_at": 20}, domain="contract", verified_at_epoch=20.0)
        row = store.get_decision("d", "contract", include_outcome=True)
        assert row is not None
        for key, expected in (("created_at", 10.0), ("verified_at", 20.0), ("verified_at_epoch", 20.0)):
            assert type(row[key]) is float and row[key] == expected

    @pytest.mark.parametrize("value", [10.0, "1970-01-01T00:00:10Z", "1970-01-01T01:00:10+01:00", "1970-01-01T00:00:10"])
    def test_checkpoint_times(self, store: ConformanceStore, value: Any) -> None:
        # Conformance: AGE must also pass this test
        store.save_centroids("contract", "risk", [[0.5]], created_at=10,
                             checkpoint_time=value, decision_time_start=value, decision_time_end=value)
        row = store.get_centroid_checkpoints("contract")[0]
        assert type(row["created_at"]) is float and row["created_at"] == 10.0
        expected_text = str(value)
        for field in ("checkpoint_time", "decision_time_start", "decision_time_end"):
            assert type(row[field]) is str and row[field] == expected_text

    def test_quality_window(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        checkpoint(store, quality_window_end="1970-01-01T00:00:10Z")
        row = store.get_centroid_checkpoints("contract", include_v2=True)[0]
        assert type(row["created_at"]) is float
        assert row["quality_window_end"] == "1970-01-01T00:00:10Z"

    def test_learning_state(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        store.update_centroid("contract", "risk", "approve", [0.5], 0.1)
        store.update_dk_weights("contract", [[0.5]], 2, 10.0)
        conservation(store)
        assert type(store.get_centroids("contract")[0]["updated_at"]) is float
        weights = store.get_dk_weights("contract")
        assert weights is not None
        assert type(weights["created_at"]) is float and type(weights["computed_at"]) is float
        updated_at = store.get_conservation_state("contract")["updated_at"]  # type: ignore[index]
        assert isinstance(updated_at, str)
        datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

    def test_events_and_links(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        event(store)
        decision(store)
        store.link_entity("d", "entity", "supplier", domain="contract")
        assert store.get_evolution_events("contract")[0]["timestamp"] == "10.0"
        assert type(store.get_decision_links(domain="contract")[0]["created_at"]) is float


class TestNullHandling:
    def test_decision_optional_fields(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        identifier = store.write_decision("contract", "risk", "approve", 0.8, {})
        row = store.get_decision(identifier, "contract")
        assert row is not None
        for field in ("factor_names", "source", "scorer_version", "preset_version", "factor_schema_version",
                      "correct", "outcome", "verified_at_epoch", "quality_signal", "override_comment",
                      "verified_by", "analyst_action", "final_action", "was_override"):
            assert field in row and row[field] is None
        assert store.get_decision(identifier, "contract", include_outcome=True) == row

    @pytest.mark.parametrize("v2", [False, True])
    def test_checkpoint_optional_fields(self, store: ConformanceStore, v2: bool) -> None:
        # Conformance: AGE must also pass this test
        if v2:
            checkpoint(store)
        else:
            store.save_centroids("contract", "risk", [[0.5]])
        row = store.get_centroid_checkpoints("contract", include_v2=True)[0]
        for field in ("decision_id", "quality_window_size", "quality_verified_count", "quality_correct_count",
                      "rolling_accuracy", "quality_window_end", "quality_policy_version", "decision_time_start", "decision_time_end"):
            assert field in row and row[field] is None

    def test_learning_optional_fields(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        store.update_centroid("contract", "risk", "approve", [0.5], 0.1)
        assert store.get_centroids("contract")[0]["caused_by_decision_id"] is None
        store.update_dk_weights("contract", [[0.5]], 2, 10.0)
        row = store.get_dk_weights("contract")
        assert row is not None
        for field in ("supersedes_id", "welford_state", "n_confirmed", "n_overridden", "entity_group"):
            assert field in row and row[field] is None
        conservation(store)
        state = store.get_conservation_state("contract")
        assert state is not None and state["caused_by_decision_id"] is None and state["old_status"] is None

    def test_event_optional_fields(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        event(store)
        row = store.get_evolution_events("contract")[0]
        for field in ("source_copilot", "source_rule", "metric", "shadow_batch_size", "min_shadow_batches"):
            assert field in row and row[field] is None

    def test_supersedes_id_is_opaque_string(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        store.update_dk_weights("contract", [[0.5]], 2, 10.0)
        store.update_dk_weights("contract", [[0.6]], 3, 20.0)
        row = store.get_dk_weights("contract")
        assert row is not None and type(row["supersedes_id"]) is str


class TestOrdering:
    @pytest.mark.parametrize("reader", ["get_decisions", "get_all_decisions", "get_verified_decisions"])
    def test_decisions_time_descending_id_ascending(self, store: ConformanceStore, reader: str) -> None:
        # Conformance: AGE must also pass this test
        for identifier, timestamp in (("z", 10.0), ("a", 10.0), ("m", 10.0), ("new", 20.0), ("old", 1.0)):
            decision(store, identifier, timestamp=timestamp)
            store.write_outcome(identifier, "approve", True, domain="contract")
        assert [r["decision_id"] for r in getattr(store, reader)("contract")] == ["new", "a", "m", "z", "old"]

    def test_events_time_descending_id_ascending(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        for identifier, timestamp in (("z", 10.0), ("a", 10.0), ("m", 10.0), ("new", 20.0), ("old", 1.0)):
            event(store, identifier, timestamp=timestamp)
        assert [r["event_id"] for r in store.get_evolution_events("contract")] == ["new", "a", "m", "z", "old"]

    def test_checkpoints_ties(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        with patch("time.time", return_value=10.0):
            for identifier in ("z", "a", "m"):
                checkpoint(store, identifier)
        assert [r["checkpoint_id"] for r in store.get_centroid_checkpoints("contract", include_v2=True)] == ["a", "m", "z"]
        assert store.get_centroid_checkpoints("contract", include_v2=True, limit=1)[0]["checkpoint_id"] == "a"

    def test_checkpoint_window_is_chronological(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        for timestamp in (30.0, 10.0, 20.0):
            store.save_centroids("contract", "risk", [[timestamp]], created_at=timestamp)
        assert [r["created_at"] for r in store.get_centroid_checkpoints("contract", limit=2)] == [20.0, 30.0]
        assert [r["created_at"] for r in store.get_centroid_checkpoints("contract", limit=None)] == [30.0, 20.0, 10.0]

    def test_centroids_sorted(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        for category, action in (("z", "b"), ("a", "b"), ("a", "a")):
            store.update_centroid("contract", category, action, [0.5], 0.1)
        assert [(r["category"], r["action"]) for r in store.get_centroids("contract")] == [("a", "a"), ("a", "b"), ("z", "b")]

    def test_control_plane_key_order(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        for key in ("z", "a", "m"):
            store.save_promotion("contract", key, {"rule": key})
        assert [r["key"] for r in store.list_promotions("contract")] == ["a", "m", "z"]


class TestFilters:
    @pytest.mark.parametrize("filters, expected", [
        ({"event_type": "promoted"}, ["a", "c"]), ({"rule_name": "r1"}, ["a", "b"]),
        ({"variant_id": "v1"}, ["a", "c"]), ({"rule_name": "r1", "event_type": "promoted", "variant_id": "v1"}, ["a"]),
        ({"event_type": "missing"}, []), ({"rule_name": ""}, []),
    ])
    def test_event_filters(self, store: ConformanceStore, filters: dict[str, Any], expected: list[str]) -> None:
        # Conformance: AGE must also pass this test
        for identifier, kind, rule, variant in (("a", "promoted", "r1", "v1"), ("b", "paused", "r1", "v2"), ("c", "promoted", "r2", "v1")):
            event(store, identifier, event_type=kind, rule_name=rule, variant_id=variant)
        event(store, "other", domain="other")
        assert [r["event_id"] for r in store.get_evolution_events("contract", **filters)] == expected

    def test_decision_category_and_domain(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        decision(store, "a")
        decision(store, "b", category="cost")
        decision(store, "c", domain="other")
        assert [r["decision_id"] for r in store.get_decisions("contract", "risk")] == ["a"]
        assert store.get_decision("a", "other") is None
        assert store.count_decisions("contract") == 2

    def test_v2_checkpoint_category(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        checkpoint(store, "a")
        checkpoint(store, "b", category="cost")
        checkpoint(store, "c", domain="other")
        assert [r["checkpoint_id"] for r in store.get_centroid_checkpoints("contract", include_v2=True, category="risk")] == ["a"]
        assert store.get_centroid_checkpoints("contract", include_v2=False) == []

    @pytest.mark.parametrize("field,bound,expected", [
        ("checkpoint_time_start", 20.0, ["d30", "d20"]), ("checkpoint_time_end", 20.0, ["d20", "d10"]),
        ("decision_time_start", 20.0, ["d30", "d20"]), ("decision_time_end", 20.0, ["d20", "d10"]),
    ])
    def test_checkpoint_time_boundaries(self, store: ConformanceStore, field: str, bound: float, expected: list[str]) -> None:
        # Conformance: AGE must also pass this test
        for timestamp in (10, 20, 30):
            store.save_centroids("contract", "risk", [[0.5]], created_at=float(timestamp), decision_id=f"d{timestamp}",
                                 checkpoint_time=float(timestamp), decision_time_start=float(timestamp), decision_time_end=float(timestamp))
        checkpoint(store, "without-times")
        rows = store.get_centroid_checkpoints("contract", include_v2=True, **{field: bound})
        assert [r["decision_id"] for r in rows] == expected


class TestLimits:
    @pytest.mark.parametrize("limit,expected", [(0, 0), (1, 1), (2, 2), (10, 3), (None, 3)])
    def test_enrichment_limits(self, store: ConformanceStore, limit: int | None, expected: int) -> None:
        # Conformance: AGE must also pass this test
        for index in range(3):
            store.write_entity_enrichment(domain="contract", entity_type="Supplier", entity_id=f"s{index}",
                namespace="context", metrics={"risk": ProvenancedValue.from_fixture(0.5)},
                computed_from=EnrichmentSourceSet(fixture_sources=["contract"]))
        assert len(store.list_entity_enrichments(domain="contract", limit=cast(Any, limit))) == expected

    @pytest.mark.parametrize("limit,expected", [(0, 0), (1, 1), (2, 2), (10, 3), (None, 3)])
    def test_scoring_extension_limits(self, store: ConformanceStore, limit: int | None, expected: int) -> None:
        # Conformance: AGE must also pass this test
        for index in range(3):
            store.save_k_utility("contract", "episode", index, 0.5)
        assert len(store.get_k_utilities("contract", limit=cast(Any, limit))) == expected

    @pytest.mark.parametrize("reader", ["decisions", "events", "checkpoints", "links", "similar"])
    @pytest.mark.parametrize("limit,expected", [(0, 0), (1, 1), (2, 2), (10, 3), (None, 3)])
    def test_limits(self, store: ConformanceStore, reader: str, limit: int | None, expected: int) -> None:
        # Conformance: AGE must also pass this test
        decision(store, "source")
        for index in range(3):
            decision(store, f"d{index}", category="selected")
            event(store, f"e{index}")
            checkpoint(store, f"cp{index}")
            store.link_entity("source", f"entity{index}", "supplier", domain="contract")
        if reader == "decisions":
            rows = store.get_decisions("contract", "selected", limit=cast(Any, limit))
        elif reader == "events":
            rows = store.get_evolution_events("contract", limit=limit)
        elif reader == "checkpoints":
            rows = store.get_centroid_checkpoints("contract", include_v2=True, limit=limit)
        elif reader == "links":
            rows = store.get_decision_links("source", domain="contract", limit=limit)
        else:
            decision(store, "selected-source", category="selected")
            rows = store.query_similar("selected-source", cast(Any, limit), domain="contract")
        assert len(rows) == expected

    @pytest.mark.parametrize("reader", ["events", "checkpoints"])
    def test_omitted_limit_is_unbounded(self, store: ConformanceStore, reader: str) -> None:
        # Conformance: AGE must also pass this test
        for index in range(105):
            if reader == "events":
                event(store, f"e{index}")
            else:
                checkpoint(store, f"cp{index}")
        rows = store.get_evolution_events("contract") if reader == "events" else store.get_centroid_checkpoints("contract", include_v2=True)
        assert len(rows) == 105

    def test_explicit_none_decisions_above_default(self, store: ConformanceStore) -> None:
        # Conformance: AGE must also pass this test
        for index in range(405):
            decision(store, f"d{index}")
        assert len(store.get_decisions("contract", limit=cast(Any, None))) == 405
        assert len(store.get_all_decisions("contract")) == 405
