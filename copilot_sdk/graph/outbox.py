"""Durable storage for secondary graph writes that need replay."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


class DurableOutbox:
    """SQLite-backed durable outbox for failed secondary writes."""

    def __init__(self, path: str) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS secondary_outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    domain TEXT,
                    payload TEXT NOT NULL,
                    error TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at REAL NOT NULL,
                    replayed_at REAL
                )
                """
            )
            self._connection.commit()

    @staticmethod
    def _json_default(value: object) -> object:
        """Serialize common numeric containers without degrading replay data."""
        to_list = getattr(value, "tolist", None)
        if callable(to_list):
            return to_list()
        if isinstance(value, Path):
            return str(value)
        raise TypeError(f"outbox payload is not JSON serializable: {type(value).__name__}")

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": int(row["id"]),
            "operation": str(row["operation"]),
            "domain": row["domain"],
            "payload": json.loads(str(row["payload"])),
            "error": row["error"],
            "status": str(row["status"]),
            "created_at": float(row["created_at"]),
            "replayed_at": None if row["replayed_at"] is None else float(row["replayed_at"]),
        }

    def append(self, operation: str, domain: str | None, payload: dict[str, Any], error: str) -> int:
        encoded_payload = json.dumps(payload, default=self._json_default, sort_keys=True)
        with self._lock:
            cursor = self._connection.execute(
                """
                INSERT INTO secondary_outbox (operation, domain, payload, error, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (operation, domain, encoded_payload, error, time.time()),
            )
            self._connection.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite did not return an outbox row ID")
            return int(cursor.lastrowid)

    def pending_count(self) -> int:
        with self._lock:
            row = self._connection.execute(
                "SELECT count(*) AS count FROM secondary_outbox WHERE status = 'pending'"
            ).fetchone()
        return int(row["count"] if row is not None else 0)

    def get_pending(self, limit: int = 100) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT id, operation, domain, payload, error, status, created_at, replayed_at
                FROM secondary_outbox
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def mark_replayed(self, row_id: int) -> None:
        with self._lock:
            self._connection.execute(
                "UPDATE secondary_outbox SET status = 'replayed', replayed_at = ? WHERE id = ?",
                (time.time(), row_id),
            )
            self._connection.commit()

    def mark_failed(self, row_id: int, error: str) -> None:
        with self._lock:
            self._connection.execute(
                "UPDATE secondary_outbox SET status = 'failed', error = ? WHERE id = ?",
                (error, row_id),
            )
            self._connection.commit()

    def purge_replayed(self, before: float) -> int:
        with self._lock:
            cursor = self._connection.execute(
                "DELETE FROM secondary_outbox WHERE status = 'replayed' AND replayed_at < ?",
                (before,),
            )
            self._connection.commit()
            return int(cursor.rowcount)

    def close(self) -> None:
        with self._lock:
            self._connection.close()
