"""Domain-scoped SQLite GraphStore implementation."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


class SQLiteGraphStore:
    """SQLite-backed GraphStore that owns decisions, outcomes, and graph tables."""

    def __init__(self, db_path: str | Path, domain: str = "graph", decision_id_prefix: str = "") -> None:
        self.db_path = str(db_path)
        self.domain = str(domain)
        self._decision_id_prefix = str(decision_id_prefix or "")
        self._lock = threading.RLock()
        self._conn: sqlite3.Connection | None = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        if self.db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()
        self._ensure_migrations()

    @property
    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("SQLiteGraphStore is closed")
        return self._conn

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
                domain TEXT NOT NULL DEFAULT '',
                actual_action TEXT NOT NULL,
                actual_index INTEGER NOT NULL,
                is_correct INTEGER NOT NULL,
                verified_at REAL NOT NULL,
                context_json TEXT
            );

            CREATE TABLE IF NOT EXISTS centroid_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL DEFAULT '',
                decision_id TEXT,
                category TEXT,
                centroids_json TEXT NOT NULL,
                decisions_count INTEGER NOT NULL,
                iks REAL NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                decision_time_start TEXT,
                decision_time_end TEXT,
                checkpoint_time TEXT
            );

            CREATE TABLE IF NOT EXISTS evolution_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL DEFAULT '',
                event_type TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                variant_id TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rl_state (
                domain TEXT NOT NULL,
                key TEXT NOT NULL,
                data_json TEXT NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (domain, key)
            );

            CREATE TABLE IF NOT EXISTS decision_entity_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL DEFAULT '',
                decision_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS decisions_archive (
                archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                category TEXT NOT NULL,
                category_index INTEGER NOT NULL,
                factors_json TEXT NOT NULL,
                factor_vector_json TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                recommended_index INTEGER NOT NULL,
                confidence REAL NOT NULL,
                probabilities_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                actual_action TEXT,
                actual_index INTEGER,
                is_correct INTEGER,
                verified_at REAL,
                context_json TEXT,
                archived_at REAL NOT NULL,
                archive_reason TEXT NOT NULL DEFAULT 'retention_window'
            );

            """
        )
        self.connection.commit()

    def _ensure_migrations(self) -> None:
        self._ensure_outcome_columns()
        self._ensure_centroid_columns()
        for table in (
            "decisions",
            "outcomes",
            "centroid_checkpoints",
            "evolution_events",
            "decision_entity_edges",
            "decisions_archive",
        ):
            self._ensure_domain_column(table)
        self._create_indexes()
        self.connection.commit()

    def _create_indexes(self) -> None:
        self.connection.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_decisions_domain ON decisions(domain);
            CREATE INDEX IF NOT EXISTS idx_decisions_domain_category ON decisions(domain, category);
            CREATE INDEX IF NOT EXISTS idx_decisions_domain_created ON decisions(domain, created_at);
            CREATE INDEX IF NOT EXISTS idx_outcomes_domain ON outcomes(domain);
            CREATE INDEX IF NOT EXISTS idx_centroid_checkpoints_domain ON centroid_checkpoints(domain);
            CREATE INDEX IF NOT EXISTS idx_cc_checkpoint_time ON centroid_checkpoints(checkpoint_time);
            CREATE INDEX IF NOT EXISTS idx_cc_decision_time ON centroid_checkpoints(decision_time_start, decision_time_end);
            CREATE INDEX IF NOT EXISTS idx_cc_category ON centroid_checkpoints(category);
            CREATE INDEX IF NOT EXISTS idx_evolution_events_domain ON evolution_events(domain);
            CREATE INDEX IF NOT EXISTS idx_rl_state_domain ON rl_state(domain);
            CREATE INDEX IF NOT EXISTS idx_decision_entity_edges_domain ON decision_entity_edges(domain);
            CREATE INDEX IF NOT EXISTS idx_decisions_archive_domain ON decisions_archive(domain);
            """
        )

    def _columns(self, table: str) -> set[str]:
        return {
            row["name"]
            for row in self.connection.execute(f"PRAGMA table_info({table})").fetchall()
        }

    def _ensure_outcome_columns(self) -> None:
        columns = self._columns("outcomes")
        if "context_json" not in columns:
            self.connection.execute("ALTER TABLE outcomes ADD COLUMN context_json TEXT")

    def _ensure_centroid_columns(self) -> None:
        columns = self._columns("centroid_checkpoints")
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

    def _ensure_domain_column(self, table: str) -> None:
        columns = self._columns(table)
        if "domain" not in columns:
            self.connection.execute(
                f"ALTER TABLE {table} ADD COLUMN domain TEXT NOT NULL DEFAULT ''"
            )
        self.connection.execute(
            f"UPDATE {table} SET domain = ? WHERE domain IS NULL OR domain = ''",
            (self.domain,),
        )
        self.connection.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table}_domain ON {table}(domain)"
        )

    def write_decision(
        self,
        domain: str,
        category: str,
        action: str,
        confidence: float,
        factors: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        meta = dict(metadata or {})
        decision_id = str(meta.get("decision_id") or uuid.uuid4().hex[:12])
        if self._decision_id_prefix and not decision_id.startswith(self._decision_id_prefix):
            decision_id = f"{self._decision_id_prefix}{decision_id}"
        entity_id = str(meta.get("entity_id") or decision_id)
        if "entity_id" not in meta:
            meta["entity_id"] = entity_id
        if "decision_id" in meta:
            meta["decision_id"] = decision_id
        factor_names = list(factors)
        factor_vector = meta.get("factor_vector")
        if factor_vector is None:
            factor_vector = [float(factors[name]) for name in factor_names]
        recommended_index = int(meta.get("recommended_index", 0))
        category_index = int(meta.get("category_index", 0))
        probabilities = meta.get("probabilities")
        if probabilities is None:
            probabilities = [float(confidence)]
        stored_factors = {
            **dict(factors),
            "entity_id": entity_id,
            "metadata": meta,
        }

        with self._lock:
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
                    str(domain),
                    category,
                    category_index,
                    _to_json(stored_factors),
                    _to_json(factor_vector),
                    action,
                    recommended_index,
                    float(confidence),
                    _to_json(probabilities),
                    float(meta.get("created_at", time.time())),
                ),
            )
            self.connection.commit()
        return decision_id

    def write_outcome(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        meta = dict(metadata or {})
        row = self.connection.execute(
            "SELECT domain FROM decisions WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()
        if row is None:
            raise KeyError(decision_id)
        domain = str(row["domain"] or self.domain)
        with self._lock:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO outcomes (
                    decision_id, domain, actual_action, actual_index, is_correct,
                    verified_at, context_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    domain,
                    actual_action,
                    int(meta.get("actual_index", 0)),
                    1 if is_correct else 0,
                    float(meta.get("verified_at", time.time())),
                    _to_json(meta.get("context")) if meta.get("context") is not None else None,
                ),
            )
            self.connection.commit()

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM decisions WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()
        if row is None:
            return None
        return self._decision_from_row(row)

    def get_decisions(
        self,
        domain: str,
        category: str | None = None,
        limit: int = 400,
    ) -> list[dict[str, Any]]:
        clauses = ["domain = ?"]
        params: list[Any] = [str(domain)]
        if category is not None:
            clauses.append("category = ?")
            params.append(category)
        rows = self.connection.execute(
            f"""
            SELECT * FROM decisions
            WHERE {' AND '.join(clauses)}
            ORDER BY created_at ASC, decision_id ASC
            LIMIT ?
            """,
            (*params, max(int(limit), 0)),
        ).fetchall()
        return [self._decision_from_row(row) for row in rows]

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT * FROM decisions
            WHERE domain = ?
            ORDER BY created_at ASC, decision_id ASC
            """,
            (str(domain),),
        ).fetchall()
        return [self._decision_from_row(row) for row in rows]

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
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
            WHERE d.domain = ?
            ORDER BY d.created_at ASC, d.decision_id ASC
            """,
            (str(domain),),
        ).fetchall()
        return [self._verified_from_row(row) for row in rows]

    def count_decisions(self, domain: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM decisions WHERE domain = ?",
            (str(domain),),
        ).fetchone()
        return int(row["n"])

    def count_verified(self, domain: str) -> int:
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM outcomes o
            INNER JOIN decisions d ON d.decision_id = o.decision_id
            WHERE d.domain = ?
            """,
            (str(domain),),
        ).fetchone()
        return int(row["n"])

    def count_correct(self, domain: str) -> int:
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM outcomes o
            INNER JOIN decisions d ON d.decision_id = o.decision_id
            WHERE d.domain = ? AND o.is_correct = 1
            """,
            (str(domain),),
        ).fetchone()
        return int(row["n"])

    def save_centroids(
        self,
        domain: str,
        category: str,
        centroids: Any,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        meta = dict(metadata or {})
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO centroid_checkpoints (
                    domain, decision_id, category, centroids_json, decisions_count, iks,
                    metadata_json, created_at, decision_time_start, decision_time_end,
                    checkpoint_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(domain),
                    kwargs.get("decision_id"),
                    category,
                    _to_json(np.asarray(centroids, dtype=float)),
                    self.count_decisions(str(domain)),
                    float(meta.get("iks", 0.0)),
                    _to_json(meta),
                    time.time(),
                    kwargs.get("decision_time_start"),
                    kwargs.get("decision_time_end"),
                    kwargs.get("checkpoint_time") or _utc_iso_now(),
                ),
            )
            self.connection.commit()

    def load_latest_centroids(self, domain: str) -> Any | None:
        row = self.connection.execute(
            """
            SELECT centroids_json FROM centroid_checkpoints
            WHERE domain = ?
            ORDER BY id DESC LIMIT 1
            """,
            (str(domain),),
        ).fetchone()
        if row is None:
            return None
        return np.asarray(_from_json(row["centroids_json"]), dtype=np.float64)

    def save_rl_state(self, key: str, data: dict) -> None:
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO rl_state (domain, key, data_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(domain, key) DO UPDATE SET
                    data_json = excluded.data_json,
                    updated_at = excluded.updated_at
                """,
                (
                    self.domain,
                    str(key),
                    _to_json(dict(data)),
                    time.time(),
                ),
            )
            self.connection.commit()

    def load_rl_state(self, key: str) -> dict | None:
        row = self.connection.execute(
            """
            SELECT data_json FROM rl_state
            WHERE domain = ? AND key = ?
            """,
            (self.domain, str(key)),
        ).fetchone()
        if row is None:
            return None
        return dict(_from_json(row["data_json"]))

    def get_centroid_checkpoints(
        self,
        domain: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        limit = kwargs.pop("limit", 50)
        where, params = _checkpoint_where_clause(domain=str(domain), **kwargs)
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
        return [self._checkpoint_from_row(row) for row in rows]

    def save_evolution_event(
        self,
        domain: str,
        event_type: str,
        rule_name: str = "",
        variant_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO evolution_events (
                    domain, event_type, rule_name, variant_id, metadata
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(domain),
                    event_type,
                    rule_name,
                    variant_id,
                    json.dumps(metadata or {}, sort_keys=True),
                ),
            )
            self.connection.commit()

    def get_evolution_events(
        self,
        domain: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        rule_name = kwargs.get("rule_name")
        limit = kwargs.get("limit", 100)
        clauses = ["domain = ?"]
        params: list[Any] = [str(domain)]
        if rule_name is not None:
            clauses.append("rule_name = ?")
            params.append(rule_name)
        rows = self.connection.execute(
            f"""
            SELECT domain, event_type, rule_name, variant_id, metadata, timestamp
            FROM evolution_events
            WHERE {' AND '.join(clauses)}
            ORDER BY id DESC
            LIMIT ?
            """,
            (*params, max(int(limit), 0)),
        ).fetchall()
        rows = list(reversed(rows))
        return [
            {
                "domain": row["domain"],
                "event_type": row["event_type"],
                "rule_name": row["rule_name"],
                "variant_id": row["variant_id"],
                "metadata": _from_json(row["metadata"]) if row["metadata"] else {},
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

    def link_decision_to_entity(
        self,
        decision_id: str,
        entity_id: str,
        edge_type: str = "DECIDED_ON",
    ) -> None:
        decision = self.get_decision(decision_id)
        domain = str((decision or {}).get("domain") or self.domain)
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO decision_entity_edges (
                    domain, decision_id, entity_id, edge_type, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (domain, decision_id, entity_id, edge_type, time.time()),
            )
            self.connection.commit()

    def get_decision_links(self, decision_id: str | None = None) -> list[dict[str, Any]]:
        if decision_id is None:
            rows = self.connection.execute(
                """
                SELECT decision_id, entity_id, edge_type, created_at
                FROM decision_entity_edges
                WHERE domain = ?
                ORDER BY id ASC
                """,
                (self.domain,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT decision_id, entity_id, edge_type, created_at
                FROM decision_entity_edges
                WHERE domain = ? AND decision_id = ?
                ORDER BY id ASC
                """,
                (self.domain, decision_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def count_categories_with_n(self, domain: str, n: int) -> int:
        rows = self.connection.execute(
            """
            SELECT d.category, COUNT(*) AS count
            FROM decisions d
            INNER JOIN outcomes o ON d.decision_id = o.decision_id
            WHERE d.domain = ?
            GROUP BY d.category
            HAVING count >= ?
            """,
            (str(domain), int(n)),
        ).fetchall()
        return len(rows)

    def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int:
        keep_recent = max(int(keep_recent), 0)
        rows = self.connection.execute(
            """
            SELECT decision_id FROM decisions
            WHERE domain = ?
            ORDER BY created_at DESC, decision_id DESC
            """,
            (str(domain),),
        ).fetchall()
        if len(rows) <= keep_recent:
            return 0
        archive_ids = [row["decision_id"] for row in rows[keep_recent:]]
        archived_at = time.time()
        with self._lock:
            for decision_id in archive_ids:
                self.connection.execute(
                    """
                    INSERT INTO decisions_archive (
                        decision_id, domain, category, category_index, factors_json,
                        factor_vector_json, recommended_action, recommended_index,
                        confidence, probabilities_json, created_at, actual_action,
                        actual_index, is_correct, verified_at, context_json, archived_at
                    )
                    SELECT
                        d.decision_id, d.domain, d.category, d.category_index, d.factors_json,
                        d.factor_vector_json, d.recommended_action, d.recommended_index,
                        d.confidence, d.probabilities_json, d.created_at, o.actual_action,
                        o.actual_index, o.is_correct, o.verified_at, o.context_json, ?
                    FROM decisions d
                    LEFT JOIN outcomes o ON d.decision_id = o.decision_id
                    WHERE d.decision_id = ? AND d.domain = ?
                    """,
                    (archived_at, decision_id, str(domain)),
                )
            placeholders = ",".join("?" for _ in archive_ids)
            self.connection.execute(
                f"DELETE FROM outcomes WHERE decision_id IN ({placeholders})",
                archive_ids,
            )
            self.connection.execute(
                f"DELETE FROM decision_entity_edges WHERE decision_id IN ({placeholders})",
                archive_ids,
            )
            self.connection.execute(
                f"DELETE FROM decisions WHERE decision_id IN ({placeholders}) AND domain = ?",
                (*archive_ids, str(domain)),
            )
            self.connection.commit()
        return len(archive_ids)

    def count_archived(self, domain: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM decisions_archive WHERE domain = ?",
            (str(domain),),
        ).fetchone()
        return int(row["n"])

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _decision_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        factors = _from_json(row["factors_json"])
        raw_metadata = factors.get("metadata") if isinstance(factors, dict) else None
        metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
        entity_id = str(
            (factors.get("entity_id") if isinstance(factors, dict) else None)
            or metadata.get("entity_id")
            or row["decision_id"]
        )
        return {
            "decision_id": row["decision_id"],
            "domain": row["domain"],
            "entity_id": entity_id,
            "category": row["category"],
            "category_index": int(row["category_index"]),
            "factors": factors,
            "factor_vector": _from_json(row["factor_vector_json"]),
            "recommended_action": row["recommended_action"],
            "recommended_index": int(row["recommended_index"]),
            "confidence": float(row["confidence"]),
            "probabilities": _from_json(row["probabilities_json"]),
            "metadata": metadata,
            "created_at": float(row["created_at"]),
        }

    def _verified_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = self._decision_from_row(row)
        context_val = _from_json(row["context_json"]) if row["context_json"] else {}
        data.update(
            {
                "actual_action": row["actual_action"],
                "actual_index": int(row["actual_index"]),
                "is_correct": bool(row["is_correct"]),
                "verified_at": float(row["verified_at"]),
                "context": context_val,
                "outcome_metadata": {"context": context_val},
            }
        )
        return data

    def _checkpoint_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": int(row["id"]),
            "domain": row["domain"],
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


def _checkpoint_where_clause(
    *,
    domain: str,
    checkpoint_time_start: str | None = None,
    checkpoint_time_end: str | None = None,
    decision_time_start: str | None = None,
    decision_time_end: str | None = None,
    category: str | None = None,
) -> tuple[str, list[Any]]:
    clauses: list[str] = ["domain = ?"]
    params: list[Any] = [domain]
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
    return "WHERE " + " AND ".join(clauses), params
