"""Lightweight local outbox for graph-persistence failures."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> Any:
    """Serialize common numeric values used by scorer artifact payloads."""
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return tolist()
    if isinstance(value, Path):
        return str(value)
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
                    status TEXT NOT NULL DEFAULT 'pending'
                )
                """
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
                  AND (
                      retry_count >= ?
                      OR error LIKE '%required positional arguments%'
                  )
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
        serialized = json.dumps(payload, default=_json_default, sort_keys=True)
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO failed_artifacts
                    (decision_id, domain, artifact_type, payload, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_id, domain, artifact_type)
                DO UPDATE SET payload=excluded.payload, error=excluded.error,
                    retry_count=failed_artifacts.retry_count + 1, status='pending'
                """,
                (
                    str(decision_id),
                    self.domain,
                    str(artifact_type),
                    serialized,
                    str(error),
                    str(time.time()),
                ),
            )

    def drain(self, graph_store: Any) -> tuple[int, int]:
        """Replay pending artifacts, returning ``(succeeded, failed)``."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, decision_id, artifact_type, payload, retry_count
                FROM failed_artifacts
                WHERE domain = ? AND status IN ('pending', 'failed')
                  AND error NOT LIKE '%required positional arguments%'
                  AND retry_count < ?
                ORDER BY id
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
                with self._connection() as connection:
                    connection.execute(
                        """
                        UPDATE failed_artifacts
                        SET status=?, retry_count=?, error=?
                        WHERE id=?
                        """,
                        (
                            "abandoned"
                            if int(row["retry_count"]) + 1 >= self.MAX_RETRIES
                            else "failed",
                            int(row["retry_count"]) + 1,
                            str(exc),
                            int(row["id"]),
                        ),
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
        else:
            raise ValueError(f"unsupported artifact type: {artifact_type}")

    def pending_count(self) -> int:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT count(*) AS pending_total FROM failed_artifacts
                WHERE domain = ?
                  AND status IN ('pending', 'failed')
                  AND error NOT LIKE '%required positional arguments%'
                  AND retry_count < ?
                """,
                (self.domain, self.MAX_RETRIES),
            ).fetchone()
        return int(row["pending_total"] if row is not None else 0)

