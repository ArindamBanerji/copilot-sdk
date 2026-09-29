"""Restore demo state bundles into a cold SQLite graph store."""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


LOGGER = logging.getLogger(__name__)
DEFAULT_MIN_DECISIONS_TO_SKIP = 180


@dataclass(frozen=True)
class RestoreReport:
    stores_restored: int = 0
    stores_failed: int = 0
    failed_stores: list[str] = field(default_factory=list)
    fully_restored: bool = False
    restored_count: int = 0
    skipped_count: int = 0

    @property
    def success(self) -> bool:
        """Backward-compatible success meaning: at least one row was restored."""

        return self.restored_count > 0

    def __bool__(self) -> bool:
        return self.success


def restore_bundle_if_empty(store: Any, bundle_path: Path, *, domain: str) -> RestoreReport:
    """Restore a demo bundle into ``store`` when the requested domain is cold."""
    path = Path(bundle_path)
    try:
        with path.open("r", encoding="utf-8") as handle:
            bundle = json.load(handle)
    except FileNotFoundError:
        LOGGER.warning("Demo bundle file does not exist: %s", path)
        return _failed_report("bundle")
    except OSError:
        LOGGER.exception("Unable to read demo bundle: %s", path)
        return _failed_report("bundle")
    except json.JSONDecodeError:
        LOGGER.exception("Unable to decode demo bundle JSON: %s", path)
        return _failed_report("bundle")

    if not isinstance(bundle, dict):
        LOGGER.error("Demo bundle must contain a JSON object: %s", path)
        return _failed_report("bundle")

    result = _restore(store, bundle, domain)
    store_names = _bundle_store_names(bundle)
    if isinstance(result, dict):
        restored_count = max(int(result.get("restored_count", 0)), 0)
        skipped_count = max(int(result.get("skipped_count", 0)), 0)
        failed_stores = ["decisions"] if skipped_count > 0 else []
        stores_restored = 1 if restored_count > 0 else 0
        if restored_count == 0 and store_names:
            failed_stores = list(store_names)
        return RestoreReport(
            stores_restored=stores_restored,
            stores_failed=len(failed_stores),
            failed_stores=failed_stores,
            fully_restored=restored_count > 0 and not failed_stores,
            restored_count=restored_count,
            skipped_count=skipped_count,
        )
    if result:
        restored_stores = len(store_names) or 1
        return RestoreReport(
            stores_restored=restored_stores,
            stores_failed=0,
            fully_restored=True,
            restored_count=1,
        )
    return RestoreReport(fully_restored=not store_names)


def _failed_report(store_name: str) -> RestoreReport:
    return RestoreReport(
        stores_failed=1,
        failed_stores=[store_name],
        fully_restored=False,
    )


def _bundle_store_names(bundle: dict[str, Any]) -> list[str]:
    sections = (
        ("decisions", bundle.get("decisions")),
        ("centroid_checkpoints", bundle.get("centroid_checkpoints")),
        ("rl_state", bundle.get("rl_state")),
        ("evolution_events", bundle.get("evolution_events")),
    )
    return [name for name, value in sections if bool(value)]


