from __future__ import annotations

import os
import sys
import importlib
import time
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.scorer import CompoundingScorer, _factor_names_hash


DOMAIN = "parity_test"


def _stores(tmp_path: Path) -> list[Any]:
    stores: list[Any] = [
        InMemoryGraphStore(domain=DOMAIN),
        SQLiteGraphStore(str(tmp_path / "parity.sqlite"), domain=DOMAIN),
    ]

    # AGE is opt-in and always receives a fresh disposable graph.
    dsn = os.environ.get("GRAPH_DSN")
    graph_name = f"protocol_v2_test_parity_{os.urandom(5).hex()}"
    if dsn and os.environ.get("PARITY_SKIP_AGE") != "1":
        ci_platform = Path(__file__).resolve().parents[2] / "ci-platform"
        sys.path.insert(0, str(ci_platform))
        psycopg = importlib.import_module("psycopg")
        conn: Any = psycopg.connect(dsn, autocommit=True)
        try:
            conn.execute("LOAD 'age'")
            conn.execute("SET search_path = ag_catalog, '$user', public")
            conn.execute(f"SELECT create_graph('{graph_name}')")
            from ci_platform.graph.age_graph_store import AGEGraphStore

            stores.append(AGEGraphStore(dsn, graph_name=graph_name))
        except Exception as exc:
            conn.execute(f"SELECT drop_graph('{graph_name}', true)")
            conn.close()
            pytest.skip(f"disposable AGE graph unavailable: {exc}")
        setattr(stores[-1], "_parity_connection", conn)
        setattr(stores[-1], "_parity_graph_name", graph_name)
    return stores


@pytest.fixture()
def stores(tmp_path: Path):
    active = _stores(tmp_path)
    try:
        yield active
    finally:
        for store in active:
            close = getattr(store, "close", None)
            if close is not None:
                close()
            conn = getattr(store, "_parity_connection", None)
            graph_name = getattr(store, "_parity_graph_name", None)
            if conn is not None and graph_name is not None:
                try:
                    conn.execute(f"SELECT drop_graph('{graph_name}', true)")
                finally:
                    conn.close()


def _write_decision(store: Any, decision_id: str) -> str:
    return str(store.write_decision(
        DOMAIN,
        category="parity",
        action="confirm",
        confidence=0.9,
        factors={"risk": 0.1},
        metadata={"decision_id": decision_id},
    ))


def _write_checkpoint_pair(store: Any) -> None:
    store.save_centroids(
        DOMAIN,
        "legacy",
        np.asarray([0.1, 0.2]),
        metadata={"iks": 1.0},
    )
    time.sleep(0.01)
    store.write_centroid_checkpoint(
        checkpoint_id="v2-parity",
        domain=DOMAIN,
        category="parity",
        action="confirm",
        centroids=np.asarray([0.9, 0.8]),
        decisions_count=2,
        verified_count=1,
        iks=2.0,
        shape=[1, 2],
        factor_names_hash="parity-hash",
        metadata={"source": "parity-test"},
    )


def test_write_outcome_idempotent_parity(stores: list[Any]) -> None:
    for store in stores:
        decision_id = _write_decision(store, f"outcome-{type(store).__name__}")
        store.write_outcome(decision_id, "confirm", True, domain=DOMAIN)
        store.write_outcome(decision_id, "confirm", True, domain=DOMAIN)
        with pytest.raises(ValueError, match="different action"):
            store.write_outcome(decision_id, "reject", True, domain=DOMAIN)


def test_write_outcome_not_found_parity(stores: list[Any]) -> None:
    for store in stores:
        with pytest.raises(KeyError):
            store.write_outcome("missing-decision", "confirm", True, domain=DOMAIN)


def test_centroid_checkpoint_v2_parity(stores: list[Any]) -> None:
    for store in stores:
        _write_checkpoint_pair(store)
        rows = store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None)
        v2 = next(row for row in rows if row.get("checkpoint_id") == "v2-parity")
        assert v2["domain"] == DOMAIN
        assert v2["category"] == "parity"
        assert v2["action"] == "confirm"
        assert np.asarray(v2["centroids"]).tolist() == [0.9, 0.8]
        assert v2["shape"] == [1, 2]
        assert v2["factor_names_hash"] == "parity-hash"


def test_load_latest_centroids_parity(stores: list[Any]) -> None:
    for store in stores:
        _write_checkpoint_pair(store)
        assert (
            np.asarray(store.load_latest_centroids(DOMAIN)).tolist() == [0.9, 0.8]
        ), type(store).__name__


def test_checkpoint_created_at_is_numeric_epoch(stores: list[Any]) -> None:
    for store in stores:
        _write_checkpoint_pair(store)
        rows = store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None)
        assert rows
        assert all(isinstance(row["created_at"], float) for row in rows)


