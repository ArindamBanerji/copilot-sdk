"""Lightweight local outbox for graph-persistence failures."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import tempfile
import time
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

CURRENT_PAYLOAD_SCHEMA = 1
_LOG = logging.getLogger(__name__)


def _json_default(value: Any) -> Any:
    """Serialize common numeric values used by scorer artifact payloads."""
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return tolist()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class PersistenceOutbox:
    """Persist failed artifact writes locally until the graph is available."""

    MAX_RETRIES = 10

    def __init__(self, domain: str, db_path: Path | None = None) -> None:
        if not domain:
            raise ValueError("domain is required")
        self.domain = str(domain)
        configured = os.environ.get("CI_PERSISTENCE_OUTBOX_PATH")
        self.db_path = Path(
            db_path
            or configured
            or Path.home() / ".ci-platform" / self.domain / "outbox.db"
        )
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            self.db_path = (
                Path(tempfile.gettempdir()) / ".ci-platform" / self.domain / "outbox.db"
            )
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS failed_artifacts (
                    id INTEGER PRIMARY KEY,
                    decision_id TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    error TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending',
                    schema_version INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            existing_cols = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(failed_artifacts)"
                ).fetchall()
            }
            if "schema_version" not in existing_cols:
                connection.execute(
                    "ALTER TABLE failed_artifacts "
                    "ADD COLUMN schema_version INTEGER NOT NULL DEFAULT 1"
                )
            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_failed_artifact_key
                ON failed_artifacts(decision_id, domain, artifact_type)
                """
            )
            connection.execute(
                """
                UPDATE failed_artifacts
                SET status='abandoned'
                WHERE domain = ?
                  AND status IN ('pending', 'failed')
                  AND retry_count >= ?
                """,
                (self.domain, self.MAX_RETRIES),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def record_failure(
        self,
        decision_id: str,
        artifact_type: str,
        payload: dict[str, Any],
        error: str,
    ) -> None:
        try:
            serialized = json.dumps(payload, default=_json_default, sort_keys=True)
        except TypeError:
            _LOG.error(
                "outbox could not serialize payload domain=%s decision_id=%s type=%s",
                self.domain,
                decision_id,
                artifact_type,
                exc_info=True,
            )
            raise
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO failed_artifacts
                    (decision_id, domain, artifact_type, payload, error, created_at, schema_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_id, domain, artifact_type)
                DO UPDATE SET payload=excluded.payload, error=excluded.error,
                    retry_count=failed_artifacts.retry_count + 1, status='pending',
                    schema_version=excluded.schema_version
                """,
                (
                    str(decision_id),
                    self.domain,
                    str(artifact_type),
                    serialized,
                    str(error),
                    str(time.time()),
                    CURRENT_PAYLOAD_SCHEMA,
                ),
            )

    def drain(self, graph_store: Any) -> tuple[int, int]:
        """Replay pending artifacts, returning ``(succeeded, failed)``."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, decision_id, artifact_type, payload, retry_count, schema_version
                FROM failed_artifacts
                WHERE domain = ? AND status IN ('pending', 'failed')
                  AND retry_count < ?
                ORDER BY
                  CASE artifact_type
                    WHEN 'decision' THEN 0
                    WHEN 'evidence_receipt' THEN 1
                    WHEN 'centroid_checkpoint' THEN 2
                    WHEN 'fingerprint' THEN 3
                    WHEN 'evolution' THEN 4
                    WHEN 'conservation' THEN 5
                    ELSE 6
                  END,
                  id
                """,
                (self.domain, self.MAX_RETRIES),
            ).fetchall()

        succeeded = 0
        failed = 0
        for row in rows:
            try:
                self._replay(graph_store, row["decision_id"], row["artifact_type"], json.loads(row["payload"]))
            except Exception as exc:
                failed += 1
                schema_stale = int(row["schema_version"]) < CURRENT_PAYLOAD_SCHEMA
                incompatible = isinstance(exc, TypeError) or schema_stale
                new_status = (
                    "abandoned"
                    if incompatible or int(row["retry_count"]) + 1 >= self.MAX_RETRIES
                    else "failed"
                )
                with self._connection() as connection:
                    connection.execute(
                        """
                        UPDATE failed_artifacts
                        SET status=?, retry_count=?, error=?
                        WHERE id=?
                        """,
                        (
                            new_status,
                            int(row["retry_count"]) + 1,
                            str(exc),
                            int(row["id"]),
                        ),
                    )
                if new_status == "abandoned":
                    _LOG.warning(
                        "outbox abandoned artifact domain=%s decision_id=%s type=%s error=%s",
                        self.domain,
                        row["decision_id"],
                        row["artifact_type"],
                        str(exc),
                    )
            else:
                succeeded += 1
                with self._connection() as connection:
                    connection.execute(
                        """
                        UPDATE failed_artifacts
                        SET status='replayed', error=''
                        WHERE id=?
                        """,
                        (int(row["id"]),),
                    )
        return succeeded, failed

    def _replay(
        self,
        graph_store: Any,
        decision_id: str,
        artifact_type: str,
        payload: dict[str, Any],
    ) -> None:
        if artifact_type == "conservation":
            graph_store.write_conservation_status(**payload)
        elif artifact_type == "fingerprint":
            graph_store.write_fingerprint(**payload)
        elif artifact_type == "evidence_receipt":
            graph_store.append_evidence_receipt(**payload)
        elif artifact_type == "centroid_checkpoint":
            graph_store.write_centroid_checkpoint(**payload)
        elif artifact_type == "decision":
            replay_payload = dict(payload)
            governed = bool(replay_payload.pop("_governed", False))
            if governed:
                graph_store.write_governed_decision(**replay_payload)
            else:
                replayed_decision_id = str(replay_payload.pop("decision_id", decision_id))
                metadata = dict(replay_payload.get("metadata") or {})
                metadata["decision_id"] = replayed_decision_id
                replay_payload["metadata"] = metadata
                graph_store.write_decision(**replay_payload)
        elif artifact_type == "evolution":
            if hasattr(graph_store, "write_evolution_event"):
                graph_store.write_evolution_event(**payload)
            else:
                payload.pop("event_id", None)
                graph_store.save_evolution_event(**payload)
        else:
            raise ValueError(f"unsupported artifact type: {artifact_type}")

    def clear(self) -> None:
        """Remove pending or failed records for this domain without deleting the DB."""
        with self._connection() as connection:
            connection.execute(
                """
                DELETE FROM failed_artifacts
                WHERE domain = ? AND status IN ('pending', 'failed')
                """,
                (self.domain,),
            )

    def pending_count(self) -> int:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT count(*) AS pending_total FROM failed_artifacts
                WHERE domain = ?
                  AND status IN ('pending', 'failed')
                  AND retry_count < ?
                """,
                (self.domain, self.MAX_RETRIES),
            ).fetchone()
        return int(row["pending_total"] if row is not None else 0)

    def count_abandoned(self) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT count(*) AS n FROM failed_artifacts "
                "WHERE domain = ? AND status = 'abandoned'",
                (self.domain,),
            ).fetchone()
        return int(row["n"] if row is not None else 0)

    def export_abandoned(self) -> list[dict[str, Any]]:
        """Return abandoned artifacts for recovery and inspection."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT decision_id, artifact_type, payload, error, retry_count "
                "FROM failed_artifacts WHERE domain = ? AND status = 'abandoned' "
                "ORDER BY id",
                (self.domain,),
            ).fetchall()
        return [
            {
                "decision_id": row["decision_id"],
                "artifact_type": row["artifact_type"],
                "payload": json.loads(row["payload"]),
                "error": row["error"],
                "retry_count": int(row["retry_count"]),
            }
            for row in rows
        ]