def _restore(store: Any, bundle: dict[str, Any], domain: str) -> bool | dict[str, int] | None:
    bundle_domain = bundle.get("domain")
    if bundle_domain != domain:
        LOGGER.error("Demo bundle domain mismatch: expected %s, got %s", domain, bundle_domain)
        return False

    # AGE-native restore is the only production path.  The bundle is clearly
    # synthetic and therefore carries provenance on every restored decision.
    graph_config = getattr(store, "graph_config", None)
    backend = str(
        getattr(graph_config, "backend", None)
        or getattr(store, "backend", "")
    ).lower()
    is_age_adapter = type(store).__name__ == "AGEGraphStoreAdapter"
    if backend == "age" or is_age_adapter:
        threshold = int(bundle.get("min_decisions_to_skip", DEFAULT_MIN_DECISIONS_TO_SKIP))
        if store.count_decisions(domain) >= threshold:
            return False
        decisions = list(_items(bundle.get("decisions")))
        written = 0
        skipped = 0
        for decision in decisions:
            metadata = dict(decision.get("metadata") or {})
            metadata["provenance"] = "synthetic"
            metadata["source"] = "demo_bundle"
            try:
                store.write_governed_decision(
                    decision_id=str(decision["decision_id"]),
                    domain=domain,
                    category=str(decision.get("category") or "unknown"),
                    category_index=int(decision.get("category_index") or 0),
                    recommended_action=str(decision.get("recommended_action") or "unknown"),
                    recommended_index=int(decision.get("recommended_index") or 0),
                    confidence=float(decision.get("confidence") or 0.0),
                    probabilities=list(decision.get("probabilities") or []),
                    factor_vector=list(decision.get("factor_vector") or []),
                    factor_names=list(decision.get("factor_names") or []),
                    source="demo_bundle",
                    metadata=metadata,
                )
                written += 1
            except Exception as exc:
                skipped += 1
                LOGGER.warning(
                    "AGE bundle decision skipped: decision_id=%s error=%s",
                    decision.get("decision_id"),
                    exc,
                )
        return {"restored_count": written, "skipped_count": skipped}

    sqlite_store = _sqlite_restore_store(store)
    threshold = int(bundle.get("min_decisions_to_skip", DEFAULT_MIN_DECISIONS_TO_SKIP))
    try:
        current = int(sqlite_store.count_decisions(domain))
    except Exception:
        current = 0
    if current >= threshold:
        return False

    connection = _sqlite_connection(sqlite_store)
    lock = getattr(sqlite_store, "_lock", None)
    if connection is None or lock is None or not hasattr(lock, "__enter__"):
        LOGGER.warning("Demo bundle restore requires a direct-write SQLiteGraphStore")
        return False

    decisions = list(_items(bundle.get("decisions")))
    outcomes = _verified_outcomes(decisions)
    checkpoints = list(_items(bundle.get("centroid_checkpoints")))
    rl_state = list(_rl_items(bundle.get("rl_state")))
    events = list(_items(bundle.get("evolution_events")))
    if not decisions and not checkpoints and not rl_state and not events:
        LOGGER.info("[demo-bundle] No supported rows in bundle - skipping")
        return False

    try:
        rows_written = 0
        with lock:
            for decision in decisions:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO decisions (
                        decision_id, domain, category, category_index, factors_json,
                        factor_vector_json, recommended_action, recommended_index,
                        confidence, probabilities_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    _decision_values(decision, domain),
                )
                rows_written += _rowcount(cursor)
            for decision, outcome in outcomes:
                correctness = _coerce_correctness(outcome.get("is_correct"))
                if correctness is None:
                    continue
                cursor = connection.execute(
                    """
                    INSERT OR REPLACE INTO outcomes (
                        decision_id, domain, actual_action, actual_index, is_correct,
                        verified_at, context_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    _outcome_values(decision, outcome, domain),
                )
                rows_written += _rowcount(cursor)
                connection.execute(
                    "UPDATE decisions SET status = ? WHERE decision_id = ? AND domain = ?",
                    (
                        (
                            "confirmed" if correctness else "overridden"
                        ),
                        str(decision["decision_id"]),
                        domain,
                    ),
                )
            for checkpoint in checkpoints:
                cursor = connection.execute(
                    """
                    INSERT INTO centroid_checkpoints (
                        domain, decision_id, category, centroids_json, decisions_count, iks,
                        metadata_json, created_at, decision_time_start, decision_time_end,
                        checkpoint_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    _checkpoint_values(checkpoint, domain, len(decisions)),
                )
                rows_written += _rowcount(cursor)
            for key, data in rl_state:
                cursor = connection.execute(
                    """
                    INSERT INTO rl_state (domain, key, data_json, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(domain, key) DO UPDATE SET
                        data_json = excluded.data_json,
                        updated_at = excluded.updated_at
                    """,
                    (domain, key, _to_json(data), _timestamp(data)),
                )
                rows_written += _rowcount(cursor)
            for event in events:
                cursor = connection.execute(
                    """
                    INSERT INTO evolution_events (
                        domain, event_type, rule_name, variant_id, metadata, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    _event_values(event, domain),
                )
                rows_written += _rowcount(cursor)
            connection.commit()
    except Exception:
        connection.rollback()
        LOGGER.exception("Demo bundle restore failed for domain %s", domain)
        return False

    restored = rows_written > 0
    backend = os.getenv("GRAPH_BACKEND", "").strip().lower()
    if restored and backend in {"age", "dual_write"}:
        LOGGER.info("Bundle restored to SQLite. AGE migration required for graph parity.")
    return restored


def _sqlite_connection(store: Any) -> Any | None:
    if str(getattr(store, "db_path", "")) == ":memory:":
        return None
    try:
        connection = getattr(store, "connection", None)
    except Exception:
        return None
    if connection is None:
        return None
    if not all(hasattr(connection, name) for name in ("execute", "commit", "rollback")):
        return None
    return connection


def _sqlite_restore_store(store: Any) -> Any:
    """Use the SQLite primary when bundle restore receives a dual-write store."""
    primary = getattr(store, "primary", None)
    return primary if primary is not None else store


def _rowcount(cursor: Any) -> int:
    return max(int(getattr(cursor, "rowcount", 0) or 0), 0)


def _items(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _rl_items(value: Any) -> list[tuple[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [(str(key), data if data is not None else {}) for key, data in value.items()]
    if isinstance(value, list):
        rows: list[tuple[str, Any]] = []
        for item in value:
            if isinstance(item, dict) and item.get("key") is not None:
                rows.append((str(item["key"]), item.get("data") or item.get("data_json") or {}))
        return rows
    return []


def _verified_outcomes(decisions: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for decision in decisions:
        if decision.get("verified") is True:
            outcome = decision.get("outcome")
            rows.append((decision, outcome if isinstance(outcome, dict) else decision))
    return rows


def _decision_values(decision: dict[str, Any], domain: str) -> tuple[Any, ...]:
    confidence = float(decision.get("confidence", 0.0))
    metadata = dict(decision.get("metadata") or {})
    decision_id = str(decision["decision_id"])
    entity_id = str(decision.get("entity_id") or metadata.get("entity_id") or decision_id)
    metadata.setdefault("entity_id", entity_id)
    metadata.setdefault("decision_id", decision_id)

    factors = dict(decision.get("factors") or {})
    stored_factors = {**factors, "entity_id": entity_id, "metadata": metadata}
    factor_vector = decision.get("factor_vector")
    if factor_vector is None:
        factor_vector = list(factors.values())

    probabilities = decision.get("probabilities")
    if probabilities is None:
        probabilities = [confidence]

    return (
        decision_id,
        domain,
        str(decision.get("category", "")),
        int(decision.get("category_index", 0)),
        _to_json(stored_factors),
        _to_json(factor_vector),
        str(decision.get("recommended_action") or decision.get("action") or ""),
        int(decision.get("recommended_index", 0)),
        confidence,
        _to_json(probabilities),
        float(decision.get("created_at", time.time())),
    )


def _outcome_values(
    decision: dict[str, Any],
    outcome: dict[str, Any],
    domain: str,
) -> tuple[Any, ...]:
    actual_action = outcome.get("actual_action") or decision.get("recommended_action") or decision.get("action") or ""
    context = outcome.get("context", decision.get("context"))
    is_correct = _coerce_correctness(outcome.get("is_correct"))
    return (
        str(decision["decision_id"]),
        domain,
        str(actual_action),
        int(outcome.get("actual_index", decision.get("recommended_index", 0))),
        None if is_correct is None else (1 if is_correct else 0),
        float(outcome.get("verified_at", decision.get("verified_at", decision.get("created_at", time.time())))),
        _to_json(context) if context is not None else None,
    )


def _coerce_correctness(value: Any) -> bool | None:
    """Normalize bundle correctness without treating missing values as verified."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
        return None
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
    return None


def _checkpoint_values(
    checkpoint: dict[str, Any],
    domain: str,
    decisions_count: int,
) -> tuple[Any, ...]:
    metadata = dict(checkpoint.get("metadata") or {})
    return (
        domain,
        checkpoint.get("decision_id"),
        checkpoint.get("category"),
        _to_json(checkpoint.get("centroids", [])),
        int(checkpoint.get("decisions_count", decisions_count)),
        float(checkpoint.get("iks", metadata.get("iks", 0.0))),
        _to_json(metadata),
        float(checkpoint.get("created_at", time.time())),
        checkpoint.get("decision_time_start"),
        checkpoint.get("decision_time_end"),
        checkpoint.get("checkpoint_time"),
    )


def _event_values(event: dict[str, Any], domain: str) -> tuple[Any, ...]:
    return (
        domain,
        str(event.get("event_type", "")),
        str(event.get("rule_name", "")),
        str(event.get("variant_id", "")),
        _to_json(event.get("metadata") or {}),
        str(event.get("timestamp") or _iso_timestamp()),
    )


def _timestamp(value: Any) -> float:
    if isinstance(value, dict):
        return float(value.get("updated_at", time.time()))
    return time.time()


def _iso_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _to_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True)
