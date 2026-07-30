from __future__ import annotations

import json
import math
import random
import re
from dataclasses import replace

import numpy as np
import pytest

from copilot_sdk.migrate import sqlite_to_age
from copilot_sdk.migrate.verify_state import (
    ScorerState,
    compare_states,
    read_decisions_from_age,
    replay_decisions,
    verify_level3,
)


class FakeConn:  # MOCK-OK: in-memory AGE boundary double for migration Cypher topology.
    """Minimal committed/uncommitted AGE model for migration verification tests."""

    _NODE_MARKERS = {
        "CREATE (d:Decision": "Decision",
        "CREATE (o:Outcome": "Outcome",
        "CREATE (c:CentroidCheckpoint": "CentroidCheckpoint",
        "CREATE (r:EvidenceReceipt": "EvidenceReceipt",
    }

    def __init__(self) -> None:
        self.nodes: list[dict[str, str | None]] = []
        self.edges: list[dict[str, str | None]] = []
        self._pending_nodes: list[dict[str, str | None]] = []
        self._pending_edges: list[dict[str, str | None]] = []
        self._last_row: tuple[int, ...] | None = None
        self._last_rows: list[tuple[int, ...]] = []
        self.queries: list[str] = []
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    @staticmethod
    def _literal(query: str, name: str) -> str | None:
        match = re.search(rf"{name}: '((?:\\\\'|[^'])*)'", query)
        return match.group(1).replace("\\'", "'") if match else None

    def _topology_count(self, label: str, query: str) -> int:
        domain = self._literal(query, "domain")
        return sum(
            node["label"] == label
            and node["domain"] == domain
            and node["migration_source"] == "sqlite"
            for node in self.nodes
        )

    def execute(self, query: str) -> FakeConn:
        """Handle the constrained MATCH/CREATE/count patterns emitted by the writer."""
        self.queries.append(query)
        self._last_row = None
        self._last_rows = []

        if "MATCH (d:Decision" in query and "RETURN d" in query:
            # The migration's MATCH-before-CREATE idempotency check sees no
            # existing node in these fresh test graphs.
            return self

        for marker, label in self._NODE_MARKERS.items():
            if marker in query:
                self._pending_nodes.append(
                    {
                        "label": label,
                        "domain": self._literal(query, "domain"),
                        "decision_id": self._literal(query, "decision_id"),
                        "migration_source": self._literal(query, "migration_source"),
                    }
                )
                return self

        edge_match = re.search(r"CREATE \(d\)-\[:([A-Z_]+)", query)
        if edge_match:
            self._pending_edges.append(
                {
                    "label": edge_match.group(1),
                    "domain": self._literal(query, "domain"),
                    "decision_id": self._literal(query, "decision_id"),
                }
            )
            return self

        if "RETURN count(DISTINCT o) AS outcomes, count(r) AS edges" in query:
            domain = self._literal(query, "domain")
            decision_id = self._literal(query, "decision_id")
            outcome_count = sum(
                node["label"] == "Outcome"
                and node["domain"] == domain
                and node["decision_id"] == decision_id
                for node in self.nodes
            )
            edge_count = sum(
                edge["label"] == "HAS_OUTCOME"
                and edge["domain"] == domain
                and edge["decision_id"] == decision_id
                for edge in self.edges
            )
            self._last_row = (outcome_count, edge_count)
            return self

        if "RETURN count(r) AS cnt" in query and "HAS_OUTCOME" in query:
            domain = self._literal(query, "domain")
            self._last_row = (
                sum(edge["label"] == "HAS_OUTCOME" and edge["domain"] == domain for edge in self.edges),
            )
            return self

        for label in self._NODE_MARKERS.values():
            if f"MATCH ({label[0].lower()}:" in query and "RETURN count(" in query:
                self._last_row = (self._topology_count(label, query),)
                return self
        return self

    def fetchone(self) -> tuple[int, ...] | None:
        return self._last_row

    def fetchall(self) -> list[tuple[int, ...]]:
        return self._last_rows

    def commit(self) -> None:
        self.nodes.extend(self._pending_nodes)
        self.edges.extend(self._pending_edges)
        self._pending_nodes.clear()
        self._pending_edges.clear()
        self.commit_count += 1

    def rollback(self) -> None:
        self._pending_nodes.clear()
        self._pending_edges.clear()
        self.rollback_count += 1

    def close(self) -> None:
        self.closed = True


