from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import pytest

from copilot_sdk.graph.dual_write_store import DualWriteStore
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


class RecordingEndpoint:  # MOCK-OK: protocol delegation boundary spy.
    def __init__(self, *, returns=None, failures=None):
        self.calls = []
        self._returns = dict(returns or {})
        self._failures = dict(failures or {})
        self._lock = Lock()

    def __getattr__(self, name):
        def call(*args, **kwargs):
            with self._lock:
                self.calls.append((name, args, kwargs))
            failure = self._failures.get(name)
            if failure is not None:
                raise failure
            return self._returns.get(name)

        return call

    def count(self, method):
        return sum(1 for name, _, _ in self.calls if name == method)


def _pair(*, primary_failures=None, secondary_failures=None, secondary_returns=None):
    primary = RecordingEndpoint(
        returns={"write_decision": "primary-id", "write_entity_enrichment": {"receipt": "primary"}, "append_evidence_receipt": (4, "hash")},
        failures=primary_failures,
    )
    return primary, RecordingEndpoint(
        returns={"write_decision": "secondary-id", **(secondary_returns or {})},
        failures=secondary_failures,
    )


def test_write_decision_returns_primary_identity_and_forwards_arguments():
    primary, secondary = _pair()
    dual = DualWriteStore(primary, secondary)
    result = dual.write_decision("trading", "cat", "buy", 0.8, {"x": 1}, {"source": "test"})
    assert result == "primary-id"
    assert primary.count("write_decision") == 1
    assert secondary.count("write_decision") == 0
    assert dual.secondary_failures[0]["status"] == "SKIPPED"
    assert dual.secondary_failures[0]["reason"] == "identity_mismatch_risk"


def test_write_outcome_calls_both_and_returns_none():
    primary, secondary = _pair()
    assert DualWriteStore(primary, secondary).write_outcome("d1", "buy", True, domain="trading") is None
    assert primary.count("write_outcome") == secondary.count("write_outcome") == 1


def test_write_governed_decision_calls_both():
    primary, secondary = _pair()
    DualWriteStore(primary, secondary).write_governed_decision("d1", "trading", "cat", 0, "buy", 0, 0.8, [0.8], [1.0], ["x"])
    assert primary.count("write_governed_decision") == secondary.count("write_governed_decision") == 1


def test_append_evidence_receipt_returns_primary_receipt():
    primary, secondary = _pair(secondary_returns={"append_evidence_receipt": (99, "secondary-hash")})
    result = DualWriteStore(primary, secondary).append_evidence_receipt("r1", "trading", "d1", {}, "actor", "route")
    assert result == (4, "hash")
    assert primary.count("append_evidence_receipt") == secondary.count("append_evidence_receipt") == 1


def test_all_protocol_write_methods_delegate_to_both_endpoints():
    primary, secondary = _pair()
    dual = DualWriteStore(primary, secondary)
    calls = {
        "write_outcome": lambda: dual.write_outcome("d1", "buy", True, domain="trading"),
        "write_governed_decision": lambda: dual.write_governed_decision("d1", "trading", "cat", 0, "buy", 0, 0.8, [], [], []),
        "write_observation": lambda: dual.write_observation("o1", "trading", "cat", "buy", 0.8, "route", "scorer", "schema"),
        "save_centroids": lambda: dual.save_centroids("trading", "cat", {}),
        "write_entity_enrichment": lambda: dual.write_entity_enrichment(domain="trading", entity_type="vendor", entity_id="v1", namespace="n", metrics={}, computed_from={}),
        "write_conservation_status": lambda: dual.write_conservation_status("s1", "trading", 1, 0.1, 0.2, 0.3, 1, 1, "measured", "v1"),
        "write_fingerprint": lambda: dual.write_fingerprint("f1", "trading", [], {}, 0, 10),
        "write_centroid_checkpoint": lambda: dual.write_centroid_checkpoint("c1", "trading", "cat", "buy", {}, 1, 1, 0.8, [1], "hash"),
        "write_evolution_event": lambda: dual.write_evolution_event("e1", "trading", "t", "rule", "variant"),
        "link_entity": lambda: dual.link_entity("d1", "v1", "vendor", "trading"),
        "append_evidence_receipt": lambda: dual.append_evidence_receipt("r1", "trading", "d1", {}, "actor", "route"),
    }
    for operation, invoke in calls.items():
        invoke()
        assert primary.count(operation) == secondary.count(operation) == 1


