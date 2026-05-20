"""SQLite persistence for CompoundingScorer decisions and checkpoints."""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _to_json(value: Any) -> str:
    return json.dumps(value, default=_json_default, sort_keys=True)


def _from_json(value: str) -> Any:
    return json.loads(value)


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DecisionStore:
    """SQLite store for decisions, outcomes, and centroid checkpoints."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS decisions (
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

            CREATE TABLE IF NOT EXISTS outcomes (
                decision_id TEXT PRIMARY KEY REFERENCES decisions(decision_id),
                actual_action TEXT NOT NULL,
                actual_index INTEGER NOT NULL,
                is_correct INTEGER NOT NULL,
                verified_at REAL NOT NULL,
                context_json TEXT
            );

            CREATE TABLE IF NOT EXISTS centroid_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT,
                category TEXT,
                centroids_json TEXT NOT NULL,
                decisions_count INTEGER NOT NULL,
                iks REAL NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL
            );
            """
        )
        self._ensure_outcome_columns()
        self._ensure_centroid_columns()
        self.connection.commit()

    def _ensure_outcome_columns(self) -> None:
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(outcomes)").fetchall()
        }
        if "context_json" not in columns:
            self.connection.execute("ALTER TABLE outcomes ADD COLUMN context_json TEXT")

    def _ensure_centroid_columns(self) -> None:
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(centroid_checkpoints)").fetchall()
        }
        if "decision_id" not in columns:
            self.connection.execute("ALTER TABLE centroid_checkpoints ADD COLUMN decision_id TEXT")
        if "category" not in columns:
            self.connection.execute("ALTER TABLE centroid_checkpoints ADD COLUMN category TEXT")
        if "metadata_json" not in columns:
            self.connection.execute(
                "ALTER TABLE centroid_checkpoints ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'"
            )
        if "decision_time_start" not in columns:
            self.connection.execute(
                "ALTER TABLE centroid_checkpoints ADD COLUMN decision_time_start TEXT"
            )
        if "decision_time_end" not in columns:
            self.connection.execute(
                "ALTER TABLE centroid_checkpoints ADD COLUMN decision_time_end TEXT"
            )
        if "checkpoint_time" not in columns:
            self.connection.execute(
                "ALTER TABLE centroid_checkpoints ADD COLUMN checkpoint_time TEXT"
            )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_cc_checkpoint_time "
            "ON centroid_checkpoints(checkpoint_time)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_cc_decision_time "
            "ON centroid_checkpoints(decision_time_start, decision_time_end)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_cc_category "
            "ON centroid_checkpoints(category)"
        )

    def save_decision(
        self,
        *,
        decision_id: str,
        domain: str,
        category: str,
        category_index: int,
        factors: dict[str, Any],
        factor_vector: list[float] | np.ndarray,
        recommended_action: str,
        recommended_index: int,
        confidence: float,
        probabilities: list[float] | np.ndarray,
        created_at: float | None = None,
    ) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO decisions (
                decision_id, domain, category, category_index, factors_json,
                factor_vector_json, recommended_action, recommended_index,
                confidence, probabilities_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                domain,
                category,
                int(category_index),
                _to_json(factors),
                _to_json(factor_vector),
                recommended_action,
                int(recommended_index),
                float(confidence),
                _to_json(probabilities),
                float(created_at if created_at is not None else time.time()),
            ),
        )
        self.connection.commit()

    def save_outcome(
        self,
        *,
        decision_id: str,
        actual_action: str,
        actual_index: int,
        is_correct: bool,
        verified_at: float | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO outcomes (
                decision_id, actual_action, actual_index, is_correct, verified_at,
                context_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                actual_action,
                int(actual_index),
                1 if is_correct else 0,
                float(verified_at if verified_at is not None else time.time()),
                _to_json(context) if context is not None else None,
            ),
        )
        self.connection.commit()

    def save_centroids(
        self,
        centroids: np.ndarray,
        iks: float = 0.0,
        *,
        decision_id: str | None = None,
        category: str | None = None,
        metadata: dict[str, Any] | None = None,
        decision_time_start: str | None = None,
        decision_time_end: str | None = None,
        checkpoint_time: str | None = None,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO centroid_checkpoints (
                decision_id, category, centroids_json, decisions_count, iks,
                metadata_json, created_at, decision_time_start, decision_time_end,
                checkpoint_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                category,
                _to_json(np.asarray(centroids, dtype=float)),
                self._count_decisions(),
                float(iks),
                _to_json(metadata or {}),
                time.time(),
                decision_time_start,
                decision_time_end,
                checkpoint_time or _utc_iso_now(),
            ),
        )
        self.connection.commit()

    def load_latest_centroids(self) -> Optional[np.ndarray]:
        row = self.connection.execute(
            """
            SELECT centroids_json FROM centroid_checkpoints
            ORDER BY id DESC LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return np.asarray(_from_json(row["centroids_json"]), dtype=np.float64)

    def get_decision(self, decision_id: str) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT * FROM decisions WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()
        if row is None:
            raise KeyError(decision_id)
        return self._decision_from_row(row)

    def get_verified_decisions(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT
                d.*,
                o.actual_action,
                o.actual_index,
                o.is_correct,
                o.verified_at,
                o.context_json
            FROM decisions d
            INNER JOIN outcomes o ON d.decision_id = o.decision_id
            ORDER BY d.created_at ASC, d.decision_id ASC
            """
        ).fetchall()
        return [self._verified_from_row(row) for row in rows]

    def get_centroid_checkpoints(
        self,
        limit: int | None = None,
        *,
        checkpoint_time_start: str | None = None,
        checkpoint_time_end: str | None = None,
        decision_time_start: str | None = None,
        decision_time_end: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        where, params = _checkpoint_where_clause(
            checkpoint_time_start=checkpoint_time_start,
            checkpoint_time_end=checkpoint_time_end,
            decision_time_start=decision_time_start,
            decision_time_end=decision_time_end,
            category=category,
        )
        if limit is None:
            rows = self.connection.execute(
                f"""
                SELECT * FROM centroid_checkpoints
                {where}
                ORDER BY id ASC
                """,
                params,
            ).fetchall()
        else:
            rows = self.connection.execute(
                f"""
                SELECT * FROM centroid_checkpoints
                {where}
                ORDER BY id DESC
                LIMIT ?
                """,
                (*params, max(int(limit), 0)),
            ).fetchall()
            rows = list(reversed(rows))
        return [
            {
                "id": int(row["id"]),
                "decision_id": row["decision_id"],
                "category": row["category"],
                "centroids": np.asarray(_from_json(row["centroids_json"]), dtype=np.float64),
                "decisions_count": int(row["decisions_count"]),
                "iks": float(row["iks"]),
                "metadata": _from_json(row["metadata_json"]),
                "created_at": float(row["created_at"]),
                "decision_time_start": row["decision_time_start"],
                "decision_time_end": row["decision_time_end"],
                "checkpoint_time": row["checkpoint_time"],
            }
            for row in rows
        ]

    def get_all_decisions(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM decisions ORDER BY created_at ASC, decision_id ASC"
        ).fetchall()
        return [self._decision_from_row(row) for row in rows]

    def count_verified(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS n FROM outcomes").fetchone()
        return int(row["n"])

    def count_correct(self) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM outcomes WHERE is_correct = 1"
        ).fetchone()
        return int(row["n"])

    def count_categories_with_n(self, n: int) -> int:
        rows = self.connection.execute(
            """
            SELECT d.category, COUNT(*) AS count
            FROM decisions d
            INNER JOIN outcomes o ON d.decision_id = o.decision_id
            GROUP BY d.category
            HAVING count >= ?
            """,
            (int(n),),
        ).fetchall()
        return len(rows)

    def close(self) -> None:
        self.connection.close()

    def _count_decisions(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS n FROM decisions").fetchone()
        return int(row["n"])

    def _decision_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "decision_id": row["decision_id"],
            "domain": row["domain"],
            "category": row["category"],
            "category_index": int(row["category_index"]),
            "factors": _from_json(row["factors_json"]),
            "factor_vector": _from_json(row["factor_vector_json"]),
            "recommended_action": row["recommended_action"],
            "recommended_index": int(row["recommended_index"]),
            "confidence": float(row["confidence"]),
            "probabilities": _from_json(row["probabilities_json"]),
            "created_at": float(row["created_at"]),
        }

    def _verified_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = self._decision_from_row(row)
        data.update(
            {
                "actual_action": row["actual_action"],
                "actual_index": int(row["actual_index"]),
                "is_correct": bool(row["is_correct"]),
                "verified_at": float(row["verified_at"]),
                "context": _from_json(row["context_json"]) if row["context_json"] else {},
            }
        )
        return data


def _checkpoint_where_clause(
    *,
    checkpoint_time_start: str | None,
    checkpoint_time_end: str | None,
    decision_time_start: str | None,
    decision_time_end: str | None,
    category: str | None,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if category is not None:
        clauses.append("category = ?")
        params.append(category)
    if checkpoint_time_start is not None:
        clauses.append("checkpoint_time IS NOT NULL")
        clauses.append("checkpoint_time >= ?")
        params.append(checkpoint_time_start)
    if checkpoint_time_end is not None:
        clauses.append("checkpoint_time IS NOT NULL")
        clauses.append("checkpoint_time <= ?")
        params.append(checkpoint_time_end)
    if decision_time_start is not None:
        clauses.append("decision_time_start IS NOT NULL")
        clauses.append("decision_time_start >= ?")
        params.append(decision_time_start)
    if decision_time_end is not None:
        clauses.append("decision_time_end IS NOT NULL")
        clauses.append("decision_time_end <= ?")
        params.append(decision_time_end)
    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params