def _decision(
    decision_id: str,
    *,
    created_at: float,
    factor_value: float,
    category_index: int = 0,
    recommended_index: int = 0,
    recommended_action: str = "strong_execution",
    actual_action: str = "strong_execution",
) -> tuple[dict, dict]:
    vector = [factor_value] * 10
    decision = {
        "decision_id": decision_id,
        "domain": "trading",
        "category": "trend_following",
        "category_index": category_index,
        "factors_json": '{"signal_alignment": %.3f}' % factor_value,
        "factor_vector_json": str(vector),
        "recommended_action": recommended_action,
        "recommended_index": recommended_index,
        "confidence": 0.8,
        "probabilities_json": "[0.8, 0.1, 0.05, 0.05]",
        "status": "confirmed",
        "created_at": created_at,
    }
    outcome = {
        "decision_id": decision_id,
        "domain": "trading",
        "actual_action": actual_action,
        "actual_index": recommended_index,
        "is_correct": 1,
        "verified_at": created_at + 100.0,
        "context_json": "{}",
    }
    return decision, outcome


def _state(**overrides) -> ScorerState:
    state = ScorerState(
        centroids={(0, 0): [0.0, 0.1], (0, 1): [0.2, 0.3]},
        dk_weights=[[1.0, 1.0]],
        conservation_V=2,
        conservation_q=1.0,
        conservation_alpha=0.2,
        conservation_phase="ACTIVE",
        decision_count=2,
    )
    return replace(state, **overrides)


def _make_decision(
    index: int,
    category_index: int = 0,
    n_factors: int = 10,
    n_actions: int = 4,
    correct: bool = True,
) -> dict:
    rng = random.Random(index)
    factors = [round(rng.random(), 4) for _ in range(n_factors)]
    probs = [round(1 / n_actions, 6)] * n_actions
    rec_idx = rng.randint(0, n_actions - 1)
    act_idx = rec_idx if correct else (rec_idx + 1) % n_actions
    actions = [
        "strong_execution",
        "partial_execution",
        "poor_execution",
        "skip_recommended",
    ]
    created_at = 1700000000.0 + index * 3600
    return {
        "decision_id": f"L3TEST-{index:04d}",
        "domain": "trading",
        "category": "trend_following",
        "category_index": category_index,
        "factors_json": json.dumps({f"f{i}": factors[i] for i in range(n_factors)}),
        "factor_vector_json": json.dumps(factors),
        "recommended_action": actions[rec_idx],
        "recommended_index": rec_idx,
        "confidence": round(probs[rec_idx], 6),
        "probabilities_json": json.dumps(probs),
        "status": "confirmed",
        "created_at": created_at,
        "actual_action": actions[act_idx],
        "actual_index": act_idx,
        "is_correct": 1 if correct else 0,
        "verified_at": created_at + 1800,
        "context_json": "{}",
    }


def test_replay_empty_decisions():
    state = replay_decisions([], {}, "trading", "trading")

    assert state.decision_count == 0
    assert state.conservation_V == 0
    assert state.dk_weights is None
    assert all(np.allclose(vector, 0.0) for vector in state.centroids.values())


def test_replay_single_decision():
    decision, outcome = _decision("d1", created_at=1.0, factor_value=0.9)

    state = replay_decisions([decision], {"d1": outcome}, "trading", "trading")

    assert state.decision_count == 1
    assert state.conservation_V == 1
    assert state.conservation_q == 1.0
    assert not np.allclose(state.centroids[(0, 0)], 0.0)
    untouched = [
        vector
        for key, vector in state.centroids.items()
        if key != (0, 0)
    ]
    assert all(np.allclose(vector, 0.0) for vector in untouched)


@pytest.mark.timeout(30)
def test_replay_post_transition_dk_weights():
    decisions = [_make_decision(index, correct=True) for index in range(210)]

    state = replay_decisions(decisions, {}, "trading", "trading")
    replayed = replay_decisions(decisions, {}, "trading", "trading")
    comparison = compare_states(state, replayed)

    assert state.decision_count == 210
    assert state.dk_weights is not None
    assert len(state.dk_weights) > 0
    assert any(not np.allclose(vector, 0.0) for vector in state.centroids.values())
    assert state.category_phases is not None
    assert state.category_phases[0] == "MEAN_CONVERGENCE"
    assert comparison.passed is True