def test_mixed_iso_and_epoch_checkpoint_ordering() -> None:
    memory = InMemoryGraphStore(domain=DOMAIN)
    memory.save_centroids(DOMAIN, "legacy", np.asarray([0.1, 0.2]), metadata={"iks": 1.0})
    memory._centroid_checkpoints[-1]["created_at"] = "2026-01-01T00:00:00+00:00"
    memory.write_centroid_checkpoint(
        checkpoint_id="epoch-newer",
        domain=DOMAIN,
        category="parity",
        action="confirm",
        centroids=np.asarray([0.9, 0.8]),
        decisions_count=2,
        verified_count=1,
        iks=2.0,
        shape=[1, 2],
        factor_names_hash="parity-hash",
    )
    rows = memory.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None)
    assert rows[0]["checkpoint_id"] == "epoch-newer"
    assert np.asarray(memory.load_latest_centroids(DOMAIN)).tolist() == [0.9, 0.8]


def test_factor_hash_mismatch_falls_back_to_bootstrap() -> None:
    preset = PRESET_REGISTRY["s2p"]()
    store = InMemoryGraphStore(domain="s2p")
    store.write_centroid_checkpoint(
        checkpoint_id="factor-mismatch",
        domain="s2p",
        category="parity",
        action=preset.shape.action_names[0],
        centroids=np.ones_like(preset.bootstrap_centroids),
        decisions_count=1,
        verified_count=0,
        iks=1.0,
        shape=list(preset.bootstrap_centroids.shape),
        factor_names_hash="wrong-hash",
    )
    scorer = CompoundingScorer.from_preset("s2p", graph_store=store, profile="test")
    np.testing.assert_array_equal(scorer._scorer.centroids, preset.bootstrap_centroids)


def test_factor_hash_match_loads_checkpoint() -> None:
    preset = PRESET_REGISTRY["s2p"]()
    store = InMemoryGraphStore(domain="s2p")
    expected = np.ones_like(preset.bootstrap_centroids) * 0.25
    store.write_centroid_checkpoint(
        checkpoint_id="factor-match",
        domain="s2p",
        category="parity",
        action=preset.shape.action_names[0],
        centroids=expected,
        decisions_count=1,
        verified_count=0,
        iks=1.0,
        shape=list(expected.shape),
        factor_names_hash=_factor_names_hash(list(preset.shape.factor_names)),
    )
    scorer = CompoundingScorer.from_preset("s2p", graph_store=store, profile="test")
    np.testing.assert_array_equal(scorer._scorer.centroids, expected)


def test_factor_hash_missing_keeps_legacy_checkpoint_compatible() -> None:
    preset = PRESET_REGISTRY["s2p"]()
    store = InMemoryGraphStore(domain="s2p")
    expected = np.ones_like(preset.bootstrap_centroids) * 0.125
    store.save_centroids("s2p", "legacy", expected)
    scorer = CompoundingScorer.from_preset("s2p", graph_store=store, profile="test")
    np.testing.assert_array_equal(scorer._scorer.centroids, expected)


def test_include_v2_false_parity(stores: list[Any]) -> None:
    for store in stores:
        _write_checkpoint_pair(store)
        legacy = store.get_centroid_checkpoints(DOMAIN, include_v2=False, limit=None)
        combined = store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None)
        assert len(legacy) == 1
        assert len(combined) == 2


def test_conservation_write_read_parity(stores: list[Any]) -> None:
    for store in stores:
        store.write_conservation_status(
            "conservation-parity",
            DOMAIN,
            V=4,
            q=0.75,
            alpha=0.8,
            theta_min=0.5,
            verified_count=4,
            correct_count=3,
            status="GREEN",
            policy_version="parity-v1",
        )
        rows = store.get_latest_conservation_statuses([DOMAIN])
        assert len(rows) == 1
        row = rows[0]
        assert row.get("domain") == DOMAIN
        assert row.get("V") == 4
        assert row.get("q") == pytest.approx(0.75)
        assert row.get("correct_count") == 3
        assert row.get("status") == "GREEN"


def test_count_verified_correct_parity(stores: list[Any]) -> None:
    for index, store in enumerate(stores):
        first = _write_decision(store, f"count-{index}-1")
        second = _write_decision(store, f"count-{index}-2")
        _write_decision(store, f"count-{index}-3")
        store.write_outcome(first, "confirm", True, domain=DOMAIN)
        store.write_outcome(second, "reject", False, domain=DOMAIN)
        assert store.count_verified(DOMAIN) == 2
        assert store.count_correct(DOMAIN) == 1
