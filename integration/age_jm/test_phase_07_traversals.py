"""Traversal evidence from populated, isolated AGE graphs; protocol policy units."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from copilot_sdk.backend.transfer import load_fingerprints_with_warnings
from copilot_sdk.backend.transfer_router import _pattern_dollar_impact, _reset_conservation_state
from copilot_sdk.di.query_providers import GraphEvidenceProvider, ProviderUnavailableError
from copilot_sdk.graph.memory_store import InMemoryGraphStore


@pytest.fixture
def linked_graph(disposable_age):
    store = disposable_age.store("trading")
    store.write_decision("trading", "risk", "buy", 0.8, {"x": 0.5}, metadata={"decision_id": "D1"})
    store.write_outcome("D1", "buy", True, domain="trading")
    store.write_decision("trading", "risk", "sell", 0.7, {"x": 0.6}, metadata={"decision_id": "D2"})
    store._store._run_query("MATCH (d:Decision {decision_id: 'D1'}) CREATE (e:Entity {domain: 'trading', entity_group: 'entity-a'})-[:CONTEXT_FOR]->(d) RETURN e")
    store._store._run_query("MATCH (d:Decision {decision_id: 'D2'}) CREATE (e:Entity {domain: 'trading', entity_group: 'entity-b'})-[:CONTEXT_FOR]->(d) RETURN e")
    store._store._run_query("MATCH (d:Decision {decision_id: 'D1'}) CREATE (r:Rule {domain: 'trading', rule_id: 'R1'})-[:SUPPORTED_BY]->(d) RETURN r")
    store.write_transfer_pattern("P1", "trading", "s2p", "factor", {"x": "x"}, 0.8, "accepted", "GREEN")
    return store


@pytest.mark.age
def test_g047_decision_movement_returns_linked_evidence(linked_graph) -> None:
    rows = linked_graph.decision_movement("trading", "D1")
    assert any(row["evidence"].get("actual_action") == "buy" for row in rows)
    assert linked_graph.decision_movement("s2p", "D1") == []


@pytest.mark.age
def test_g047_contextual_judgment_returns_entity_partitions(linked_graph) -> None:
    left = linked_graph.contextual_judgment("trading", "entity-a", "risk")
    right = linked_graph.contextual_judgment("trading", "entity-b", "risk")
    assert left and right and left != right
    assert linked_graph.contextual_judgment("trading", "missing", "risk") == []


@pytest.mark.age
def test_g047_promotion_basis_returns_rule_evidence(linked_graph) -> None:
    rows = linked_graph.promotion_basis("trading", "R1")
    assert rows and "R1" in json.dumps(rows)
    assert linked_graph.promotion_basis("s2p", "R1") == []


@pytest.mark.age
def test_g047_transfer_witness_returns_cross_domain_path(linked_graph) -> None:
    result = linked_graph.transfer_witness("trading", "s2p", "P1")
    assert result[0]["transfer_pattern"]["pattern_id"] == "P1"
    assert result[0]["source_domain"]["domain_id"] == "trading"
    assert result[0]["target_domain"]["domain_id"] == "s2p"
    assert linked_graph.transfer_witness("s2p", "trading", "P1") == []


@pytest.mark.age
def test_g047_invalid_domain_rejected_and_unlinked_pair_empty(linked_graph) -> None:
    with pytest.raises(ValueError, match="unsupported graph domain"):
        linked_graph.transfer_witness("trading", "invalid/domain", "P1")
    assert linked_graph.transfer_witness("trading", "unknown", "P1") == []


def test_g044_production_fingerprint_from_graph_not_json(tmp_path: Path) -> None:
    (tmp_path / "trading.json").write_text(json.dumps({"domain": "trading", "fixture": True}), encoding="utf-8")
    store = InMemoryGraphStore(domain="trading")
    store.write_fingerprint("FP1", "trading", ["x"], {"factor_stats": {"x": 1}}, 0, 20)
    loaded, warnings = load_fingerprints_with_warnings(tmp_path, graph_store=store, profile="production")
    assert loaded["trading"]["fingerprint"]["factor_stats"]["x"] == 1
    assert not warnings


def test_g044_demo_allows_json_fingerprints(tmp_path: Path) -> None:
    (tmp_path / "trading.json").write_text(json.dumps({"domain": "trading", "fixture": True}), encoding="utf-8")
    loaded, _ = load_fingerprints_with_warnings(tmp_path, profile="test")
    assert loaded["trading"]["fixture"] is True


def test_g021_impact_unknown_on_failed_read(monkeypatch) -> None:
    store = InMemoryGraphStore(domain="trading")
    monkeypatch.setattr(store, "get_all_decisions", Mock(side_effect=RuntimeError("read failed")))
    assert _pattern_dollar_impact(store, {}, "trading", "s2p") == "unknown"


@pytest.mark.age
def test_g021_reset_requires_atomic_capability(disposable_age) -> None:
    store = disposable_age.store("trading")
    before = store.get_conservation_state("trading")
    assert _reset_conservation_state(SimpleNamespace(graph_store=store), "trading") is False
    assert store.get_conservation_state("trading") == before


def test_g021_no_unconditional_green_reset(monkeypatch) -> None:
    store = InMemoryGraphStore(domain="trading")
    spy = Mock(wraps=store.update_conservation_state)
    monkeypatch.setattr(store, "update_conservation_state", spy)
    assert _reset_conservation_state(SimpleNamespace(graph_store=store), "trading") is False
    spy.assert_not_called()


@pytest.mark.age
def test_g048_production_evidence_from_graph(linked_graph) -> None:
    provider = GraphEvidenceProvider(linked_graph, domain="trading")
    evidence = provider.read_evidence("D1", 0, "risk")
    assert evidence and evidence["provenance"] == "graph_traversal"
    assert evidence["graph_path"]["decision"]["decision_id"] == "D1"
    assert provider.read_evidence("missing", 0, "risk") is None


@pytest.mark.age
def test_g048_evidence_linked_to_trace(linked_graph) -> None:
    evidence = GraphEvidenceProvider(linked_graph, domain="trading").read_evidence("D1", 1, "timing")
    assert evidence and evidence["trace_link"] == "decision:D1:movement"
    assert evidence["graph_path"]["evidence"]


def test_g048_graph_provider_fails_closed_without_traversal() -> None:
    with pytest.raises(ProviderUnavailableError):
        GraphEvidenceProvider(object(), domain="trading").read_evidence("D1", 0, "risk")