def test_secondary_failure_does_not_propagate_and_is_logged():
    primary, secondary = _pair(secondary_failures={"write_outcome": RuntimeError("age down")})
    dual = DualWriteStore(primary, secondary)
    assert dual.write_outcome("d1", "buy", True, domain="trading") is None
    assert dual.secondary_failures[0]["operation"] == "write_outcome"
    assert dual.secondary_failures[0]["status"] == "SECONDARY_WRITE_FAILURE"


def test_not_implemented_secondary_enrichment_is_unsupported_not_error():
    primary, secondary = _pair(secondary_failures={"write_entity_enrichment": NotImplementedError("deferred")})
    dual = DualWriteStore(primary, secondary)
    assert dual.write_entity_enrichment(domain="trading", entity_type="vendor", entity_id="v1", namespace="n", metrics={}, computed_from={}) == {"receipt": "primary"}
    assert dual.secondary_failures[0]["status"] == "UNSUPPORTED"
    assert dual.secondary_failures[0]["reason"] == "not_implemented"


def test_primary_failure_propagates_and_secondary_is_not_called():
    primary, secondary = _pair(primary_failures={"write_decision": ValueError("primary failure")})
    with pytest.raises(ValueError, match="primary failure"):
        DualWriteStore(primary, secondary).write_decision("trading", "cat", "buy", 0.8, {})
    assert secondary.count("write_decision") == 0


def test_all_reads_delegate_only_to_primary():
    primary, secondary = _pair()
    primary._returns.update({
        "get_decision": {"decision_id": "d1"}, "get_decisions": [], "get_all_decisions": [],
        "get_verified_decisions": [], "count_verified": 2, "count_correct": 1,
        "count_decisions": 3, "load_latest_centroids": {}, "get_centroid_checkpoints": [],
        "count_archived": 0, "read_entity_enrichment": {}, "list_entity_enrichments": [],
        "count_verified_decisions": 2,
    })
    dual = DualWriteStore(primary, secondary)
    assert dual.get_decision("d1", domain="trading") == {"decision_id": "d1"}
    assert dual.get_decisions("trading") == dual.get_all_decisions("trading") == dual.get_verified_decisions("trading") == []
    assert (dual.count_verified("trading"), dual.count_correct("trading"), dual.count_decisions("trading"), dual.count_verified_decisions("trading")) == (2, 1, 3, 2)
    assert dual.load_latest_centroids("trading") == {}
    assert dual.get_centroid_checkpoints("trading") == []
    assert dual.count_archived("trading") == 0
    assert dual.read_entity_enrichment(domain="trading", entity_type="vendor", entity_id="v1") == {}
    assert dual.list_entity_enrichments(domain="trading") == []
    assert secondary.calls == []


def test_lifecycle_calls_both_endpoints():
    primary, secondary = _pair(secondary_returns={"archive_decisions": 5, "archive_old_decisions": 2})
    primary._returns.update({"archive_decisions": 5, "archive_old_decisions": 2})
    dual = DualWriteStore(primary, secondary)
    assert dual.archive_decisions("trading", 1.0) == 5
    assert dual.archive_old_decisions("trading") == 2
    dual.domain_scoped_reset("trading")
    assert primary.count("archive_decisions") == secondary.count("archive_decisions") == 1
    assert primary.count("archive_old_decisions") == secondary.count("archive_old_decisions") == 1
    assert primary.count("domain_scoped_reset") == secondary.count("domain_scoped_reset") == 1


def test_retention_archives_identical_ids_in_both_concrete_stores(tmp_path):
    domain = "trading"
    primary = SQLiteGraphStore(tmp_path / "trading.db", domain=domain)
    secondary = InMemoryGraphStore(domain=domain)
    dual = DualWriteStore(primary, secondary)
    try:
        for index in range(802):
            dual.write_governed_decision(
                f"TRD-{index:04}", domain, "trend", 0, "buy", 0, 0.8,
                [0.8, 0.2], [float(index)], ["factor"], metadata={"created_at": float(index)},
            )

        assert dual.archive_old_decisions(domain, keep_recent=800) == 2
        assert primary.count_decisions(domain) == secondary.count_decisions(domain) == 800
        assert [row["decision_id"] for row in primary.get_archived_decisions(domain)] == [
            row["decision_id"] for row in secondary.get_archived_decisions(domain)
        ] == ["TRD-0000", "TRD-0001"]
    finally:
        dual.close()


