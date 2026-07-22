from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import pytest

from copilot_sdk.graph.dual_write_store import DualWriteStore


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
    assert primary.calls[0] == secondary.calls[0]


def test_write_outcome_calls_both_and_returns_none():
    primary, secondary = _pair()
    assert DualWriteStore(primary, secondary).write_outcome("d1", "buy", True) is None
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
        "write_decision": lambda: dual.write_decision("trading", "cat", "buy", 0.8, {}),
        "write_outcome": lambda: dual.write_outcome("d1", "buy", True),
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
    assert dual.write_outcome("d1", "buy", True) is None
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
    assert dual.get_decision("d1") == {"decision_id": "d1"}
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
        dual.write_outcome(f"d{index}", "buy", True)
    assert dual.secondary_failure_count == 3
    assert len(dual.flush_secondary_failures()) == 3
    assert dual.secondary_failure_count == 0


def test_concurrent_domain_writes_reach_both_endpoints_with_their_domains():
    primary, secondary = _pair()
    dual = DualWriteStore(primary, secondary)
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda domain: dual.write_decision(domain, "cat", "buy", 0.8, {}), ["trading", "purchasing"]))
    assert {args[0] for name, args, _ in primary.calls if name == "write_decision"} == {"trading", "purchasing"}
    assert {args[0] for name, args, _ in secondary.calls if name == "write_decision"} == {"trading", "purchasing"}


def test_new_wrapper_has_no_secondary_failures():
    primary, secondary = _pair()
    dual = DualWriteStore(primary, secondary)
    assert dual.secondary_failure_count == 0
    assert dual.secondary_failures == []
