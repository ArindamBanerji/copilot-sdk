"""Domain-scoped SQLite GraphStore implementation."""

from __future__ import annotations

import json
import hashlib
import sqlite3
import threading
import time
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import numpy as np

from copilot_sdk.graph.enrichment import (
    EnrichmentSourceSet,
    EntityEnrichmentReceipt,
    EntityEnrichmentRecord,
    ProvenancedValue,
    is_protected_metric_name,
    utc_iso_now,
)

SQLITE_BUSY_TIMEOUT_MS = 5000
SQLITE_LOCK_RETRY_DELAYS = (0.05, 0.1, 0.25, 0.5)
_WRITE_LOCKS_LOCK = threading.Lock()
_WRITE_LOCKS: dict[str, threading.RLock] = {}


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


def _normalize_centroid_vector(centroid_vector: Any) -> list[float]:
    if isinstance(centroid_vector, (str, bytes, bytearray)):
        raise TypeError("centroid_vector must be a non-string iterable of numeric values")
    if isinstance(centroid_vector, Mapping):
        raise TypeError("centroid_vector must be a non-mapping iterable of numeric values")
    if not isinstance(centroid_vector, Iterable):
        raise TypeError("centroid_vector must be an iterable of numeric values")
    try:
        return [float(value) for value in centroid_vector]
    except (TypeError, ValueError) as error:
        raise TypeError("centroid_vector must contain only numeric values") from error


def _normalize_dk_weight_tensor(weight_tensor: Any) -> list[list[float]]:
    if isinstance(weight_tensor, (str, bytes, bytearray)):
        raise TypeError("weight_tensor must be a non-string 2D numeric iterable")
    if isinstance(weight_tensor, Mapping):
        raise TypeError("weight_tensor must be a non-mapping 2D numeric iterable")
    if not isinstance(weight_tensor, Iterable):
        raise TypeError("weight_tensor must be a 2D numeric iterable")

    rows: list[list[float]] = []
    expected_width: int | None = None
    for row in weight_tensor:
        if isinstance(row, (str, bytes, bytearray)):
            raise TypeError("weight_tensor rows must be non-string numeric iterables")
        if isinstance(row, Mapping):
            raise TypeError("weight_tensor rows must be non-mapping numeric iterables")
        if not isinstance(row, Iterable):
            raise TypeError("weight_tensor must be 2D, not a 1D numeric iterable")
        try:
            normalized_row = [float(value) for value in row]
        except (TypeError, ValueError) as error:
            raise TypeError("weight_tensor must contain only numeric values") from error
        if not normalized_row:
            raise ValueError("weight_tensor rows must be non-empty")
        if expected_width is None:
            expected_width = len(normalized_row)
        elif len(normalized_row) != expected_width:
            raise ValueError("weight_tensor rows must be rectangular")
        rows.append(normalized_row)

    if not rows:
        raise ValueError("weight_tensor must be non-empty")
    return rows


def _normalize_n_decisions_used(n_decisions_used: Any) -> int:
    try:
        value = int(n_decisions_used)
    except (TypeError, ValueError) as error:
        raise TypeError("n_decisions_used must be an integer") from error
    if value < 0:
        raise ValueError("n_decisions_used must be non-negative")
    return value


def _normalize_computed_at(computed_at: Any) -> float:
    try:
        return float(computed_at)
    except (TypeError, ValueError) as error:
        raise TypeError("computed_at must be numeric") from error


_DK_WELFORD_VECTOR_KEYS = (
    "confirmed_mean",
    "confirmed_m2",
    "overridden_mean",
    "overridden_m2",
    "all_mean",
    "all_m2",
)


