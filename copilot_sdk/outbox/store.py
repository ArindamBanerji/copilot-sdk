"""SQLite-backed outbox store."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from .models import EVENT_TYPES, OutboxEvent


class OutboxStore:
    """SQLite-backed outbox table stored separately from GraphStore."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outbox (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    processed INTEGER DEFAULT 0,
                    processed_at REAL,
                    error TEXT
                )
                """
            )
            self._conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_outbox_unprocessed
                    ON outbox (processed, created_at)
                """
            )
            self._conn.commit()

    def append(self, event_type: str, domain: str, payload: dict[str, Any]) -> int:
        """Write an event and return its auto-increment event id."""

        if event_type not in EVENT_TYPES:
            raise ValueError(f"Unknown event_type: {event_type}")
        created_at = time.time()
        payload_json = json.dumps(payload, sort_keys=True)
        with self._lock:
            cursor = self._conn.execute(
                """
                INSERT INTO outbox (
                    event_type, domain, payload, created_at, processed
                )
                VALUES (?, ?, ?, ?, 0)
                """,
                (event_type, domain, payload_json, created_at),
            )
            self._conn.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("outbox insert did not produce an event_id")
            return int(cursor.lastrowid)

    def get_unprocessed(self, limit: int = 100) -> list[OutboxEvent]:
        """Return oldest-first unprocessed events."""

        with self._lock:
            rows = self._conn.execute(
                """
                SELECT event_id, event_type, domain, payload, created_at,
                       processed, processed_at, error
                FROM outbox
                WHERE processed = 0
                ORDER BY created_at ASC, event_id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def mark_processed(self, event_id: int) -> None:
        """Mark an event as successfully processed."""

        with self._lock:
            self._conn.execute(
                """
                UPDATE outbox
                SET processed = 1, processed_at = ?, error = NULL
                WHERE event_id = ?
                """,
                (time.time(), event_id),
            )
            self._conn.commit()

    def mark_dead_letter(self, event_id: int, error: str) -> None:
        """Mark an event as processed with a dead-letter error."""

        with self._lock:
            self._conn.execute(
                """
                UPDATE outbox
                SET processed = 1, processed_at = ?, error = ?
                WHERE event_id = ?
                """,
                (time.time(), error, event_id),
            )
            self._conn.commit()

    def get_dead_letters(self, limit: int = 50) -> list[OutboxEvent]:
        """Return dead-lettered events, newest first."""

        with self._lock:
            rows = self._conn.execute(
                """
                SELECT event_id, event_type, domain, payload, created_at,
                       processed, processed_at, error
                FROM outbox
                WHERE processed = 1 AND error IS NOT NULL
                ORDER BY processed_at DESC, event_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def replay_from(self, offset: int = 0) -> list[OutboxEvent]:
        """Return all events with event_id greater than or equal to offset."""

        with self._lock:
            rows = self._conn.execute(
                """
                SELECT event_id, event_type, domain, payload, created_at,
                       processed, processed_at, error
                FROM outbox
                WHERE event_id >= ?
                ORDER BY event_id ASC
                """,
                (offset,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def count_unprocessed(self) -> int:
        """Return the count of pending events."""

        with self._lock:
            row = self._conn.execute(
                "SELECT count(*) AS n FROM outbox WHERE processed = 0"
            ).fetchone()
        return int(row["n"])

    def count_total(self) -> int:
        """Return the total event count."""

        with self._lock:
            row = self._conn.execute("SELECT count(*) AS n FROM outbox").fetchone()
        return int(row["n"])

    def clear(self) -> None:
        """Remove all outbox events."""

        with self._lock:
            self._conn.execute("DELETE FROM outbox")
            self._conn.commit()

    def close(self) -> None:
        """Close the underlying SQLite connection."""

        with self._lock:
            self._conn.close()

    @staticmethod
    def _from_row(row: sqlite3.Row) -> OutboxEvent:
        payload = json.loads(row["payload"])
        return OutboxEvent(
            event_id=int(row["event_id"]),
            event_type=str(row["event_type"]),
            domain=str(row["domain"]),
            payload=dict(payload),
            created_at=float(row["created_at"]),
            processed=bool(row["processed"]),
            processed_at=(
                float(row["processed_at"]) if row["processed_at"] is not None else None
            ),
            error=str(row["error"]) if row["error"] is not None else None,
        )
