from __future__ import annotations

import importlib
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore


DOMAIN = "jm_conformance"
STORE_NAMES = ("memory", "sqlite") + (("age",) if os.environ.get("GRAPH_DSN") else ())


def _age_store() -> tuple[Any, Any, str]:
    dsn = os.environ["GRAPH_DSN"]
    ci_platform = Path(__file__).resolve().parents[2] / "ci-platform"
    sys.path.insert(0, str(ci_platform))
    psycopg = importlib.import_module("psycopg")
    connection = psycopg.connect(dsn, autocommit=True)
    graph_name = f"jm_conformance_{os.urandom(5).hex()}"
    try:
        connection.execute("LOAD 'age'")
        connection.execute("SET search_path = ag_catalog, '$user', public")
        connection.execute(f"SELECT create_graph('{graph_name}')")
        from ci_platform.graph.age_graph_store import AGEGraphStore

        return AGEGraphStore(dsn, graph_name=graph_name), connection, graph_name
    except Exception:
        connection.close()
        raise


@pytest.fixture(params=STORE_NAMES)
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Any:
    if request.param == "memory":
        yield InMemoryGraphStore(domain=DOMAIN)
        return
    if request.param == "sqlite":
        instance = SQLiteGraphStore(str(tmp_path / "conformance.sqlite"), domain=DOMAIN)
        try:
            yield instance
        finally:
            instance.close()
        return

    try:
        instance, connection, graph_name = _age_store()
    except Exception as exc:
        pytest.skip(f"disposable AGE graph unavailable: {exc}")
    try:
        yield instance
    finally:
        try:
            connection.execute(f"SELECT drop_graph('{graph_name}', true)")
        finally:
            connection.close()


def _write_v2(store: Any, checkpoint_id: str = "checkpoint-v2") -> None:
    store.write_centroid_checkpoint(
        checkpoint_id=checkpoint_id,
        domain=DOMAIN,
        category="quality",
        action="confirm",
        centroids=np.asarray([0.25, 0.75]),
        decisions_count=8,
        verified_count=6,
        iks=4.5,
        shape=[2],
        factor_names_hash="factor-hash-v1",
        metadata={"source": "conformance", "quality": {"source": "checkpoint"}},
    )


def _first(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0]


def test_write_v2_checkpoint_round_trip(store: Any) -> None:
    _write_v2(store)
    checkpoint = next(
        row for row in store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None)
        if row.get("checkpoint_id") == "checkpoint-v2"
    )
    assert checkpoint["domain"] == DOMAIN
    assert checkpoint["category"] == "quality"
    assert checkpoint["action"] == "confirm"
    assert np.asarray(checkpoint["centroids"]).tolist() == [0.25, 0.75]
    assert checkpoint["decisions_count"] == 8
    assert checkpoint["verified_count"] == 6
    assert checkpoint["iks"] == pytest.approx(4.5)
    assert checkpoint["shape"] == [2]
    assert checkpoint["factor_names_hash"] == "factor-hash-v1"


def test_write_legacy_checkpoint_round_trip(store: Any) -> None:
    store.save_centroids(DOMAIN, "legacy", np.asarray([0.1, 0.2]), {"iks": 1.5, "source": "legacy"})
    checkpoint = _first(store.get_centroid_checkpoints(DOMAIN, include_v2=False, limit=None))
    assert checkpoint.get("checkpoint_id") in (None, "")
    assert checkpoint["domain"] == DOMAIN
    assert checkpoint["category"] == "legacy"
    assert np.asarray(checkpoint["centroids"]).tolist() == [0.1, 0.2]
    assert checkpoint["metadata"] == {"iks": 1.5, "source": "legacy"}


def test_checkpoint_created_at_is_epoch(store: Any) -> None:
    _write_v2(store)
    checkpoint = _first(store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None))
    assert isinstance(checkpoint["created_at"], float)


def test_include_v2_controls_visibility(store: Any) -> None:
    store.save_centroids(DOMAIN, "legacy", [0.1], {"iks": 1.0})
    _write_v2(store)
    legacy = store.get_centroid_checkpoints(DOMAIN, include_v2=False, limit=None)
    combined = store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None)
    assert len(legacy) == 1
    assert len(combined) == 2
    assert all(row.get("checkpoint_id") in (None, "") for row in legacy)


