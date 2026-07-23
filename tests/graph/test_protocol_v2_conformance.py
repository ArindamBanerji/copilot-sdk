from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys
import json
import sqlite3
import uuid
from pathlib import Path

import numpy as np
import psycopg
import pytest

from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
from copilot_sdk.migrate.sqlite_to_age import run_migration
from copilot_sdk.scoring import CompoundingScorer


PENDING = pytest.mark.skip(reason="Protocol v2 implementation pending")
AGE_PENDING = pytest.mark.skip(reason="Protocol v2 AGE adapter implementation pending")
AGE_CROSS_DOMAIN_CONCURRENCY_PENDING = pytest.mark.skip(
    reason="AGE cross-domain concurrency/isolation stress coverage pending"
)
GENERIC_AGE_ROLLBACK_PENDING = pytest.mark.skip(
    reason=(
        "Generic AGE transaction rollback coverage pending; EvidenceReceipt rollback is active, "
        "reset mid-failure needs safe live failure injection"
    )
)
DEFAULT_AGE_DSN = "postgresql://localhost:5432/soc_copilot"


@pytest.fixture()
def sqlite_store(tmp_path):
    store = SQLiteGraphStore(tmp_path / "protocol_v2.sqlite", domain="test")
    try:
        yield store
    finally:
        store.close()


@pytest.fixture()
def age_store(request):
    if os.getenv("AGE_INTEGRATION") != "1":
        pytest.skip("AGE_INTEGRATION=1 required for AGE Protocol v2 conformance")
    dsn = os.getenv("AGE_TEST_DSN", "").strip()
    graph_name = os.getenv("AGE_TEST_GRAPH", "").strip()
    if not dsn:
        pytest.skip("AGE_TEST_DSN is required for AGE Protocol v2 conformance")
    if dsn == DEFAULT_AGE_DSN:
        pytest.skip("AGE_TEST_DSN must not use the default SOC demo DSN")
    if not graph_name:
        pytest.skip("AGE_TEST_GRAPH is required for AGE Protocol v2 conformance")
    if graph_name == "soc_graph":
        pytest.fail("AGE Protocol v2 conformance must never target soc_graph")
    if not graph_name.startswith("protocol_v2_test"):
        pytest.skip("AGE_TEST_GRAPH must start with protocol_v2_test")

    repo_root = Path(__file__).resolve().parents[2]
    ci_platform_path = repo_root.parent / "ci-platform"
    if str(ci_platform_path) not in sys.path:
        sys.path.insert(0, str(ci_platform_path))

    from ci_platform.graph import AGEGraphStoreAdapter  # noqa: PLC0415

    store = AGEGraphStoreAdapter(dsn=dsn, graph_name=graph_name)
    store._store._run(store._store._client.ensure_graph())
    test_name = request.node.name.replace("[", "_").replace("]", "_").replace("-", "_")
    store.protocol_v2_test_domain = f"pytest_protocol_v2_{test_name}_{uuid.uuid4().hex[:8]}"
    try:
        yield store
    finally:
        store.close()


def _write_governed_decision(
    store: SQLiteGraphStore,
    decision_id: str,
    *,
    domain: str = "test",
    category: str = "category_a",
    action: str = "approve",
    created_at: float = 100.0,
) -> None:
    store.write_governed_decision(
        decision_id=decision_id,
        domain=domain,
        category=category,
        category_index=0,
        recommended_action=action,
        recommended_index=0,
        confidence=0.8,
        probabilities=[0.8, 0.2],
        factor_vector=[0.25, 0.75],
        factor_names=["factor_a", "factor_b"],
        source="test",
        scorer_version="slice-1",
        preset_version="slice-1",
        factor_schema_version="slice-1",
        metadata={"created_at": created_at},
    )


def _create_migration_source(
    db_path: Path,
    domain: str,
    decision_ids: list[str],
    *,
    checkpoint_decision_id: str | None = None,
    receipt_decision_id: str | None = None,
) -> None:
    """Create a minimal real SQLite source compatible with the migration reader."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE decisions (
                decision_id TEXT PRIMARY KEY, domain TEXT, category TEXT,
                category_index INTEGER, factors_json TEXT, factor_vector_json TEXT,
                recommended_action TEXT, recommended_index INTEGER, confidence REAL,
                probabilities_json TEXT, status TEXT, created_at REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE outcomes (
                decision_id TEXT PRIMARY KEY, domain TEXT, actual_action TEXT,
                actual_index INTEGER, is_correct INTEGER, verified_at REAL,
                context_json TEXT
            )
            """
        )
        conn.executemany(
            "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    decision_id,
                    domain,
                    "category_a",
                    0,
                    '{"factor_a": 0.5}',
                    "[0.5]",
                    "approve",
                    0,
                    0.8,
                    '{"approve": 0.8}',
                    "confirmed",
                    float(index + 1),
                )
                for index, decision_id in enumerate(decision_ids)
            ],
        )
        conn.executemany(
            "INSERT INTO outcomes VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (decision_id, domain, "approve", 0, 1, float(index + 100), "{}")
                for index, decision_id in enumerate(decision_ids)
            ],
        )
        if checkpoint_decision_id is not None:
            conn.execute(
                """
                CREATE TABLE centroid_checkpoints (
                    checkpoint_id TEXT, domain TEXT, decision_id TEXT,
                    category TEXT, centroids_json TEXT, verified_count INTEGER,
                    created_at REAL
                )
                """
            )
            conn.execute(
                "INSERT INTO centroid_checkpoints VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("checkpoint-1", domain, checkpoint_decision_id, "category_a", "{}", 1, 10.0),
            )
        if receipt_decision_id is not None:
            conn.execute(
                """
                CREATE TABLE evidence_receipts (
                    receipt_intent_id TEXT, domain TEXT, decision_id TEXT,
                    chain_index INTEGER, canonical_payload_json TEXT, created_at REAL
                )
                """
            )
            conn.execute(
                "INSERT INTO evidence_receipts VALUES (?, ?, ?, ?, ?, ?)",
                ("receipt-1", domain, receipt_decision_id, 0, "{}", 11.0),
            )


def _create_disposable_migration_graph(dsn: str) -> tuple[psycopg.Connection, str]:
    """Create a graph isolated from the configured Protocol v2 test graph."""
    graph_name = f"protocol_v2_test_migration_{uuid.uuid4().hex[:8]}"
    conn = psycopg.connect(dsn, autocommit=True)
    conn.execute("LOAD 'age'")
    conn.execute("SET search_path = ag_catalog, '$user', public")
    conn.execute(f"SELECT create_graph('{graph_name}')")
    return conn, graph_name


