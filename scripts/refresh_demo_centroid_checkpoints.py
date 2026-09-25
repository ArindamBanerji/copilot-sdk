"""Refresh demo centroid checkpoints from regenerated demo bundles.

This utility inserts a new superseding centroid checkpoint row for domains whose
warm SQLite databases still contain collapsed legacy checkpoint tensors. It does
not delete or mutate decisions, L5 centroids, outcomes, DK weights, or other
state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from copilot_sdk.scoring.presets import PurchasingPreset, TradingPreset
from copilot_sdk.scoring.scorer import _factor_names_hash

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DomainConfig:
    name: str
    db_path: Path
    bundle_path: Path
    expected_shape: tuple[int, int, int]
    factor_names: tuple[str, ...]


DOMAIN_CONFIGS: dict[str, DomainConfig] = {
    "purchasing": DomainConfig(
        name="purchasing",
        db_path=ROOT / "apps" / "purchasing" / "backend" / "data" / "purchasing.db",
        bundle_path=ROOT / "demo" / "purchasing_demo_bundle.json",
        expected_shape=(
            PurchasingPreset().shape.n_categories,
            PurchasingPreset().shape.n_actions,
            PurchasingPreset().shape.n_factors,
        ),
        factor_names=tuple(PurchasingPreset().shape.factor_names),
    ),
    "trading": DomainConfig(
        name="trading",
        db_path=ROOT / "apps" / "trading" / "backend" / "data" / "trading.db",
        bundle_path=ROOT / "demo" / "trading_demo_bundle.json",
        expected_shape=(
            TradingPreset().shape.n_categories,
            TradingPreset().shape.n_actions,
            TradingPreset().shape.n_factors,
        ),
        factor_names=tuple(TradingPreset().shape.factor_names),
    ),
}


class CentroidRefreshError(RuntimeError):
    """Raised when a bundle cannot be used to refresh checkpoint centroids."""


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def action_spreads(mu: np.ndarray) -> list[float]:
    """Return max coordinate spread between actions for each category."""
    arr = np.asarray(mu, dtype=float)
    if arr.ndim != 3:
        raise CentroidRefreshError(f"Expected 3D centroid tensor, got shape {arr.shape}")
    spreads: list[float] = []
    for category_idx in range(arr.shape[0]):
        diffs = [
            float(np.max(np.abs(arr[category_idx, i] - arr[category_idx, j])))
            for i in range(arr.shape[1])
            for j in range(i + 1, arr.shape[1])
        ]
        spreads.append(max(diffs) if diffs else 0.0)
    return spreads


def collapsed_categories(mu: np.ndarray, threshold: float = 0.01) -> list[int]:
    return [idx for idx, spread in enumerate(action_spreads(mu)) if spread <= threshold]


def load_bundle_centroids(bundle_path: Path) -> tuple[np.ndarray, dict[str, Any]]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    checkpoints = bundle.get("centroid_checkpoints") or bundle.get("checkpoints") or []
    if not checkpoints:
        raise CentroidRefreshError(f"No centroid checkpoints in {bundle_path}")
    latest = checkpoints[-1]
    raw = latest.get("centroids", latest.get("centroid_values", None))
    if raw is None:
        raise CentroidRefreshError(f"Latest checkpoint in {bundle_path} has no centroids")
    mu = np.asarray(raw, dtype=float)
    return mu, latest


def validate_centroids(
    mu: np.ndarray,
    expected_shape: tuple[int, int, int],
    threshold: float = 0.01,
) -> None:
    if tuple(mu.shape) != tuple(expected_shape):
        raise CentroidRefreshError(f"Expected shape {expected_shape}, got {tuple(mu.shape)}")
    if not np.all(np.isfinite(mu)):
        raise CentroidRefreshError("Centroids contain NaN or infinite values")
    collapsed = collapsed_categories(mu, threshold=threshold)
    if collapsed:
        spreads = [round(v, 6) for v in action_spreads(mu)]
        raise CentroidRefreshError(
            f"Collapsed categories {collapsed}; spreads={spreads}; threshold={threshold}"
        )


def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except sqlite3.OperationalError:
        return 0


def latest_checkpoint(conn: sqlite3.Connection) -> dict[str, Any] | None:
    cols = _table_columns(conn, "centroid_checkpoints")
    if not cols:
        raise CentroidRefreshError("centroid_checkpoints table is missing")
    row = conn.execute("SELECT * FROM centroid_checkpoints ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        return None
    return dict(zip(cols, row))


def latest_checkpoint_centroids(conn: sqlite3.Connection) -> np.ndarray | None:
    row = latest_checkpoint(conn)
    if row is None or not row.get("centroids_json"):
        return None
    return np.asarray(json.loads(row["centroids_json"]), dtype=float)


def _insert_checkpoint(
    conn: sqlite3.Connection,
    domain: str,
    mu: np.ndarray,
    bundle_checkpoint: dict[str, Any],
    factor_names: Iterable[str],
) -> int:
    cols = _table_columns(conn, "centroid_checkpoints")
    now = time.time()
    now_iso = datetime.now(timezone.utc).isoformat()
    latest = latest_checkpoint(conn) or {}
    decisions_count = _table_count(conn, "decisions") or latest.get("decisions_count") or bundle_checkpoint.get("decisions_count") or 0
    centroid_json = json.dumps(mu.tolist())
    checkpoint_hash = hashlib.sha256(centroid_json.encode("utf-8")).hexdigest()
    metadata = {
        "source": "demo_centroid_refresh",
        "bundle_checkpoint_id": bundle_checkpoint.get("checkpoint_id"),
        "bundle_label": (bundle_checkpoint.get("metadata") or {}).get("label") or bundle_checkpoint.get("label"),
        "bundle_created_at": bundle_checkpoint.get("created_at"),
        "centroid_sha256": checkpoint_hash,
        "old_checkpoint_id": latest.get("checkpoint_id"),
        "old_row_id": latest.get("id"),
        "old_spreads": action_spreads(np.asarray(json.loads(latest["centroids_json"]), dtype=float)) if latest.get("centroids_json") else [],
        "new_spreads": action_spreads(mu),
    }
    values: dict[str, Any] = {
        "domain": domain,
        "decision_id": None,
        "category": None,
        "centroids_json": centroid_json,
        "decisions_count": int(decisions_count),
        "iks": float(bundle_checkpoint.get("iks", latest.get("iks") or 0.0)),
        "metadata_json": _json_dumps(metadata),
        "created_at": now,
        "decision_time_start": bundle_checkpoint.get("decision_time_start") or latest.get("decision_time_start"),
        "decision_time_end": bundle_checkpoint.get("decision_time_end") or latest.get("decision_time_end"),
        "checkpoint_time": now_iso,
        "checkpoint_id": f"{domain}:demo-refresh:{checkpoint_hash[:24]}:{int(now)}",
        "action": None,
        "verified_count": int(latest.get("verified_count") or 0),
        "shape_json": _json_dumps(list(mu.shape)),
        "factor_names_hash": _factor_names_hash(tuple(factor_names)),
        "quality_window_size": latest.get("quality_window_size"),
        "quality_verified_count": latest.get("quality_verified_count"),
        "quality_correct_count": latest.get("quality_correct_count"),
        "rolling_accuracy": latest.get("rolling_accuracy"),
        "quality_window_end": latest.get("quality_window_end"),
        "quality_policy_version": latest.get("quality_policy_version"),
    }
    insert_cols = [col for col in cols if col != "id" and col in values]
    placeholders = ", ".join("?" for _ in insert_cols)
    sql = f"INSERT INTO centroid_checkpoints ({', '.join(insert_cols)}) VALUES ({placeholders})"
    conn.execute(sql, [values[col] for col in insert_cols])
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def refresh_database_from_bundle(
    domain: str,
    db_path: Path,
    bundle_path: Path,
    expected_shape: tuple[int, int, int],
    factor_names: Iterable[str],
    *,
    dry_run: bool = False,
    verify_only: bool = False,
    threshold: float = 0.01,
) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    try:
        before_decisions = _table_count(conn, "decisions")
        before_l5 = _table_count(conn, "l5_centroids")
        current_mu = latest_checkpoint_centroids(conn)
        current_spreads = action_spreads(current_mu) if current_mu is not None else []
        if verify_only:
            return {
                "domain": domain,
                "mode": "verify-only",
                "db_path": str(db_path),
                "current_spreads": current_spreads,
                "collapsed": collapsed_categories(current_mu, threshold=threshold) if current_mu is not None else [],
                "decisions": before_decisions,
                "l5_rows": before_l5,
            }

        bundle_mu, checkpoint = load_bundle_centroids(bundle_path)
        validate_centroids(bundle_mu, expected_shape=expected_shape, threshold=threshold)
        new_spreads = action_spreads(bundle_mu)
        result = {
            "domain": domain,
            "mode": "dry-run" if dry_run else "refresh",
            "db_path": str(db_path),
            "bundle_path": str(bundle_path),
            "old_spreads": current_spreads,
            "new_spreads": new_spreads,
            "decisions_before": before_decisions,
            "l5_before": before_l5,
            "inserted_row_id": None,
        }
        if dry_run:
            return result

        row_id = _insert_checkpoint(conn, domain, bundle_mu, checkpoint, factor_names)
        conn.commit()
        after_decisions = _table_count(conn, "decisions")
        after_l5 = _table_count(conn, "l5_centroids")
        latest_mu = latest_checkpoint_centroids(conn)
        validate_centroids(latest_mu, expected_shape=expected_shape, threshold=threshold)
        if before_decisions != after_decisions:
            raise CentroidRefreshError(f"Decision count changed: {before_decisions} -> {after_decisions}")
        if before_l5 != after_l5:
            raise CentroidRefreshError(f"L5 row count changed: {before_l5} -> {after_l5}")
        result.update(
            inserted_row_id=row_id,
            verified_spreads=action_spreads(latest_mu),
            decisions_after=after_decisions,
            l5_after=after_l5,
        )
        return result
    finally:
        conn.close()


def _print_result(result: dict[str, Any]) -> None:
    print(f"=== {result['domain']} ({result['mode']}) ===")
    if result["mode"] == "verify-only":
        spreads = [round(float(v), 4) for v in result.get("current_spreads", [])]
        status = "DIFFERENTIATED" if not result.get("collapsed") else f"COLLAPSED {result['collapsed']}"
        print(f"current: {status} spreads={spreads}")
        print(f"decisions={result.get('decisions')} l5_rows={result.get('l5_rows')}")
        return
    print(f"old spreads: {[round(float(v), 4) for v in result['old_spreads']]}")
    print(f"new spreads: {[round(float(v), 4) for v in result['new_spreads']]}")
    if result.get("inserted_row_id"):
        print(f"inserted checkpoint row id: {result['inserted_row_id']}")
        print(f"verified spreads: {[round(float(v), 4) for v in result['verified_spreads']]}")
    else:
        print("no write performed")
    print(f"decisions: {result['decisions_before']} -> {result.get('decisions_after', result['decisions_before'])}")
    print(f"l5_rows: {result['l5_before']} -> {result.get('l5_after', result['l5_before'])}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", choices=sorted(DOMAIN_CONFIGS), action="append", help="Domain to refresh; defaults to purchasing and trading")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print planned changes without writing")
    parser.add_argument("--verify-only", action="store_true", help="Inspect latest database checkpoint without reading the bundle or writing")
    args = parser.parse_args()
    domains = args.domain or ["purchasing", "trading"]
    ok = True
    for domain in domains:
        cfg = DOMAIN_CONFIGS[domain]
        try:
            result = refresh_database_from_bundle(
                domain=cfg.name,
                db_path=cfg.db_path,
                bundle_path=cfg.bundle_path,
                expected_shape=cfg.expected_shape,
                factor_names=cfg.factor_names,
                dry_run=args.dry_run,
                verify_only=args.verify_only,
            )
            _print_result(result)
        except Exception as exc:
            ok = False
            print(f"=== {domain} ERROR ===")
            print(exc)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
