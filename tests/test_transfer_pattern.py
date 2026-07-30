from __future__ import annotations

import hashlib
import json

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


def _stores(tmp_path):
    return [
        InMemoryGraphStore(domain="soc"),
        SQLiteGraphStore(tmp_path / "graph.db", domain="soc"),
    ]


def _write(store, pattern_id="pattern-1", **overrides):
    payload = {
        "pattern_id": pattern_id,
        "source_domain": "soc",
        "target_domain": "trading",
        "pattern_type": "factor_quality_transfer",
        "factor_mapping": {"risk": "supplier_risk", "quality": "quality"},
        "confidence": 0.91,
        "validation_status": "proposed",
        "conservation_status": "GREEN",
        "source_rule": None,
        "target_rule": None,
        "source_fingerprint_id": "soc-fp-1",
        "evolution_event_id": None,
        "metadata": {"source": "test"},
    }
    payload.update(overrides)
    store.write_transfer_pattern(**payload)


@pytest.mark.parametrize("store_index", [0, 1], ids=["memory", "sqlite"])
def test_write_transfer_pattern_creates_node(tmp_path, store_index):
    store = _stores(tmp_path)[store_index]
    _write(store)

    pattern = store.get_transfer_patterns()[0]
    assert pattern["pattern_id"] == "pattern-1"
    assert pattern["pattern_type"] == "factor_quality_transfer"
    assert pattern["source_domain"] == "soc"
    assert pattern["target_domain"] == "trading"
    assert pattern["factor_mapping"] == {"risk": "supplier_risk", "quality": "quality"}
    assert pattern["source_rule"] is None
    assert pattern["target_rule"] is None


def test_transfer_pattern_edges_from_to_domain():
    store = InMemoryGraphStore(domain="soc")
    _write(store)
    # Local stores represent the two domain endpoints as scalar fields; AGE
    # conformance covers the corresponding FROM_DOMAIN/TO_DOMAIN edges.
    pattern = store.get_transfer_patterns()[0]
    assert pattern["source_domain"] == "soc"
    assert pattern["target_domain"] == "trading"


def test_transfer_pattern_no_derived_from_without_event(tmp_path):
    for store in _stores(tmp_path):
        _write(store)
        assert store.get_transfer_patterns()[0]["evolution_event_id"] is None


def test_transfer_pattern_idempotent_same_content(tmp_path):
    for store in _stores(tmp_path):
        _write(store)
        _write(store)
        assert len(store.get_transfer_patterns()) == 1


def test_transfer_pattern_rejects_conflicting_content(tmp_path):
    for store in _stores(tmp_path):
        _write(store)
        with pytest.raises(ValueError):
            _write(store, confidence=0.12)


def test_get_transfer_patterns_filters(tmp_path):
    store = InMemoryGraphStore(domain="soc")
    _write(store, pattern_id="soc-trading")
    _write(
        store,
        pattern_id="dataops-trading",
        source_domain="dataops",
    )
    _write(
        store,
        pattern_id="soc-s2p",
        target_domain="s2p",
    )
    assert len(store.get_transfer_patterns(source_domain="soc")) == 2
    assert len(store.get_transfer_patterns(target_domain="trading")) == 2
    assert len(store.get_transfer_patterns(source_domain="soc", target_domain="s2p")) == 1


def test_deterministic_pattern_id():
    content = {
        "source_domain": "soc",
        "target_domain": "trading",
        "pattern_type": "factor_quality_transfer",
        "factor_mapping": {"quality": "quality"},
    }
    encoded = json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
    first = hashlib.sha256(encoded).hexdigest()
    second = hashlib.sha256(encoded).hexdigest()
    assert first == second


def test_sqlite_transfer_pattern(tmp_path):
    store = SQLiteGraphStore(tmp_path / "transfer.db", domain="soc")
    _write(store)
    assert store.get_transfer_patterns(source_domain="soc")[0]["pattern_id"] == "pattern-1"


def test_inmemory_transfer_pattern():
    store = InMemoryGraphStore(domain="soc")
    _write(store)
    assert store.get_transfer_patterns(target_domain="trading")[0]["pattern_id"] == "pattern-1"