def _age_outcome_count(age_store, decision_id: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (o:Outcome {{decision_id: {age_store._store._S(decision_id)}}})
        RETURN count(o) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_has_outcome_edge_count(age_store, decision_id: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (d:Decision {{decision_id: {age_store._store._S(decision_id)}}})-[:HAS_OUTCOME]->(o:Outcome)
        RETURN count(o) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_get_outcome(age_store, decision_id: str) -> dict | None:
    rows = age_store._store._run_query(
        f"""
        MATCH (o:Outcome {{decision_id: {age_store._store._S(decision_id)}}})
        RETURN o
        LIMIT 1
        """
    )
    if not rows:
        return None
    return age_store._store._node_to_dict(rows[0].get("o", rows[0]))


def _age_observation_count(age_store, observation_id: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (o:Observation {{observation_id: {age_store._store._S(observation_id)}}})
        RETURN count(o) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_get_observation(age_store, observation_id: str) -> dict | None:
    rows = age_store._store._run_query(
        f"""
        MATCH (o:Observation {{observation_id: {age_store._store._S(observation_id)}}})
        RETURN o
        LIMIT 1
        """
    )
    if not rows:
        return None
    return age_store._store._node_to_dict(rows[0].get("o", rows[0]))


def _age_domain_outcome_count(age_store, domain: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (o:Outcome)
        WHERE o.domain = {age_store._store._S(domain)}
        RETURN count(o) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_observation_triggered_evolution_count(age_store, observation_id: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (o:Observation {{observation_id: {age_store._store._S(observation_id)}}})-[r:TRIGGERED_EVOLUTION]->()
        RETURN count(r) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_conservation_status_count(age_store, status_id: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (c:ConservationStatus {{status_id: {age_store._store._S(status_id)}}})
        RETURN count(c) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_get_conservation_status(age_store, status_id: str) -> dict | None:
    rows = age_store._store._run_query(
        f"""
        MATCH (c:ConservationStatus {{status_id: {age_store._store._S(status_id)}}})
        RETURN c
        LIMIT 1
        """
    )
    if not rows:
        return None
    return age_store._store._node_to_dict(rows[0].get("c", rows[0]))


def _age_node_count(age_store, label: str, key: str, value: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (n:{label} {{{key}: {age_store._store._S(value)}}})
        RETURN count(n) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_decision_node_count(age_store, decision_id: str, domain: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (d:Decision {{decision_id: {age_store._store._S(decision_id)}}})
        WHERE d.domain = {age_store._store._S(domain)}
        RETURN count(d) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_get_node(age_store, label: str, key: str, value: str) -> dict | None:
    rows = age_store._store._run_query(
        f"""
        MATCH (n:{label} {{{key}: {age_store._store._S(value)}}})
        RETURN n
        LIMIT 1
        """
    )
    if not rows:
        return None
    return age_store._store._node_to_dict(rows[0].get("n", rows[0]))


def _age_get_receipts_for_domain(age_store, domain: str) -> list[dict]:
    rows = age_store._store._run_query(
        f"""
        MATCH (r:EvidenceReceipt)
        WHERE r.domain = {age_store._store._S(domain)}
        RETURN r
        ORDER BY r.chain_index
        """
    )
    return [age_store._store._node_to_dict(row.get("r", row)) for row in rows]


def _age_receipt_edge_count(age_store, decision_id: str, receipt_intent_id: str, domain: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (d:Decision {{decision_id: {age_store._store._S(decision_id)}}})-[:EMITTED_RECEIPT]->(r:EvidenceReceipt)
        WHERE d.domain = {age_store._store._S(domain)}
          AND r.domain = {age_store._store._S(domain)}
          AND r.receipt_intent_id = {age_store._store._S(receipt_intent_id)}
        RETURN count(r) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_about_edge_count(age_store, decision_id: str, entity_id: str, domain: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (d:Decision {{decision_id: {age_store._store._S(decision_id)}}})-[r:ABOUT]->(e:DomainContext)
        WHERE d.domain = {age_store._store._S(domain)}
          AND e.domain = {age_store._store._S(domain)}
          AND e.entity_id = {age_store._store._S(entity_id)}
        RETURN count(r) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_decision_triggered_evolution_count(age_store, decision_id: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (d:Decision {{decision_id: {age_store._store._S(decision_id)}}})-[r:TRIGGERED_EVOLUTION]->()
        RETURN count(r) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_domain_label_count(age_store, label: str, domain: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (n:{label})
        WHERE n.domain = {age_store._store._S(domain)}
        RETURN count(n) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _age_domain_about_edge_count(age_store, domain: str) -> int:
    rows = age_store._store._run_query(
        f"""
        MATCH (d:Decision)-[r:ABOUT]->(e:DomainContext)
        WHERE d.domain = {age_store._store._S(domain)}
          AND e.domain = {age_store._store._S(domain)}
        RETURN count(r) AS cnt
        """
    )
    return int(rows[0]["cnt"]) if rows else 0


def _json_value(value):
    return json.loads(value) if isinstance(value, str) else value


def _write_observation(
    store: SQLiteGraphStore,
    observation_id: str = "OBS-1",
    *,
    domain: str = "test",
) -> None:
    store.write_observation(
        observation_id=observation_id,
        domain=domain,
        category="category_a",
        recommended_action="approve",
        confidence=0.77,
        source_route="preview",
        scorer_version="slice-4",
        factor_schema_version="slice-4",
        entity_id="entity-1",
        factor_vector=[0.2, 0.8],
        factor_names=["factor_a", "factor_b"],
        metadata={"created_at": 123.0, "purpose": "preview"},
    )


def _append_receipt(
    store: SQLiteGraphStore,
    receipt_intent_id: str,
    *,
    payload_value: str = "approved",
    domain: str = "test",
) -> tuple[int, str]:
    return store.append_evidence_receipt(
        receipt_intent_id=receipt_intent_id,
        domain=domain,
        decision_id="GOV-1",
        canonical_payload={
            "decision_id": "GOV-1",
            "action": payload_value,
            "confidence": 0.8,
            "factor_hash": "factor-hash",
            "timestamp": "2026-01-01T00:00:00Z",
        },
        actor="scorer",
        source_route="/api/test",
        metadata={"purpose": "conformance"},
    )


def test_write_decision(sqlite_store):
    """Creates Decision(pending), counted by count_decisions."""
    # Protocol v2 invariant: v1 write_decision remains compatible.
    decision_id = sqlite_store.write_decision(
        "test",
        category="category_a",
        action="approve",
        confidence=0.9,
        factors={"factor_a": 0.1, "factor_b": 0.9},
        metadata={"created_at": 100.0},
    )

    decision = sqlite_store.get_decision(decision_id)

    assert isinstance(decision_id, str)
    assert decision is not None
    assert decision["decision_id"] == decision_id
    assert decision["status"] == "pending"
    assert sqlite_store.count_decisions("test") == 1
    assert sqlite_store.count_verified_decisions("test") == 0


def test_v1_write_decision_generates_distinct_ids(sqlite_store):
    """Repeated v1 write_decision calls create distinct pending Decisions."""
    # Protocol v2 invariant: v1 compatibility is additive; idempotent replay belongs
    # to caller-supplied v2 IDs and receipt/outbox semantics, not generated v1 IDs.
    memory = InMemoryGraphStore(domain="test")
    for store in (sqlite_store, memory):
        first_id = store.write_decision(
            "test",
            category="category_a",
            action="approve",
            confidence=0.9,
            factors={"factor_a": 0.1, "factor_b": 0.9},
            metadata={"created_at": 100.0},
        )
        second_id = store.write_decision(
            "test",
            category="category_a",
            action="approve",
            confidence=0.9,
            factors={"factor_a": 0.1, "factor_b": 0.9},
            metadata={"created_at": 101.0},
        )

        assert first_id
        assert second_id
        assert first_id != second_id
        assert store.get_decision(first_id)["status"] == "pending"
        assert store.get_decision(second_id)["status"] == "pending"
        assert store.count_decisions("test") == 2
        assert store.count_verified_decisions("test") == 0


def test_v2_governed_decision_caller_id(sqlite_store):
    """write_governed_decision persists the caller-supplied decision_id."""
    # Protocol v2 method/invariant: v2 decision writes are additive to v1.
    _write_governed_decision(sqlite_store, "GOV-1")

    decision = sqlite_store.get_decision("GOV-1")

    assert decision is not None
    assert decision["decision_id"] == "GOV-1"
    assert decision["recommended_action"] == "approve"
    assert decision["factor_vector"] == [0.25, 0.75]
    assert decision["metadata"]["source"] == "test"
    assert decision["status"] == "pending"
    assert sqlite_store.count_decisions("test") == 1
    assert sqlite_store.count_verified_decisions("test") == 0


@pytest.mark.age
def test_age_v2_governed_decision_caller_id(age_store):
    """AGE write_governed_decision persists caller ID and pending status."""
    # Protocol v2 AGE Slice 1 invariant: AGE creates pending Decisions without Outcomes.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)

    decision = age_store.get_decision(decision_id)

    assert decision is not None
    assert decision["decision_id"] == decision_id
    assert decision["domain"] == domain
    assert decision["recommended_action"] == "approve"
    assert decision["factor_vector"] == [0.25, 0.75]
    assert decision["status"] == "pending"
    assert age_store.count_decisions(domain) == 1
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_governed_decision_identical_replay_skips(age_store):
    """AGE write_governed_decision is idempotent for identical Class A replay."""
    # Protocol v2 invariant: caller-supplied governed Decision IDs are Class A keys.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-IDEMP-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain, created_at=100.0)
    before = age_store.get_decision(decision_id)

    _write_governed_decision(age_store, decision_id, domain=domain, created_at=200.0)

    after = age_store.get_decision(decision_id)
    assert after == before
    assert age_store.count_decisions(domain) == 1
    assert age_store.count_verified_decisions(domain) == 0
    assert _age_decision_node_count(age_store, decision_id, domain) == 1


@pytest.mark.age
def test_age_governed_decision_conflict_raises(age_store):
    """AGE write_governed_decision rejects conflicting Class A replay."""
    # Protocol v2 invariant: same governed Decision ID cannot be reused for a different payload.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-CONFLICT-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain, created_at=100.0)
    before = age_store.get_decision(decision_id)

    with pytest.raises(ValueError, match="conflicting governed decision_id"):
        _write_governed_decision(
            age_store,
            decision_id,
            domain=domain,
            action="manual_review",
            created_at=200.0,
        )

    after = age_store.get_decision(decision_id)
    assert after == before
    assert age_store.count_decisions(domain) == 1
    assert age_store.count_verified_decisions(domain) == 0
    assert _age_decision_node_count(age_store, decision_id, domain) == 1


def test_write_outcome_confirmed(sqlite_store):
    """write_outcome with is_correct=True transitions status to confirmed."""
    # Protocol v2 method/invariant: write_outcome atomically updates Decision.status.
    _write_governed_decision(sqlite_store, "GOV-1")

    sqlite_store.write_outcome("GOV-1", "approve", True)
    decision = sqlite_store.get_decision("GOV-1")

    assert decision is not None
    assert decision["status"] == "confirmed"
    assert sqlite_store.count_verified_decisions("test") == 1


@pytest.mark.age
def test_age_write_outcome_confirmed(age_store):
    """AGE write_outcome with is_correct=True creates Outcome and confirms Decision."""
    # Protocol v2 AGE Slice 2 invariant: Outcome write and status transition are one write.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)

    age_store.write_outcome(
        decision_id,
        "approve",
        True,
        metadata={"actual_index": 0, "reward": 1.0, "verifier": "analyst-a", "verified_at": 123.0},
    )
    decision = age_store.get_decision(decision_id)
    outcome = _age_get_outcome(age_store, decision_id)

    assert decision is not None
    assert decision["status"] == "confirmed"
    assert outcome is not None
    assert outcome["actual_action"] == "approve"
    assert outcome["actual_index"] == 0
    assert outcome["reward"] == 1.0
    assert outcome["verifier"] == "analyst-a"
    assert outcome["verified_at"] == 123.0
    assert _age_has_outcome_edge_count(age_store, decision_id) == 1
    assert age_store.count_verified_decisions(domain) == 1


def test_write_outcome_overridden(sqlite_store):
    """write_outcome with is_correct=False transitions status to overridden."""
    # Protocol v2 method/invariant: write_outcome atomically updates Decision.status.
    _write_governed_decision(sqlite_store, "GOV-1")

    sqlite_store.write_outcome("GOV-1", "manual_review", False)
    decision = sqlite_store.get_decision("GOV-1")

    assert decision is not None
    assert decision["status"] == "overridden"
    assert sqlite_store.count_verified_decisions("test") == 1


@pytest.mark.age
def test_age_write_outcome_overridden(age_store):
    """AGE write_outcome with is_correct=False overrides Decision."""
    # Protocol v2 AGE Slice 2 invariant: incorrect outcomes verify as overridden.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)

    age_store.write_outcome(
        decision_id,
        "manual_review",
        False,
        metadata={"actual_index": 1, "override_reason": "policy"},
    )
    decision = age_store.get_decision(decision_id)
    outcome = _age_get_outcome(age_store, decision_id)

    assert decision is not None
    assert decision["status"] == "overridden"
    assert outcome is not None
    assert outcome["actual_action"] == "manual_review"
    assert outcome["actual_index"] == 1
    assert outcome["reward"] == 0.0
    assert outcome["verifier"] == "analyst"
    assert outcome["override_reason"] == "policy"
    assert _age_has_outcome_edge_count(age_store, decision_id) == 1
    assert age_store.count_verified_decisions(domain) == 1


def test_outcome_atomic(sqlite_store):
    """Outcome insert and Decision.status update commit or roll back together."""
    # Protocol v2 invariant: no orphan Outcome and no orphan status transition.
    _write_governed_decision(sqlite_store, "GOV-1")
    sqlite_store.connection.execute(
        """
        CREATE TEMP TRIGGER fail_decision_status_update
        BEFORE UPDATE OF status ON decisions
        BEGIN
            SELECT RAISE(ABORT, 'status update blocked');
        END
        """
    )
    sqlite_store.connection.commit()

    with pytest.raises(sqlite3.IntegrityError, match="status update blocked"):
        sqlite_store.write_outcome("GOV-1", "approve", True)

    outcome = sqlite_store.connection.execute(
        "SELECT * FROM outcomes WHERE decision_id = ?",
        ("GOV-1",),
    ).fetchone()
    decision = sqlite_store.get_decision("GOV-1")

    assert outcome is None
    assert decision is not None
    assert decision["status"] == "pending"


def test_outcome_missing_decision(sqlite_store):
    """write_outcome for a missing decision_id raises."""
    # Protocol v2 method/invariant: write_outcome requires an existing Decision.
    with pytest.raises(KeyError):
        sqlite_store.write_outcome("missing", "approve", True)


@pytest.mark.age
def test_age_outcome_missing_decision(age_store):
    """AGE write_outcome for a missing Decision raises without creating Outcome."""
    # Protocol v2 AGE Slice 2 invariant: outcomes require a canonical Decision.
    decision_id = f"AGE-MISSING-{uuid.uuid4().hex[:8]}"

    with pytest.raises(KeyError):
        age_store.write_outcome(decision_id, "approve", True)

    assert _age_outcome_count(age_store, decision_id) == 0


@pytest.mark.age
def test_age_outcome_direct_duplicate_raises(age_store):
    """AGE direct duplicate write_outcome raises and preserves original state."""
    # Protocol v2 AGE Slice 2 invariant: one Outcome per Decision for direct calls.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    age_store.write_outcome(decision_id, "approve", True, metadata={"actual_index": 0})

    with pytest.raises(ValueError, match="outcome already exists"):
        age_store.write_outcome(decision_id, "manual_review", False, metadata={"actual_index": 1})

    decision = age_store.get_decision(decision_id)
    outcome = _age_get_outcome(age_store, decision_id)
    assert decision is not None
    assert decision["status"] == "confirmed"
    assert outcome is not None
    assert outcome["actual_action"] == "approve"
    assert outcome["actual_index"] == 0
    assert _age_outcome_count(age_store, decision_id) == 1
    assert _age_has_outcome_edge_count(age_store, decision_id) == 1
    assert age_store.count_verified_decisions(domain) == 1


@pytest.mark.age
def test_age_outcome_non_pending_decision_raises(age_store):
    """AGE write_outcome requires a pending Decision for Slice 2."""
    # Protocol v2 AGE Slice 2 invariant: conformance-created Decisions transition from pending.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    age_store._store._run_query(
        f"""
        MATCH (d:Decision {{decision_id: {age_store._store._S(decision_id)}}})
        SET d.status = 'confirmed'
        RETURN d
        """
    )

    with pytest.raises(ValueError, match="status is not pending"):
        age_store.write_outcome(decision_id, "approve", True)

    assert _age_outcome_count(age_store, decision_id) == 0
    assert age_store.count_verified_decisions(domain) == 1


@pytest.mark.age
def test_age_count_verified_after_outcome(age_store):
    """AGE count_verified_decisions increments only after successful outcomes."""
    # Protocol v2 AGE Slice 2 invariant: V is status-based after canonical write.
    domain = age_store.protocol_v2_test_domain
    pending_id = f"AGE-GOV-PENDING-{uuid.uuid4().hex[:8]}"
    confirmed_id = f"AGE-GOV-CONFIRMED-{uuid.uuid4().hex[:8]}"
    overridden_id = f"AGE-GOV-OVERRIDDEN-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, pending_id, domain=domain)
    _write_governed_decision(age_store, confirmed_id, domain=domain)
    _write_governed_decision(age_store, overridden_id, domain=domain)

    assert age_store.count_verified_decisions(domain) == 0
    age_store.write_outcome(confirmed_id, "approve", True)
    age_store.write_outcome(overridden_id, "manual_review", False)

    assert age_store.count_decisions(domain) == 3
    assert age_store.count_verified_decisions(domain) == 2
    assert age_store.get_decision(pending_id)["status"] == "pending"


@pytest.mark.age
def test_age_outcome_no_orphan_on_duplicate(age_store):
    """Standalone duplicate Outcome.decision_id blocks write without creating an edge."""
    # Protocol v2 AGE Slice 2 invariant: malformed standalone Outcomes still enforce uniqueness.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    age_store._store._run_query(
        f"""
        CREATE (o:Outcome {{
            decision_id: {age_store._store._S(decision_id)},
            domain: {age_store._store._S(domain)},
            actual_action: 'preexisting',
            is_correct: true
        }})
        RETURN o
        """
    )

    with pytest.raises(ValueError, match="outcome already exists"):
        age_store.write_outcome(decision_id, "approve", True)

    decision = age_store.get_decision(decision_id)
    assert decision is not None
    assert decision["status"] == "pending"
    assert _age_outcome_count(age_store, decision_id) == 1
    assert _age_has_outcome_edge_count(age_store, decision_id) == 0
    assert age_store.count_verified_decisions(domain) == 0


def test_write_observation(sqlite_store):
    """write_observation creates a queryable Observation, not a Decision."""
    # Protocol v2 method/invariant: write_observation is separate from write_decision.
    _write_observation(sqlite_store)
    _write_observation(sqlite_store)

    observation = sqlite_store.connection.execute(
        "SELECT * FROM observations WHERE observation_id = ?",
        ("OBS-1",),
    ).fetchone()
    edge_count = sqlite_store.connection.execute(
        "SELECT COUNT(*) AS n FROM observation_entity_edges WHERE observation_id = ?",
        ("OBS-1",),
    ).fetchone()["n"]
    factor_vector = sqlite_store.connection.execute(
        "SELECT * FROM observation_factor_vectors WHERE observation_id = ?",
        ("OBS-1",),
    ).fetchone()

    assert observation is not None
    assert observation["domain"] == "test"
    assert observation["source_route"] == "preview"
    assert int(edge_count) == 1
    assert factor_vector is not None
    assert factor_vector["factor_vector_json"] == "[0.2, 0.8]"
    assert sqlite_store.count_decisions("test") == 0
    assert sqlite_store.count_verified_decisions("test") == 0


@pytest.mark.age
def test_age_write_observation(age_store):
    """AGE write_observation creates one Observation and no Decisions."""
    # Protocol v2 AGE Slice 3 invariant: Observations are distinct from Decisions.
    domain = age_store.protocol_v2_test_domain
    observation_id = f"AGE-OBS-{uuid.uuid4().hex[:8]}"

    _write_observation(age_store, observation_id, domain=domain)
    _write_observation(age_store, observation_id, domain=domain)
    observation = _age_get_observation(age_store, observation_id)

    assert observation is not None
    assert observation["observation_id"] == observation_id
    assert observation["domain"] == domain
    assert observation["source_route"] == "preview"
    assert observation["entity_id"] == "entity-1"
    assert observation["factor_vector"] == [0.2, 0.8]
    assert observation["factor_names"] == ["factor_a", "factor_b"]
    assert _age_observation_count(age_store, observation_id) == 1
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0
    assert _age_domain_outcome_count(age_store, domain) == 0


def test_observation_not_in_V(sqlite_store):
    """Observations never increment conservation V."""
    # Protocol v2 invariant: count_verified_decisions excludes Observation nodes.
    _write_observation(sqlite_store)
    _write_governed_decision(sqlite_store, "GOV-1")
    sqlite_store.write_outcome("GOV-1", "approve", True)

    assert sqlite_store.count_decisions("test") == 1
    assert sqlite_store.count_verified_decisions("test") == 1


@pytest.mark.age
def test_age_observation_not_in_V(age_store):
    """AGE Observations do not increment verified Decision count."""
    # Protocol v2 AGE Slice 3 invariant: V counts verified Decisions only.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    observation_id = f"AGE-OBS-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    age_store.write_outcome(decision_id, "approve", True)

    _write_observation(age_store, observation_id, domain=domain)

    assert age_store.count_decisions(domain) == 1
    assert age_store.count_verified_decisions(domain) == 1
    assert _age_observation_count(age_store, observation_id) == 1


def test_observation_not_in_flywheel(sqlite_store):
    """Observations do not create AgentEvolver flywheel edges."""
    # Protocol v2 invariant: no TRIGGERED_EVOLUTION edge from Observation.
    _write_observation(sqlite_store)

    events = sqlite_store.get_evolution_events("test")

    assert events == []


@pytest.mark.age
def test_age_observation_not_in_flywheel(age_store):
    """AGE Observations do not create TRIGGERED_EVOLUTION edges."""
    # Protocol v2 AGE Slice 3 invariant: Observation writes do not enter flywheel edges.
    domain = age_store.protocol_v2_test_domain
    observation_id = f"AGE-OBS-{uuid.uuid4().hex[:8]}"

    _write_observation(age_store, observation_id, domain=domain)

    assert _age_observation_triggered_evolution_count(age_store, observation_id) == 0


def test_count_verified_empty(sqlite_store):
    """count_verified_decisions returns zero on an empty store."""
    # Protocol v2 method/invariant: count_verified_decisions defines V.
    assert sqlite_store.count_verified_decisions("test") == 0


@pytest.mark.age
def test_age_count_verified_empty(age_store):
    """AGE count_verified_decisions returns 0 for an empty test domain."""
    # Protocol v2 AGE Slice 1 invariant: verified count is status-based.
    assert age_store.count_decisions(age_store.protocol_v2_test_domain) == 0
    assert age_store.count_verified_decisions(age_store.protocol_v2_test_domain) == 0


def test_count_verified_pending(sqlite_store):
    """Pending decisions are excluded from count_verified_decisions."""
    # Protocol v2 invariant: only verified decisions count.
    _write_governed_decision(sqlite_store, "GOV-1")
    _write_governed_decision(sqlite_store, "GOV-2", created_at=101.0)

    assert sqlite_store.get_decision("GOV-1")["status"] == "pending"
    assert sqlite_store.get_decision("GOV-2")["status"] == "pending"
    assert sqlite_store.count_decisions("test") == 2
    assert sqlite_store.count_verified_decisions("test") == 0


@pytest.mark.age
def test_age_count_verified_pending(age_store):
    """AGE pending Decisions count as decisions but not verified V."""
    # Protocol v2 AGE Slice 1 invariant: pending Decisions are excluded from V.
    domain = age_store.protocol_v2_test_domain
    _write_governed_decision(age_store, f"AGE-GOV-{uuid.uuid4().hex[:8]}", domain=domain)

    assert age_store.count_decisions(domain) == 1
    assert age_store.count_verified_decisions(domain) == 0


def test_count_verified_mixed(sqlite_store):
    """count_verified_decisions counts only decisions with outcomes in Slice 1."""
    # Protocol v2 invariant: pending rows are excluded from V.
    _write_governed_decision(sqlite_store, "GOV-1")
    _write_governed_decision(sqlite_store, "GOV-2", created_at=101.0)
    _write_governed_decision(sqlite_store, "GOV-3", created_at=102.0)

    sqlite_store.write_outcome("GOV-1", "approve", True)
    sqlite_store.write_outcome("GOV-2", "manual_review", False)

    assert sqlite_store.get_decision("GOV-1")["status"] == "confirmed"
    assert sqlite_store.get_decision("GOV-2")["status"] == "overridden"
    assert sqlite_store.get_decision("GOV-3")["status"] == "pending"
    assert sqlite_store.count_decisions("test") == 3
    assert sqlite_store.count_verified_decisions("test") == 2


@pytest.mark.age
def test_age_count_verified_status_based_without_outcomes(age_store):
    """AGE verified count uses Decision.status, not Outcome nodes."""
    # Protocol v2 AGE Slice 1 invariant: V counts confirmed/overridden statuses only.
    domain = age_store.protocol_v2_test_domain
    pending_id = f"AGE-GOV-PENDING-{uuid.uuid4().hex[:8]}"
    confirmed_id = f"AGE-GOV-CONFIRMED-{uuid.uuid4().hex[:8]}"
    overridden_id = f"AGE-GOV-OVERRIDDEN-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, pending_id, domain=domain)
    _write_governed_decision(age_store, confirmed_id, domain=domain)
    _write_governed_decision(age_store, overridden_id, domain=domain)
    age_store._store._run_query(
        f"""
        MATCH (d:Decision)
        WHERE d.domain = {age_store._store._S(domain)}
          AND d.decision_id = {age_store._store._S(confirmed_id)}
        SET d.status = 'confirmed'
        RETURN d
        """
    )
    age_store._store._run_query(
        f"""
        MATCH (d:Decision)
        WHERE d.domain = {age_store._store._S(domain)}
          AND d.decision_id = {age_store._store._S(overridden_id)}
        SET d.status = 'overridden'
        RETURN d
        """
    )

    assert age_store.count_decisions(domain) == 3
    assert age_store.count_verified_decisions(domain) == 2


def test_sqlite_status_migration_backfills_from_outcomes(tmp_path):
    """Existing pre-status SQLite rows are backfilled from reliable outcomes."""
    db_path = tmp_path / "legacy.sqlite"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE decisions (
            decision_id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            category TEXT NOT NULL,
            category_index INTEGER NOT NULL,
            factors_json TEXT NOT NULL,
            factor_vector_json TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            recommended_index INTEGER NOT NULL,
            confidence REAL NOT NULL,
            probabilities_json TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE TABLE outcomes (
            decision_id TEXT PRIMARY KEY REFERENCES decisions(decision_id),
            domain TEXT NOT NULL DEFAULT '',
            actual_action TEXT NOT NULL,
            actual_index INTEGER NOT NULL,
            is_correct INTEGER NOT NULL,
            verified_at REAL NOT NULL,
            context_json TEXT
        );
        INSERT INTO decisions VALUES
            ('D-1', 'test', 'category_a', 0, '{}', '[0.1]', 'approve', 0, 0.9, '[0.9]', 100.0),
            ('D-2', 'test', 'category_a', 0, '{}', '[0.2]', 'approve', 0, 0.8, '[0.8]', 101.0),
            ('D-3', 'test', 'category_a', 0, '{}', '[0.3]', 'approve', 0, 0.7, '[0.7]', 102.0);
        INSERT INTO outcomes VALUES
            ('D-1', 'test', 'approve', 0, 1, 200.0, NULL),
            ('D-2', 'test', 'manual_review', 1, 0, 201.0, NULL);
        """
    )
    conn.commit()
    conn.close()

    store = SQLiteGraphStore(db_path, domain="test")
    try:
        assert store.get_decision("D-1")["status"] == "confirmed"
        assert store.get_decision("D-2")["status"] == "overridden"
        assert store.get_decision("D-3")["status"] == "pending"
        assert store.count_verified_decisions("test") == 2
    finally:
        store.close()


def test_evidence_receipt_chain(sqlite_store):
    """append_evidence_receipt maintains chain_index and previous_hash order."""
    # Protocol v2 method/invariant: append_evidence_receipt owns hash-chain append.
    first = _append_receipt(sqlite_store, "RCP-1", payload_value="approved")
    second = _append_receipt(sqlite_store, "RCP-2", payload_value="review")
    third = _append_receipt(sqlite_store, "RCP-3", payload_value="blocked")

    rows = sqlite_store.connection.execute(
        """
        SELECT chain_index, previous_hash, payload_hash
        FROM evidence_receipts
        WHERE domain = ?
        ORDER BY chain_index
        """,
        ("test",),
    ).fetchall()

    assert [first[0], second[0], third[0]] == [0, 1, 2]
    assert [row["chain_index"] for row in rows] == [0, 1, 2]
    assert rows[0]["previous_hash"] == "GENESIS"
    assert rows[1]["previous_hash"] == rows[0]["payload_hash"]
    assert rows[2]["previous_hash"] == rows[1]["payload_hash"]
    assert first[1] == rows[0]["payload_hash"]
    assert second[1] == rows[1]["payload_hash"]
    assert third[1] == rows[2]["payload_hash"]
    assert sqlite_store.count_decisions("test") == 0
    assert sqlite_store.count_verified_decisions("test") == 0


def test_evidence_receipt_hash_json_parity(tmp_path):
    """Memory and SQLite receipt hashing use the same canonical JSON rules."""
    # Protocol v2 invariant: local adapters agree on canonical receipt payload hashes.
    sqlite = SQLiteGraphStore(tmp_path / "receipt-parity.sqlite", domain="test")
    memory = InMemoryGraphStore(domain="test")
    try:
        payload = {
            "decision_id": "GOV-1",
            "action": "approved",
            "weights": np.asarray([0.25, 0.75], dtype=np.float64),
            "count": np.int64(2),
        }
        metadata = {"score": np.float64(0.91)}

        sqlite_receipt = sqlite.append_evidence_receipt(
            receipt_intent_id="RCP-NP",
            domain="test",
            decision_id="GOV-1",
            canonical_payload=payload,
            actor="scorer",
            source_route="/api/test",
            metadata=metadata,
        )
        memory_receipt = memory.append_evidence_receipt(
            receipt_intent_id="RCP-NP",
            domain="test",
            decision_id="GOV-1",
            canonical_payload=payload,
            actor="scorer",
            source_route="/api/test",
            metadata=metadata,
        )

        assert sqlite_receipt[1] == memory_receipt[1]
    finally:
        sqlite.close()


@pytest.mark.age
def test_age_evidence_receipt_chain(age_store):
    """AGE append_evidence_receipt maintains chain_index and previous_hash order."""
    # Protocol v2 AGE Slice 7 invariant: EvidenceReceipt append owns the audit chain.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    decisions_before = age_store.count_decisions(domain)
    verified_before = age_store.count_verified_decisions(domain)

    first = age_store.append_evidence_receipt(
        receipt_intent_id=f"AGE-RCP-{uuid.uuid4().hex[:8]}",
        domain=domain,
        decision_id=decision_id,
        canonical_payload={"decision_id": decision_id, "action": "approved"},
        actor="scorer",
        source_route="/api/test",
        metadata={"purpose": "chain"},
    )
    second = age_store.append_evidence_receipt(
        receipt_intent_id=f"AGE-RCP-{uuid.uuid4().hex[:8]}",
        domain=domain,
        decision_id=decision_id,
        canonical_payload={"decision_id": decision_id, "action": "review"},
        actor="scorer",
        source_route="/api/test",
        metadata={"purpose": "chain"},
    )
    third = age_store.append_evidence_receipt(
        receipt_intent_id=f"AGE-RCP-{uuid.uuid4().hex[:8]}",
        domain=domain,
        decision_id=decision_id,
        canonical_payload={"decision_id": decision_id, "action": "blocked"},
        actor="scorer",
        source_route="/api/test",
        metadata={"purpose": "chain"},
    )
    receipts = _age_get_receipts_for_domain(age_store, domain)

    assert [first[0], second[0], third[0]] == [0, 1, 2]
    assert [receipt["chain_index"] for receipt in receipts] == [0, 1, 2]
    assert receipts[0]["previous_hash"] == "GENESIS"
    assert receipts[1]["previous_hash"] == receipts[0]["payload_hash"]
    assert receipts[2]["previous_hash"] == receipts[1]["payload_hash"]
    assert first[1] == receipts[0]["payload_hash"]
    assert second[1] == receipts[1]["payload_hash"]
    assert third[1] == receipts[2]["payload_hash"]
    for receipt in receipts:
        assert receipt["receipt_id"] == receipt["receipt_intent_id"]
        assert receipt["decision_id"] == decision_id
        assert receipt["schema_version"] == "protocol_v2"
        assert _age_receipt_edge_count(
            age_store,
            decision_id,
            receipt["receipt_intent_id"],
            domain,
        ) == 1
    assert age_store.count_decisions(domain) == decisions_before
    assert age_store.count_verified_decisions(domain) == verified_before


@pytest.mark.age
def test_age_evidence_replay_same_intent_skips(age_store):
    """AGE same receipt_intent_id and same payload returns the existing tuple."""
    # Protocol v2 AGE Slice 7 invariant: identical receipt replay is idempotent.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    receipt_intent_id = f"AGE-RCP-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    payload = {
        "receipt_intent_id": receipt_intent_id,
        "domain": domain,
        "decision_id": decision_id,
        "canonical_payload": {"decision_id": decision_id, "action": "approved"},
        "actor": "scorer",
        "source_route": "/api/test",
        "metadata": {"purpose": "replay"},
    }

    first = age_store.append_evidence_receipt(**payload)
    second = age_store.append_evidence_receipt(**payload)
    receipt = _age_get_node(age_store, "EvidenceReceipt", "receipt_intent_id", receipt_intent_id)

    assert second == first
    assert _age_node_count(age_store, "EvidenceReceipt", "receipt_intent_id", receipt_intent_id) == 1
    assert receipt is not None
    assert receipt["receipt_id"] == receipt_intent_id
    assert receipt["chain_index"] == first[0]
    assert receipt["payload_hash"] == first[1]
    assert _age_receipt_edge_count(age_store, decision_id, receipt_intent_id, domain) == 1
    assert age_store.count_decisions(domain) == 1
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_evidence_replay_conflict_raises(age_store):
    """AGE same receipt_intent_id with different payload raises without mutation."""
    # Protocol v2 AGE Slice 7 invariant: conflicting receipt replay is visible.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    receipt_intent_id = f"AGE-RCP-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    first = age_store.append_evidence_receipt(
        receipt_intent_id=receipt_intent_id,
        domain=domain,
        decision_id=decision_id,
        canonical_payload={"decision_id": decision_id, "action": "approved"},
        actor="scorer",
        source_route="/api/test",
        metadata={"purpose": "conflict"},
    )
    original = _age_get_node(age_store, "EvidenceReceipt", "receipt_intent_id", receipt_intent_id)

    with pytest.raises(ValueError, match="conflicting evidence receipt_intent_id"):
        age_store.append_evidence_receipt(
            receipt_intent_id=receipt_intent_id,
            domain=domain,
            decision_id=decision_id,
            canonical_payload={"decision_id": decision_id, "action": "blocked"},
            actor="scorer",
            source_route="/api/test",
            metadata={"purpose": "conflict"},
        )

    receipts = _age_get_receipts_for_domain(age_store, domain)
    assert len(receipts) == 1
    assert receipts[0]["chain_index"] == first[0]
    assert receipts[0]["payload_hash"] == first[1]
    assert _age_get_node(age_store, "EvidenceReceipt", "receipt_intent_id", receipt_intent_id) == original
    assert _age_receipt_edge_count(age_store, decision_id, receipt_intent_id, domain) == 1
    assert age_store.count_decisions(domain) == 1
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_evidence_missing_decision(age_store):
    """AGE append_evidence_receipt for a missing Decision raises KeyError."""
    # Protocol v2 AGE Slice 7 invariant: receipt append never creates Decisions.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-MISSING-{uuid.uuid4().hex[:8]}"
    receipt_intent_id = f"AGE-RCP-{uuid.uuid4().hex[:8]}"

    with pytest.raises(KeyError):
        age_store.append_evidence_receipt(
            receipt_intent_id=receipt_intent_id,
            domain=domain,
            decision_id=decision_id,
            canonical_payload={"decision_id": decision_id, "action": "approved"},
            actor="scorer",
            source_route="/api/test",
            metadata={"purpose": "missing"},
        )

    assert age_store.get_decision(decision_id) is None
    assert _age_node_count(age_store, "EvidenceReceipt", "receipt_intent_id", receipt_intent_id) == 0
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_evidence_no_decision_or_V_side_effect(age_store):
    """AGE EvidenceReceipt append does not mutate Decision status or V."""
    # Protocol v2 AGE Slice 7 invariant: EvidenceReceipt is audit memory, not V input.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    receipt_intent_id = f"AGE-RCP-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    decisions_before = age_store.count_decisions(domain)
    verified_before = age_store.count_verified_decisions(domain)
    status_before = age_store.get_decision(decision_id)["status"]

    age_store.append_evidence_receipt(
        receipt_intent_id=receipt_intent_id,
        domain=domain,
        decision_id=decision_id,
        canonical_payload={"decision_id": decision_id, "action": "approved"},
        actor="scorer",
        source_route="/api/test",
        metadata={"purpose": "side-effect"},
    )

    decision = age_store.get_decision(decision_id)
    assert decision is not None
    assert decision["status"] == status_before == "pending"
    assert age_store.count_decisions(domain) == decisions_before
    assert age_store.count_verified_decisions(domain) == verified_before
    assert _age_receipt_edge_count(age_store, decision_id, receipt_intent_id, domain) == 1


@pytest.mark.age
def test_age_evidence_receipt_concurrent_append(age_store):
    """AGE concurrent EvidenceReceipt appends serialize into one unbroken chain."""
    # Protocol v2 invariant: per-domain receipt lock prevents chain forks and gaps.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    decisions_before = age_store.count_decisions(domain)
    verified_before = age_store.count_verified_decisions(domain)
    receipt_count = 8
    intents = [f"AGE-RCP-{uuid.uuid4().hex[:8]}" for _ in range(receipt_count)]

    def append(index: int) -> tuple[str, int, str]:
        intent = intents[index]
        chain_index, payload_hash = age_store.append_evidence_receipt(
            receipt_intent_id=intent,
            domain=domain,
            decision_id=decision_id,
            canonical_payload={"decision_id": decision_id, "sequence": index},
            actor="scorer",
            source_route="/api/test",
            metadata={"purpose": "concurrent"},
        )
        return intent, chain_index, payload_hash

    with ThreadPoolExecutor(max_workers=receipt_count) as executor:
        results = [future.result() for future in as_completed(
            executor.submit(append, index) for index in range(receipt_count)
        )]

    receipts = _age_get_receipts_for_domain(age_store, domain)
    indexes = [receipt["chain_index"] for receipt in receipts]
    returned_indexes = [chain_index for _, chain_index, _ in results]
    hash_by_index = {receipt["chain_index"]: receipt["payload_hash"] for receipt in receipts}

    assert sorted(returned_indexes) == list(range(receipt_count))
    assert indexes == list(range(receipt_count))
    assert len(set(indexes)) == receipt_count
    assert receipts[0]["previous_hash"] == "GENESIS"
    for receipt in receipts[1:]:
        assert receipt["previous_hash"] == hash_by_index[receipt["chain_index"] - 1]
    for intent, chain_index, payload_hash in results:
        assert hash_by_index[chain_index] == payload_hash
        assert _age_receipt_edge_count(age_store, decision_id, intent, domain) == 1
    assert age_store.count_decisions(domain) == decisions_before
    assert age_store.count_verified_decisions(domain) == verified_before


@pytest.mark.age
def test_age_evidence_receipt_rollback_on_failure(age_store):
    """AGE EvidenceReceipt transaction rollback removes uncommitted receipt state."""
    # Protocol v2 invariant: failed receipt append leaves no orphan receipt or edge.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    receipt_intent_id = f"AGE-RCP-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    decisions_before = age_store.count_decisions(domain)
    verified_before = age_store.count_verified_decisions(domain)
    age_store._store._protocol_v2_fail_after_receipt_create = receipt_intent_id
    try:
        with pytest.raises(RuntimeError, match="injected EvidenceReceipt failure"):
            age_store.append_evidence_receipt(
                receipt_intent_id=receipt_intent_id,
                domain=domain,
                decision_id=decision_id,
                canonical_payload={"decision_id": decision_id, "action": "approved"},
                actor="scorer",
                source_route="/api/test",
                metadata={"purpose": "rollback"},
            )
    finally:
        delattr(age_store._store, "_protocol_v2_fail_after_receipt_create")

    assert _age_node_count(age_store, "EvidenceReceipt", "receipt_intent_id", receipt_intent_id) == 0
    assert _age_receipt_edge_count(age_store, decision_id, receipt_intent_id, domain) == 0
    assert age_store.count_decisions(domain) == decisions_before
    assert age_store.count_verified_decisions(domain) == verified_before
    decision = age_store.get_decision(decision_id)
    assert decision is not None
    assert decision["status"] == "pending"


def test_conservation_status_write(sqlite_store):
    """write_conservation_status persists an auditable conservation snapshot."""
    # Protocol v2 method/invariant: snapshots record V, q, alpha, theta_min, status.
    _write_governed_decision(sqlite_store, "GOV-1")
    sqlite_store.write_outcome("GOV-1", "approve", True)
    decisions_before = sqlite_store.count_decisions("test")
    verified_before = sqlite_store.count_verified_decisions("test")

    sqlite_store.write_conservation_status(
        status_id="CS-1",
        domain="test",
        V=verified_before,
        q=1.0,
        alpha=0.5,
        theta_min=47.06,
        verified_count=verified_before,
        correct_count=1,
        status="GREEN",
        policy_version="slice-6",
    )
    sqlite_store.write_conservation_status(
        status_id="CS-1",
        domain="test",
        V=verified_before,
        q=1.0,
        alpha=0.5,
        theta_min=47.06,
        verified_count=verified_before,
        correct_count=1,
        status="GREEN",
        policy_version="slice-6",
    )

    rows = sqlite_store.connection.execute(
        """
        SELECT *
        FROM conservation_snapshots
        WHERE snapshot_id = ?
        """,
        ("CS-1",),
    ).fetchall()
    decision = sqlite_store.get_decision("GOV-1")

    assert len(rows) == 1
    assert rows[0]["domain"] == "test"
    assert rows[0]["V"] == verified_before
    assert rows[0]["q"] == 1.0
    assert rows[0]["alpha"] == 0.5
    assert rows[0]["theta_min"] == 47.06
    assert rows[0]["verified_count"] == verified_before
    assert rows[0]["correct_count"] == 1
    assert rows[0]["status"] == "GREEN"
    assert rows[0]["policy_version"] == "slice-6"
    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before
    assert decision is not None
    assert decision["status"] == "confirmed"

    with pytest.raises(ValueError, match="conflicting conservation status_id"):
        sqlite_store.write_conservation_status(
            status_id="CS-1",
            domain="test",
            V=verified_before + 1,
            q=1.0,
            alpha=0.5,
            theta_min=47.06,
            verified_count=verified_before + 1,
            correct_count=1,
            status="GREEN",
            policy_version="slice-6",
        )

    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before


@pytest.mark.age
def test_age_conservation_status_write(age_store):
    """AGE write_conservation_status persists an auditable snapshot without changing V."""
    # Protocol v2 AGE Slice 4 invariant: ConservationStatus is audit output, not V input.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    status_id = f"AGE-CS-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    age_store.write_outcome(decision_id, "approve", True)
    decisions_before = age_store.count_decisions(domain)
    verified_before = age_store.count_verified_decisions(domain)

    age_store.write_conservation_status(
        status_id=status_id,
        domain=domain,
        V=verified_before,
        q=1.0,
        alpha=0.5,
        theta_min=47.06,
        verified_count=verified_before,
        correct_count=1,
        status="GREEN",
        policy_version="age-slice-4",
    )
    snapshot = _age_get_conservation_status(age_store, status_id)

    assert snapshot is not None
    assert snapshot["status_id"] == status_id
    assert snapshot["snapshot_id"] == status_id
    assert snapshot["domain"] == domain
    assert snapshot["V"] == verified_before
    assert snapshot["q"] == 1.0
    assert snapshot["alpha"] == 0.5
    assert snapshot["theta_min"] == 47.06
    assert snapshot["verified_count"] == verified_before
    assert snapshot["correct_count"] == 1
    assert snapshot["status"] == "GREEN"
    assert snapshot["policy_version"] == "age-slice-4"
    assert snapshot["counts_scope"] == "verified_only"
    assert isinstance(snapshot["computed_at"], float)
    assert _age_conservation_status_count(age_store, status_id) == 1
    assert age_store.count_decisions(domain) == decisions_before
    assert age_store.count_verified_decisions(domain) == verified_before


@pytest.mark.age
def test_age_conservation_status_duplicate_identical_skips(age_store):
    """AGE identical ConservationStatus replay does not create a duplicate node."""
    # Protocol v2 AGE Slice 4 invariant: same status_id and same payload are idempotent.
    domain = age_store.protocol_v2_test_domain
    status_id = f"AGE-CS-{uuid.uuid4().hex[:8]}"
    payload = {
        "status_id": status_id,
        "domain": domain,
        "V": 0,
        "q": 0.0,
        "alpha": 0.0,
        "theta_min": 47.06,
        "verified_count": 0,
        "correct_count": 0,
        "status": "RED",
        "policy_version": "age-slice-4",
    }

    age_store.write_conservation_status(**payload)
    first = _age_get_conservation_status(age_store, status_id)
    age_store.write_conservation_status(**payload)
    second = _age_get_conservation_status(age_store, status_id)

    assert _age_conservation_status_count(age_store, status_id) == 1
    assert first is not None
    assert second is not None
    assert second["computed_at"] == first["computed_at"]
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_conservation_status_conflict_raises(age_store):
    """AGE conflicting ConservationStatus replay raises without mutating the snapshot."""
    # Protocol v2 AGE Slice 4 invariant: same status_id with different payload conflicts.
    domain = age_store.protocol_v2_test_domain
    status_id = f"AGE-CS-{uuid.uuid4().hex[:8]}"
    age_store.write_conservation_status(
        status_id=status_id,
        domain=domain,
        V=1,
        q=1.0,
        alpha=0.5,
        theta_min=47.06,
        verified_count=1,
        correct_count=1,
        status="GREEN",
        policy_version="age-slice-4",
    )
    original = _age_get_conservation_status(age_store, status_id)

    with pytest.raises(ValueError, match="conflicting conservation status_id"):
        age_store.write_conservation_status(
            status_id=status_id,
            domain=domain,
            V=2,
            q=1.0,
            alpha=0.5,
            theta_min=47.06,
            verified_count=2,
            correct_count=1,
            status="GREEN",
            policy_version="age-slice-4",
        )

    assert _age_conservation_status_count(age_store, status_id) == 1
    assert _age_get_conservation_status(age_store, status_id) == original
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0


def test_fingerprint_write_read(sqlite_store):
    """write_fingerprint persists and retrieves canonical fingerprint data."""
    # Protocol v2 method/invariant: fingerprint snapshots are queryable by domain.
    decisions_before = sqlite_store.count_decisions("test")
    verified_before = sqlite_store.count_verified_decisions("test")
    memory = InMemoryGraphStore(domain="test")

    for store in (sqlite_store, memory):
        store.write_fingerprint(
            fingerprint_id="FPR-1",
            domain="test",
            factor_names=["factor_a", "factor_b"],
            factor_stats={
                "factor_a": {"mean": 0.2, "sigma": 0.01, "weight": 1.0},
                "factor_b": {"mean": 0.8, "sigma": 0.05, "weight": 0.75},
            },
            skipped_incompatible=2,
            window=50,
            metadata={"policy": "slice-7"},
        )
        store.write_fingerprint(
            fingerprint_id="FPR-1",
            domain="test",
            factor_names=["factor_a", "factor_b"],
            factor_stats={
                "factor_a": {"mean": 0.2, "sigma": 0.01, "weight": 1.0},
                "factor_b": {"mean": 0.8, "sigma": 0.05, "weight": 0.75},
            },
            skipped_incompatible=2,
            window=50,
            metadata={"policy": "slice-7"},
        )

    row = sqlite_store.connection.execute(
        "SELECT * FROM fingerprints WHERE fingerprint_id = ?",
        ("FPR-1",),
    ).fetchone()
    assert row is not None
    assert row["domain"] == "test"
    assert row["factor_names_json"] == '["factor_a", "factor_b"]'
    assert '"factor_a"' in row["factor_stats_json"]
    assert row["skipped_incompatible"] == 2
    assert row["window"] == 50
    assert row["metadata_json"] == '{"policy": "slice-7"}'
    assert len(memory._fingerprints) == 1
    assert memory._fingerprints["FPR-1"]["domain"] == "test"
    assert memory._fingerprints["FPR-1"]["window"] == 50
    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before

    with pytest.raises(ValueError, match="conflicting fingerprint_id"):
        sqlite_store.write_fingerprint(
            fingerprint_id="FPR-1",
            domain="test",
            factor_names=["factor_a"],
            factor_stats={"factor_a": {"mean": 0.1}},
            skipped_incompatible=0,
            window=10,
            metadata={"policy": "conflict"},
        )

    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before


@pytest.mark.age
def test_age_fingerprint_write_read(age_store):
    """AGE write_fingerprint persists a standalone Fingerprint snapshot."""
    # Protocol v2 AGE Slice 5 invariant: Fingerprint snapshots do not affect V.
    domain = age_store.protocol_v2_test_domain
    fingerprint_id = f"AGE-FPR-{uuid.uuid4().hex[:8]}"
    decisions_before = age_store.count_decisions(domain)
    verified_before = age_store.count_verified_decisions(domain)

    age_store.write_fingerprint(
        fingerprint_id=fingerprint_id,
        domain=domain,
        factor_names=["factor_a", "factor_b"],
        factor_stats={
            "factor_a": {"mean": 0.2, "sigma": 0.01, "weight": 1.0},
            "factor_b": {"mean": 0.8, "sigma": 0.05, "weight": 0.75},
        },
        skipped_incompatible=2,
        window=50,
        metadata={"policy": "age-slice-5"},
    )
    fingerprint = _age_get_node(age_store, "Fingerprint", "fingerprint_id", fingerprint_id)

    assert fingerprint is not None
    assert fingerprint["fingerprint_id"] == fingerprint_id
    assert fingerprint["domain"] == domain
    assert fingerprint["factor_names"] == ["factor_a", "factor_b"]
    assert _json_value(fingerprint["factor_stats"])["factor_a"]["mean"] == 0.2
    assert fingerprint["skipped_incompatible"] == 2
    assert fingerprint["window"] == 50
    assert fingerprint["metadata"] == {"policy": "age-slice-5"}
    assert fingerprint["schema_version"] == "protocol_v2"
    assert isinstance(fingerprint["created_at"], float)
    assert _age_node_count(age_store, "Fingerprint", "fingerprint_id", fingerprint_id) == 1
    assert age_store.count_decisions(domain) == decisions_before
    assert age_store.count_verified_decisions(domain) == verified_before


@pytest.mark.age
def test_age_fingerprint_duplicate_identical_skips(age_store):
    """AGE identical Fingerprint replay preserves the original node."""
    # Protocol v2 AGE Slice 5 invariant: same fingerprint_id and payload are idempotent.
    domain = age_store.protocol_v2_test_domain
    fingerprint_id = f"AGE-FPR-{uuid.uuid4().hex[:8]}"
    payload = {
        "fingerprint_id": fingerprint_id,
        "domain": domain,
        "factor_names": ["factor_a"],
        "factor_stats": {"factor_a": {"mean": 0.2}},
        "skipped_incompatible": 0,
        "window": 10,
        "metadata": {"policy": "age-slice-5"},
    }

    age_store.write_fingerprint(**payload)
    first = _age_get_node(age_store, "Fingerprint", "fingerprint_id", fingerprint_id)
    age_store.write_fingerprint(**payload)
    second = _age_get_node(age_store, "Fingerprint", "fingerprint_id", fingerprint_id)

    assert _age_node_count(age_store, "Fingerprint", "fingerprint_id", fingerprint_id) == 1
    assert first is not None
    assert second == first
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_fingerprint_conflict_raises(age_store):
    """AGE conflicting Fingerprint replay raises without mutating the original node."""
    # Protocol v2 AGE Slice 5 invariant: same fingerprint_id with different payload conflicts.
    domain = age_store.protocol_v2_test_domain
    fingerprint_id = f"AGE-FPR-{uuid.uuid4().hex[:8]}"
    age_store.write_fingerprint(
        fingerprint_id=fingerprint_id,
        domain=domain,
        factor_names=["factor_a"],
        factor_stats={"factor_a": {"mean": 0.2}},
        skipped_incompatible=0,
        window=10,
        metadata={"policy": "age-slice-5"},
    )
    original = _age_get_node(age_store, "Fingerprint", "fingerprint_id", fingerprint_id)

    with pytest.raises(ValueError, match="conflicting fingerprint_id"):
        age_store.write_fingerprint(
            fingerprint_id=fingerprint_id,
            domain=domain,
            factor_names=["factor_a"],
            factor_stats={"factor_a": {"mean": 0.3}},
            skipped_incompatible=0,
            window=10,
            metadata={"policy": "age-slice-5"},
        )

    assert _age_node_count(age_store, "Fingerprint", "fingerprint_id", fingerprint_id) == 1
    assert _age_get_node(age_store, "Fingerprint", "fingerprint_id", fingerprint_id) == original
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0


def test_centroid_checkpoint(sqlite_store):
    """write_centroid_checkpoint persists judgment geometry checkpoints."""
    # Protocol v2 method/invariant: centroid checkpoints are auditable.
    decisions_before = sqlite_store.count_decisions("test")
    verified_before = sqlite_store.count_verified_decisions("test")
    memory = InMemoryGraphStore(domain="test")
    centroids = {"approve": [0.1, 0.9], "review": [0.7, 0.3]}

    for store in (sqlite_store, memory):
        store.write_centroid_checkpoint(
            checkpoint_id="CKP-1",
            domain="test",
            category="category_a",
            action="approve",
            centroids=centroids,
            decisions_count=12,
            verified_count=7,
            iks=0.88,
            shape=[2, 2],
            factor_names_hash="factor-hash",
            metadata={"policy": "slice-7"},
        )
        store.write_centroid_checkpoint(
            checkpoint_id="CKP-1",
            domain="test",
            category="category_a",
            action="approve",
            centroids=centroids,
            decisions_count=12,
            verified_count=7,
            iks=0.88,
            shape=[2, 2],
            factor_names_hash="factor-hash",
            metadata={"policy": "slice-7"},
        )

    row = sqlite_store.connection.execute(
        """
        SELECT *
        FROM centroid_checkpoints
        WHERE checkpoint_id = ?
        """,
        ("CKP-1",),
    ).fetchone()
    assert row is not None
    assert row["domain"] == "test"
    assert row["category"] == "category_a"
    assert row["action"] == "approve"
    assert '"approve": [0.1, 0.9]' in row["centroids_json"]
    assert row["decisions_count"] == 12
    assert row["verified_count"] == 7
    assert row["iks"] == 0.88
    assert row["shape_json"] == "[2, 2]"
    assert row["factor_names_hash"] == "factor-hash"
    assert row["metadata_json"] == '{"policy": "slice-7"}'
    assert len(memory._protocol_centroid_checkpoints) == 1
    assert memory._protocol_centroid_checkpoints["CKP-1"]["domain"] == "test"
    assert memory._protocol_centroid_checkpoints["CKP-1"]["verified_count"] == 7
    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before

    with pytest.raises(ValueError, match="conflicting checkpoint_id"):
        sqlite_store.write_centroid_checkpoint(
            checkpoint_id="CKP-1",
            domain="test",
            category="category_a",
            action="review",
            centroids=centroids,
            decisions_count=12,
            verified_count=7,
            iks=0.88,
            shape=[2, 2],
            factor_names_hash="factor-hash",
            metadata={"policy": "slice-7"},
        )

    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before


@pytest.mark.age
def test_age_centroid_checkpoint(age_store):
    """AGE write_centroid_checkpoint persists a Protocol v2 checkpoint."""
    # Protocol v2 AGE Slice 5 invariant: checkpoints are standalone judgment snapshots.
    domain = age_store.protocol_v2_test_domain
    checkpoint_id = f"AGE-CKP-{uuid.uuid4().hex[:8]}"
    centroids = {"approve": [0.1, 0.9], "review": [0.7, 0.3]}
    decisions_before = age_store.count_decisions(domain)
    verified_before = age_store.count_verified_decisions(domain)

    age_store.write_centroid_checkpoint(
        checkpoint_id=checkpoint_id,
        domain=domain,
        category="category_a",
        action="approve",
        centroids=centroids,
        decisions_count=12,
        verified_count=7,
        iks=0.88,
        shape=[2, 2],
        factor_names_hash="factor-hash",
        metadata={"policy": "age-slice-5"},
    )
    checkpoint = _age_get_node(age_store, "CentroidCheckpoint", "checkpoint_id", checkpoint_id)

    assert checkpoint is not None
    assert checkpoint["checkpoint_id"] == checkpoint_id
    assert checkpoint["domain"] == domain
    assert checkpoint["category"] == "category_a"
    assert checkpoint["action"] == "approve"
    assert checkpoint["centroids"] == centroids
    assert checkpoint["decisions_count"] == 12
    assert checkpoint["verified_count"] == 7
    assert checkpoint["iks"] == 0.88
    assert _json_value(checkpoint["shape"]) == [2, 2]
    assert checkpoint["factor_names_hash"] == "factor-hash"
    assert checkpoint["metadata"] == {"policy": "age-slice-5"}
    assert checkpoint["schema_version"] == "protocol_v2"
    assert isinstance(checkpoint["created_at"], float)
    assert _age_node_count(age_store, "CentroidCheckpoint", "checkpoint_id", checkpoint_id) == 1
    assert age_store.count_decisions(domain) == decisions_before
    assert age_store.count_verified_decisions(domain) == verified_before


@pytest.mark.age
def test_age_centroid_checkpoint_duplicate_identical_skips(age_store):
    """AGE identical CentroidCheckpoint replay preserves the original node."""
    # Protocol v2 AGE Slice 5 invariant: same checkpoint_id and payload are idempotent.
    domain = age_store.protocol_v2_test_domain
    checkpoint_id = f"AGE-CKP-{uuid.uuid4().hex[:8]}"
    payload = {
        "checkpoint_id": checkpoint_id,
        "domain": domain,
        "category": "category_a",
        "action": "approve",
        "centroids": {"approve": [0.1, 0.9]},
        "decisions_count": 1,
        "verified_count": 1,
        "iks": 0.9,
        "shape": [1, 2],
        "factor_names_hash": "factor-hash",
        "metadata": {"policy": "age-slice-5"},
    }

    age_store.write_centroid_checkpoint(**payload)
    first = _age_get_node(age_store, "CentroidCheckpoint", "checkpoint_id", checkpoint_id)
    age_store.write_centroid_checkpoint(**payload)
    second = _age_get_node(age_store, "CentroidCheckpoint", "checkpoint_id", checkpoint_id)

    assert _age_node_count(age_store, "CentroidCheckpoint", "checkpoint_id", checkpoint_id) == 1
    assert first is not None
    assert second == first
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_centroid_checkpoint_conflict_raises(age_store):
    """AGE conflicting CentroidCheckpoint replay raises without mutating the original node."""
    # Protocol v2 AGE Slice 5 invariant: same checkpoint_id with different payload conflicts.
    domain = age_store.protocol_v2_test_domain
    checkpoint_id = f"AGE-CKP-{uuid.uuid4().hex[:8]}"
    age_store.write_centroid_checkpoint(
        checkpoint_id=checkpoint_id,
        domain=domain,
        category="category_a",
        action="approve",
        centroids={"approve": [0.1, 0.9]},
        decisions_count=1,
        verified_count=1,
        iks=0.9,
        shape=[1, 2],
        factor_names_hash="factor-hash",
        metadata={"policy": "age-slice-5"},
    )
    original = _age_get_node(age_store, "CentroidCheckpoint", "checkpoint_id", checkpoint_id)

    with pytest.raises(ValueError, match="conflicting checkpoint_id"):
        age_store.write_centroid_checkpoint(
            checkpoint_id=checkpoint_id,
            domain=domain,
            category="category_a",
            action="review",
            centroids={"approve": [0.1, 0.9]},
            decisions_count=1,
            verified_count=1,
            iks=0.9,
            shape=[1, 2],
            factor_names_hash="factor-hash",
            metadata={"policy": "age-slice-5"},
        )

    assert _age_node_count(age_store, "CentroidCheckpoint", "checkpoint_id", checkpoint_id) == 1
    assert _age_get_node(age_store, "CentroidCheckpoint", "checkpoint_id", checkpoint_id) == original
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0


def test_protocol_v2_checkpoint_does_not_break_legacy_centroid_load(sqlite_store):
    """Legacy centroid reads ignore Protocol v2 checkpoint rows."""
    # Protocol v2 checkpoint rows are distinct from legacy save_centroids rows.
    sqlite_store.write_centroid_checkpoint(
        checkpoint_id="CKP-1",
        domain="test",
        category="category_a",
        action="approve",
        centroids={"approve": [0.1, 0.9]},
        decisions_count=12,
        verified_count=7,
        iks=0.88,
        shape=[1, 2],
        factor_names_hash="factor-hash",
        metadata={"policy": "slice-8"},
    )

    assert sqlite_store.load_latest_centroids("test") is None

    legacy_centroids = np.asarray([[0.3, 0.7], [0.6, 0.4]], dtype=float)
    sqlite_store.save_centroids(
        "test",
        "category_a",
        legacy_centroids,
        metadata={"iks": 0.42},
    )
    loaded = sqlite_store.load_latest_centroids("test")
    checkpoints = sqlite_store.get_centroid_checkpoints("test", limit=None)

    assert loaded is not None
    np.testing.assert_allclose(loaded, legacy_centroids)
    assert len(checkpoints) == 1
    assert checkpoints[0]["category"] == "category_a"


def test_evolution_event(sqlite_store):
    """write_evolution_event records procedural-memory lineage."""
    # Protocol v2 method/invariant: EvolutionEvent writes preserve AgentEvolver trace.
    decisions_before = sqlite_store.count_decisions("test")
    verified_before = sqlite_store.count_verified_decisions("test")
    memory = InMemoryGraphStore(domain="test")

    for store in (sqlite_store, memory):
        store.write_evolution_event(
            event_id="EVO-1",
            domain="test",
            event_type="promoted",
            rule_name="amount_rule",
            variant_id="variant-a",
            source_copilot="s2p",
            source_rule="legacy_rule",
            metric=0.91,
            shadow_batch_size=20,
            min_shadow_batches=3,
            metadata={"policy": "slice-8"},
        )
        store.write_evolution_event(
            event_id="EVO-1",
            domain="test",
            event_type="promoted",
            rule_name="amount_rule",
            variant_id="variant-a",
            source_copilot="s2p",
            source_rule="legacy_rule",
            metric=0.91,
            shadow_batch_size=20,
            min_shadow_batches=3,
            metadata={"policy": "slice-8"},
        )

    row = sqlite_store.connection.execute(
        "SELECT * FROM evolution_events WHERE event_id = ?",
        ("EVO-1",),
    ).fetchone()
    assert row is not None
    assert row["domain"] == "test"
    assert row["event_type"] == "promoted"
    assert row["rule_name"] == "amount_rule"
    assert row["variant_id"] == "variant-a"
    assert row["source_copilot"] == "s2p"
    assert row["source_rule"] == "legacy_rule"
    assert row["metric"] == 0.91
    assert row["shadow_batch_size"] == 20
    assert row["min_shadow_batches"] == 3
    assert row["metadata_json"] == '{"policy": "slice-8"}'
    assert len(memory._protocol_evolution_events) == 1
    assert memory._protocol_evolution_events["EVO-1"]["event_type"] == "promoted"
    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before

    with pytest.raises(ValueError, match="conflicting evolution event_id"):
        sqlite_store.write_evolution_event(
            event_id="EVO-1",
            domain="test",
            event_type="rejected",
            rule_name="amount_rule",
            variant_id="variant-a",
            metadata={"policy": "slice-8"},
        )

    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before


def test_entity_link(sqlite_store):
    """link_entity connects a Decision to DomainContext without duplication."""
    # Protocol v2 method/invariant: entity links are domain-scoped and idempotent.
    _write_governed_decision(sqlite_store, "GOV-1")
    memory = InMemoryGraphStore(domain="test")
    _write_governed_decision(memory, "GOV-1")
    decisions_before = sqlite_store.count_decisions("test")
    verified_before = sqlite_store.count_verified_decisions("test")

    for store in (sqlite_store, memory):
        store.link_entity(
            decision_id="GOV-1",
            entity_id="invoice-1",
            entity_type="invoice",
            domain="test",
        )
        store.link_entity(
            decision_id="GOV-1",
            entity_id="invoice-1",
            entity_type="invoice",
            domain="test",
        )

    rows = sqlite_store.connection.execute(
        """
        SELECT decision_id, entity_id, entity_type, domain
        FROM decision_entity_edges
        WHERE decision_id = ?
        """,
        ("GOV-1",),
    ).fetchall()

    assert len(rows) == 1
    assert rows[0]["decision_id"] == "GOV-1"
    assert rows[0]["entity_id"] == "invoice-1"
    assert rows[0]["entity_type"] == "invoice"
    assert rows[0]["domain"] == "test"
    assert len(memory.get_decision_links("GOV-1")) == 1
    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before

    with pytest.raises(KeyError):
        sqlite_store.link_entity(
            decision_id="missing",
            entity_id="invoice-2",
            entity_type="invoice",
            domain="test",
        )

    assert sqlite_store.get_decision("missing") is None
    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before


@pytest.mark.age
def test_age_evolution_event(age_store):
    """AGE write_evolution_event persists standalone procedural memory."""
    # Protocol v2 AGE Slice 6 invariant: EvolutionEvent writes do not affect V.
    domain = age_store.protocol_v2_test_domain
    event_id = f"AGE-EVO-{uuid.uuid4().hex[:8]}"
    decisions_before = age_store.count_decisions(domain)
    verified_before = age_store.count_verified_decisions(domain)

    age_store.write_evolution_event(
        event_id=event_id,
        domain=domain,
        event_type="promoted",
        rule_name="amount_rule",
        variant_id="variant-a",
        source_copilot="s2p",
        source_rule="legacy_rule",
        metric=0.91,
        shadow_batch_size=20,
        min_shadow_batches=3,
        metadata={"policy": "age-slice-6"},
    )
    event = _age_get_node(age_store, "EvolutionEvent", "event_id", event_id)

    assert event is not None
    assert event["event_id"] == event_id
    assert event["domain"] == domain
    assert event["event_type"] == "promoted"
    assert event["rule_name"] == "amount_rule"
    assert event["variant_id"] == "variant-a"
    assert event["source_copilot"] == "s2p"
    assert event["source_rule"] == "legacy_rule"
    assert event["metric"] == 0.91
    assert event["shadow_batch_size"] == 20
    assert event["min_shadow_batches"] == 3
    assert event["metadata"] == {"policy": "age-slice-6"}
    assert event["schema_version"] == "protocol_v2"
    assert isinstance(event["created_at"], float)
    assert _age_node_count(age_store, "EvolutionEvent", "event_id", event_id) == 1
    assert age_store.count_decisions(domain) == decisions_before
    assert age_store.count_verified_decisions(domain) == verified_before


@pytest.mark.age
def test_age_evolution_event_duplicate_identical_skips(age_store):
    """AGE identical EvolutionEvent replay does not create a duplicate node."""
    # Protocol v2 AGE Slice 6 invariant: same event_id and same payload are idempotent.
    domain = age_store.protocol_v2_test_domain
    event_id = f"AGE-EVO-{uuid.uuid4().hex[:8]}"
    payload = {
        "event_id": event_id,
        "domain": domain,
        "event_type": "promoted",
        "rule_name": "amount_rule",
        "variant_id": "variant-a",
        "source_copilot": "s2p",
        "source_rule": "legacy_rule",
        "metric": 0.91,
        "shadow_batch_size": 20,
        "min_shadow_batches": 3,
        "metadata": {"policy": "age-slice-6"},
    }

    age_store.write_evolution_event(**payload)
    first = _age_get_node(age_store, "EvolutionEvent", "event_id", event_id)
    age_store.write_evolution_event(**payload)
    second = _age_get_node(age_store, "EvolutionEvent", "event_id", event_id)

    assert _age_node_count(age_store, "EvolutionEvent", "event_id", event_id) == 1
    assert first is not None
    assert second is not None
    assert second["created_at"] == first["created_at"]
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_evolution_event_conflict_raises(age_store):
    """AGE conflicting EvolutionEvent replay raises without mutating the event."""
    # Protocol v2 AGE Slice 6 invariant: same event_id with different payload conflicts.
    domain = age_store.protocol_v2_test_domain
    event_id = f"AGE-EVO-{uuid.uuid4().hex[:8]}"
    age_store.write_evolution_event(
        event_id=event_id,
        domain=domain,
        event_type="promoted",
        rule_name="amount_rule",
        variant_id="variant-a",
        source_copilot="s2p",
        source_rule="legacy_rule",
        metric=0.91,
        shadow_batch_size=20,
        min_shadow_batches=3,
        metadata={"policy": "age-slice-6"},
    )
    original = _age_get_node(age_store, "EvolutionEvent", "event_id", event_id)

    with pytest.raises(ValueError, match="conflicting evolution event_id"):
        age_store.write_evolution_event(
            event_id=event_id,
            domain=domain,
            event_type="rejected",
            rule_name="amount_rule",
            variant_id="variant-a",
            metadata={"policy": "age-slice-6"},
        )

    assert _age_node_count(age_store, "EvolutionEvent", "event_id", event_id) == 1
    assert _age_get_node(age_store, "EvolutionEvent", "event_id", event_id) == original
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_entity_link(age_store):
    """AGE link_entity creates an ABOUT edge to DomainContext without changing V."""
    # Protocol v2 AGE Slice 6 invariant: entity links never create Decisions implicitly.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    entity_id = f"invoice-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)
    decisions_before = age_store.count_decisions(domain)
    verified_before = age_store.count_verified_decisions(domain)

    age_store.link_entity(
        decision_id=decision_id,
        entity_id=entity_id,
        entity_type="invoice",
        domain=domain,
    )
    context = _age_get_node(age_store, "DomainContext", "entity_id", entity_id)
    decision = age_store.get_decision(decision_id)

    assert context is not None
    assert context["entity_id"] == entity_id
    assert context["natural_key"] == entity_id
    assert context["entity_type"] == "invoice"
    assert context["domain"] == domain
    assert context["schema_version"] == "protocol_v2"
    assert isinstance(context["created_at"], float)
    assert _age_about_edge_count(age_store, decision_id, entity_id, domain) == 1
    assert decision is not None
    assert decision["status"] == "pending"
    assert age_store.count_decisions(domain) == decisions_before
    assert age_store.count_verified_decisions(domain) == verified_before


@pytest.mark.age
def test_age_entity_link_duplicate_skips(age_store):
    """AGE duplicate entity links are harmless for the same decision/entity/domain."""
    # Protocol v2 AGE Slice 6 invariant: link identity is decision_id/entity_id/domain.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-GOV-{uuid.uuid4().hex[:8]}"
    entity_id = f"invoice-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)

    age_store.link_entity(decision_id, entity_id, "invoice", domain)
    age_store.link_entity(decision_id, entity_id, "invoice", domain)
    age_store.link_entity(decision_id, entity_id, "vendor", domain)

    context = _age_get_node(age_store, "DomainContext", "entity_id", entity_id)
    assert _age_about_edge_count(age_store, decision_id, entity_id, domain) == 1
    assert context is not None
    assert context["entity_type"] == "invoice"
    assert age_store.count_decisions(domain) == 1
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_entity_link_missing_decision_raises(age_store):
    """AGE link_entity for a missing Decision raises and creates no Decision."""
    # Protocol v2 AGE Slice 6 invariant: entity links require an existing Decision.
    domain = age_store.protocol_v2_test_domain
    missing_decision_id = f"AGE-MISSING-{uuid.uuid4().hex[:8]}"
    entity_id = f"invoice-{uuid.uuid4().hex[:8]}"

    with pytest.raises(KeyError):
        age_store.link_entity(missing_decision_id, entity_id, "invoice", domain)

    assert age_store.get_decision(missing_decision_id) is None
    assert _age_node_count(age_store, "DomainContext", "entity_id", entity_id) == 0
    assert _age_about_edge_count(age_store, missing_decision_id, entity_id, domain) == 0
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0


@pytest.mark.age
def test_age_archive_pending(age_store):
    """AGE archive_decisions soft-archives pending Decisions without changing V."""
    # Protocol v2 AGE Slice 8 invariant: archived pending Decisions leave active V unchanged.
    domain = age_store.protocol_v2_test_domain
    other_domain = f"{domain}_other"
    pending_old = f"AGE-P-OLD-{uuid.uuid4().hex[:8]}"
    pending_new = f"AGE-P-NEW-{uuid.uuid4().hex[:8]}"
    confirmed_old = f"AGE-C-OLD-{uuid.uuid4().hex[:8]}"
    other_pending = f"AGE-OTHER-P-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, pending_old, domain=domain, created_at=10.0)
    _write_governed_decision(age_store, pending_new, domain=domain, created_at=60.0)
    _write_governed_decision(age_store, confirmed_old, domain=domain, created_at=20.0)
    _write_governed_decision(age_store, other_pending, domain=other_domain, created_at=10.0)
    age_store.write_outcome(confirmed_old, "approve", True)
    verified_before = age_store.count_verified_decisions(domain)

    archived = age_store.archive_decisions(domain, before=50.0, status_filter="pending")

    pending_old_decision = age_store.get_decision(pending_old)
    assert archived == 1
    assert pending_old_decision is not None
    assert pending_old_decision["archived"] is True
    assert pending_old_decision["archive_status"] == "archived"
    assert pending_old_decision["archived_from_status"] == "pending"
    assert age_store.get_decision(pending_new).get("archived") is None
    assert age_store.get_decision(confirmed_old).get("archived") is None
    assert age_store.get_decision(other_pending).get("archived") is None
    assert age_store.count_decisions(domain) == 2
    assert age_store.count_verified_decisions(domain) == verified_before == 1
    assert age_store.count_decisions(other_domain) == 1
    assert age_store.count_archived(domain) == 1


@pytest.mark.age
def test_age_archive_verified_requires_confirmation(age_store):
    """AGE verified archive requires explicit confirmation."""
    # Protocol v2 AGE Slice 8 invariant: verified archive cannot silently reduce active V.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-C-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain, created_at=10.0)
    age_store.write_outcome(decision_id, "approve", True)

    with pytest.raises(ValueError, match="Archiving verified decisions reduces active V"):
        age_store.archive_decisions(domain, before=50.0, status_filter="confirmed")

    decision = age_store.get_decision(decision_id)
    assert decision is not None
    assert decision.get("archived") is None
    assert age_store.count_verified_decisions(domain) == 1
    assert age_store.count_archived(domain) == 0


@pytest.mark.age
def test_age_archive_verified_decreases_active_V(age_store):
    """AGE confirmed archive removes the Decision from active V while preserving graph state."""
    # Protocol v2 AGE Slice 8 invariant: archived verified Decisions are replayable but inactive.
    domain = age_store.protocol_v2_test_domain
    decision_id = f"AGE-C-{uuid.uuid4().hex[:8]}"
    receipt_id = f"AGE-RCP-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain, created_at=10.0)
    age_store.write_outcome(decision_id, "approve", True)
    age_store.append_evidence_receipt(
        receipt_intent_id=receipt_id,
        domain=domain,
        decision_id=decision_id,
        canonical_payload={"decision_id": decision_id, "action": "approve"},
        actor="scorer",
        source_route="/api/test",
        metadata={"purpose": "archive"},
    )

    archived = age_store.archive_decisions(
        domain,
        before=50.0,
        status_filter="confirmed",
        confirm_verified=True,
    )
    decision = age_store.get_decision(decision_id)

    assert archived == 1
    assert decision is not None
    assert decision["archived"] is True
    assert decision["archived_from_status"] == "confirmed"
    assert age_store.count_verified_decisions(domain) == 0
    assert age_store.count_decisions(domain) == 0
    assert _age_has_outcome_edge_count(age_store, decision_id) == 1
    assert _age_receipt_edge_count(age_store, decision_id, receipt_id, domain) == 1


@pytest.mark.age
def test_age_archive_cutoff_respected(age_store):
    """AGE archive_decisions respects created_at cutoff and ignores missing created_at."""
    # Protocol v2 AGE Slice 8 invariant: only numeric created_at before cutoff is archivable.
    domain = age_store.protocol_v2_test_domain
    before_cutoff = f"AGE-P-BEFORE-{uuid.uuid4().hex[:8]}"
    at_cutoff = f"AGE-P-AT-{uuid.uuid4().hex[:8]}"
    after_cutoff = f"AGE-P-AFTER-{uuid.uuid4().hex[:8]}"
    missing_created_at = f"AGE-P-MISSING-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, before_cutoff, domain=domain, created_at=49.0)
    _write_governed_decision(age_store, at_cutoff, domain=domain, created_at=50.0)
    _write_governed_decision(age_store, after_cutoff, domain=domain, created_at=51.0)
    age_store._store._run_query(
        f"""
        CREATE (d:Decision {{
            decision_id: {age_store._store._S(missing_created_at)},
            domain: {age_store._store._S(domain)},
            status: 'pending',
            category: 'category_a',
            recommended_action: 'approve'
        }})
        RETURN d
        """
    )

    archived = age_store.archive_decisions(domain, before=50.0, status_filter="pending")

    assert archived == 1
    assert age_store.get_decision(before_cutoff)["archived"] is True
    assert age_store.get_decision(at_cutoff).get("archived") is None
    assert age_store.get_decision(after_cutoff).get("archived") is None
    assert age_store.get_decision(missing_created_at).get("archived") is None
    assert age_store.count_decisions(domain) == 3
    assert age_store.count_archived(domain) == 1


@pytest.mark.age
def test_age_archive_other_domain_isolation(age_store):
    """AGE archive_decisions only touches the explicitly supplied domain."""
    # Protocol v2 AGE Slice 8 invariant: archive is domain-scoped.
    domain = age_store.protocol_v2_test_domain
    other_domain = f"{domain}_other"
    target_id = f"AGE-P-TARGET-{uuid.uuid4().hex[:8]}"
    other_id = f"AGE-P-OTHER-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, target_id, domain=domain, created_at=10.0)
    _write_governed_decision(age_store, other_id, domain=other_domain, created_at=10.0)

    archived = age_store.archive_decisions(domain, before=50.0, status_filter="pending")

    assert archived == 1
    assert age_store.get_decision(target_id)["archived"] is True
    assert age_store.get_decision(other_id).get("archived") is None
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_decisions(other_domain) == 1


def _populate_age_reset_domain(age_store, domain: str, prefix: str) -> dict[str, str]:
    decision_id = f"{prefix}-D-{uuid.uuid4().hex[:8]}"
    receipt_id = f"{prefix}-RCP-{uuid.uuid4().hex[:8]}"
    observation_id = f"{prefix}-OBS-{uuid.uuid4().hex[:8]}"
    status_id = f"{prefix}-CSV-{uuid.uuid4().hex[:8]}"
    fingerprint_id = f"{prefix}-FPR-{uuid.uuid4().hex[:8]}"
    checkpoint_id = f"{prefix}-CKP-{uuid.uuid4().hex[:8]}"
    event_id = f"{prefix}-EVO-{uuid.uuid4().hex[:8]}"
    entity_id = f"{prefix}-entity-{uuid.uuid4().hex[:8]}"

    _write_governed_decision(age_store, decision_id, domain=domain, created_at=10.0)
    age_store.write_outcome(decision_id, "approve", True)
    age_store.write_observation(
        observation_id=observation_id,
        domain=domain,
        category="category_a",
        recommended_action="approve",
        confidence=0.8,
        source_route="preview",
        scorer_version="slice-8",
        factor_schema_version="slice-8",
        entity_id=entity_id,
        factor_vector=[0.1, 0.9],
        factor_names=["factor_a", "factor_b"],
        metadata={"purpose": "reset-test"},
    )
    age_store.append_evidence_receipt(
        receipt_intent_id=receipt_id,
        domain=domain,
        decision_id=decision_id,
        canonical_payload={"decision_id": decision_id, "action": "approve"},
        actor="test",
        source_route="/api/test",
        metadata={"purpose": "reset-test"},
    )
    age_store.write_conservation_status(
        status_id=status_id,
        domain=domain,
        V=1,
        q=1.0,
        alpha=1.0,
        theta_min=23.53,
        verified_count=1,
        correct_count=1,
        status="GREEN",
        policy_version="slice-8",
    )
    age_store.write_fingerprint(
        fingerprint_id=fingerprint_id,
        domain=domain,
        factor_names=["factor_a"],
        factor_stats={"factor_a": {"mean": 0.5}},
        skipped_incompatible=0,
        window=10,
        metadata={"purpose": "reset-test"},
    )
    age_store.write_centroid_checkpoint(
        checkpoint_id=checkpoint_id,
        domain=domain,
        category="category_a",
        action="approve",
        centroids={"approve": [0.1, 0.9]},
        decisions_count=1,
        verified_count=1,
        iks=0.9,
        shape=[1, 2],
        factor_names_hash="factor-hash",
        metadata={"purpose": "reset-test"},
    )
    age_store.write_evolution_event(
        event_id=event_id,
        domain=domain,
        event_type="promoted",
        rule_name="amount_rule",
        variant_id="variant-a",
        metadata={"purpose": "reset-test"},
    )
    age_store.link_entity(decision_id, entity_id, "invoice", domain)
    return {
        "decision_id": decision_id,
        "receipt_id": receipt_id,
        "observation_id": observation_id,
        "status_id": status_id,
        "fingerprint_id": fingerprint_id,
        "checkpoint_id": checkpoint_id,
        "event_id": event_id,
        "entity_id": entity_id,
    }


def _age_reset_domain_snapshot(age_store, domain: str, ids: dict[str, str]) -> dict[str, object]:
    labels = (
        "Decision",
        "Outcome",
        "Observation",
        "EvidenceReceipt",
        "ConservationStatus",
        "Fingerprint",
        "CentroidCheckpoint",
        "EvolutionEvent",
        "DomainContext",
    )
    return {
        "labels": {label: _age_domain_label_count(age_store, label, domain) for label in labels},
        "about_edges": _age_domain_about_edge_count(age_store, domain),
        "receipt_edges": _age_receipt_edge_count(age_store, ids["decision_id"], ids["receipt_id"], domain),
        "decision_exists": age_store.get_decision(ids["decision_id"]) is not None,
        "count_decisions": age_store.count_decisions(domain),
        "count_verified_decisions": age_store.count_verified_decisions(domain),
    }


@pytest.mark.age
def test_age_domain_scoped_reset(age_store):
    """AGE domain_scoped_reset clears one guarded test domain and preserves another."""
    # Protocol v2 AGE Slice 8 invariant: destructive reset is domain-scoped and guarded.
    domain = age_store.protocol_v2_test_domain
    other_domain = f"pytest_protocol_v2_other_{uuid.uuid4().hex[:8]}"
    target = _populate_age_reset_domain(age_store, domain, "AGE-TARGET")
    other = _populate_age_reset_domain(age_store, other_domain, "AGE-OTHER")

    age_store.domain_scoped_reset(domain)
    age_store.domain_scoped_reset(domain)

    for label in (
        "Decision",
        "Outcome",
        "Observation",
        "EvidenceReceipt",
        "ConservationStatus",
        "Fingerprint",
        "CentroidCheckpoint",
        "EvolutionEvent",
    ):
        assert _age_domain_label_count(age_store, label, domain) == 0
        assert _age_domain_label_count(age_store, label, other_domain) > 0
    assert _age_domain_label_count(age_store, "DomainContext", domain) == 0
    assert _age_domain_label_count(age_store, "DomainContext", other_domain) > 0
    assert _age_domain_about_edge_count(age_store, domain) == 0
    assert _age_domain_about_edge_count(age_store, other_domain) == 1
    assert age_store.get_decision(target["decision_id"]) is None
    assert age_store.get_decision(other["decision_id"]) is not None
    assert _age_receipt_edge_count(age_store, target["decision_id"], target["receipt_id"], domain) == 0
    assert _age_receipt_edge_count(age_store, other["decision_id"], other["receipt_id"], other_domain) == 1
    assert age_store.count_decisions(domain) == 0
    assert age_store.count_verified_decisions(domain) == 0
    assert age_store.count_decisions(other_domain) == 1
    assert age_store.count_verified_decisions(other_domain) == 1


@pytest.mark.age
def test_age_domain_scoped_reset_rejects_unsafe_domain(age_store):
    """AGE domain_scoped_reset rejects non-test domains before destructive work."""
    # Protocol v2 AGE Slice 8 invariant: reset cannot target arbitrary product domains.
    unsafe_domain = f"unsafe_domain_{uuid.uuid4().hex[:8]}"
    decision_id = f"AGE-UNSAFE-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=unsafe_domain, created_at=10.0)

    with pytest.raises(ValueError, match="pytest_protocol_v2"):
        age_store.domain_scoped_reset(unsafe_domain)

    assert age_store.get_decision(decision_id) is not None
    assert age_store.count_decisions(unsafe_domain) == 1


def test_entity_link_migration_deduplicates_legacy_edges(tmp_path):
    """Legacy duplicate entity edges do not break the uniqueness migration."""
    # Protocol v2 invariant: local adapter migrations are non-destructive except duplicates.
    db_path = tmp_path / "legacy-links.sqlite"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE decisions (
            decision_id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            category TEXT NOT NULL,
            category_index INTEGER NOT NULL,
            factors_json TEXT NOT NULL,
            factor_vector_json TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            recommended_index INTEGER NOT NULL,
            confidence REAL NOT NULL,
            probabilities_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at REAL NOT NULL
        );
        CREATE TABLE decision_entity_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL DEFAULT '',
            decision_id TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        INSERT INTO decisions VALUES
            ('D-1', 'test', 'category_a', 0, '{}', '[0.1]', 'approve', 0, 0.9, '[0.9]', 'pending', 100.0),
            ('D-2', 'test', 'category_a', 0, '{}', '[0.2]', 'approve', 0, 0.8, '[0.8]', 'pending', 101.0);
        INSERT INTO decision_entity_edges (domain, decision_id, entity_id, edge_type, created_at) VALUES
            ('test', 'D-1', 'invoice-1', 'DECIDED_ON', 10.0),
            ('test', 'D-1', 'invoice-1', 'DECIDED_ON', 11.0),
            ('test', 'D-2', 'invoice-2', 'DECIDED_ON', 12.0);
        """
    )
    conn.commit()
    conn.close()

    store = SQLiteGraphStore(db_path, domain="test")
    try:
        rows = store.connection.execute(
            """
            SELECT decision_id, entity_id, entity_type, domain, created_at
            FROM decision_entity_edges
            ORDER BY decision_id
            """
        ).fetchall()

        assert len(rows) == 2
        assert rows[0]["decision_id"] == "D-1"
        assert rows[0]["entity_id"] == "invoice-1"
        assert rows[0]["entity_type"] == "DECIDED_ON"
        assert rows[0]["created_at"] == 10.0
        assert rows[1]["decision_id"] == "D-2"
        assert rows[1]["entity_id"] == "invoice-2"
        assert store.count_decisions("test") == 2
        assert store.count_verified_decisions("test") == 0
    finally:
        store.close()


def test_legacy_link_decision_to_entity_duplicate_is_harmless(sqlite_store):
    """Legacy link_decision_to_entity remains duplicate-safe after Protocol v2 indexing."""
    # Protocol v2 link identity is (decision_id, entity_id, domain); legacy duplicates skip.
    _write_governed_decision(sqlite_store, "GOV-1")
    decisions_before = sqlite_store.count_decisions("test")
    verified_before = sqlite_store.count_verified_decisions("test")

    sqlite_store.link_decision_to_entity("GOV-1", "invoice-1")
    sqlite_store.link_decision_to_entity("GOV-1", "invoice-1")

    rows = sqlite_store.connection.execute(
        """
        SELECT decision_id, entity_id, entity_type, domain
        FROM decision_entity_edges
        WHERE decision_id = ?
        """,
        ("GOV-1",),
    ).fetchall()

    assert len(rows) == 1
    assert rows[0]["decision_id"] == "GOV-1"
    assert rows[0]["entity_id"] == "invoice-1"
    assert rows[0]["entity_type"] == "DECIDED_ON"
    assert rows[0]["domain"] == "test"
    assert sqlite_store.count_decisions("test") == decisions_before
    assert sqlite_store.count_verified_decisions("test") == verified_before


def test_archive_pending(sqlite_store):
    """Archiving pending decisions does not change conservation V."""
    # Protocol v2 method/invariant: archive_decisions preserves verified-only V.
    memory = InMemoryGraphStore(domain="test")
    for store in (sqlite_store, memory):
        _write_governed_decision(store, "P-OLD", created_at=10.0)
        _write_governed_decision(store, "P-NEW", created_at=60.0)
        _write_governed_decision(store, "C-OLD", created_at=20.0)
        _write_governed_decision(store, "OTHER-P", domain="other", created_at=10.0)
        store.write_outcome("C-OLD", "approve", True)
        verified_before = store.count_verified_decisions("test")

        archived = store.archive_decisions("test", before=50.0, status_filter="pending")

        assert archived == 1
        assert store.get_decision("P-OLD") is None
        assert store.get_decision("P-NEW") is not None
        assert store.get_decision("C-OLD") is not None
        assert store.get_decision("OTHER-P") is not None
        assert store.count_verified_decisions("test") == verified_before
        assert store.count_archived("test") == 1


def test_archive_verified(sqlite_store):
    """Archiving verified decisions removes them from active V."""
    # Protocol v2 method/invariant: active V excludes archived verified decisions.
    memory = InMemoryGraphStore(domain="test")
    for store in (sqlite_store, memory):
        _write_governed_decision(store, "C-OLD", created_at=10.0)
        _write_governed_decision(store, "O-OLD", created_at=11.0)
        _write_governed_decision(store, "C-NEW", created_at=60.0)
        _write_governed_decision(store, "P-OLD", created_at=10.0)
        _write_governed_decision(store, "OTHER-C", domain="other", created_at=10.0)
        store.write_outcome("C-OLD", "approve", True)
        store.write_outcome("O-OLD", "review", False)
        store.write_outcome("C-NEW", "approve", True)
        store.write_outcome("OTHER-C", "approve", True)

        with pytest.raises(ValueError, match="Archiving verified decisions reduces active V"):
            store.archive_decisions("test", before=50.0, status_filter="confirmed")

        archived = store.archive_decisions(
            "test",
            before=50.0,
            status_filter="confirmed",
            confirm_verified=True,
        )

        assert archived == 1
        assert store.get_decision("C-OLD") is None
        assert store.get_decision("O-OLD") is not None
        assert store.get_decision("C-NEW") is not None
        assert store.get_decision("P-OLD") is not None
        assert store.get_decision("OTHER-C") is not None
        assert store.count_verified_decisions("test") == 2
        assert store.count_verified_decisions("other") == 1
        assert store.count_archived("test") == 1


def _populate_reset_domain(store, domain: str, prefix: str) -> None:
    _write_governed_decision(store, f"{prefix}-D", domain=domain, created_at=10.0)
    _write_governed_decision(store, f"{prefix}-ARCH", domain=domain, created_at=1.0)
    store.write_outcome(f"{prefix}-D", "approve", True)
    store.link_entity(f"{prefix}-D", f"{prefix}-entity", "invoice", domain)
    store.write_observation(
        observation_id=f"{prefix}-OBS",
        domain=domain,
        category="category_a",
        recommended_action="approve",
        confidence=0.8,
        source_route="preview",
        scorer_version="slice-9",
        factor_schema_version="slice-9",
        entity_id=f"{prefix}-entity",
        factor_vector=[0.1, 0.9],
        factor_names=["factor_a", "factor_b"],
        metadata={"purpose": "reset-test"},
    )
    store.append_evidence_receipt(
        receipt_intent_id=f"{prefix}-RCP",
        domain=domain,
        decision_id=f"{prefix}-D",
        canonical_payload={"decision_id": f"{prefix}-D", "action": "approve"},
        actor="test",
        source_route="/api/test",
        metadata={"purpose": "reset-test"},
    )
    store.write_conservation_status(
        status_id=f"{prefix}-CSV",
        domain=domain,
        V=1,
        q=1.0,
        alpha=1.0,
        theta_min=23.53,
        verified_count=1,
        correct_count=1,
        status="GREEN",
        policy_version="slice-9",
    )
    store.write_fingerprint(
        fingerprint_id=f"{prefix}-FPR",
        domain=domain,
        factor_names=["factor_a"],
        factor_stats={"factor_a": {"mean": 0.5}},
        skipped_incompatible=0,
        window=10,
        metadata={"purpose": "reset-test"},
    )
    store.write_centroid_checkpoint(
        checkpoint_id=f"{prefix}-CKP",
        domain=domain,
        category="category_a",
        action="approve",
        centroids={"approve": [0.1, 0.9]},
        decisions_count=1,
        verified_count=1,
        iks=0.9,
        shape=[1, 2],
        factor_names_hash="factor-hash",
        metadata={"purpose": "reset-test"},
    )
    store.write_evolution_event(
        event_id=f"{prefix}-EVO",
        domain=domain,
        event_type="promoted",
        rule_name="amount_rule",
        variant_id="variant-a",
        metadata={"purpose": "reset-test"},
    )
    store.save_centroids(
        domain,
        "category_a",
        np.asarray([[0.1, 0.9]], dtype=float),
        metadata={"iks": 0.5},
    )
    store.archive_decisions(domain, before=5.0, status_filter="pending")


def test_domain_scoped_reset(sqlite_store):
    """domain_scoped_reset clears only the target domain partition."""
    # Protocol v2 method/invariant: no cross-domain deletion.
    memory = InMemoryGraphStore(domain="alpha")
    for store in (sqlite_store, memory):
        _populate_reset_domain(store, "alpha", "A")
        _populate_reset_domain(store, "beta", "B")

        store.domain_scoped_reset("alpha")
        store.domain_scoped_reset("alpha")

        assert store.count_decisions("alpha") == 0
        assert store.count_verified_decisions("alpha") == 0
        assert store.count_archived("alpha") == 0
        assert store.get_decision("A-D") is None
        assert store.count_decisions("beta") == 1
        assert store.count_verified_decisions("beta") == 1
        assert store.count_archived("beta") == 1
        assert store.get_decision("B-D") is not None

    sqlite_tables = (
        "observations",
        "observation_entity_edges",
        "observation_factor_vectors",
        "evidence_receipts",
        "conservation_snapshots",
        "fingerprints",
        "centroid_checkpoints",
        "evolution_events",
        "decision_entity_edges",
        "decisions_archive",
    )
    for table in sqlite_tables:
        alpha_count = sqlite_store.connection.execute(
            f"SELECT COUNT(*) AS n FROM {table} WHERE domain = ?",
            ("alpha",),
        ).fetchone()["n"]
        beta_count = sqlite_store.connection.execute(
            f"SELECT COUNT(*) AS n FROM {table} WHERE domain = ?",
            ("beta",),
        ).fetchone()["n"]
        assert alpha_count == 0
        assert beta_count > 0


def test_local_idempotent_replay_does_not_duplicate_class_a_records(sqlite_store):
    """Repeating implemented local Protocol v2 writes preserves the same state."""
    # Protocol v2 local invariant: identical Class A writes are idempotent without
    # depending on the future outbox worker or AGE migration replay.
    _write_governed_decision(sqlite_store, "GOV-1")
    _write_governed_decision(sqlite_store, "GOV-1")
    sqlite_store.write_outcome("GOV-1", "approve", True)
    first_receipt = _append_receipt(sqlite_store, "RCP-1")
    replay_receipt = _append_receipt(sqlite_store, "RCP-1")

    sqlite_store.write_conservation_status(
        status_id="CONS-1",
        domain="test",
        V=1,
        q=1.0,
        alpha=1.0,
        theta_min=0.5,
        verified_count=1,
        correct_count=1,
        status="green",
        policy_version="slice-6",
    )
    sqlite_store.write_conservation_status(
        status_id="CONS-1",
        domain="test",
        V=1,
        q=1.0,
        alpha=1.0,
        theta_min=0.5,
        verified_count=1,
        correct_count=1,
        status="green",
        policy_version="slice-6",
    )
    sqlite_store.write_fingerprint(
        fingerprint_id="FP-1",
        domain="test",
        factor_names=["factor_a"],
        factor_stats={"factor_a": {"mean": 0.5}},
        skipped_incompatible=0,
        window=10,
    )
    sqlite_store.write_fingerprint(
        fingerprint_id="FP-1",
        domain="test",
        factor_names=["factor_a"],
        factor_stats={"factor_a": {"mean": 0.5}},
        skipped_incompatible=0,
        window=10,
    )
    sqlite_store.write_centroid_checkpoint(
        checkpoint_id="CP-1",
        domain="test",
        category="category_a",
        action="approve",
        centroids={"approve": [0.1, 0.2]},
        decisions_count=1,
        verified_count=1,
        iks=0.9,
        shape=[1, 2],
        factor_names_hash="hash-a",
    )
    sqlite_store.write_centroid_checkpoint(
        checkpoint_id="CP-1",
        domain="test",
        category="category_a",
        action="approve",
        centroids={"approve": [0.1, 0.2]},
        decisions_count=1,
        verified_count=1,
        iks=0.9,
        shape=[1, 2],
        factor_names_hash="hash-a",
    )
    sqlite_store.write_evolution_event(
        event_id="EV-1",
        domain="test",
        event_type="rule_promoted",
        rule_name="rule-a",
        variant_id="variant-a",
    )
    sqlite_store.write_evolution_event(
        event_id="EV-1",
        domain="test",
        event_type="rule_promoted",
        rule_name="rule-a",
        variant_id="variant-a",
    )
    sqlite_store.link_entity("GOV-1", "entity-1", "Invoice", "test")
    sqlite_store.link_entity("GOV-1", "entity-1", "Invoice", "test")
    _write_observation(sqlite_store, "OBS-1")
    _write_observation(sqlite_store, "OBS-1")

    counts = {
        table: sqlite_store.connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        for table in (
            "decisions",
            "outcomes",
            "observations",
            "evidence_receipts",
            "conservation_snapshots",
            "fingerprints",
            "centroid_checkpoints",
            "evolution_events",
            "decision_entity_edges",
        )
    }

    assert first_receipt == replay_receipt
    assert counts == {
        "decisions": 1,
        "outcomes": 1,
        "observations": 1,
        "evidence_receipts": 1,
        "conservation_snapshots": 1,
        "fingerprints": 1,
        "centroid_checkpoints": 1,
        "evolution_events": 1,
        "decision_entity_edges": 1,
    }
    assert sqlite_store.count_decisions("test") == 1
    assert sqlite_store.count_verified_decisions("test") == 1


@AGE_CROSS_DOMAIN_CONCURRENCY_PENDING
def test_concurrent_cross_domain():
    """Concurrent writes to different domains do not cross-contaminate."""
    # Protocol v2 invariant: domain partitioning is enforced under concurrency.
    pass


@pytest.mark.age
def test_migration_replay(tmp_path, age_store):
    """SQLite-to-AGE replay preserves canonical counts and links."""
    # Protocol v2 invariant: migration is replay-safe and idempotent.
    domain = f"pytest_protocol_v2_migration_{uuid.uuid4().hex[:8]}"
    source_db = tmp_path / "migration.sqlite"
    _create_migration_source(source_db, domain, [f"migration-{index}" for index in range(5)])
    dsn = os.environ["AGE_TEST_DSN"]
    graph_conn, graph_name = _create_disposable_migration_graph(dsn)
    store = type(age_store)(dsn=dsn, graph_name=graph_name)
    try:
        first = run_migration(domain, str(source_db), dsn, graph_name, batch_size=2, verify=False)
        assert first["status"] == "PASS"
        assert first["write"]["written"] == 5
        assert store.count_decisions(domain) == 5
        assert _age_domain_outcome_count(store, domain) == 5
        edge_rows = store._store._run_query(
            f"MATCH ()-[r:HAS_OUTCOME]->() WHERE r.domain = {store._store._S(domain)} RETURN count(r) AS cnt"
        )
        assert edge_rows == [{"cnt": 5}]

        replay = run_migration(domain, str(source_db), dsn, graph_name, batch_size=2, verify=False)
        assert replay["status"] == "PASS"
        assert store.count_decisions(domain) == 5
        assert _age_domain_outcome_count(store, domain) == 5
        assert store._store._run_query(
            f"MATCH ()-[r:HAS_OUTCOME]->() WHERE r.domain = {store._store._S(domain)} RETURN count(r) AS cnt"
        ) == [{"cnt": 5}]
    finally:
        store.close()
        graph_conn.execute(f"SELECT drop_graph('{graph_name}', true)")
        graph_conn.close()


def test_v1_scorer_compatibility(tmp_path):
    """CompoundingScorer.score continues to work with v1 write_decision."""
    # Protocol v2 invariant: Protocol v2 is additive, not breaking.
    scorer = CompoundingScorer.from_preset("s2p", db_path=str(tmp_path / "s2p.sqlite"))
    try:
        factors = {name: 0.5 for name in scorer._preset.shape.factor_names}
        category = scorer._preset.shape.category_names[0]

        result = scorer.score(factors, category)

        assert isinstance(result.decision_id, str)
        decision = scorer.graph_store.get_decision(result.decision_id)
        assert decision is not None
        assert decision["status"] == "pending"
        assert scorer.graph_store.count_decisions("s2p") == 1
        assert scorer.graph_store.count_verified_decisions("s2p") == 0
    finally:
        scorer.graph_store.close()


def test_outcome_direct_duplicate_raises(sqlite_store):
    """A direct duplicate write_outcome call raises."""
    # Protocol v2 invariant: one Outcome per Decision for direct calls.
    _write_governed_decision(sqlite_store, "GOV-1")
    sqlite_store.write_outcome("GOV-1", "approve", True)

    with pytest.raises(ValueError, match="outcome already exists"):
        sqlite_store.write_outcome("GOV-1", "manual_review", False)

    outcome = sqlite_store.connection.execute(
        "SELECT actual_action, actual_index, is_correct FROM outcomes WHERE decision_id = ?",
        ("GOV-1",),
    ).fetchone()
    decision = sqlite_store.get_decision("GOV-1")

    assert outcome is not None
    assert outcome["actual_action"] == "approve"
    assert int(outcome["actual_index"]) == 0
    assert bool(outcome["is_correct"]) is True
    assert decision is not None
    assert decision["status"] == "confirmed"


def test_outcome_replay_identical_skips(sqlite_store):
    """Outbox replay of an identical outcome skips without duplication."""
    # Protocol v2 invariant: identical replay is idempotent.
    _write_governed_decision(sqlite_store, "GOV-1")
    sqlite_store.write_outcome("GOV-1", "approve", True)

    replay_decision = sqlite_store._check_outcome_replay("GOV-1", "approve", True)
    outcome_count = sqlite_store.connection.execute(
        "SELECT COUNT(*) AS n FROM outcomes WHERE decision_id = ?",
        ("GOV-1",),
    ).fetchone()["n"]
    decision = sqlite_store.get_decision("GOV-1")

    assert replay_decision == "already_applied"
    assert int(outcome_count) == 1
    assert decision is not None
    assert decision["status"] == "confirmed"


def test_outcome_replay_conflicting_errors(sqlite_store):
    """Outbox replay of a conflicting outcome quarantines or errors."""
    # Protocol v2 invariant: conflicting Class A replay is never silently ignored.
    _write_governed_decision(sqlite_store, "GOV-1")
    sqlite_store.write_outcome("GOV-1", "approve", True)

    replay_decision = sqlite_store._check_outcome_replay("GOV-1", "manual_review", False)
    outcome = sqlite_store.connection.execute(
        "SELECT actual_action, actual_index, is_correct FROM outcomes WHERE decision_id = ?",
        ("GOV-1",),
    ).fetchone()
    decision = sqlite_store.get_decision("GOV-1")

    assert replay_decision == "conflict"
    assert outcome is not None
    assert outcome["actual_action"] == "approve"
    assert bool(outcome["is_correct"]) is True
    assert decision is not None
    assert decision["status"] == "confirmed"


@pytest.mark.age
def test_age_transaction_rollback_preserves_domain_on_mid_reset_failure(age_store, monkeypatch):
    """Failed AGE reset transaction leaves the target domain unchanged."""
    # Protocol v2 AGE invariant: failure inside the real transaction helper rolls
    # back relationship and node deletes. This is live-only because SQLite/Memory
    # cannot exercise PostgreSQL+AGE transaction rollback.
    domain = age_store.protocol_v2_test_domain
    other_domain = f"pytest_protocol_v2_other_rollback_{uuid.uuid4().hex[:8]}"
    target = _populate_age_reset_domain(age_store, domain, "AGE-RB-TARGET")
    other = _populate_age_reset_domain(age_store, other_domain, "AGE-RB-OTHER")

    original_delete_domain_label = age_store._store._delete_domain_label
    delete_calls: list[tuple[str, str]] = []

    def fail_after_first_target_delete(tx, label: str, delete_domain: str) -> None:
        original_delete_domain_label(tx, label, delete_domain)
        delete_calls.append((label, delete_domain))
        if label == "EvidenceReceipt" and delete_domain == domain:
            raise RuntimeError("injected reset rollback failure")

    try:
        target_before = _age_reset_domain_snapshot(age_store, domain, target)
        other_before = _age_reset_domain_snapshot(age_store, other_domain, other)
        monkeypatch.setattr(age_store._store, "_delete_domain_label", fail_after_first_target_delete)

        with pytest.raises(RuntimeError, match="injected reset rollback failure"):
            age_store.domain_scoped_reset(domain)

        monkeypatch.undo()
        assert delete_calls == [("EvidenceReceipt", domain)]
        assert _age_reset_domain_snapshot(age_store, domain, target) == target_before
        assert _age_reset_domain_snapshot(age_store, other_domain, other) == other_before
    finally:
        monkeypatch.undo()
        age_store.domain_scoped_reset(domain)
        age_store.domain_scoped_reset(other_domain)


def test_preview_no_decision_write(sqlite_store):
    """Adapter-level preview persistence creates Observation, not Decision rows."""
    # Protocol v2 invariant: preview persistence uses Observation, not Decision.
    _write_observation(sqlite_store, "OBS-PREVIEW")

    assert sqlite_store.count_decisions("test") == 0
    assert sqlite_store.get_decision("OBS-PREVIEW") is None


@pytest.mark.age
def test_age_preview_no_decision_write(age_store):
    """AGE adapter-level preview persistence creates Observation, not Decision nodes."""
    # Protocol v2 AGE Slice 3 invariant: preview persistence uses Observation, not Decision.
    domain = age_store.protocol_v2_test_domain
    observation_id = f"AGE-OBS-PREVIEW-{uuid.uuid4().hex[:8]}"

    _write_observation(age_store, observation_id, domain=domain)

    assert _age_observation_count(age_store, observation_id) == 1
    assert age_store.count_decisions(domain) == 0
    assert age_store.get_decision(observation_id) is None


def test_outbox_replay_ordering(sqlite_store):
    """Outbox replay applies Decisions before dependent Outcomes and receipts."""
    # Protocol v2 invariant: replay ordering preserves referential integrity.
    decision_id = sqlite_store.enqueue_to_outbox(
        "test",
        "write_governed_decision",
        "GOV-OUTBOX-1",
        {"decision_id": "GOV-OUTBOX-1"},
    )
    outcome_id = sqlite_store.enqueue_to_outbox(
        "test",
        "write_outcome",
        "GOV-OUTBOX-1",
        {"decision_id": "GOV-OUTBOX-1", "actual_action": "approve"},
        causal_decision_id="GOV-OUTBOX-1",
    )
    receipt_id = sqlite_store.enqueue_to_outbox(
        "test",
        "append_evidence_receipt",
        "RCP-OUTBOX-1",
        {"decision_id": "GOV-OUTBOX-1", "receipt_intent_id": "RCP-OUTBOX-1"},
        causal_decision_id="GOV-OUTBOX-1",
    )

    rows = sqlite_store.connection.execute(
        """
        SELECT outbox_id, operation_type, causal_decision_id, status, schema_version
        FROM outbox
        WHERE domain = ?
        ORDER BY outbox_id
        """,
        ("test",),
    ).fetchall()

    assert [int(row["outbox_id"]) for row in rows] == [decision_id, outcome_id, receipt_id]
    assert [row["operation_type"] for row in rows] == [
        "write_governed_decision",
        "write_outcome",
        "append_evidence_receipt",
    ]
    assert rows[0]["causal_decision_id"] is None
    assert rows[1]["causal_decision_id"] == "GOV-OUTBOX-1"
    assert rows[2]["causal_decision_id"] == "GOV-OUTBOX-1"
    assert {row["status"] for row in rows} == {"pending"}
    assert {int(row["schema_version"]) for row in rows} == {1}


def test_evidence_replay_same_intent_skips(sqlite_store):
    """Same receipt_intent_id and same payload returns the existing receipt."""
    # Protocol v2 method/invariant: append_evidence_receipt replay is idempotent.
    first = _append_receipt(sqlite_store, "RCP-1")
    replay = _append_receipt(sqlite_store, "RCP-1")

    receipt_count = sqlite_store.connection.execute(
        "SELECT COUNT(*) AS n FROM evidence_receipts WHERE domain = ?",
        ("test",),
    ).fetchone()["n"]

    assert replay == first
    assert int(receipt_count) == 1


def test_evidence_replay_conflict_quarantines(sqlite_store):
    """Same receipt_intent_id with different payload quarantines or errors."""
    # Protocol v2 invariant: evidence hash-chain conflicts are visible.
    first = _append_receipt(sqlite_store, "RCP-1", payload_value="approved")

    with pytest.raises(ValueError, match="conflicting evidence receipt_intent_id"):
        _append_receipt(sqlite_store, "RCP-1", payload_value="blocked")

    rows = sqlite_store.connection.execute(
        """
        SELECT chain_index, previous_hash, payload_hash
        FROM evidence_receipts
        WHERE domain = ?
        ORDER BY chain_index
        """,
        ("test",),
    ).fetchall()

    assert len(rows) == 1
    assert rows[0]["chain_index"] == 0
    assert rows[0]["previous_hash"] == "GENESIS"
    assert rows[0]["payload_hash"] == first[1]


def test_governed_decision_conflict_quarantines(sqlite_store):
    """Same governed decision_id with different payload quarantines or errors."""
    # Protocol v2 method/invariant: write_governed_decision is Class A.
    original_id = sqlite_store.enqueue_to_outbox(
        "test",
        "write_governed_decision",
        "GOV-1",
        {"decision_id": "GOV-1", "recommended_action": "approve"},
    )

    with pytest.raises(ValueError, match="payload_hash_conflict"):
        sqlite_store.enqueue_to_outbox(
            "test",
            "write_governed_decision",
            "GOV-1",
            {"decision_id": "GOV-1", "recommended_action": "manual_review"},
        )

    outbox_rows = sqlite_store.connection.execute(
        "SELECT outbox_id, payload_json FROM outbox WHERE domain = ? AND target_key = ?",
        ("test", "GOV-1"),
    ).fetchall()
    quarantine_rows = sqlite_store.connection.execute(
        "SELECT outbox_id, new_payload_json, reason FROM outbox_quarantine WHERE domain = ? AND target_key = ?",
        ("test", "GOV-1"),
    ).fetchall()
    assert len(outbox_rows) == 1
    assert int(outbox_rows[0]["outbox_id"]) == original_id
    assert json.loads(outbox_rows[0]["payload_json"])["recommended_action"] == "approve"
    assert len(quarantine_rows) == 1
    assert int(quarantine_rows[0]["outbox_id"]) == original_id
    assert json.loads(quarantine_rows[0]["new_payload_json"])["recommended_action"] == "manual_review"
    assert quarantine_rows[0]["reason"] == "payload_hash_conflict"


def test_evolution_event_conflict_quarantines(sqlite_store):
    """Same event_id with different evolution payload quarantines or errors."""
    # Protocol v2 method/invariant: write_evolution_event conflict policy is strict.
    original_id = sqlite_store.enqueue_to_outbox(
        "test",
        "write_evolution_event",
        "EVT-1",
        {"event_id": "EVT-1", "variant_id": "variant-a"},
    )

    with pytest.raises(ValueError, match="payload_hash_conflict"):
        sqlite_store.enqueue_to_outbox(
            "test",
            "write_evolution_event",
            "EVT-1",
            {"event_id": "EVT-1", "variant_id": "variant-b"},
        )

    outbox_rows = sqlite_store.connection.execute(
        "SELECT outbox_id, payload_json FROM outbox WHERE domain = ? AND target_key = ?",
        ("test", "EVT-1"),
    ).fetchall()
    quarantine_rows = sqlite_store.connection.execute(
        "SELECT outbox_id, new_payload_json, reason FROM outbox_quarantine WHERE domain = ? AND target_key = ?",
        ("test", "EVT-1"),
    ).fetchall()
    assert len(outbox_rows) == 1
    assert int(outbox_rows[0]["outbox_id"]) == original_id
    assert json.loads(outbox_rows[0]["payload_json"])["variant_id"] == "variant-a"
    assert len(quarantine_rows) == 1
    assert int(quarantine_rows[0]["outbox_id"]) == original_id
    assert json.loads(quarantine_rows[0]["new_payload_json"])["variant_id"] == "variant-b"
    assert quarantine_rows[0]["reason"] == "payload_hash_conflict"


def test_outbox_quarantine_recorded(sqlite_store):
    """Conflicting outbox replay records a quarantine trail."""
    # Protocol v2 invariant: conflicts are auditable, not silently dropped.
    original_id = sqlite_store.enqueue_to_outbox(
        "test",
        "operation",
        "TARGET-1",
        {"value": "original"},
    )
    with pytest.raises(ValueError, match="payload_hash_conflict"):
        sqlite_store.enqueue_to_outbox(
            "test",
            "operation",
            "TARGET-1",
            {"value": "conflict"},
        )

    quarantine = sqlite_store.connection.execute(
        """
        SELECT *
        FROM outbox_quarantine
        WHERE domain = ? AND operation_type = ? AND target_key = ?
        """,
        ("test", "operation", "TARGET-1"),
    ).fetchone()
    original = sqlite_store.connection.execute(
        "SELECT payload_hash, payload_json FROM outbox WHERE outbox_id = ?",
        (original_id,),
    ).fetchone()

    assert quarantine is not None
    assert int(quarantine["outbox_id"]) == original_id
    assert quarantine["existing_payload_hash"] == original["payload_hash"]
    assert quarantine["new_payload_hash"] != original["payload_hash"]
    assert json.loads(original["payload_json"]) == {"value": "original"}
    assert json.loads(quarantine["new_payload_json"]) == {"value": "conflict"}
    assert quarantine["reason"] == "payload_hash_conflict"
    assert quarantine["resolved_at"] is None
    assert quarantine["resolution"] is None


def test_write_outcome_domain_is_optional_and_scopes_sqlite_store(sqlite_store):
    """Explicit domain succeeds; omitted domain keeps the v1 call path working."""
    _write_governed_decision(sqlite_store, "OUTCOME-DOMAIN", domain="test")
    sqlite_store.write_outcome("OUTCOME-DOMAIN", "approve", True, domain="test")
    assert sqlite_store.get_decision("OUTCOME-DOMAIN")["status"] == "confirmed"

    _write_governed_decision(sqlite_store, "OUTCOME-LEGACY", domain="test")
    sqlite_store.write_outcome("OUTCOME-LEGACY", "approve", True)
    assert sqlite_store.get_decision("OUTCOME-LEGACY")["status"] == "confirmed"


def test_age_write_outcome_compound_domain_identity(age_store):
    """A shared decision ID updates only the explicitly selected AGE domain."""
    decision_id = f"OUTCOME-COMPOUND-{uuid.uuid4().hex}"
    first_domain = f"pytest_protocol_v2_first_{uuid.uuid4().hex}"
    second_domain = f"pytest_protocol_v2_second_{uuid.uuid4().hex}"
    _write_governed_decision(age_store, decision_id, domain=first_domain)
    _write_governed_decision(age_store, decision_id, domain=second_domain)

    age_store.write_outcome(decision_id, "approve", True, domain=first_domain)
    first = next(decision for decision in age_store.get_decisions(first_domain) if decision["decision_id"] == decision_id)
    second = next(decision for decision in age_store.get_decisions(second_domain) if decision["decision_id"] == decision_id)
    assert first["status"] == "confirmed"
    assert second["status"] == "pending"

    outcome_rows = age_store._store._run_query(
        f"""
        MATCH (o:Outcome {{decision_id: {age_store._store._S(decision_id)}}})
        RETURN o.domain AS domain, count(o) AS cnt
        """
    )
    assert outcome_rows == [{"domain": first_domain, "cnt": 1}]

    edge_rows = age_store._store._run_query(
        f"""
        MATCH (d:Decision {{decision_id: {age_store._store._S(decision_id)}}})-[:HAS_OUTCOME]->(o:Outcome {{decision_id: {age_store._store._S(decision_id)}}})
        RETURN d.domain AS decision_domain, o.domain AS outcome_domain, count(o) AS cnt
        """
    )
    assert edge_rows == [{"decision_domain": first_domain, "outcome_domain": first_domain, "cnt": 1}]

    other_edge_rows = age_store._store._run_query(
        f"""
        MATCH (d:Decision {{decision_id: {age_store._store._S(decision_id)}}})-[:HAS_OUTCOME]->(o:Outcome)
        WHERE d.domain = {age_store._store._S(second_domain)}
        RETURN count(o) AS cnt
        """
    )
    assert other_edge_rows == [{"cnt": 0}]


@pytest.mark.age
def test_age_write_outcome_domain_preserves_status_transition(age_store):
    """A domain-scoped outcome confirms its pending Decision and keeps its domain."""
    domain = age_store.protocol_v2_test_domain
    decision_id = f"OUTCOME-TRANSITION-{uuid.uuid4().hex[:8]}"
    _write_governed_decision(age_store, decision_id, domain=domain)

    age_store.write_outcome(decision_id, "approve", True, domain=domain)

    decision = age_store.get_decision(decision_id)
    outcome = _age_get_outcome(age_store, decision_id)
    assert decision is not None
    assert decision["status"] == "confirmed"
    assert outcome is not None
    assert outcome["domain"] == domain


@pytest.mark.age
def test_age_migration_source_tag_is_counted_in_active_v(age_store):
    """Confirmed SQLite-migrated Decisions are active verified evidence."""
    domain = age_store.protocol_v2_test_domain
    decision_id = f"MIGRATION-V-{uuid.uuid4().hex[:8]}"
    store = age_store._store
    store._run_query(
        f"""
        CREATE (d:Decision {{
            decision_id: {store._S(decision_id)}, domain: {store._S(domain)},
            status: 'confirmed', migration_source: 'sqlite'
        }})
        CREATE (o:Outcome {{
            decision_id: {store._S(decision_id)}, domain: {store._S(domain)}, is_correct: true
        }})
        CREATE (d)-[:HAS_OUTCOME {{decision_id: {store._S(decision_id)}, domain: {store._S(domain)}}}]->(o)
        RETURN 1 AS created
        """
    )

    assert age_store.count_verified(domain) == 1
    assert age_store.count_verified_decisions(domain) == 1


@pytest.mark.age
def test_age_checkpoint_receipt_per_decision_isolation(tmp_path, age_store):
    """Migrated checkpoints and receipts link only to their originating Decision."""
    domain = age_store.protocol_v2_test_domain
    decision_one = f"ISOLATION-ONE-{uuid.uuid4().hex[:8]}"
    decision_two = f"ISOLATION-TWO-{uuid.uuid4().hex[:8]}"
    source_db = tmp_path / "isolation.sqlite"
    _create_migration_source(
        source_db,
        domain,
        [decision_one, decision_two],
        checkpoint_decision_id=decision_one,
        receipt_decision_id=decision_two,
    )

    result = run_migration(
        domain,
        str(source_db),
        os.environ["AGE_TEST_DSN"],
        os.environ["AGE_TEST_GRAPH"],
        verify=False,
    )
    assert result["status"] == "PASS"
    store = age_store._store
    checkpoint_edges = store._run_query(
        f"""
        MATCH (d:Decision)-[:HAS_CENTROID_CHECKPOINT]->(c:CentroidCheckpoint)
        WHERE d.domain = {store._S(domain)}
        RETURN d.decision_id AS decision_id, c.decision_id AS checkpoint_decision_id, count(c) AS cnt
        """
    )
    receipt_edges = store._run_query(
        f"""
        MATCH (d:Decision)-[:EMITTED_RECEIPT]->(r:EvidenceReceipt)
        WHERE d.domain = {store._S(domain)}
        RETURN d.decision_id AS decision_id, r.decision_id AS receipt_decision_id, count(r) AS cnt
        """
    )
    assert checkpoint_edges == [{"decision_id": decision_one, "checkpoint_decision_id": decision_one, "cnt": 1}]
    assert receipt_edges == [{"decision_id": decision_two, "receipt_decision_id": decision_two, "cnt": 1}]
