from __future__ import annotations

from copilot_sdk.graph import InMemoryGraphStore
from tests.graph_store_test_helpers import make_memory_store
from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.graph.memory_store import InMemoryGraphStore as MemoryStore


def _write_decision(store, metadata=None):
    decision_metadata = dict(metadata or {})
    if metadata is None:
        metadata = None
    else:
        metadata = decision_metadata
    return store.write_decision(
        getattr(store, "domain", "test"),
        category="price_variance",
        action="hold_for_review",
        confidence=0.82,
        factors={"match_status": 0.7},
        metadata=metadata,
    )


def test_in_memory_write_decision_preserves_metadata():
    store = InMemoryGraphStore()

    decision_id = _write_decision(
        store,
        metadata={"decision_id": "d-meta", "invoice_id": "S2P-INV-0001"},
    )

    decision = store.get_decision(decision_id, domain=getattr(store, "domain", "test"))
    assert decision["metadata"]["invoice_id"] == "S2P-INV-0001"


def test_in_memory_write_decision_without_metadata_still_works():
    store = InMemoryGraphStore()

    decision_id = _write_decision(store)

    decision = store.get_decision(decision_id, domain=getattr(store, "domain", "test"))
    assert decision["decision_id"] == decision_id
    assert decision["metadata"]["entity_id"]


def test_sqlite_write_decision_preserves_metadata(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = make_memory_store(db_path)

    decision_id = _write_decision(
        store,
        metadata={"decision_id": "d-sql", "invoice_id": "S2P-INV-0002"},
    )

    decision = store.get_decision(decision_id, domain=getattr(store, "domain", "test"))
    assert decision["metadata"]["invoice_id"] == "S2P-INV-0002"


def test_sqlite_write_decision_without_metadata_still_works(tmp_path):
    db_path = tmp_path / "graph.sqlite"
    store = make_memory_store(db_path)

    decision_id = _write_decision(store)

    decision = store.get_decision(decision_id, domain=getattr(store, "domain", "test"))
    assert decision["decision_id"] == decision_id
    assert decision["metadata"]["entity_id"]




def test_compounding_scorer_score_persists_caller_metadata(tmp_path):
    graph_store = MemoryStore(domain="s2p")
    scorer = CompoundingScorer.from_preset(
        "s2p",
        profile="test",
        graph_store=graph_store,
    )
    factors = {name: 0.5 for name in scorer._preset.shape.factor_names}

    result = scorer.score(
        factors,
        "price_variance",
        metadata={"invoice_id": "S2P-INV-0004", "supplier_id": "SUP-001"},
    )

    decision = graph_store.get_decision(result.decision_id, domain="s2p")
    assert decision["metadata"]["invoice_id"] == "S2P-INV-0004"
    assert decision["metadata"]["supplier_id"] == "SUP-001"
    assert decision["metadata"]["domain"] == "s2p"
    scorer.graph_store.close()