def _normalize_optional_nonnegative_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be an integer")
    try:
        normalized = int(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{field_name} must be an integer") from error
    if normalized < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _normalize_dk_welford_vector(vector: Any, field_name: str) -> list[float]:
    if isinstance(vector, (str, bytes, bytearray)):
        raise TypeError(f"{field_name} must be a non-string 1D numeric iterable")
    if isinstance(vector, Mapping):
        raise TypeError(f"{field_name} must be a non-mapping 1D numeric iterable")
    if not isinstance(vector, Iterable):
        raise TypeError(f"{field_name} must be a 1D numeric iterable")
    try:
        normalized = [float(value) for value in vector]
    except (TypeError, ValueError) as error:
        raise TypeError(f"{field_name} must contain only numeric values") from error
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _normalize_dk_welford_state(
    welford_state: Any,
    *,
    n_decisions_used: int,
) -> dict[str, object] | None:
    if welford_state is None:
        return None
    if not isinstance(welford_state, Mapping):
        raise TypeError("welford_state must be a mapping")
    missing = [key for key in (*_DK_WELFORD_VECTOR_KEYS, "n_all") if key not in welford_state]
    if missing:
        raise ValueError(f"welford_state missing required fields: {', '.join(missing)}")

    normalized: dict[str, object] = {}
    expected_width: int | None = None
    for key in _DK_WELFORD_VECTOR_KEYS:
        vector = _normalize_dk_welford_vector(welford_state[key], key)
        if expected_width is None:
            expected_width = len(vector)
        elif len(vector) != expected_width:
            raise ValueError("welford_state vectors must have equal length")
        normalized[key] = vector

    n_all = _normalize_optional_nonnegative_int(welford_state["n_all"], "n_all")
    if n_all is None:
        raise TypeError("n_all must be an integer")
    if n_all != n_decisions_used:
        raise ValueError("welford_state n_all must equal n_decisions_used")
    normalized["n_all"] = n_all
    return normalized


def _decode_dk_welford_state(
    row: Mapping[str, Any],
    *,
    n_decisions_used: int,
) -> dict[str, object] | None:
    json_fields = {key: f"{key}_json" for key in _DK_WELFORD_VECTOR_KEYS}
    if not any(row.get(field) is not None for field in json_fields.values()):
        return None
    state: dict[str, object] = {}
    for key, field in json_fields.items():
        raw_value = row.get(field)
        if raw_value is None:
            raise ValueError("stored DK Welford state is partial")
        if not isinstance(raw_value, str):
            raise TypeError(f"{field} must be a JSON string")
        state[key] = json.loads(raw_value)
    state["n_all"] = n_decisions_used
    return _normalize_dk_welford_state(state, n_decisions_used=n_decisions_used)


_CONSERVATION_STATUSES = {"GREEN", "AMBER", "RED"}


def _normalize_domain(domain: Any) -> str:
    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("domain must be a non-empty string")
    return domain


def _normalize_conservation_status(status: Any, field_name: str = "status") -> str:
    if not isinstance(status, str) or status not in _CONSERVATION_STATUSES:
        raise ValueError(f"{field_name} must be one of GREEN, AMBER, RED")
    return status


def _normalize_optional_conservation_status(old_status: Any) -> str | None:
    if old_status is None:
        return None
    return _normalize_conservation_status(old_status, field_name="old_status")


def _normalize_bounded_float(value: Any, field_name: str) -> float:
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{field_name} must be numeric") from error
    if normalized < 0.0 or normalized > 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")
    return normalized


def _normalize_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{field_name} must be numeric") from error


def _normalize_positive_float(value: Any, field_name: str) -> float:
    normalized = _normalize_float(value, field_name)
    if normalized <= 0.0:
        raise ValueError(f"{field_name} must be greater than 0")
    return normalized


def _normalize_non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be an integer")
    try:
        normalized = int(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{field_name} must be an integer") from error
    if normalized < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _normalize_complacency_flag(complacency_flag: Any) -> str:
    if not isinstance(complacency_flag, str) or complacency_flag not in {"true", "false"}:
        raise ValueError("complacency_flag must be exactly 'true' or 'false'")
    return complacency_flag


def _normalize_optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    return value


def _normalize_conservation_state_values(
    *,
    domain: Any,
    status: Any,
    alpha: Any,
    q: Any,
    V: Any,
    theta_min: Any,
    product: Any,
    categories_total: Any,
    categories_with_data: Any,
    baseline_product: Any,
    relative_threshold: Any,
    complacency_flag: Any,
    caused_by_decision_id: Any,
    old_status: Any,
) -> dict[str, object]:
    categories_total_value = _normalize_non_negative_int(
        categories_total, "categories_total"
    )
    categories_with_data_value = _normalize_non_negative_int(
        categories_with_data, "categories_with_data"
    )
    if categories_with_data_value > categories_total_value:
        raise ValueError("categories_with_data must be less than or equal to categories_total")
    return {
        "domain": _normalize_domain(domain),
        "status": _normalize_conservation_status(status),
        "alpha": _normalize_bounded_float(alpha, "alpha"),
        "q": _normalize_bounded_float(q, "q"),
        "V": _normalize_non_negative_int(V, "V"),
        "theta_min": _normalize_positive_float(theta_min, "theta_min"),
        "product": _normalize_float(product, "product"),
        "categories_total": categories_total_value,
        "categories_with_data": categories_with_data_value,
        "baseline_product": _normalize_float(baseline_product, "baseline_product"),
        "relative_threshold": _normalize_float(relative_threshold, "relative_threshold"),
        "complacency_flag": _normalize_complacency_flag(complacency_flag),
        "caused_by_decision_id": _normalize_optional_string(
            caused_by_decision_id, "caused_by_decision_id"
        ),
        "old_status": _normalize_optional_conservation_status(old_status),
    }


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _receipt_payload_hash(
    receipt_intent_id: str,
    domain: str,
    decision_id: str,
    canonical_payload: dict[str, Any],
    actor: str,
    source_route: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    payload = {
        "receipt_intent_id": str(receipt_intent_id),
        "domain": str(domain),
        "decision_id": str(decision_id),
        "canonical_payload": dict(canonical_payload),
        "actor": actor,
        "source_route": source_route,
        "metadata": dict(metadata or {}),
    }
    encoded = json.dumps(
        payload,
        default=_json_default,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _write_lock_key(db_path: str) -> str:
    if db_path == ":memory:":
        return f"memory:{id(db_path)}"
    return str(Path(db_path).expanduser().resolve())


def _write_lock_for(db_path: str) -> threading.RLock:
    key = _write_lock_key(db_path)
    with _WRITE_LOCKS_LOCK:
        lock = _WRITE_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _WRITE_LOCKS[key] = lock
        return lock


def _is_transient_sqlite_lock(error: sqlite3.OperationalError) -> bool:
    message = str(error).lower()
    return "database is locked" in message or "database is busy" in message


class SQLiteGraphStore:
    """SQLite-backed GraphStore that owns decisions, outcomes, and graph tables."""

    def __init__(self, db_path: str | Path, domain: str = "graph", decision_id_prefix: str = "") -> None:
        self.db_path = str(db_path)
        self.domain = str(domain)
        self._decision_id_prefix = str(decision_id_prefix or "")
        self._lock = threading.RLock()
        self._write_lock = _write_lock_for(self.db_path)
        self._conn: sqlite3.Connection | None = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=SQLITE_BUSY_TIMEOUT_MS / 1000,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        with self._write_lock:
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
                status TEXT NOT NULL DEFAULT 'pending',
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
                checkpoint_id TEXT UNIQUE,
                domain TEXT NOT NULL DEFAULT '',
                decision_id TEXT,
                category TEXT,
                action TEXT,
                centroids_json TEXT NOT NULL,
                decisions_count INTEGER NOT NULL,
                verified_count INTEGER NOT NULL DEFAULT 0,
                iks REAL NOT NULL,
                shape_json TEXT NOT NULL DEFAULT '[]',
                factor_names_hash TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                decision_time_start TEXT,
                decision_time_end TEXT,
                checkpoint_time TEXT
            );

             CREATE TABLE IF NOT EXISTS l5_centroids (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 domain TEXT NOT NULL,
                 category TEXT NOT NULL,
                action TEXT NOT NULL,
                vector_json TEXT NOT NULL,
                delta_norm REAL NOT NULL,
                caused_by_decision_id TEXT,
                updated_at TEXT NOT NULL,
                 UNIQUE(domain, category, action)
             );

             CREATE TABLE IF NOT EXISTS l5_dk_weights (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 domain TEXT NOT NULL,
                 weight_json TEXT NOT NULL,
                 n_decisions_used INTEGER NOT NULL,
                  computed_at REAL NOT NULL,
                  supersedes_id INTEGER,
                  is_current INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL,
                  confirmed_mean_json TEXT,
                  confirmed_m2_json TEXT,
                  overridden_mean_json TEXT,
                  overridden_m2_json TEXT,
                  all_mean_json TEXT,
                  all_m2_json TEXT,
                  n_confirmed INTEGER,
                  n_overridden INTEGER,
                  entity_group TEXT
              );

             CREATE TABLE IF NOT EXISTS l5_conservation_state (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 domain TEXT NOT NULL UNIQUE,
                 status TEXT NOT NULL,
                 alpha REAL NOT NULL,
                 q REAL NOT NULL,
                 V INTEGER NOT NULL,
                 theta_min REAL NOT NULL,
                 product REAL NOT NULL,
                 categories_total INTEGER NOT NULL,
                 categories_with_data INTEGER NOT NULL,
                 baseline_product REAL NOT NULL,
                 relative_threshold REAL NOT NULL,
                 complacency_flag TEXT NOT NULL DEFAULT 'false',
                 caused_by_decision_id TEXT,
                 old_status TEXT,
                 updated_at TEXT NOT NULL
             );

            CREATE TABLE IF NOT EXISTS evolution_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE,
                domain TEXT NOT NULL DEFAULT '',
                event_type TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                variant_id TEXT NOT NULL,
                source_copilot TEXT,
                source_rule TEXT,
                metric REAL,
                shadow_batch_size INTEGER,
                min_shadow_batches INTEGER,
                metadata_json TEXT,
                created_at REAL,
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

             CREATE TABLE IF NOT EXISTS outbox (
                 outbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 domain TEXT NOT NULL,
                 operation_type TEXT NOT NULL,
                 target_key TEXT NOT NULL,
                 payload_json TEXT NOT NULL,
                 payload_hash TEXT NOT NULL,
                 causal_decision_id TEXT,
                 status TEXT NOT NULL DEFAULT 'pending',
                 attempt_count INTEGER NOT NULL DEFAULT 0,
                 last_error_redacted TEXT,
                 schema_version INTEGER NOT NULL DEFAULT 1,
                 created_at TEXT NOT NULL,
                 updated_at TEXT NOT NULL,
                 replayed_at TEXT,
                 UNIQUE(domain, operation_type, target_key, payload_hash)
             );

             CREATE TABLE IF NOT EXISTS outbox_quarantine (
                 quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 domain TEXT NOT NULL,
                 outbox_id INTEGER,
                 operation_type TEXT NOT NULL,
                 target_key TEXT NOT NULL,
                 existing_payload_hash TEXT NOT NULL,
                 new_payload_hash TEXT NOT NULL,
                 new_payload_json TEXT NOT NULL,
                 reason TEXT NOT NULL,
                 quarantined_at TEXT NOT NULL,
                 resolved_at TEXT,
                 resolution TEXT
             );

             CREATE TABLE IF NOT EXISTS decision_entity_edges (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 domain TEXT NOT NULL DEFAULT '',
                decision_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                entity_type TEXT NOT NULL DEFAULT '',
                edge_type TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS observations (
                observation_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                category TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                confidence REAL NOT NULL,
                source_route TEXT NOT NULL,
                scorer_version TEXT NOT NULL,
                factor_schema_version TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS observation_entity_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                observation_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                edge_type TEXT NOT NULL DEFAULT 'ABOUT',
                created_at REAL NOT NULL,
                UNIQUE(observation_id, entity_id, edge_type)
            );

            CREATE TABLE IF NOT EXISTS observation_factor_vectors (
                observation_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                dimension INTEGER NOT NULL,
                factor_names TEXT NOT NULL,
                factor_vector_json TEXT NOT NULL,
                factor_names_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evidence_receipts (
                receipt_intent_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                decision_id TEXT NOT NULL,
                chain_index INTEGER NOT NULL,
                previous_hash TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                actor TEXT NOT NULL,
                source_route TEXT NOT NULL,
                canonical_payload_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                PRIMARY KEY (domain, receipt_intent_id),
                UNIQUE(domain, chain_index)
            );

            CREATE TABLE IF NOT EXISTS conservation_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                V INTEGER NOT NULL,
                q REAL NOT NULL,
                alpha REAL NOT NULL,
                theta_min REAL NOT NULL,
                verified_count INTEGER NOT NULL,
                correct_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                computed_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS fingerprints (
                fingerprint_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                factor_names_json TEXT NOT NULL,
                factor_stats_json TEXT NOT NULL,
                skipped_incompatible INTEGER NOT NULL,
                window INTEGER NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
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

            CREATE TABLE IF NOT EXISTS entity_enrichments (
                domain TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                namespace TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value_json TEXT NOT NULL,
                provenance_json TEXT NOT NULL,
                source_set_json TEXT NOT NULL,
                computed_at TEXT NOT NULL,
                idempotency_key TEXT,
                PRIMARY KEY (domain, entity_type, entity_id, namespace, metric_name)
            );

            """
        )
        self.connection.commit()

    def _ensure_migrations(self) -> None:
        self._ensure_decision_status_column()
        self._ensure_outcome_columns()
        self._ensure_centroid_columns()
        self._ensure_l5_dk_weight_columns()
        self._ensure_evolution_columns()
        self._ensure_entity_edge_columns()
        for table in (
            "decisions",
            "outcomes",
            "centroid_checkpoints",
            "evolution_events",
            "decision_entity_edges",
            "observations",
            "observation_entity_edges",
            "observation_factor_vectors",
            "evidence_receipts",
            "conservation_snapshots",
            "fingerprints",
            "decisions_archive",
            "entity_enrichments",
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
            CREATE INDEX IF NOT EXISTS idx_decisions_domain_status ON decisions(domain, status);
            CREATE INDEX IF NOT EXISTS idx_outcomes_domain ON outcomes(domain);
            CREATE INDEX IF NOT EXISTS idx_centroid_checkpoints_domain ON centroid_checkpoints(domain);
            CREATE INDEX IF NOT EXISTS idx_cc_checkpoint_time ON centroid_checkpoints(checkpoint_time);
            CREATE INDEX IF NOT EXISTS idx_cc_decision_time ON centroid_checkpoints(decision_time_start, decision_time_end);
            CREATE INDEX IF NOT EXISTS idx_cc_category ON centroid_checkpoints(category);
             CREATE INDEX IF NOT EXISTS idx_evolution_events_domain ON evolution_events(domain);
             CREATE INDEX IF NOT EXISTS idx_rl_state_domain ON rl_state(domain);
             CREATE INDEX IF NOT EXISTS idx_outbox_domain_status ON outbox(domain, status);
             CREATE INDEX IF NOT EXISTS idx_outbox_identity ON outbox(domain, operation_type, target_key);
             CREATE INDEX IF NOT EXISTS idx_outbox_quarantine_domain_identity ON outbox_quarantine(domain, operation_type, target_key);
             CREATE INDEX IF NOT EXISTS idx_decision_entity_edges_domain ON decision_entity_edges(domain);
            CREATE INDEX IF NOT EXISTS idx_observations_domain ON observations(domain);
            CREATE INDEX IF NOT EXISTS idx_observation_entity_edges_domain ON observation_entity_edges(domain);
            CREATE INDEX IF NOT EXISTS idx_observation_factor_vectors_domain ON observation_factor_vectors(domain);
            CREATE INDEX IF NOT EXISTS idx_evidence_receipts_domain ON evidence_receipts(domain);
            CREATE INDEX IF NOT EXISTS idx_conservation_domain ON conservation_snapshots(domain, computed_at);
             CREATE INDEX IF NOT EXISTS idx_fingerprints_domain_created ON fingerprints(domain, created_at);
             CREATE INDEX IF NOT EXISTS idx_centroid_checkpoints_domain_category_action_created ON centroid_checkpoints(domain, category, action, created_at);
             CREATE INDEX IF NOT EXISTS idx_l5_centroids_domain ON l5_centroids(domain);
             CREATE UNIQUE INDEX IF NOT EXISTS idx_l5_dk_weights_current_domain ON l5_dk_weights(domain) WHERE is_current = 1;
             CREATE INDEX IF NOT EXISTS idx_decisions_archive_domain ON decisions_archive(domain);
             CREATE INDEX IF NOT EXISTS idx_entity_enrichments_lookup ON entity_enrichments(domain, entity_type, entity_id, namespace);
             CREATE INDEX IF NOT EXISTS idx_entity_enrichments_namespace ON entity_enrichments(domain, entity_type, namespace);
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

    def _ensure_decision_status_column(self) -> None:
        columns = self._columns("decisions")
        if "status" not in columns:
            self.connection.execute(
                "ALTER TABLE decisions ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'"
            )
        self.connection.execute(
            """
            UPDATE decisions
            SET status = 'confirmed'
            WHERE decision_id IN (
                SELECT decision_id FROM outcomes WHERE is_correct = 1
            )
            """
        )
        self.connection.execute(
            """
            UPDATE decisions
            SET status = 'overridden'
            WHERE decision_id IN (
                SELECT decision_id FROM outcomes WHERE is_correct = 0
            )
            """
        )
        self.connection.execute(
            """
            UPDATE decisions
            SET status = 'pending'
            WHERE status IS NULL OR status NOT IN ('pending', 'confirmed', 'overridden')
            """
        )

    def _ensure_centroid_columns(self) -> None:
        columns = self._columns("centroid_checkpoints")
        if "checkpoint_id" not in columns:
            self.connection.execute("ALTER TABLE centroid_checkpoints ADD COLUMN checkpoint_id TEXT")
            self.connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_cc_checkpoint_id "
                "ON centroid_checkpoints(checkpoint_id)"
            )
        if "decision_id" not in columns:
            self.connection.execute("ALTER TABLE centroid_checkpoints ADD COLUMN decision_id TEXT")
        if "category" not in columns:
            self.connection.execute("ALTER TABLE centroid_checkpoints ADD COLUMN category TEXT")
        if "action" not in columns:
            self.connection.execute("ALTER TABLE centroid_checkpoints ADD COLUMN action TEXT")
        if "metadata_json" not in columns:
            self.connection.execute(
                "ALTER TABLE centroid_checkpoints ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'"
            )
        if "verified_count" not in columns:
            self.connection.execute(
                "ALTER TABLE centroid_checkpoints ADD COLUMN verified_count INTEGER NOT NULL DEFAULT 0"
            )
        if "shape_json" not in columns:
            self.connection.execute(
                "ALTER TABLE centroid_checkpoints ADD COLUMN shape_json TEXT NOT NULL DEFAULT '[]'"
            )
        if "factor_names_hash" not in columns:
            self.connection.execute(
                "ALTER TABLE centroid_checkpoints ADD COLUMN factor_names_hash TEXT NOT NULL DEFAULT ''"
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
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_cc_checkpoint_id "
            "ON centroid_checkpoints(checkpoint_id)"
        )

    def _ensure_l5_dk_weight_columns(self) -> None:
        columns = self._columns("l5_dk_weights")
        additions = {
            "confirmed_mean_json": "TEXT",
            "confirmed_m2_json": "TEXT",
            "overridden_mean_json": "TEXT",
            "overridden_m2_json": "TEXT",
            "all_mean_json": "TEXT",
            "all_m2_json": "TEXT",
            "n_confirmed": "INTEGER",
            "n_overridden": "INTEGER",
            "entity_group": "TEXT",
        }
        for column, column_type in additions.items():
            if column not in columns:
                self.connection.execute(
                    f"ALTER TABLE l5_dk_weights ADD COLUMN {column} {column_type}"
                )

    def _ensure_evolution_columns(self) -> None:
        columns = self._columns("evolution_events")
        if "event_id" not in columns:
            self.connection.execute("ALTER TABLE evolution_events ADD COLUMN event_id TEXT")
        if "source_copilot" not in columns:
            self.connection.execute("ALTER TABLE evolution_events ADD COLUMN source_copilot TEXT")
        if "source_rule" not in columns:
            self.connection.execute("ALTER TABLE evolution_events ADD COLUMN source_rule TEXT")
        if "metric" not in columns:
            self.connection.execute("ALTER TABLE evolution_events ADD COLUMN metric REAL")
        if "shadow_batch_size" not in columns:
            self.connection.execute("ALTER TABLE evolution_events ADD COLUMN shadow_batch_size INTEGER")
        if "min_shadow_batches" not in columns:
            self.connection.execute("ALTER TABLE evolution_events ADD COLUMN min_shadow_batches INTEGER")
        if "metadata_json" not in columns:
            self.connection.execute("ALTER TABLE evolution_events ADD COLUMN metadata_json TEXT")
        if "created_at" not in columns:
            self.connection.execute("ALTER TABLE evolution_events ADD COLUMN created_at REAL")
        self.connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_evolution_events_event_id "
            "ON evolution_events(event_id)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_evolution_events_domain_created "
            "ON evolution_events(domain, created_at)"
        )

    def _ensure_entity_edge_columns(self) -> None:
        columns = self._columns("decision_entity_edges")
        if "entity_type" not in columns:
            self.connection.execute(
                "ALTER TABLE decision_entity_edges ADD COLUMN entity_type TEXT NOT NULL DEFAULT ''"
            )
            self.connection.execute(
                "UPDATE decision_entity_edges SET entity_type = edge_type "
                "WHERE entity_type IS NULL OR entity_type = ''"
            )
        self.connection.execute(
            """
            DELETE FROM decision_entity_edges
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM decision_entity_edges
                GROUP BY decision_id, entity_id, domain
            )
            """
        )
        self.connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_decision_entity_unique "
            "ON decision_entity_edges(decision_id, entity_id, domain)"
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

    def _run_write(self, operation: Any) -> Any:
        delays = (0.0, *SQLITE_LOCK_RETRY_DELAYS)
        for attempt, delay in enumerate(delays):
            if delay:
                time.sleep(delay)
            try:
                with self._write_lock:
                    with self._lock:
                        result = operation()
                        self.connection.commit()
                        return result
            except sqlite3.OperationalError as error:
                self.connection.rollback()
                if not _is_transient_sqlite_lock(error) or attempt == len(delays) - 1:
                    raise
            except Exception:
                self.connection.rollback()
                raise
        raise RuntimeError("SQLite write retry loop exited unexpectedly")

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
        decision_id = str(meta.get("decision_id") or self.generate_decision_id(domain))
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

        def persist() -> str:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO decisions (
                    decision_id, domain, category, category_index, factors_json,
                    factor_vector_json, recommended_action, recommended_index,
                    confidence, probabilities_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    "pending",
                    float(meta.get("created_at", time.time())),
                ),
            )
            return decision_id

        return str(self._run_write(persist))

    def generate_decision_id(self, domain: str) -> str:
        """Return a unique ID using this store's configured prefix policy."""
        _ = domain
        raw_id = uuid.uuid4().hex[:12]
        if self._decision_id_prefix:
            return f"{self._decision_id_prefix}{raw_id}"
        return raw_id

    def write_governed_decision(
        self,
        decision_id: str,
        domain: str,
        category: str,
        category_index: int,
        recommended_action: str,
        recommended_index: int,
        confidence: float,
        probabilities: list[float],
        factor_vector: list[float],
        factor_names: list[str],
        source: str = "score",
        scorer_version: str = "",
        preset_version: str = "",
        factor_schema_version: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        meta = dict(metadata or {})
        decision_id = str(decision_id)
        domain = str(domain)
        meta["decision_id"] = decision_id
        meta.setdefault("entity_id", decision_id)
        meta["source"] = source
        meta["scorer_version"] = scorer_version
        meta["preset_version"] = preset_version
        meta["factor_schema_version"] = factor_schema_version
        meta["factor_names"] = list(factor_names)
        meta["factor_vector"] = [float(value) for value in factor_vector]
        meta["probabilities"] = [float(value) for value in probabilities]
        meta["category_index"] = int(category_index)
        meta["recommended_index"] = int(recommended_index)
        created_at = float(meta.get("created_at", time.time()))
        factors = {
            name: float(value)
            for name, value in zip(factor_names, factor_vector, strict=False)
        }
        stored_factors = {
            **factors,
            "entity_id": str(meta["entity_id"]),
            "metadata": meta,
        }
        row_payload = {
            "decision_id": decision_id,
            "domain": domain,
            "category": category,
            "category_index": int(category_index),
            "factors_json": _to_json(stored_factors),
            "factor_vector_json": _to_json(meta["factor_vector"]),
            "recommended_action": recommended_action,
            "recommended_index": int(recommended_index),
            "confidence": float(confidence),
            "probabilities_json": _to_json(meta["probabilities"]),
            "status": "pending",
            "created_at": created_at,
        }

        def persist() -> None:
            existing = self.connection.execute(
                "SELECT * FROM decisions WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
            if existing is not None:
                current = {key: existing[key] for key in row_payload}
                if current == row_payload:
                    return None
                raise ValueError(f"conflicting governed decision_id: {decision_id}")
            self.connection.execute(
                """
                INSERT INTO decisions (
                    decision_id, domain, category, category_index, factors_json,
                    factor_vector_json, recommended_action, recommended_index,
                    confidence, probabilities_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(row_payload[key] for key in (
                    "decision_id",
                    "domain",
                    "category",
                    "category_index",
                    "factors_json",
                    "factor_vector_json",
                    "recommended_action",
                    "recommended_index",
                    "confidence",
                    "probabilities_json",
                    "status",
                    "created_at",
                )),
            )
            return None

        self._run_write(persist)
        return None

    def write_outcome(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
        domain: str | None = None,
    ) -> None:
        meta = dict(metadata or {})
        status = "confirmed" if is_correct else "overridden"
        def persist() -> None:
            if domain is None:
                row = self.connection.execute(
                    "SELECT domain FROM decisions WHERE decision_id = ?",
                    (decision_id,),
                ).fetchone()
            else:
                row = self.connection.execute(
                    "SELECT domain FROM decisions WHERE decision_id = ? AND domain = ?",
                    (decision_id, domain),
                ).fetchone()
            if row is None:
                raise KeyError(decision_id)
            outcome_domain = str(row["domain"] or self.domain)
            existing = self.connection.execute(
                "SELECT 1 FROM outcomes WHERE decision_id = ? AND domain = ?",
                (decision_id, outcome_domain),
            ).fetchone()
            if existing is not None:
                raise ValueError(f"outcome already exists for decision_id: {decision_id}")
            self.connection.execute(
                """
                INSERT INTO outcomes (
                    decision_id, domain, actual_action, actual_index, is_correct,
                    verified_at, context_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    outcome_domain,
                    actual_action,
                    int(meta.get("actual_index", 0)),
                    1 if is_correct else 0,
                    float(meta.get("verified_at", time.time())),
                    _to_json(meta.get("context")) if meta.get("context") is not None else None,
                ),
            )
            cursor = self.connection.execute(
                "UPDATE decisions SET status = ? WHERE decision_id = ? AND domain = ?",
                (status, decision_id, outcome_domain),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(f"failed to update decision status for {decision_id}")

        self._run_write(persist)

    def write_observation(
        self,
        observation_id: str,
        domain: str,
        category: str,
        recommended_action: str,
        confidence: float,
        source_route: str,
        scorer_version: str,
        factor_schema_version: str,
        entity_id: str | None = None,
        factor_vector: list[float] | None = None,
        factor_names: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        observation_id = str(observation_id)
        domain = str(domain)
        created_at = float((metadata or {}).get("created_at", time.time()))
        names = list(factor_names or [])
        vector = [float(value) for value in factor_vector] if factor_vector is not None else None

        def persist() -> None:
            cursor = self.connection.execute(
                """
                INSERT OR IGNORE INTO observations (
                    observation_id, domain, category, recommended_action, confidence,
                    source_route, scorer_version, factor_schema_version, metadata_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                observation_id,
                domain,
                category,
                    recommended_action,
                    float(confidence),
                    source_route,
                    scorer_version,
                    factor_schema_version,
                    _to_json(dict(metadata or {})),
                    created_at,
                ),
            )
            if cursor.rowcount != 1:
                return None
            if entity_id is not None:
                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO observation_entity_edges (
                        domain, observation_id, entity_id, edge_type, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (domain, observation_id, str(entity_id), "ABOUT", created_at),
                )
            if vector is not None:
                factor_names_json = _to_json(names)
                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO observation_factor_vectors (
                        observation_id, domain, dimension, factor_names,
                        factor_vector_json, factor_names_hash, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        observation_id,
                        domain,
                        len(vector),
                        factor_names_json,
                        _to_json(vector),
                        hashlib.sha256(factor_names_json.encode("utf-8")).hexdigest(),
                        created_at,
                    ),
                )

        self._run_write(persist)

    def append_evidence_receipt(
        self,
        receipt_intent_id: str,
        domain: str,
        decision_id: str,
        canonical_payload: dict[str, Any],
        actor: str,
        source_route: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[int, str]:
        receipt_intent_id = str(receipt_intent_id)
        domain = str(domain)
        decision_id = str(decision_id)
        payload_json = _to_json(dict(canonical_payload))
        metadata_json = _to_json(dict(metadata or {}))
        payload_hash = _receipt_payload_hash(
            receipt_intent_id,
            domain,
            decision_id,
            canonical_payload,
            actor,
            source_route,
            metadata,
        )

        def persist() -> tuple[int, str]:
            existing = self.connection.execute(
                """
                SELECT chain_index, payload_hash
                FROM evidence_receipts
                WHERE domain = ? AND receipt_intent_id = ?
                """,
                (domain, receipt_intent_id),
            ).fetchone()
            if existing is not None:
                if existing["payload_hash"] == payload_hash:
                    return int(existing["chain_index"]), str(existing["payload_hash"])
                raise ValueError(
                    f"conflicting evidence receipt_intent_id: {receipt_intent_id}"
                )
            last = self.connection.execute(
                """
                SELECT chain_index, payload_hash
                FROM evidence_receipts
                WHERE domain = ?
                ORDER BY chain_index DESC
                LIMIT 1
                """,
                (domain,),
            ).fetchone()
            if last is None:
                chain_index = 0
                previous_hash = "GENESIS"
            else:
                chain_index = int(last["chain_index"]) + 1
                previous_hash = str(last["payload_hash"])
            self.connection.execute(
                """
                INSERT INTO evidence_receipts (
                    receipt_intent_id, domain, decision_id, chain_index,
                    previous_hash, payload_hash, actor, source_route,
                    canonical_payload_json, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_intent_id,
                    domain,
                    decision_id,
                    chain_index,
                    previous_hash,
                    payload_hash,
                    actor,
                    source_route,
                    payload_json,
                    metadata_json,
                    time.time(),
                ),
            )
            return chain_index, payload_hash

        return cast(tuple[int, str], self._run_write(persist))

    def write_conservation_status(
        self,
        status_id: str,
        domain: str,
        V: int,
        q: float,
        alpha: float,
        theta_min: float,
        verified_count: int,
        correct_count: int,
        status: str,
        policy_version: str,
    ) -> None:
        snapshot_payload = {
            "snapshot_id": str(status_id),
            "domain": str(domain),
            "V": int(V),
            "q": float(q),
            "alpha": float(alpha),
            "theta_min": float(theta_min),
            "verified_count": int(verified_count),
            "correct_count": int(correct_count),
            "status": str(status),
            "policy_version": str(policy_version),
        }

        def persist() -> None:
            existing = self.connection.execute(
                """
                SELECT snapshot_id, domain, V, q, alpha, theta_min,
                       verified_count, correct_count, status, policy_version
                FROM conservation_snapshots
                WHERE snapshot_id = ?
                """,
                (snapshot_payload["snapshot_id"],),
            ).fetchone()
            if existing is not None:
                existing_payload = {
                    "snapshot_id": existing["snapshot_id"],
                    "domain": existing["domain"],
                    "V": int(existing["V"]),
                    "q": float(existing["q"]),
                    "alpha": float(existing["alpha"]),
                    "theta_min": float(existing["theta_min"]),
                    "verified_count": int(existing["verified_count"]),
                    "correct_count": int(existing["correct_count"]),
                    "status": existing["status"],
                    "policy_version": existing["policy_version"],
                }
                if existing_payload == snapshot_payload:
                    return None
                raise ValueError(
                    f"conflicting conservation status_id: {snapshot_payload['snapshot_id']}"
                )
            self.connection.execute(
                """
                INSERT INTO conservation_snapshots (
                    snapshot_id, domain, V, q, alpha, theta_min, verified_count,
                    correct_count, status, policy_version, computed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_payload["snapshot_id"],
                    snapshot_payload["domain"],
                    snapshot_payload["V"],
                    snapshot_payload["q"],
                    snapshot_payload["alpha"],
                    snapshot_payload["theta_min"],
                    snapshot_payload["verified_count"],
                    snapshot_payload["correct_count"],
                    snapshot_payload["status"],
                    snapshot_payload["policy_version"],
                    time.time(),
                ),
            )
            return None

        self._run_write(persist)
        return None

    def write_fingerprint(
        self,
        fingerprint_id: str,
        domain: str,
        factor_names: list[str],
        factor_stats: dict[str, Any],
        skipped_incompatible: int,
        window: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        fingerprint_payload = {
            "fingerprint_id": str(fingerprint_id),
            "domain": str(domain),
            "factor_names_json": _to_json(list(factor_names)),
            "factor_stats_json": _to_json(dict(factor_stats)),
            "skipped_incompatible": int(skipped_incompatible),
            "window": int(window),
            "metadata_json": _to_json(dict(metadata or {})),
        }

        def persist() -> None:
            existing = self.connection.execute(
                """
                SELECT fingerprint_id, domain, factor_names_json, factor_stats_json,
                       skipped_incompatible, window, metadata_json
                FROM fingerprints
                WHERE fingerprint_id = ?
                """,
                (fingerprint_payload["fingerprint_id"],),
            ).fetchone()
            if existing is not None:
                existing_payload = {
                    "fingerprint_id": existing["fingerprint_id"],
                    "domain": existing["domain"],
                    "factor_names_json": existing["factor_names_json"],
                    "factor_stats_json": existing["factor_stats_json"],
                    "skipped_incompatible": int(existing["skipped_incompatible"]),
                    "window": int(existing["window"]),
                    "metadata_json": existing["metadata_json"],
                }
                if existing_payload == fingerprint_payload:
                    return None
                raise ValueError(
                    f"conflicting fingerprint_id: {fingerprint_payload['fingerprint_id']}"
                )
            self.connection.execute(
                """
                INSERT INTO fingerprints (
                    fingerprint_id, domain, factor_names_json, factor_stats_json,
                    skipped_incompatible, window, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fingerprint_payload["fingerprint_id"],
                    fingerprint_payload["domain"],
                    fingerprint_payload["factor_names_json"],
                    fingerprint_payload["factor_stats_json"],
                    fingerprint_payload["skipped_incompatible"],
                    fingerprint_payload["window"],
                    fingerprint_payload["metadata_json"],
                    time.time(),
                ),
            )
            return None

        self._run_write(persist)
        return None

    def write_centroid_checkpoint(
        self,
        checkpoint_id: str,
        domain: str,
        category: str,
        action: str,
        centroids: Any,
        decisions_count: int,
        verified_count: int,
        iks: float,
        shape: list[int],
        factor_names_hash: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        checkpoint_payload = {
            "checkpoint_id": str(checkpoint_id),
            "domain": str(domain),
            "category": category,
            "action": action,
            "centroids_json": _to_json(centroids),
            "decisions_count": int(decisions_count),
            "verified_count": int(verified_count),
            "iks": float(iks),
            "shape_json": _to_json([int(value) for value in shape]),
            "factor_names_hash": str(factor_names_hash),
            "metadata_json": _to_json(dict(metadata or {})),
        }

        def persist() -> None:
            existing = self.connection.execute(
                """
                SELECT checkpoint_id, domain, category, action, centroids_json,
                       decisions_count, verified_count, iks, shape_json,
                       factor_names_hash, metadata_json
                FROM centroid_checkpoints
                WHERE checkpoint_id = ?
                """,
                (checkpoint_payload["checkpoint_id"],),
            ).fetchone()
            if existing is not None:
                existing_payload = {
                    "checkpoint_id": existing["checkpoint_id"],
                    "domain": existing["domain"],
                    "category": existing["category"],
                    "action": existing["action"],
                    "centroids_json": existing["centroids_json"],
                    "decisions_count": int(existing["decisions_count"]),
                    "verified_count": int(existing["verified_count"]),
                    "iks": float(existing["iks"]),
                    "shape_json": existing["shape_json"],
                    "factor_names_hash": existing["factor_names_hash"],
                    "metadata_json": existing["metadata_json"],
                }
                if existing_payload == checkpoint_payload:
                    return None
                raise ValueError(
                    f"conflicting checkpoint_id: {checkpoint_payload['checkpoint_id']}"
                )
            self.connection.execute(
                """
                INSERT INTO centroid_checkpoints (
                    checkpoint_id, domain, category, action, centroids_json,
                    decisions_count, verified_count, iks, shape_json,
                    factor_names_hash, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint_payload["checkpoint_id"],
                    checkpoint_payload["domain"],
                    checkpoint_payload["category"],
                    checkpoint_payload["action"],
                    checkpoint_payload["centroids_json"],
                    checkpoint_payload["decisions_count"],
                    checkpoint_payload["verified_count"],
                    checkpoint_payload["iks"],
                    checkpoint_payload["shape_json"],
                    checkpoint_payload["factor_names_hash"],
                    checkpoint_payload["metadata_json"],
                    time.time(),
                ),
            )
            return None

        self._run_write(persist)
        return None

    def write_evolution_event(
        self,
        event_id: str,
        domain: str,
        event_type: str,
        rule_name: str,
        variant_id: str,
        source_copilot: str | None = None,
        source_rule: str | None = None,
        metric: float | None = None,
        shadow_batch_size: int | None = None,
        min_shadow_batches: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        event_payload = {
            "event_id": str(event_id),
            "domain": str(domain),
            "event_type": event_type,
            "rule_name": rule_name,
            "variant_id": variant_id,
            "source_copilot": source_copilot,
            "source_rule": source_rule,
            "metric": None if metric is None else float(metric),
            "shadow_batch_size": None if shadow_batch_size is None else int(shadow_batch_size),
            "min_shadow_batches": None if min_shadow_batches is None else int(min_shadow_batches),
            "metadata_json": _to_json(dict(metadata or {})),
        }

        def persist() -> None:
            existing = self.connection.execute(
                """
                SELECT event_id, domain, event_type, rule_name, variant_id,
                       source_copilot, source_rule, metric, shadow_batch_size,
                       min_shadow_batches, metadata_json
                FROM evolution_events
                WHERE event_id = ?
                """,
                (event_payload["event_id"],),
            ).fetchone()
            if existing is not None:
                existing_payload = {
                    "event_id": existing["event_id"],
                    "domain": existing["domain"],
                    "event_type": existing["event_type"],
                    "rule_name": existing["rule_name"],
                    "variant_id": existing["variant_id"],
                    "source_copilot": existing["source_copilot"],
                    "source_rule": existing["source_rule"],
                    "metric": None if existing["metric"] is None else float(existing["metric"]),
                    "shadow_batch_size": (
                        None
                        if existing["shadow_batch_size"] is None
                        else int(existing["shadow_batch_size"])
                    ),
                    "min_shadow_batches": (
                        None
                        if existing["min_shadow_batches"] is None
                        else int(existing["min_shadow_batches"])
                    ),
                    "metadata_json": existing["metadata_json"],
                }
                if existing_payload == event_payload:
                    return None
                raise ValueError(f"conflicting evolution event_id: {event_payload['event_id']}")
            created_at = time.time()
            self.connection.execute(
                """
                INSERT INTO evolution_events (
                    event_id, domain, event_type, rule_name, variant_id,
                    source_copilot, source_rule, metric, shadow_batch_size,
                    min_shadow_batches, metadata_json, created_at, metadata,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_payload["event_id"],
                    event_payload["domain"],
                    event_payload["event_type"],
                    event_payload["rule_name"],
                    event_payload["variant_id"],
                    event_payload["source_copilot"],
                    event_payload["source_rule"],
                    event_payload["metric"],
                    event_payload["shadow_batch_size"],
                    event_payload["min_shadow_batches"],
                    event_payload["metadata_json"],
                    created_at,
                    event_payload["metadata_json"],
                    _utc_iso_now(),
                ),
            )
            return None

        self._run_write(persist)
        return None

    def link_entity(
        self,
        decision_id: str,
        entity_id: str,
        entity_type: str,
        domain: str,
    ) -> None:
        decision_id = str(decision_id)
        domain = str(domain)

        def persist() -> None:
            decision = self.connection.execute(
                "SELECT 1 FROM decisions WHERE decision_id = ? AND domain = ?",
                (decision_id, domain),
            ).fetchone()
            if decision is None:
                raise KeyError(decision_id)
            self.connection.execute(
                """
                INSERT OR IGNORE INTO decision_entity_edges (
                    domain, decision_id, entity_id, entity_type, edge_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    domain,
                    decision_id,
                    str(entity_id),
                    str(entity_type),
                    "DECIDED_ON",
                    time.time(),
                ),
            )
            return None

        self._run_write(persist)
        return None

    def _check_outcome_replay(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Classify future outbox replay without mutating outcome state."""
        meta = dict(metadata or {})
        with self._lock:
            decision = self.connection.execute(
                "SELECT 1 FROM decisions WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
            if decision is None:
                return "missing"
            outcome = self.connection.execute(
                """
                SELECT actual_action, actual_index, is_correct
                FROM outcomes
                WHERE decision_id = ?
                """,
                (decision_id,),
            ).fetchone()
            if outcome is None:
                return "needs_apply"
            if (
                outcome["actual_action"] == actual_action
                and int(outcome["actual_index"]) == int(meta.get("actual_index", 0))
                and bool(outcome["is_correct"]) is bool(is_correct)
            ):
                return "already_applied"
            return "conflict"

    def enqueue_to_outbox(
        self,
        domain: str,
        operation_type: str,
        target_key: str,
        payload: dict[str, Any],
        causal_decision_id: str | None = None,
    ) -> int:
        domain = str(domain)
        operation_type = str(operation_type)
        target_key = str(target_key)
        payload_json = json.dumps(
            payload,
            default=str,
            sort_keys=True,
            separators=(",", ":"),
        )
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        def persist() -> tuple[str, int | None]:
            rows = self.connection.execute(
                """
                SELECT outbox_id, payload_hash
                FROM outbox
                WHERE domain = ? AND operation_type = ? AND target_key = ?
                ORDER BY outbox_id
                """,
                (domain, operation_type, target_key),
            ).fetchall()
            for row in rows:
                if row["payload_hash"] == payload_hash:
                    return ("existing", int(row["outbox_id"]))
            if rows:
                original = rows[0]
                self.connection.execute(
                    """
                    INSERT INTO outbox_quarantine (
                        domain,
                        outbox_id,
                        operation_type,
                        target_key,
                        existing_payload_hash,
                        new_payload_hash,
                        new_payload_json,
                        reason,
                        quarantined_at,
                        resolved_at,
                        resolution
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
                    """,
                    (
                        domain,
                        int(original["outbox_id"]),
                        operation_type,
                        target_key,
                        str(original["payload_hash"]),
                        payload_hash,
                        payload_json,
                        "payload_hash_conflict",
                        _utc_iso_now(),
                    ),
                )
                return ("conflict", None)

            now = _utc_iso_now()
            cursor = self.connection.execute(
                """
                INSERT INTO outbox (
                    domain,
                    operation_type,
                    target_key,
                    payload_json,
                    payload_hash,
                    causal_decision_id,
                    status,
                    attempt_count,
                    last_error_redacted,
                    schema_version,
                    created_at,
                    updated_at,
                    replayed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'pending', 0, NULL, 1, ?, ?, NULL)
                """,
                (
                    domain,
                    operation_type,
                    target_key,
                    payload_json,
                    payload_hash,
                    causal_decision_id,
                    now,
                    now,
                ),
             )
            if cursor.lastrowid is None:
                raise RuntimeError("outbox insert did not produce an outbox_id")
            return ("inserted", int(cursor.lastrowid))

        status, outbox_id = self._run_write(persist)
        if status == "conflict":
            raise ValueError(
                "outbox payload_hash_conflict quarantined for "
                f"{domain}:{operation_type}:{target_key}"
            )
        if outbox_id is None:
            raise RuntimeError("outbox enqueue did not produce an outbox_id")
        return int(outbox_id)

    def get_decision(self, decision_id: str, domain: str | None = None) -> dict[str, Any] | None:
        if domain is None:
            row = self.connection.execute(
                "SELECT * FROM decisions WHERE decision_id = ?", (decision_id,)
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT * FROM decisions WHERE decision_id = ? AND domain = ?", (decision_id, domain)
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

    def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT * FROM decisions_archive
            WHERE domain = ?
            ORDER BY created_at ASC, decision_id ASC
            """,
            (str(domain),),
        ).fetchall()
        return [self._archived_decision_from_row(row) for row in rows]

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

    def count_verified_decisions(self, domain: str) -> int:
        row = self.connection.execute(
            """
            SELECT COUNT(DISTINCT d.decision_id) AS n
            FROM decisions d
            LEFT JOIN outcomes o ON o.decision_id = d.decision_id
            WHERE d.domain = ?
              AND (
                  d.status IN ('confirmed', 'overridden')
                  OR o.decision_id IS NOT NULL
              )
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

    def update_centroid(
        self,
        domain: str,
        category: str,
        action: str,
        centroid_vector: list[float],
        delta_norm: float,
        caused_by_decision_id: str | None = None,
    ) -> None:
        vector = _normalize_centroid_vector(centroid_vector)
        delta_value = float(delta_norm)
        updated_at = datetime.now(timezone.utc).isoformat()
        vector_json = json.dumps(vector, separators=(",", ":"))

        def persist() -> None:
            self.connection.execute(
                """
                INSERT INTO l5_centroids (
                    domain, category, action, vector_json, delta_norm,
                    caused_by_decision_id, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(domain, category, action) DO UPDATE SET
                    vector_json = excluded.vector_json,
                    delta_norm = excluded.delta_norm,
                    caused_by_decision_id = excluded.caused_by_decision_id,
                    updated_at = excluded.updated_at
                """,
                (
                    str(domain),
                    str(category),
                    str(action),
                    vector_json,
                    delta_value,
                    None if caused_by_decision_id is None else str(caused_by_decision_id),
                    updated_at,
                ),
            )
            return None

        self._run_write(persist)
        return None

    def get_centroids(self, domain: str) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """
            SELECT category, action, vector_json, delta_norm, caused_by_decision_id, updated_at
            FROM l5_centroids
            WHERE domain = ?
            ORDER BY category, action
            """,
            (str(domain),),
        ).fetchall()
        return [
            {
                "category": row["category"],
                "action": row["action"],
                "vector_json": [float(value) for value in json.loads(row["vector_json"])],
                "delta_norm": float(row["delta_norm"]),
                "caused_by_decision_id": row["caused_by_decision_id"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def update_dk_weights(
        self,
        domain: str,
        weight_tensor: list[list[float]],
        n_decisions_used: int,
        computed_at: float,
        *,
        welford_state: dict[str, object] | None = None,
        n_confirmed: int | None = None,
        n_overridden: int | None = None,
        entity_group: str | None = None,
    ) -> None:
        tensor = _normalize_dk_weight_tensor(weight_tensor)
        decisions_used = _normalize_n_decisions_used(n_decisions_used)
        computed_at_value = _normalize_computed_at(computed_at)
        normalized_welford = _normalize_dk_welford_state(
            welford_state,
            n_decisions_used=decisions_used,
        )
        confirmed_count = _normalize_optional_nonnegative_int(n_confirmed, "n_confirmed")
        overridden_count = _normalize_optional_nonnegative_int(n_overridden, "n_overridden")
        entity_group_value = None if entity_group is None else str(entity_group)
        welford_json = {
            key: (
                json.dumps(normalized_welford[key], separators=(",", ":"))
                if normalized_welford is not None
                else None
            )
            for key in _DK_WELFORD_VECTOR_KEYS
        }
        weight_json = json.dumps(tensor, separators=(",", ":"))
        created_at = _utc_iso_now()
        domain_value = str(domain)

        def persist() -> None:
            row = self.connection.execute(
                """
                SELECT id FROM l5_dk_weights
                WHERE domain = ? AND is_current = 1
                """,
                (domain_value,),
            ).fetchone()
            old_id = int(row["id"]) if row is not None else None
            self.connection.execute(
                """
                UPDATE l5_dk_weights
                SET is_current = 0
                WHERE domain = ? AND is_current = 1
                """,
                (domain_value,),
            )
            self.connection.execute(
                """
                INSERT INTO l5_dk_weights (
                    domain, weight_json, n_decisions_used, computed_at,
                    supersedes_id, is_current, created_at,
                    confirmed_mean_json, confirmed_m2_json,
                    overridden_mean_json, overridden_m2_json,
                    all_mean_json, all_m2_json,
                    n_confirmed, n_overridden, entity_group
                )
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    domain_value,
                    weight_json,
                    decisions_used,
                    computed_at_value,
                    old_id,
                    created_at,
                    welford_json["confirmed_mean"],
                    welford_json["confirmed_m2"],
                    welford_json["overridden_mean"],
                    welford_json["overridden_m2"],
                    welford_json["all_mean"],
                    welford_json["all_m2"],
                    confirmed_count,
                    overridden_count,
                    entity_group_value,
                ),
            )
            return None

        self._run_write(persist)
        return None

    def get_dk_weights(self, domain: str) -> dict[str, object] | None:
        row = self.connection.execute(
            """
            SELECT domain, weight_json, n_decisions_used, computed_at, supersedes_id, created_at,
                   confirmed_mean_json, confirmed_m2_json,
                   overridden_mean_json, overridden_m2_json,
                   all_mean_json, all_m2_json,
                   n_confirmed, n_overridden, entity_group
            FROM l5_dk_weights
            WHERE domain = ? AND is_current = 1
            """,
            (str(domain),),
        ).fetchone()
        if row is None:
            return None
        decisions_used = int(row["n_decisions_used"])
        tensor = _normalize_dk_weight_tensor(json.loads(row["weight_json"]))
        welford_state = _decode_dk_welford_state(dict(row), n_decisions_used=decisions_used)
        return {
            "weight_json": tensor,
            "n_decisions_used": decisions_used,
            "computed_at": float(row["computed_at"]),
            "supersedes_id": row["supersedes_id"],
            "created_at": row["created_at"],
            "domain": row["domain"],
            "welford_state": welford_state,
            "n_confirmed": (
                _normalize_optional_nonnegative_int(row["n_confirmed"], "n_confirmed")
                if row["n_confirmed"] is not None
                else None
            ),
            "n_overridden": (
                _normalize_optional_nonnegative_int(row["n_overridden"], "n_overridden")
                if row["n_overridden"] is not None
                else None
            ),
            "entity_group": row["entity_group"],
        }

    def update_conservation_state(
        self,
        domain: str,
        status: str,
        alpha: float,
        q: float,
        V: int,
        theta_min: float,
        product: float,
        categories_total: int,
        categories_with_data: int,
        baseline_product: float,
        relative_threshold: float,
        complacency_flag: str,
        caused_by_decision_id: str | None = None,
        old_status: str | None = None,
    ) -> str:
        state = _normalize_conservation_state_values(
            domain=domain,
            status=status,
            alpha=alpha,
            q=q,
            V=V,
            theta_min=theta_min,
            product=product,
            categories_total=categories_total,
            categories_with_data=categories_with_data,
            baseline_product=baseline_product,
            relative_threshold=relative_threshold,
            complacency_flag=complacency_flag,
            caused_by_decision_id=caused_by_decision_id,
            old_status=old_status,
        )
        updated_at = _utc_iso_now()

        def persist() -> str:
            self.connection.execute(
                """
                INSERT INTO l5_conservation_state (
                    domain, status, alpha, q, V, theta_min, product,
                    categories_total, categories_with_data, baseline_product,
                    relative_threshold, complacency_flag, caused_by_decision_id,
                    old_status, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    status = excluded.status,
                    alpha = excluded.alpha,
                    q = excluded.q,
                    V = excluded.V,
                    theta_min = excluded.theta_min,
                    product = excluded.product,
                    categories_total = excluded.categories_total,
                    categories_with_data = excluded.categories_with_data,
                    baseline_product = excluded.baseline_product,
                    relative_threshold = excluded.relative_threshold,
                    complacency_flag = excluded.complacency_flag,
                    caused_by_decision_id = excluded.caused_by_decision_id,
                    old_status = excluded.old_status,
                    updated_at = excluded.updated_at
                """,
                (
                    state["domain"],
                    state["status"],
                    state["alpha"],
                    state["q"],
                    state["V"],
                    state["theta_min"],
                    state["product"],
                    state["categories_total"],
                    state["categories_with_data"],
                    state["baseline_product"],
                    state["relative_threshold"],
                    state["complacency_flag"],
                    state["caused_by_decision_id"],
                    state["old_status"],
                    updated_at,
                ),
            )
            row = self.connection.execute(
                "SELECT id FROM l5_conservation_state WHERE domain = ?",
                (state["domain"],),
            ).fetchone()
            if row is None:
                raise RuntimeError("l5_conservation_state upsert did not return a row id")
            return str(row["id"])

        return cast(str, self._run_write(persist))

    def get_conservation_state(self, domain: str) -> dict[str, object] | None:
        row = self.connection.execute(
            """
            SELECT id, domain, status, alpha, q, V, theta_min, product,
                   categories_total, categories_with_data, baseline_product,
                   relative_threshold, complacency_flag, caused_by_decision_id,
                   old_status, updated_at
            FROM l5_conservation_state
            WHERE domain = ?
            """,
            (str(domain),),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": str(row["id"]),
            "domain": row["domain"],
            "status": row["status"],
            "alpha": float(row["alpha"]),
            "q": float(row["q"]),
            "V": int(row["V"]),
            "theta_min": float(row["theta_min"]),
            "product": float(row["product"]),
            "categories_total": int(row["categories_total"]),
            "categories_with_data": int(row["categories_with_data"]),
            "baseline_product": float(row["baseline_product"]),
            "relative_threshold": float(row["relative_threshold"]),
            "complacency_flag": row["complacency_flag"],
            "caused_by_decision_id": row["caused_by_decision_id"],
            "old_status": row["old_status"],
            "updated_at": row["updated_at"],
        }

    def save_centroids(
        self,
        domain: str,
        category: str,
        centroids: Any,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        meta = dict(metadata or {})
        def persist() -> None:
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

        self._run_write(persist)

    def load_latest_centroids(self, domain: str) -> Any | None:
        row = self.connection.execute(
            """
            SELECT centroids_json FROM centroid_checkpoints
            WHERE domain = ? AND checkpoint_id IS NULL
            ORDER BY id DESC LIMIT 1
            """,
            (str(domain),),
        ).fetchone()
        if row is None:
            return None
        return np.asarray(_from_json(row["centroids_json"]), dtype=np.float64)

    def save_rl_state(self, key: str, data: dict) -> None:
        def persist() -> None:
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

        self._run_write(persist)

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
        def persist() -> None:
            metadata_json = _to_json(dict(metadata or {}))
            self.connection.execute(
                """
                INSERT INTO evolution_events (
                    domain, event_type, rule_name, variant_id, metadata,
                    metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(domain),
                    event_type,
                    rule_name,
                    variant_id,
                    metadata_json,
                    metadata_json,
                    time.time(),
                ),
            )

        self._run_write(persist)

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
        def persist() -> None:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO decision_entity_edges (
                    domain, decision_id, entity_id, entity_type, edge_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (domain, decision_id, entity_id, edge_type, edge_type, time.time()),
            )

        self._run_write(persist)

    def get_decision_links(
        self,
        decision_id: str | None = None,
        domain: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if domain is not None and str(domain) != self.domain:
            return []
        limit_value = _bounded_traversal_limit(limit) if limit is not None else None
        if decision_id is None:
            limit_clause = "" if limit_value is None else "LIMIT ?"
            params: tuple[Any, ...] = (
                (self.domain,) if limit_value is None else (self.domain, limit_value)
            )
            rows = self.connection.execute(
                f"""
                SELECT decision_id, entity_id, edge_type, created_at
                FROM decision_entity_edges
                WHERE domain = ?
                ORDER BY id ASC
                {limit_clause}
                """,
                params,
            ).fetchall()
        else:
            limit_clause = "" if limit_value is None else "LIMIT ?"
            params = (
                (self.domain, decision_id)
                if limit_value is None
                else (self.domain, decision_id, limit_value)
            )
            rows = self.connection.execute(
                f"""
                SELECT decision_id, entity_id, edge_type, created_at
                FROM decision_entity_edges
                WHERE domain = ? AND decision_id = ?
                ORDER BY id ASC
                {limit_clause}
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def query_context(
        self,
        entity_id: str,
        max_depth: int,
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        depth = _bounded_traversal_depth(max_depth)
        root_id = str(entity_id)
        rows: list[dict[str, Any]] = [
            {
                "node": "entity",
                "id": root_id,
                "depth": 0,
                "properties": {"entity_id": root_id, "provenance": "graph_store"},
            }
        ]
        if depth == 0:
            return rows

        links = self._get_entity_links(root_id, limit=100)
        linked_decision_ids = [
            str(link["decision_id"])
            for link in links
        ]
        if self.get_decision(root_id) is not None and root_id not in linked_decision_ids:
            linked_decision_ids.insert(0, root_id)

        seen_decisions: set[str] = set()
        seen_entities: set[str] = {root_id}
        for decision_id in linked_decision_ids[:100]:
            if decision_id in seen_decisions:
                continue
            seen_decisions.add(decision_id)
            decision = self.get_decision(decision_id)
            if decision is None or (
                domain is not None and decision.get("domain") != str(domain)
            ):
                continue
            rows.append(
                {
                    "node": "decision",
                    "id": decision_id,
                    "depth": 1,
                    "properties": decision,
                }
            )
            if depth < 2:
                continue
            for link in self.get_decision_links(decision_id, limit=100):
                neighbor_id = str(link.get("entity_id") or "")
                if not neighbor_id or neighbor_id in seen_entities:
                    continue
                seen_entities.add(neighbor_id)
                rows.append(
                    {
                        "node": "entity",
                        "id": neighbor_id,
                        "depth": 2,
                        "properties": {
                            "entity_id": neighbor_id,
                            "edge_type": link.get("edge_type"),
                            "provenance": "graph_store",
                        },
                    }
                )
                if depth < 3:
                    continue
                for neighbor_link in self._get_entity_links(neighbor_id, limit=100):
                    neighbor_decision_id = str(neighbor_link.get("decision_id") or "")
                    if not neighbor_decision_id or neighbor_decision_id in seen_decisions:
                        continue
                    neighbor_decision = self.get_decision(neighbor_decision_id)
                    if neighbor_decision is None or (
                        domain is not None
                        and neighbor_decision.get("domain") != str(domain)
                    ):
                        continue
                    seen_decisions.add(neighbor_decision_id)
                    rows.append(
                        {
                            "node": "decision",
                            "id": neighbor_decision_id,
                            "depth": 3,
                            "properties": neighbor_decision,
                        }
                    )
        return rows[:100]

    def _get_entity_links(self, entity_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT decision_id, entity_id, edge_type, created_at
            FROM decision_entity_edges
            WHERE domain = ? AND entity_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (self.domain, str(entity_id), _bounded_traversal_limit(limit)),
        ).fetchall()
        return [dict(row) for row in rows]

    def query_similar(self, entity_id: str, limit: int) -> list[dict[str, Any]]:
        limit_value = _bounded_traversal_limit(limit)
        source = self.get_decision(str(entity_id))
        if source is None:
            for link in self._get_entity_links(str(entity_id), limit=100):
                if str(link.get("entity_id")) == str(entity_id):
                    source = self.get_decision(str(link.get("decision_id")))
                    break
        if source is None:
            return []
        category = str(source.get("category") or "")
        domain = str(source.get("domain") or self.domain)
        source_supplier = _decision_supplier(source)
        candidates = self.get_decisions(domain, category or None, limit=400)
        matches: list[dict[str, Any]] = []
        for candidate in candidates:
            if candidate.get("decision_id") == source.get("decision_id"):
                continue
            if source_supplier and _decision_supplier(candidate) != source_supplier:
                continue
            matches.append(candidate)
            if len(matches) >= limit_value:
                break
        return matches

    def write_entity_enrichment(
        self,
        *,
        domain: str,
        entity_type: str,
        entity_id: str,
        namespace: str,
        metrics: dict[str, ProvenancedValue],
        computed_from: EnrichmentSourceSet,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> EntityEnrichmentReceipt:
        domain = str(domain)
        entity_type = str(entity_type)
        entity_id = str(entity_id)
        namespace = str(namespace)
        computed_at = utc_iso_now()
        allowed: dict[str, ProvenancedValue] = {}
        protected: list[str] = []
        rejected: list[str] = []
        warnings: list[str] = []

        for metric_name, value in dict(metrics or {}).items():
            metric_key = str(metric_name)
            if is_protected_metric_name(metric_key):
                protected.append(metric_key)
                rejected.append(metric_key)
                continue
            if not isinstance(value, ProvenancedValue):
                raise TypeError("metrics values must be ProvenancedValue instances")
            allowed[metric_key] = value

        if protected:
            warnings.append("protected metric names were rejected")
        if not allowed:
            warnings.append("no enrichment metrics were written")
            return EntityEnrichmentReceipt(
                domain=domain,
                entity_type=entity_type,
                entity_id=entity_id,
                namespace=namespace,
                persisted=False,
                dry_run=bool(dry_run),
                metrics_written=[],
                metrics_rejected=rejected,
                protected_fields_rejected=protected,
                idempotency_key=str(idempotency_key or ""),
                computed_at=computed_at,
                warnings=warnings,
            )

        if dry_run:
            return EntityEnrichmentReceipt(
                domain=domain,
                entity_type=entity_type,
                entity_id=entity_id,
                namespace=namespace,
                persisted=False,
                dry_run=True,
                metrics_written=list(allowed),
                metrics_rejected=rejected,
                protected_fields_rejected=protected,
                idempotency_key=str(idempotency_key or ""),
                computed_at=computed_at,
                warnings=warnings,
            )

        source_set_json = _to_json(asdict(computed_from))

        def persist() -> None:
            for metric_name, value in allowed.items():
                self.connection.execute(
                    """
                    INSERT INTO entity_enrichments (
                        domain, entity_type, entity_id, namespace, metric_name,
                        value_json, provenance_json, source_set_json, computed_at, idempotency_key
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(domain, entity_type, entity_id, namespace, metric_name)
                    DO UPDATE SET
                        value_json = excluded.value_json,
                        provenance_json = excluded.provenance_json,
                        source_set_json = excluded.source_set_json,
                        computed_at = excluded.computed_at,
                        idempotency_key = excluded.idempotency_key
                    """,
                    (
                        domain,
                        entity_type,
                        entity_id,
                        namespace,
                        metric_name,
                        _to_json(value.value),
                        _to_json(value.to_storage_dict()),
                        source_set_json,
                        computed_at,
                        idempotency_key,
                    ),
                )
            return None

        self._run_write(persist)
        return EntityEnrichmentReceipt(
            domain=domain,
            entity_type=entity_type,
            entity_id=entity_id,
            namespace=namespace,
            persisted=True,
            dry_run=False,
            metrics_written=list(allowed),
            metrics_rejected=rejected,
            protected_fields_rejected=protected,
            idempotency_key=str(idempotency_key or ""),
            computed_at=computed_at,
            warnings=warnings,
        )

    def read_entity_enrichment(
        self,
        *,
        domain: str,
        entity_type: str,
        entity_id: str,
        namespace: str | None = None,
    ) -> dict[str, ProvenancedValue]:
        params: list[Any] = [str(domain), str(entity_type), str(entity_id)]
        namespace_filter = ""
        if namespace is not None:
            namespace_filter = " AND namespace = ?"
            params.append(str(namespace))
        rows = self.connection.execute(
            f"""
            SELECT namespace, metric_name, value_json, provenance_json
            FROM entity_enrichments
            WHERE domain = ? AND entity_type = ? AND entity_id = ?{namespace_filter}
            ORDER BY namespace, metric_name
            """,
            params,
        ).fetchall()
        result: dict[str, ProvenancedValue] = {}
        for row in rows:
            key = row["metric_name"] if namespace is not None else f"{row['namespace']}.{row['metric_name']}"
            result[key] = ProvenancedValue.from_storage_dict(
                _from_json(row["value_json"]),
                _from_json(row["provenance_json"]),
            )
        return result

    def list_entity_enrichments(
        self,
        *,
        domain: str,
        entity_type: str | None = None,
        namespace: str | None = None,
        limit: int = 500,
    ) -> list[EntityEnrichmentRecord]:
        try:
            limit_value = int(limit)
        except (TypeError, ValueError):
            limit_value = 500
        limit_value = max(0, limit_value)
        params: list[Any] = [str(domain)]
        filters = ["domain = ?"]
        if entity_type is not None:
            filters.append("entity_type = ?")
            params.append(str(entity_type))
        if namespace is not None:
            filters.append("namespace = ?")
            params.append(str(namespace))
        params.append(limit_value)
        rows = self.connection.execute(
            f"""
            SELECT domain, entity_type, entity_id, namespace, metric_name,
                   value_json, provenance_json, source_set_json, computed_at, idempotency_key
            FROM entity_enrichments
            WHERE {" AND ".join(filters)}
            ORDER BY domain, entity_type, entity_id, namespace, metric_name
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [self._entity_enrichment_record_from_row(row) for row in rows]

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
        def persist() -> None:
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

        self._run_write(persist)
        return len(archive_ids)

    def archive_decisions(
        self,
        domain: str,
        before: float,
        status_filter: str = "pending",
        confirm_verified: bool = False,
    ) -> int:
        domain = str(domain)
        status_filter = str(status_filter)
        if status_filter in {"confirmed", "overridden"} and not confirm_verified:
            raise ValueError(
                "Archiving verified decisions reduces active V. "
                "Pass confirm_verified=True to proceed."
            )
        if status_filter not in {"pending", "confirmed", "overridden"}:
            raise ValueError(f"Unsupported archive status_filter: {status_filter}")

        def persist() -> int:
            rows = self.connection.execute(
                """
                SELECT decision_id FROM decisions
                WHERE domain = ? AND status = ? AND created_at < ?
                ORDER BY created_at ASC, decision_id ASC
                """,
                (domain, status_filter, float(before)),
            ).fetchall()
            archive_ids = [row["decision_id"] for row in rows]
            if not archive_ids:
                return 0
            archived_at = time.time()
            for decision_id in archive_ids:
                self.connection.execute(
                    """
                    INSERT INTO decisions_archive (
                        decision_id, domain, category, category_index, factors_json,
                        factor_vector_json, recommended_action, recommended_index,
                        confidence, probabilities_json, created_at, actual_action,
                        actual_index, is_correct, verified_at, context_json,
                        archived_at, archive_reason
                    )
                    SELECT
                        d.decision_id, d.domain, d.category, d.category_index, d.factors_json,
                        d.factor_vector_json, d.recommended_action, d.recommended_index,
                        d.confidence, d.probabilities_json, d.created_at, o.actual_action,
                        o.actual_index, o.is_correct, o.verified_at, o.context_json,
                        ?, ?
                    FROM decisions d
                    LEFT JOIN outcomes o ON d.decision_id = o.decision_id
                    WHERE d.decision_id = ? AND d.domain = ?
                    """,
                    (
                        archived_at,
                        f"protocol_v2_{status_filter}",
                        decision_id,
                        domain,
                    ),
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
                (*archive_ids, domain),
            )
            return len(archive_ids)

        return int(self._run_write(persist))

    def count_archived(self, domain: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS n FROM decisions_archive WHERE domain = ?",
            (str(domain),),
        ).fetchone()
        return int(row["n"])

    def domain_scoped_reset(self, domain: str) -> None:
        domain = str(domain)

        def persist() -> None:
            decision_rows = self.connection.execute(
                "SELECT decision_id FROM decisions WHERE domain = ?",
                (domain,),
            ).fetchall()
            decision_ids = [row["decision_id"] for row in decision_rows]
            if decision_ids:
                placeholders = ",".join("?" for _ in decision_ids)
                self.connection.execute(
                    f"DELETE FROM outcomes WHERE decision_id IN ({placeholders})",
                    decision_ids,
                )
                self.connection.execute(
                    f"DELETE FROM decision_entity_edges WHERE decision_id IN ({placeholders})",
                    decision_ids,
                )
            self.connection.execute("DELETE FROM outcomes WHERE domain = ?", (domain,))
            for table in (
                "decisions",
                "observations",
                "observation_entity_edges",
                "observation_factor_vectors",
                "evidence_receipts",
                "conservation_snapshots",
                "fingerprints",
                "centroid_checkpoints",
                "evolution_events",
                "decision_entity_edges",
                  "decisions_archive",
                  "rl_state",
                  "outbox",
                  "outbox_quarantine",
                  "l5_centroids",
                  "l5_dk_weights",
                  "l5_conservation_state",
                  "entity_enrichments",
                ):
                    self.connection.execute(f"DELETE FROM {table} WHERE domain = ?", (domain,))
            return None

        self._run_write(persist)
        return None

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
            "status": row["status"],
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

    @staticmethod
    def _archived_decision_from_row(row: sqlite3.Row) -> dict[str, Any]:
        """Normalize the denormalized SQLite archive row for history reads."""
        actual_index = row["actual_index"]
        is_correct = row["is_correct"]
        verified_at = row["verified_at"]
        return {
            "decision_id": row["decision_id"],
            "domain": row["domain"],
            "category": row["category"],
            "category_index": int(row["category_index"]),
            "recommended_action": row["recommended_action"],
            "recommended_index": int(row["recommended_index"]),
            "confidence": float(row["confidence"]),
            "factor_vector": _from_json(row["factor_vector_json"]),
            "probabilities": _from_json(row["probabilities_json"]),
            "created_at": float(row["created_at"]),
            "actual_action": row["actual_action"],
            "actual_index": int(actual_index) if actual_index is not None else None,
            "is_correct": bool(is_correct) if is_correct is not None else None,
            "verified_at": float(verified_at) if verified_at is not None else None,
            "archived_at": float(row["archived_at"]),
            "archive_reason": row["archive_reason"],
        }

    def _entity_enrichment_record_from_row(self, row: sqlite3.Row) -> EntityEnrichmentRecord:
        value = ProvenancedValue.from_storage_dict(
            _from_json(row["value_json"]),
            _from_json(row["provenance_json"]),
        )
        return EntityEnrichmentRecord(
            domain=row["domain"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            namespace=row["namespace"],
            metric_name=row["metric_name"],
            value=value,
            computed_from=EnrichmentSourceSet(**_from_json(row["source_set_json"])),
            computed_at=row["computed_at"],
            idempotency_key=row["idempotency_key"] or "",
        )

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
    clauses: list[str] = ["domain = ?", "checkpoint_id IS NULL"]
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


def _bounded_traversal_depth(value: Any) -> int:
    try:
        depth = int(value)
    except (TypeError, ValueError):
        depth = 3
    return max(0, min(depth, 3))


def _bounded_traversal_limit(value: Any) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = 5
    return max(0, min(limit, 100))


def _decision_supplier(decision: dict[str, Any]) -> str:
    metadata = decision.get("metadata")
    metadata_dict = metadata if isinstance(metadata, dict) else {}
    for key in ("supplier_id", "supplier", "supplier_name"):
        value = decision.get(key)
        if value not in (None, ""):
            return str(value)
        value = metadata_dict.get(key)
        if value not in (None, ""):
            return str(value)
    return ""
