"""Live Trading shadow-scorer validation using SQLite source data.

The script reads verified Trading decisions from an existing SQLite database,
copies that database into temporary primary/shadow stores, scores each
decision through ShadowScorer, prints the report, and removes the temporary
copies. The source database is never used as a write target.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.migrate.shadow_scorer import ShadowScorer
from copilot_sdk.scoring.presets.trading import TradingPreset


def _default_source_candidates() -> list[Path]:
    return [
        Path.home() / ".ci-platform" / "trading" / "trading.db",
        Path("apps") / "trading" / "backend" / "data" / "trading.db",
    ]


def _open_readable_store(path: Path) -> SQLiteGraphStore | None:
    try:
        return SQLiteGraphStore(path, domain="trading")
    except Exception:
        return None


def _resolve_source(explicit_source: str | None) -> Path:
    candidates = [Path(explicit_source).expanduser()] if explicit_source else _default_source_candidates()
    for candidate in candidates:
        if not candidate.exists():
            continue
        store = _open_readable_store(candidate)
        if store is not None:
            store.close()
            return candidate
    checked = ", ".join(str(path) for path in candidates)
    raise SystemExit(f"No readable Trading SQLite DB found. Checked: {checked}")


def _copy_db_with_sidecars(source: Path, destination: Path) -> None:
    shutil.copy2(source, destination)
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{source}{suffix}")
        if sidecar.exists():
            shutil.copy2(sidecar, Path(f"{destination}{suffix}"))


def _filtered_factors(decision: dict[str, Any], recognized: set[str]) -> dict[str, float]:
    raw = decision.get("factors") or {}
    if not isinstance(raw, dict):
        return {}
    return {
        key: float(value)
        for key, value in raw.items()
        if key in recognized and isinstance(value, (int, float))
    }


def _run(source: Path, limit: int | None) -> dict[str, Any]:
    preset = TradingPreset()
    recognized_factors = set(preset.shape.factor_names)
    source_store = SQLiteGraphStore(source, domain="trading")
    try:
        verified = source_store.get_verified_decisions("trading")
    finally:
        source_store.close()

    if limit is not None:
        verified = verified[:limit]

    with tempfile.TemporaryDirectory(prefix="trading_shadow_") as temp_dir:
        temp_path = Path(temp_dir)
        primary_db = temp_path / "primary_trading.db"
        shadow_db = temp_path / "shadow_trading.db"
        _copy_db_with_sidecars(source, primary_db)
        _copy_db_with_sidecars(source, shadow_db)

        primary_store = SQLiteGraphStore(primary_db, domain="trading", decision_id_prefix="TRD-P-")
        shadow_store = SQLiteGraphStore(shadow_db, domain="trading", decision_id_prefix="TRD-S-")
        try:
            shadow = ShadowScorer.from_preset(
                "trading",
                primary_store=primary_store,
                shadow_store=shadow_store,
                proven_threshold=max(len(verified), 1),
            )
            skipped = 0
            for decision in verified:
                category = str(decision.get("category") or "")
                factors = _filtered_factors(decision, recognized_factors)
                if not category or not factors:
                    skipped += 1
                    continue
                shadow.score(factors=factors, category=category)

            report = shadow.report()
            report.update(
                {
                    "source_db": str(source),
                    "verified_decisions": len(verified),
                    "scored_decisions": report["total_comparisons"],
                    "skipped_decisions": skipped,
                    "recognized_factor_names": list(preset.shape.factor_names),
                }
            )
            return report
        finally:
            primary_store.close()
            shadow_store.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Trading SQLite shadow scorer validation.")
    parser.add_argument("--source", help="Path to Trading SQLite DB. Defaults to home DB, then repo demo DB.")
    parser.add_argument("--limit", type=int, default=None, help="Optional max verified decisions to score.")
    args = parser.parse_args()

    source = _resolve_source(args.source)
    report = _run(source, args.limit)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
