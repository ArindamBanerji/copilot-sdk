"""SQLite-backed, bounded cross-application fact delivery."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import threading
from typing import Any, Iterator
import uuid
MAX_SIGNALS = 1000
EVICTION_BATCH = 100
SIGNAL_TTL = timedelta(hours=24)


def shared_signal_path() -> str:
    """One path independent of each app's working directory; overridable."""
    default = Path(__file__).resolve().parents[2] / "data" / "shared_signals.db"
    return str(Path(os.environ.get("CROSS_SIGNAL_DB_PATH", str(default))).resolve())


class SQLiteSignalStore:
    """Atomic publication/eviction across processes sharing a SQLite file."""

    def __init__(self, db_path: str = ":memory:", *, profile: str | None = None) -> None:
        self.db_path = db_path
        self._lock = threading.RLock()
        self._memory = (
            sqlite3.connect(":memory:", check_same_thread=False)
            if db_path == ":memory:" else None
        )
        if self._memory is None:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS signals ("
                "seq INTEGER PRIMARY KEY AUTOINCREMENT, signal_id TEXT UNIQUE NOT NULL,"
                "created REAL NOT NULL, source TEXT NOT NULL, target TEXT, payload TEXT NOT NULL)"
            )
            db.execute("CREATE INDEX IF NOT EXISTS signals_created ON signals(created)")

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            db = self._memory if self._memory is not None else sqlite3.connect(self.db_path, timeout=30)
            try:
                with db:
                    yield db
            finally:
                if self._memory is None:
                    db.close()

    @staticmethod
    def _prune(db: sqlite3.Connection) -> None:
        cutoff = (datetime.now(timezone.utc) - SIGNAL_TTL).timestamp()
        db.execute("DELETE FROM signals WHERE created < ?", (cutoff,))

    def publish(self, signal: dict[str, Any]) -> str:
        record = dict(signal)
        stamp = record.get("timestamp") or datetime.now(timezone.utc).isoformat()
        parsed = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        record["timestamp"] = parsed.isoformat()
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            self._prune(db)
            if db.execute("SELECT COUNT(*) FROM signals").fetchone()[0] >= MAX_SIGNALS:
                db.execute(
                    "DELETE FROM signals WHERE seq IN "
                    "(SELECT seq FROM signals ORDER BY seq LIMIT ?)", (EVICTION_BATCH,)
                )
            # Retain the public ID format; unique constraint + transaction handle collisions.
            while True:
                signal_id = f"sig-{uuid.uuid4().hex[:8]}"
                record["signal_id"] = signal_id
                try:
                    db.execute(
                        "INSERT INTO signals(signal_id,created,source,target,payload) VALUES(?,?,?,?,?)",
                        (signal_id, parsed.timestamp(), record["source_copilot"],
                         record.get("target_copilot"), json.dumps(record)),
                    )
                    return signal_id
                except sqlite3.IntegrityError:
                    if db.execute("SELECT 1 FROM signals WHERE signal_id=?", (signal_id,)).fetchone() is None:
                        raise

    def page(
        self, limit: int = 50, offset: int = 0,
        source_copilot: str | None = None, target_copilot: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        if not 1 <= limit <= MAX_SIGNALS or offset < 0:
            raise ValueError("invalid pagination")
        clauses: list[str] = []
        params: list[str] = []
        if source_copilot is not None:
            clauses.append("source = ?")
            params.append(source_copilot)
        if target_copilot is not None:
            clauses.append("(target IS NULL OR target = ?)")
            params.append(target_copilot)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._connection() as db:
            self._prune(db)
            count = int(db.execute("SELECT COUNT(*) FROM signals" + where, params).fetchone()[0])
            rows = db.execute(
                "SELECT payload FROM signals" + where + " ORDER BY seq LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
            return [json.loads(row[0]) for row in rows], count

    def list(
        self, limit: int = 50, offset: int = 0, source_copilot: str | None = None,
        target_copilot: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.page(limit, offset, source_copilot, target_copilot)[0]

    def count(self) -> int:
        return self.page(limit=1)[1]

    def get(self, signal_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            self._prune(db)
            row = db.execute("SELECT payload FROM signals WHERE signal_id=?", (signal_id,)).fetchone()
            return json.loads(row[0]) if row else None

    def close(self) -> None:
        with self._lock:
            if self._memory is not None:
                self._memory.close()


class GraphSignalStore:
    """Signal view backed by the shared graph's domain decisions."""

    def __init__(self, graph_store: Any, domain: str) -> None:
        self.graph_store = graph_store
        self.domain = domain

    def _records(self) -> list[dict[str, Any]]:
        decisions = self.graph_store.get_all_decisions(domain=self.domain)
        records: list[dict[str, Any]] = []
        for decision in decisions:
            metadata = decision.get("metadata")
            metadata = metadata if isinstance(metadata, dict) else {}
            records.append({
                "signal_id": str(decision.get("decision_id") or decision.get("_age_id") or ""),
                "source_copilot": str(decision.get("domain") or self.domain),
                "target_copilot": metadata.get("target_copilot"),
                "signal_type": str(decision.get("category") or "decision"),
                "entity_id": str(metadata.get("entity_id") or decision.get("decision_id") or ""),
                "confidence": float(decision.get("confidence") or 0.0),
                "detail": str(decision.get("recommended_action") or ""),
                "timestamp": decision.get("created_at"),
            })
        return records

    def publish(self, signal: dict[str, Any]) -> str:
        metadata = {
            "entity_id": signal.get("entity_id"),
            "target_copilot": signal.get("target_copilot"),
            "signal_detail": signal.get("detail"),
            "signal_timestamp": signal.get("timestamp"),
        }
        return str(self.graph_store.write_decision(
            domain=self.domain,
            category=str(signal.get("signal_type") or "signal"),
            action=str(signal.get("detail") or "signal"),
            confidence=float(signal.get("confidence") or 0.0),
            factors={"entity_id": signal.get("entity_id")},
            metadata=metadata,
        ))

    def page(
        self, limit: int = 50, offset: int = 0,
        source_copilot: str | None = None, target_copilot: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = self._records()
        if source_copilot is not None:
            rows = [row for row in rows if row["source_copilot"] == source_copilot]
        if target_copilot is not None:
            rows = [row for row in rows if row.get("target_copilot") in {None, target_copilot}]
        return rows[offset:offset + limit], len(rows)

    def get(self, signal_id: str) -> dict[str, Any] | None:
        return next((row for row in self._records() if row["signal_id"] == signal_id), None)
