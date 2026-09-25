import json
import sqlite3
from pathlib import Path

import numpy as np
import pytest

from scripts.refresh_demo_centroid_checkpoints import (
    CentroidRefreshError,
    action_spreads,
    refresh_database_from_bundle,
)


def _schema(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE decisions (id INTEGER PRIMARY KEY, decision_id TEXT)")
    conn.execute("CREATE TABLE l5_centroids (id INTEGER PRIMARY KEY, payload TEXT)")
    conn.execute(
        """
        CREATE TABLE centroid_checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            decision_id TEXT,
            category TEXT,
            centroids_json TEXT NOT NULL,
            decisions_count INTEGER,
            iks REAL,
            metadata_json TEXT,
            created_at REAL,
            decision_time_start TEXT,
            decision_time_end TEXT,
            checkpoint_time TEXT,
            checkpoint_id TEXT,
            action TEXT,
            verified_count INTEGER,
            shape_json TEXT,
            factor_names_hash TEXT,
            quality_window_size INTEGER,
            quality_verified_count INTEGER,
            quality_correct_count INTEGER,
            rolling_accuracy REAL,
            quality_window_end TEXT,
            quality_policy_version TEXT
        )
        """
    )


def _collapsed(shape=(2, 3, 4)):
    arr = np.zeros(shape, dtype=float)
    arr[:, :, :] = np.arange(shape[0], dtype=float)[:, None, None] / 10.0
    return arr


def _differentiated(shape=(2, 3, 4)):
    arr = _collapsed(shape)
    for action in range(shape[1]):
        arr[:, action, :] += action * 0.05
    return arr


def _make_db(tmp_path: Path, mu=None) -> Path:
    db = tmp_path / "demo.db"
    conn = sqlite3.connect(db)
    _schema(conn)
    for idx in range(3):
        conn.execute("INSERT INTO decisions (decision_id) VALUES (?)", (f"d{idx}",))
    conn.execute("INSERT INTO l5_centroids (payload) VALUES ('keep')")
    mu = _collapsed() if mu is None else mu
    conn.execute(
        """
        INSERT INTO centroid_checkpoints
            (domain, centroids_json, decisions_count, iks, metadata_json, created_at, checkpoint_id, verified_count)
        VALUES ('demo', ?, 3, 0.1, '{}', 1.0, 'old', 0)
        """,
        (json.dumps(mu.tolist()),),
    )
    conn.commit()
    conn.close()
    return db


def _make_bundle(tmp_path: Path, mu) -> Path:
    bundle = tmp_path / "bundle.json"
    bundle.write_text(
        json.dumps(
            {
                "centroid_checkpoints": [
                    {
                        "centroids": np.asarray(mu).tolist(),
                        "iks": 0.42,
                        "metadata": {"label": "unit bundle"},
                        "created_at": 2.0,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return bundle


def _checkpoint_count(db: Path) -> int:
    conn = sqlite3.connect(db)
    try:
        return conn.execute("SELECT COUNT(*) FROM centroid_checkpoints").fetchone()[0]
    finally:
        conn.close()


def _counts(db: Path):
    conn = sqlite3.connect(db)
    try:
        return (
            conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM l5_centroids").fetchone()[0],
        )
    finally:
        conn.close()


def test_refresh_replaces_collapsed_checkpoint(tmp_path):
    db = _make_db(tmp_path)
    bundle = _make_bundle(tmp_path, _differentiated())

    result = refresh_database_from_bundle(
        "demo", db, bundle, (2, 3, 4), ("a", "b", "c", "d"), dry_run=False
    )

    assert result["inserted_row_id"] is not None
    assert _checkpoint_count(db) == 2
    assert min(result["verified_spreads"]) > 0.01


def test_refresh_rejects_collapsed_bundle(tmp_path):
    db = _make_db(tmp_path)
    bundle = _make_bundle(tmp_path, _collapsed())

    with pytest.raises(CentroidRefreshError):
        refresh_database_from_bundle("demo", db, bundle, (2, 3, 4), ("a", "b", "c", "d"))

    assert _checkpoint_count(db) == 1


def test_refresh_preserves_decisions(tmp_path):
    db = _make_db(tmp_path)
    before_decisions, _ = _counts(db)
    bundle = _make_bundle(tmp_path, _differentiated())

    refresh_database_from_bundle("demo", db, bundle, (2, 3, 4), ("a", "b", "c", "d"))

    after_decisions, _ = _counts(db)
    assert after_decisions == before_decisions


def test_refresh_preserves_l5(tmp_path):
    db = _make_db(tmp_path)
    _, before_l5 = _counts(db)
    bundle = _make_bundle(tmp_path, _differentiated())

    refresh_database_from_bundle("demo", db, bundle, (2, 3, 4), ("a", "b", "c", "d"))

    _, after_l5 = _counts(db)
    assert after_l5 == before_l5


def test_dry_run_does_not_write(tmp_path):
    db = _make_db(tmp_path)
    bundle = _make_bundle(tmp_path, _differentiated())

    result = refresh_database_from_bundle(
        "demo", db, bundle, (2, 3, 4), ("a", "b", "c", "d"), dry_run=True
    )

    assert result["mode"] == "dry-run"
    assert result["inserted_row_id"] is None
    assert _checkpoint_count(db) == 1


def test_verify_only_reports_spread(tmp_path):
    db = _make_db(tmp_path, _differentiated())
    bundle = _make_bundle(tmp_path, _differentiated())

    result = refresh_database_from_bundle(
        "demo", db, bundle, (2, 3, 4), ("a", "b", "c", "d"), verify_only=True
    )

    assert result["mode"] == "verify-only"
    assert min(result["current_spreads"]) > 0.01
    assert result["collapsed"] == []
    assert action_spreads(_differentiated()) == result["current_spreads"]