def test_replay_preserves_order():
    pairs = [
        _decision(f"d{i}", created_at=float(i), factor_value=0.1 * i)
        for i in range(1, 6)
    ]
    decisions = [decision for decision, _outcome in pairs]
    outcomes = {decision["decision_id"]: outcome for decision, outcome in pairs}
    forward = replay_decisions(decisions, outcomes, "trading", "trading")
    reversed_decisions = [
        {**decision, "created_at": float(10 - index)}
        for index, decision in enumerate(decisions)
    ]
    reversed_outcomes = {
        decision["decision_id"]: outcomes[decision["decision_id"]]
        for decision in reversed_decisions
    }

    backward = replay_decisions(reversed_decisions, reversed_outcomes, "trading", "trading")

    assert not np.allclose(forward.centroids[(0, 0)], backward.centroids[(0, 0)])


def test_compare_identical_states():
    state = _state()

    comparison = compare_states(state, state)

    assert comparison.passed is True
    assert comparison.centroid_match is True
    assert comparison.dk_match is True
    assert comparison.conservation_match is True


def test_compare_centroid_divergence():
    left = _state()
    right = _state(centroids={(0, 0): [9.0, 0.1], (0, 1): [0.2, 0.3]})

    comparison = compare_states(left, right)

    assert comparison.passed is False
    assert comparison.centroid_match is False
    assert comparison.details["centroid_mismatches"][0]["category_index"] == 0


def test_compare_conservation_divergence():
    left = _state()
    right = _state(conservation_V=3)

    comparison = compare_states(left, right)

    assert comparison.passed is False
    assert comparison.conservation_match is False
    assert comparison.details["conservation"]["checks"]["V"] is False


def test_compare_dk_divergence():
    left = _state()
    right = _state(dk_weights=[[1.0, 2.0]])

    comparison = compare_states(left, right)

    assert comparison.passed is False
    assert comparison.dk_match is False
    assert math.isclose(comparison.details["dk"]["max_abs_delta"], 1.0)


def test_level3_pass_with_matching_sources(monkeypatch):
    decision, outcome = _decision("d1", created_at=1.0, factor_value=0.2)
    expected_state = _state(decision_count=1, conservation_V=1)
    monkeypatch.setattr(sqlite_to_age, "_read_verified_decisions", lambda source: [decision])
    monkeypatch.setattr(sqlite_to_age, "_read_outcomes", lambda source: {"d1": outcome})
    monkeypatch.setattr(
        "copilot_sdk.migrate.verify_state.read_decisions_from_age",
        lambda conn, graph, domain: [{**decision, **outcome}],
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.verify_state.replay_decisions",
        lambda decisions, outcomes, domain, preset_config: expected_state,
    )

    result = verify_level3("source.db", object(), "graph", "trading", "trading")

    assert result["passed"] is True


def test_level3_fail_with_mismatched_count(monkeypatch):
    decisions = [_decision(f"d{i}", created_at=float(i), factor_value=0.2)[0] for i in range(10)]
    monkeypatch.setattr(sqlite_to_age, "_read_verified_decisions", lambda source: decisions)
    monkeypatch.setattr(
        "copilot_sdk.migrate.verify_state.read_decisions_from_age",
        lambda conn, graph, domain: decisions[:9],
    )

    result = verify_level3("source.db", object(), "graph", "trading", "trading")

    assert result["passed"] is False
    assert result["comparison"]["reason"] == "decision_count_mismatch"
    assert result["comparison"]["sqlite_count"] == 10
    assert result["comparison"]["age_count"] == 9


def test_read_decisions_from_age():
    class Cursor:
        def __init__(self, rows):
            self._rows = rows

        def fetchall(self):
            return self._rows

    class Conn:
        def __init__(self):
            self.query = ""

        def execute(self, query):
            self.query = query
            rows = [
                (
                    "d1",
                    "trading",
                    "trend_following",
                    0,
                    "{}",
                    "[0.1]",
                    "strong_execution",
                    0,
                    0.8,
                    "[0.8, 0.2]",
                    "confirmed",
                    1.0,
                    "strong_execution",
                    0,
                    1,
                    2.0,
                    "{}",
                )
            ]
            return Cursor(rows)

    conn = Conn()

    decisions = read_decisions_from_age(conn, "graph", "trading")

    assert "ORDER BY d.created_at ASC, d.decision_id ASC" in conn.query
    assert decisions == [
        {
            "decision_id": "d1",
            "domain": "trading",
            "category": "trend_following",
            "category_index": 0,
            "factors_json": "{}",
            "factor_vector_json": "[0.1]",
            "recommended_action": "strong_execution",
            "recommended_index": 0,
            "confidence": 0.8,
            "probabilities_json": "[0.8, 0.2]",
            "status": "confirmed",
            "created_at": 1.0,
            "actual_action": "strong_execution",
            "actual_index": 0,
            "is_correct": 1,
            "verified_at": 2.0,
            "context_json": "{}",
        }
    ]


