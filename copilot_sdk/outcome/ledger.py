"""SQLite persistence for canonical verified-outcome receipts."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path

from .models import VerifiedOutcome


class OutcomeLedger:
    """Thread-safe, restart-safe receipt ledger with stable-id deduplication."""

    def __init__(self, db_path: str | os.PathLike[str] = ":memory:") -> None:
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS verified_outcomes (
                receipt_id TEXT PRIMARY KEY,
                copilot TEXT NOT NULL,
                decision_id TEXT NOT NULL,
                category TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                receipt_json TEXT NOT NULL,
                created_at REAL NOT NULL DEFAULT (unixepoch('now'))
            )
            """
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_verified_outcomes_scope "
            "ON verified_outcomes(copilot, category, timestamp)"
        )
        self._connection.commit()

    def append(self, outcome: VerifiedOutcome) -> bool:
        """Append once; return whether this call inserted a new receipt."""
        receipt_id = outcome.receipt_id()
        with self._lock:
            cursor = self._connection.execute(
                """
                INSERT OR IGNORE INTO verified_outcomes
                    (receipt_id, copilot, decision_id, category, timestamp, receipt_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    outcome.copilot,
                    outcome.decision_id,
                    outcome.category,
                    outcome.timestamp,
                    json.dumps(outcome.to_dict(), sort_keys=True, separators=(",", ":")),
                ),
            )
            self._connection.commit()
            return cursor.rowcount == 1

    def get(self, receipt_id: str) -> VerifiedOutcome | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT receipt_json FROM verified_outcomes WHERE receipt_id = ?",
                (str(receipt_id),),
            ).fetchone()
        return None if row is None else VerifiedOutcome.from_dict(json.loads(str(row["receipt_json"])))

    def exists(self, receipt_id: str) -> bool:
        with self._lock:
            row = self._connection.execute(
                "SELECT 1 FROM verified_outcomes WHERE receipt_id = ? LIMIT 1",
                (str(receipt_id),),
            ).fetchone()
        return row is not None

    def count(self, copilot: str, category: str | None = None) -> int:
        query = "SELECT COUNT(*) FROM verified_outcomes WHERE copilot = ?"
        parameters: tuple[str, ...] = (str(copilot),)
        if category is not None:
            query += " AND category = ?"
            parameters += (str(category),)
        with self._lock:
            row = self._connection.execute(query, parameters).fetchone()
        return int(row[0]) if row is not None else 0

    def list_recent(self, copilot: str, limit: int = 100) -> list[VerifiedOutcome]:
        bounded_limit = max(1, min(int(limit), 10_000))
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT receipt_json FROM verified_outcomes
                WHERE copilot = ? ORDER BY timestamp DESC, created_at DESC LIMIT ?
                """,
                (str(copilot), bounded_limit),
            ).fetchall()
        return [VerifiedOutcome.from_dict(json.loads(str(row["receipt_json"]))) for row in rows]

    def close(self) -> None:
        with self._lock:
            self._connection.close()