def test_lifecycle_secondary_failure_is_recorded_not_propagated():
    primary, secondary = _pair(secondary_failures={"domain_scoped_reset": RuntimeError("secondary reset")})
    DualWriteStore(primary, secondary).domain_scoped_reset("trading")
    assert primary.count("domain_scoped_reset") == secondary.count("domain_scoped_reset") == 1


def test_close_always_closes_secondary_when_primary_fails():
    primary, secondary = _pair(primary_failures={"close": RuntimeError("primary close")})
    with pytest.raises(RuntimeError, match="primary close"):
        DualWriteStore(primary, secondary).close()
    assert secondary.count("close") == 1


def test_failure_log_counts_and_flushes_entries():
    primary, secondary = _pair(secondary_failures={"write_outcome": RuntimeError("x")})
    dual = DualWriteStore(primary, secondary)
    for index in range(3):
        dual.write_outcome(f"d{index}", "buy", True, domain="trading")
    assert dual.secondary_failure_count == 3
    assert len(dual.flush_secondary_failures()) == 3
    assert dual.secondary_failure_count == 0


def test_concurrent_domain_writes_reach_both_endpoints_with_their_domains():
    primary, secondary = _pair()
    dual = DualWriteStore(primary, secondary)
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda domain: dual.write_decision(domain, "cat", "buy", 0.8, {}), ["trading", "purchasing"]))
    assert {args[0] for name, args, _ in primary.calls if name == "write_decision"} == {"trading", "purchasing"}
    assert secondary.count("write_decision") == 0


def test_write_decision_logs_identity_preserving_skip(caplog):
    primary, secondary = _pair()
    dual = DualWriteStore(primary, secondary)
    with caplog.at_level("WARNING"):
        assert dual.write_decision("trading", "cat", "buy", 0.8, {}) == "primary-id"
    assert "write_decision skipped on secondary" in caplog.text


def test_governed_decision_and_outcome_use_same_identity_on_both_stores():
    primary, secondary = _pair()
    dual = DualWriteStore(primary, secondary)
    dual.write_governed_decision("shared-id", "trading", "cat", 2, "buy", 1, 0.8, [0.2, 0.8], [1.0], ["x"], "score", "scorer", "preset", "schema", {"trace": "t"})
    dual.write_outcome("shared-id", "buy", True, {"verified_at": 1.0}, domain="trading")
    governed_primary = next(call for call in primary.calls if call[0] == "write_governed_decision")
    governed_secondary = next(call for call in secondary.calls if call[0] == "write_governed_decision")
    outcome_primary = next(call for call in primary.calls if call[0] == "write_outcome")
    outcome_secondary = next(call for call in secondary.calls if call[0] == "write_outcome")
    assert governed_primary == governed_secondary
    assert outcome_primary == outcome_secondary
    assert governed_secondary[1][0] == outcome_secondary[1][0] == "shared-id"


def test_failure_log_is_bounded_fifo_and_warns(caplog):
    primary, secondary = _pair(secondary_failures={"write_outcome": RuntimeError("age down")})
    dual = DualWriteStore(primary, secondary, max_failures=3)
    with caplog.at_level("WARNING"):
        for index in range(5):
            dual.write_outcome(f"d{index}", "buy", True, domain="trading")
    assert [entry["args"]["first_arg"] for entry in dual.secondary_failures] == ["d2", "d3", "d4"]
    assert "dropped 1 oldest entries" in caplog.text


def test_failure_log_persists_and_loads(tmp_path):
    primary, secondary = _pair(secondary_failures={"write_outcome": RuntimeError("age down")})
    log_path = tmp_path / "secondary_failures.json"
    dual = DualWriteStore(primary, secondary)
    dual.write_outcome("d1", "buy", True, domain="trading")
    dual.persist_failures(str(log_path))
    restored = DualWriteStore(*_pair(), failure_log_path=str(log_path))
    assert restored.secondary_failures == dual.secondary_failures


def test_constructor_rejects_store_without_protocol_v2_methods():
    class PlainGraphStore:
        def write_decision(self, domain, category, action, confidence, factors, metadata=None):
            return "legacy-id"

    primary, _ = _pair()
    with pytest.raises(TypeError, match="secondary must implement ProtocolV2GraphStore"):
        DualWriteStore(primary, PlainGraphStore())


def test_new_wrapper_has_no_secondary_failures():
    primary, secondary = _pair()
    dual = DualWriteStore(primary, secondary)
    assert dual.secondary_failure_count == 0
    assert dual.secondary_failures == []