def test_l3_handles_agtype_encoded_values(monkeypatch):
    decision, outcome = _decision("d1", created_at=1.0, factor_value=0.2)

    class Cursor:
        def __init__(self, rows):
            self._rows = rows

        def fetchall(self):
            return self._rows

    class Conn:
        def execute(self, query):
            return Cursor(
                [
                    (
                        '"d1"',
                        '"trading"',
                        '"trend_following"',
                        0,
                        '"{\\"signal_alignment\\": 0.200}"',
                        '"[0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]"',
                        '"strong_execution"',
                        0,
                        0.8,
                        '"[0.8, 0.1, 0.05, 0.05]"',
                        '"confirmed"',
                        1.0,
                        '"strong_execution"',
                        0,
                        1,
                        101.0,
                        '"{}"',
                    )
                ]
            )

    monkeypatch.setattr(sqlite_to_age, "_read_verified_decisions", lambda source: [decision])
    monkeypatch.setattr(sqlite_to_age, "_read_outcomes", lambda source: {"d1": outcome})

    result = verify_level3("source.db", Conn(), "graph", "trading", "trading")

    assert result["passed"] is True


def test_run_migration_level3_failure_gates_result(tmp_path, monkeypatch):
    from tests.test_sqlite_to_age_migration import _make_db

    db_path = _make_db(tmp_path)

    conn = FakeConn()
    monkeypatch.setattr(sqlite_to_age, "_connect_age", lambda *args: conn)
    monkeypatch.setattr(sqlite_to_age, "_verify_level1", lambda *args: {"passed": True, "details": {}})
    monkeypatch.setattr(sqlite_to_age, "_verify_level2", lambda *args: {"passed": True, "details": {}})
    monkeypatch.setattr(
        "copilot_sdk.migrate.verify_state.verify_level3",
        lambda *args: {"passed": False, "comparison": {"reason": "state_divergence"}},
    )

    result = sqlite_to_age.run_migration(
        "trading",
        str(db_path),
        "dsn",
        "graph",
        verify_l3=True,
        preset_config="trading",
    )

    assert result["status"] == "FAIL"
    assert result["fail_reason"] == "Level 3 state-vector verification failed"
    assert result["verification"]["level3"]["comparison"]["reason"] == "state_divergence"


def test_scratch_l3_verifies_live_not_scratch(tmp_path, monkeypatch):
    from tests.test_sqlite_to_age_migration import _make_db

    db_path = _make_db(tmp_path)
    l3_graphs = []

    conn = FakeConn()
    monkeypatch.setattr(sqlite_to_age, "_connect_age", lambda *args: conn)
    monkeypatch.setattr(sqlite_to_age, "create_scratch_graph", lambda dsn, domain: "scratch_graph")
    monkeypatch.setattr(sqlite_to_age, "verify_scratch_clean", lambda conn, graph: True)
    monkeypatch.setattr(sqlite_to_age, "_verify_level1", lambda *args: {"passed": True, "details": {}})
    monkeypatch.setattr(sqlite_to_age, "_verify_level2", lambda *args: {"passed": True, "details": {}})
    monkeypatch.setattr(sqlite_to_age, "copy_to_live", lambda *args: {"written": 4, "skipped": 0, "errors": 0})
    monkeypatch.setattr(sqlite_to_age, "drop_scratch_graph", lambda *args: None)

    def fake_verify_level3(source_db, conn, graph_name, domain, preset_config):
        l3_graphs.append(graph_name)
        return {"passed": True, "comparison": {}}

    monkeypatch.setattr("copilot_sdk.migrate.verify_state.verify_level3", fake_verify_level3)

    result = sqlite_to_age.run_migration(
        "trading",
        str(db_path),
        "dsn",
        "live_graph",
        use_scratch=True,
        verify_l3=True,
        preset_config="trading",
    )

    assert result["status"] == "PASS"
    assert l3_graphs == ["live_graph"]
