from __future__ import annotations

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.namespace import GraphStoreNamespace
from copilot_sdk.graph.protocol import ProtocolV2GraphStore


def _write(ns: GraphStoreNamespace, action: str = "approve") -> str:
    return ns.write_decision(
        domain="s2p",
        category="cat1",
        action=action,
        confidence=0.9,
        factors={"f1": 0.5},
    )


def test_protocol_conformance() -> None:
    ns = GraphStoreNamespace(InMemoryGraphStore(domain="test"), "arm1")
    assert isinstance(ns, ProtocolV2GraphStore)


def test_domain_rewriting_roundtrip() -> None:
    shared = InMemoryGraphStore(domain="test")
    ns = GraphStoreNamespace(shared, "arm1")
    decision_id = _write(ns)
    result = ns.get_decision(decision_id, domain="s2p", include_outcome=False)
    assert result is not None
    assert result["domain"] == "s2p"
    raw = shared.get_decision(
        decision_id,
        domain=ns._domain("s2p"),
        include_outcome=False,
    )
    assert raw is not None
    assert raw["domain"] == ns._domain("s2p")


def test_namespace_isolation() -> None:
    shared = InMemoryGraphStore(domain="test")
    ns_a = GraphStoreNamespace(shared, "arm_a")
    ns_b = GraphStoreNamespace(shared, "arm_b")
    decision_id = _write(ns_a)
    ns_a.write_outcome(
        decision_id,
        actual_action="approve",
        is_correct=True,
        domain="s2p",
        metadata={},
    )
    assert ns_a.count_verified(domain="s2p") >= 1
    assert ns_b.count_verified(domain="s2p") == 0
    assert id(ns_a._store) == id(ns_b._store)


def test_close_noop() -> None:
    shared = InMemoryGraphStore(domain="test")
    ns = GraphStoreNamespace(shared, "arm1")
    _write(ns)
    ns.close()
    decisions = shared.get_all_decisions(domain=ns._domain("s2p"))
    assert len(decisions) >= 1


def test_invalid_namespace() -> None:
    shared = InMemoryGraphStore(domain="test")
    for namespace in ("", "  "):
        with pytest.raises(ValueError):
            GraphStoreNamespace(shared, namespace)


def test_empty_domain_rejected() -> None:
    shared = InMemoryGraphStore(domain="test")
    ns = GraphStoreNamespace(shared, "arm1")
    with pytest.raises(ValueError):
        ns.write_decision(
            domain="",
            category="cat1",
            action="approve",
            confidence=0.9,
            factors={"f1": 0.5},
        )


def test_cross_domain_transfer_rewriting() -> None:
    shared = InMemoryGraphStore(domain="test")
    ns = GraphStoreNamespace(shared, "arm1")
    ns.write_transfer_pattern(
        pattern_id="tp-001",
        source_domain="s2p",
        target_domain="trading",
        pattern_type="judgment_memory_transfer",
        factor_mapping={"f1": "f2"},
        confidence=0.85,
        validation_status="validated",
        conservation_status="GREEN",
    )
    patterns = ns.get_transfer_patterns(source_domain="s2p")
    assert len(patterns) == 1
    assert patterns[0]["source_domain"] == "s2p"
    assert patterns[0]["target_domain"] == "trading"
    raw = shared.get_transfer_patterns(source_domain=ns._domain("s2p"))
    assert len(raw) >= 1
    assert raw[0]["source_domain"] == ns._domain("s2p")


def test_multi_domain_filtering() -> None:
    shared = InMemoryGraphStore(domain="test")
    ns_a = GraphStoreNamespace(shared, "arm_a")
    ns_b = GraphStoreNamespace(shared, "arm_b")
    _write(ns_a, "a1")
    _write(ns_b, "a2")
    a_decisions = ns_a.get_all_decisions(domain="s2p")
    b_decisions = ns_b.get_all_decisions(domain="s2p")
    assert len(a_decisions) == 1
    assert len(b_decisions) == 1
    assert a_decisions[0]["recommended_action"] != b_decisions[0]["recommended_action"]