def test_checkpoint_ordering_newest_first(store: Any) -> None:
    store.save_centroids(DOMAIN, "old", [0.1], {"iks": 1.0})
    time.sleep(0.01)
    _write_v2(store, "checkpoint-new")
    rows = store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None)
    assert rows[0]["checkpoint_id"] == "checkpoint-new"
    assert float(rows[0]["created_at"]) >= float(rows[1]["created_at"])


def test_load_latest_returns_newest(store: Any) -> None:
    store.save_centroids(DOMAIN, "old", [0.1], {"iks": 1.0})
    time.sleep(0.01)
    _write_v2(store, "checkpoint-new")
    np.testing.assert_allclose(store.load_latest_centroids(DOMAIN), [0.25, 0.75])


def test_load_latest_across_legacy_and_v2(store: Any) -> None:
    store.save_centroids(DOMAIN, "legacy", [0.2], {"iks": 1.0})
    time.sleep(0.01)
    _write_v2(store, "checkpoint-v2-new")
    np.testing.assert_allclose(store.load_latest_centroids(DOMAIN), [0.25, 0.75])


def test_load_latest_empty_returns_none(store: Any) -> None:
    assert store.load_latest_centroids(DOMAIN) is None


def test_write_outcome_idempotent(store: Any) -> None:
    decision_id = store.write_decision(
        DOMAIN, "quality", "confirm", 0.9, {"risk": 0.1}, {"decision_id": "outcome-1"}
    )
    store.write_outcome(decision_id, "confirm", True, domain=DOMAIN)
    store.write_outcome(decision_id, "confirm", True, domain=DOMAIN)


def test_write_outcome_conflict(store: Any) -> None:
    decision_id = store.write_decision(
        DOMAIN, "quality", "confirm", 0.9, {"risk": 0.1}, {"decision_id": "outcome-2"}
    )
    store.write_outcome(decision_id, "confirm", True, domain=DOMAIN)
    with pytest.raises(ValueError, match="different action"):
        store.write_outcome(decision_id, "override", True, domain=DOMAIN)


def test_write_outcome_not_found(store: Any) -> None:
    with pytest.raises(KeyError):
        store.write_outcome("missing", "confirm", True, domain=DOMAIN)


def test_conservation_write_read(store: Any) -> None:
    store.write_conservation_status(
        "conservation-1", DOMAIN, 4, 0.75, 0.8, 0.5, 4, 3, "GREEN", "v1"
    )
    row = store.get_latest_conservation_statuses([DOMAIN])[0]
    assert row["domain"] == DOMAIN
    assert row["V"] == 4
    assert row["q"] == pytest.approx(0.75)
    assert row["correct_count"] == 3
    assert row["status"] == "GREEN"


def test_count_verified_correct(store: Any) -> None:
    first = store.write_decision(DOMAIN, "quality", "confirm", 0.9, {}, {"decision_id": "count-1"})
    second = store.write_decision(DOMAIN, "quality", "reject", 0.8, {}, {"decision_id": "count-2"})
    store.write_decision(DOMAIN, "quality", "confirm", 0.7, {}, {"decision_id": "count-3"})
    store.write_outcome(first, "confirm", True, domain=DOMAIN)
    store.write_outcome(second, "reject", False, domain=DOMAIN)
    assert store.count_verified(DOMAIN) == 2
    assert store.count_correct(DOMAIN) == 1


def test_checkpoint_preserves_factor_hash(store: Any) -> None:
    _write_v2(store)
    checkpoint = _first(store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None))
    assert checkpoint["factor_names_hash"] == "factor-hash-v1"


def test_warm_start_checkpoint_has_category(store: Any) -> None:
    store.write_centroid_checkpoint(
        checkpoint_id="warm-start-1",
        domain=DOMAIN,
        category="warm_start",
        action="restore",
        centroids=[0.5, 0.5],
        decisions_count=0,
        verified_count=0,
        iks=0.0,
        shape=[2],
        factor_names_hash="factor-hash-v1",
        metadata={"reason": "warm_start"},
    )
    checkpoint = _first(store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None))
    assert checkpoint["category"] == "warm_start"
