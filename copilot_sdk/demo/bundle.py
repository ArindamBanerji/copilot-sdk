"""Restore synthetic demo bundles through graph-store APIs."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from copilot_sdk.timestamps import normalize_timestamp

from copilot_sdk.graph.protocol import GraphStore, ProtocolV2GraphStore, ScoringPersistenceStore

LOGGER = logging.getLogger(__name__)
DEFAULT_MIN_DECISIONS_TO_SKIP = 180
# Bounded event reads cannot prove a total at this ceiling. AGE-SDK #11 tracks
# the missing count/pagination contract; apply the same safe bound to all stores.
EVENT_COUNT_LIMIT = 1000


@dataclass(frozen=True)
class RestoreReport:
    stores_restored: int = 0
    stores_failed: int = 0
    failed_stores: list[str] = field(default_factory=list)
    fully_restored: bool = False
    restored_count: int = 0
    skipped_count: int = 0
    section_counts: dict[str, int] = field(default_factory=dict)
    skipped_stores: list[str] = field(default_factory=list)
    skipped_reasons: dict[str, str] = field(default_factory=dict)
    failed_reasons: dict[str, str] = field(default_factory=dict)
    replayed_count: int = 0
    section_replay_counts: dict[str, int] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Backward-compatible success: at least one record was written."""
        return self.restored_count > 0

    def __bool__(self) -> bool:
        return self.success


def restore_bundle_if_empty(
    store: GraphStore | ScoringPersistenceStore, bundle_path: Path, *, domain: str,
) -> RestoreReport:
    """Restore a cold domain; callers serialize concurrent startup restores.

    Writes are individually durable, not a cross-section transaction. A partial
    report must not be treated as complete merely because decisions were written.
    """
    path = Path(bundle_path)
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        LOGGER.exception("Unable to read demo bundle: %s", path)
        return _failed_report("bundle")
    if not isinstance(bundle, dict):
        LOGGER.error("Demo bundle must contain a JSON object: %s", path)
        return _failed_report("bundle")
    return _restore(store, bundle, domain)


def _failed_report(section: str) -> RestoreReport:
    return RestoreReport(stores_failed=1, failed_stores=[section])


def _items(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError("bundle section must be a list of objects")
    return value


def _rl_items(value: Any) -> list[tuple[str, dict[str, Any]]]:
    if value is None:
        return []
    if isinstance(value, dict) and isinstance(value.get("key"), str):
        key = value["key"]
        data = value.get("data", value.get(key))
        if data is None:
            data = {k: v for k, v in value.items() if k != "key"}
        elif isinstance(data, dict):
            data = dict(data)
            if "updated_at" in value:
                data.setdefault("updated_at", value["updated_at"])
        pairs = [(key, data)]
    elif isinstance(value, dict):
        pairs = list(value.items())
    else:
        pairs = [(row["key"], row.get("data", row.get("data_json"))) for row in _items(value)]
    result = []
    for key, data in pairs:
        if isinstance(data, str):
            data = json.loads(data)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ValueError(f"RL state {key!r} must be an object")
        result.append((str(key), data))
    return result


def _coerce_correctness(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        if value.strip().lower() in {"true", "1"}:
            return True
        if value.strip().lower() in {"false", "0"}:
            return False
    return None


def _synthetic_metadata(value: Any) -> dict[str, Any]:
    metadata = dict(value or {})
    if metadata.get("source") not in (None, "demo-bundle"):
        metadata.setdefault("original_source", metadata["source"])
    metadata.update(provenance="synthetic", source="demo-bundle", synthetic=True)
    return metadata


def _record_field(record: dict[str, Any], name: str, default: Any = None) -> Any:
    """Read public record fields, including fields retained in metadata."""
    return record.get(name, (record.get("metadata") or {}).get(name, default))


def _decision_payload(row: dict[str, Any], domain: str, names: Any) -> dict[str, Any]:
    metadata = _synthetic_metadata(row.get("metadata"))
    factors = dict(row.get("factors") or {})
    factor_names = row.get("factor_names", metadata.get("factor_names", names))
    vector = row.get("factor_vector")
    if not isinstance(factor_names, list) or any(not isinstance(name, str) for name in factor_names):
        raise ValueError("Demo bundle decision requires explicit factor_names (row or bundle schema)")
    if len(set(factor_names)) != len(factor_names):
        raise ValueError("factor_names must be unique")
    if vector is None:
        vector = [factors[name] for name in factor_names]
    if len(factor_names) != len(vector):
        raise ValueError("factor_names and factor_vector lengths differ")
    if factors and any(float(factors[name]) != float(value)
                       for name, value in zip(factor_names, vector)):
        raise ValueError("factor_names/vector do not match the factors mapping")
    decision_id = str(row["decision_id"])
    metadata["created_at"] = normalize_timestamp(row.get("created_at", metadata.get("created_at", time.time())))
    if row.get("entity_id") is not None:
        metadata["entity_id"] = row["entity_id"]
    confidence = float(row.get("confidence", 0.0))
    return {
        "decision_id": decision_id, "domain": domain,
        "category": str(row.get("category") or "unknown"),
        "category_index": int(row.get("category_index") or 0),
        "recommended_action": str(row.get("recommended_action") or row.get("action") or "unknown"),
        "recommended_index": int(row.get("recommended_index") or 0),
        "confidence": confidence,
        "probabilities": list(row["probabilities"]) if row.get("probabilities") is not None else [confidence],
        "factor_vector": list(vector), "factor_names": list(factor_names),
        "source": "demo-bundle", "metadata": metadata,
        "scorer_version": str(row.get("scorer_version") or ""),
        "preset_version": str(row.get("preset_version") or ""),
        "factor_schema_version": str(row.get("factor_schema_version") or ""),
    }


def _restore(
    store: GraphStore | ScoringPersistenceStore, bundle: dict[str, Any], domain: str,
) -> RestoreReport:
    if bundle.get("domain") != domain:
        LOGGER.error("Demo bundle domain mismatch: expected %s, got %s", domain, bundle.get("domain"))
        return _failed_report("domain")
    try:
        decisions = _items(bundle.get("decisions"))
        checkpoints = _items(bundle.get("centroid_checkpoints"))
        events = _items(bundle.get("evolution_events"))
        rl_state = _rl_items(bundle.get("rl_state"))
        outcomes = list(_items(bundle.get("outcomes")))
        for row in decisions:
            if row.get("verified") is True:
                nested = row.get("outcome")
                outcome = nested if isinstance(nested, dict) else row
                if _coerce_correctness(outcome.get("is_correct")) is not None:
                    outcomes.append({**outcome, "decision_id": row["decision_id"]})
        for row in [*decisions, *outcomes, *checkpoints, *events]:
            if row.get("domain", domain) != domain:
                raise ValueError("bundle record belongs to a different domain")
    except (KeyError, TypeError, ValueError):
        LOGGER.exception("Invalid demo bundle for domain %s", domain)
        return _failed_report("bundle")

    # Validate factor schema before the first write; never guess vector order.
    for decision in decisions:
        _decision_payload(decision, domain, bundle.get("factor_names"))

    # Resolve the declared capabilities before any mutation, not individual methods.
    graph_store = store if isinstance(store, GraphStore) else None
    governed_store = store if isinstance(store, ProtocolV2GraphStore) else None
    if graph_store is not None:
        try:
            current = graph_store.count_decisions(domain)
            if not isinstance(current, int) or isinstance(current, bool) or current < 0:
                raise ValueError("count_decisions must return a non-negative integer")
            if current >= int(bundle.get("min_decisions_to_skip", DEFAULT_MIN_DECISIONS_TO_SKIP)):
                return RestoreReport()
        except Exception:
            LOGGER.exception("Cannot determine whether demo domain %s is cold", domain)
            return _failed_report("count_decisions")

    counts: dict[str, int] = {}
    failed: list[str] = []
    skipped: list[str] = []
    skipped_reasons: dict[str, str] = {}
    failed_reasons: dict[str, str] = {}
    replay_counts: dict[str, int] = {}
    skipped_count = 0
    ready_decisions: set[str] = set()
    by_id = {str(row["decision_id"]): row for row in decisions if "decision_id" in row}

    def skip(section: str, count: int, reason: str) -> None:
        nonlocal skipped_count
        if not count:
            return
        counts[section] = 0
        skipped.append(section)
        skipped_count += count
        skipped_reasons[section] = reason
        LOGGER.warning("Demo bundle %s skipped: %s", section, reason)

    def apply(
        section: str, rows: list[dict[str, Any]], supported: bool,
        required_protocol: str, writer: Callable[[dict[str, Any]], bool],
    ) -> None:
        nonlocal skipped_count
        if not rows:
            return
        counts[section] = 0
        if not supported:
            skip(section, len(rows), f"{required_protocol} required")
            return
        replay_counts[section] = 0
        for row in rows:
            try:
                if writer(row):
                    counts[section] += 1
                else:
                    replay_counts[section] += 1
            except Exception as exc:
                skipped_count += 1
                if section not in failed:
                    failed.append(section)
                failed_reasons.setdefault(section, str(exc))
                LOGGER.exception("Demo bundle %s write failed for domain %s decision_id=%s",
                                 section, domain, row.get("decision_id") if isinstance(row, dict) else None)

    def write_decision(row: dict[str, Any]) -> bool:
        assert governed_store is not None
        payload = _decision_payload(row, domain, bundle.get("factor_names"))
        identifier = payload["decision_id"]
        existing = governed_store.get_decision(identifier, domain=domain)
        if existing is not None:
            fields = ("domain", "category", "category_index", "recommended_action",
                      "recommended_index", "confidence", "factor_vector", "probabilities")
            if not isinstance(existing, dict) or any(existing.get(key) != payload[key] for key in fields):
                raise ValueError(f"bundle decision conflicts with existing decision: {identifier}")
            for key in ("factor_names", "scorer_version", "preset_version", "factor_schema_version"):
                if _record_field(existing, key, "" if key != "factor_names" else None) != payload[key]:
                    raise ValueError(f"bundle decision conflicts on {key}: {identifier}")
            if ("created_at" in row or "created_at" in (row.get("metadata") or {})) and (
                _record_field(existing, "created_at") != payload["metadata"]["created_at"]
            ):
                raise ValueError(f"bundle decision conflicts on created_at: {identifier}")
            if (existing.get("metadata") or {}).get("provenance") != "synthetic":
                raise ValueError(f"bundle would reuse a non-synthetic decision: {identifier}")
            if _record_field(existing, "source") not in ("demo-bundle", "demo_bundle"):
                raise ValueError(f"bundle decision conflicts on source: {identifier}")
            ready_decisions.add(identifier)
            return False
        governed_store.write_governed_decision(**payload)
        ready_decisions.add(identifier)
        return True

    def write_outcome(row: dict[str, Any]) -> bool:
        assert graph_store is not None
        identifier = str(row["decision_id"])
        if identifier in by_id and identifier not in ready_decisions:
            raise ValueError(f"outcome's decision was not restored: {identifier}")
        decision = by_id.get(identifier, {})
        correct = _coerce_correctness(row.get("is_correct"))
        if correct is None:
            raise ValueError("outcome requires explicit boolean correctness")
        action = str(row.get("actual_action") or decision.get("recommended_action") or decision.get("action") or "")
        existing = graph_store.get_decision(identifier, domain=domain, include_outcome=True)
        metadata = _synthetic_metadata(row.get("metadata"))
        # Missing input time reuses the recorded value on replay; wall-clock
        # defaults must not manufacture a conflict for an otherwise identical row.
        default_verified_at = decision.get(
            "verified_at", decision.get("created_at", (existing or {}).get("verified_at", time.time()))
        )
        metadata.update(
            actual_index=int(row.get("actual_index", metadata.get("actual_index", decision.get("recommended_index", 0)))),
            verified_at=normalize_timestamp(row.get("verified_at", metadata.get("verified_at", default_verified_at))),
            context=row.get("context", metadata.get("context", decision.get("context", {}))),
        )
        if isinstance(existing, dict) and existing.get("actual_action") is not None:
            if existing["actual_action"] != action or existing.get("is_correct") != correct:
                raise ValueError(f"bundle outcome conflicts with existing outcome: {identifier}")
            outcome_metadata = existing.get("outcome_metadata") or {}
            for key in ("actual_index", "verified_at", "context"):
                if existing.get(key, outcome_metadata.get(key)) != metadata[key]:
                    raise ValueError(f"bundle outcome conflicts on {key}: {identifier}")
            return False
        graph_store.write_outcome(identifier, action, correct, metadata, domain=domain)
        return True

    def write_checkpoint(row: dict[str, Any]) -> bool:
        assert graph_store is not None
        metadata = _synthetic_metadata(row.get("metadata"))
        metadata["iks"] = float(row.get("iks", metadata.get("iks", 0.0)))
        graph_store.save_centroids(
            domain, str(row.get("category") or ""), row.get("centroids", []), metadata,
            decision_id=row.get("decision_id"),
            decisions_count=int(row.get("decisions_count", len(decisions))),
            created_at=normalize_timestamp(row.get("created_at", time.time())),
            decision_time_start=row.get("decision_time_start"),
            decision_time_end=row.get("decision_time_end"),
            checkpoint_time=row.get("checkpoint_time"),
        )
        return True

    def write_event(row: dict[str, Any]) -> bool:
        assert governed_store is not None
        metadata = _synthetic_metadata(row.get("metadata"))
        if row.get("timestamp") is not None:
            metadata["timestamp"] = row["timestamp"]
        event_id = str(row.get("event_id") or "demo-bundle-" + hashlib.sha256(
            json.dumps([domain, row], sort_keys=True).encode("utf-8")
        ).hexdigest())
        before = len(governed_store.get_evolution_events(domain, limit=EVENT_COUNT_LIMIT))
        if before >= EVENT_COUNT_LIMIT:
            raise ValueError(
                f"event inventory reached {EVENT_COUNT_LIMIT}; cannot count new records safely "
                "without a total-count/pagination protocol (AGE-SDK #11)"
            )
        governed_store.write_evolution_event(
            event_id=event_id, domain=domain, event_type=str(row.get("event_type") or ""),
            rule_name=str(row.get("rule_name") or ""), variant_id=str(row.get("variant_id") or ""),
            metadata=metadata, decision_id=row.get("decision_id"),
            source_copilot=row.get("source_copilot"), source_rule=row.get("source_rule"),
            metric=row.get("metric"), shadow_batch_size=row.get("shadow_batch_size"),
            min_shadow_batches=row.get("min_shadow_batches"),
        )
        after = len(governed_store.get_evolution_events(domain, limit=EVENT_COUNT_LIMIT))
        delta = after - before
        if delta not in (0, 1):
            raise ValueError("event inventory changed concurrently; restore requires exclusive startup ownership")
        return delta == 1

    apply("decisions", decisions, governed_store is not None, "ProtocolV2GraphStore", write_decision)
    apply("outcomes", outcomes, graph_store is not None, "GraphStore", write_outcome)
    apply("centroid_checkpoints", checkpoints, graph_store is not None, "GraphStore", write_checkpoint)
    # RL state: no protocol method exists; skip documented in REV-P4a
    skip("rl_state", len(rl_state), "no protocol method for RL state (REV-P4a)")
    apply("evolution_events", events, governed_store is not None, "ProtocolV2GraphStore", write_event)
    return RestoreReport(
        stores_restored=sum(value > 0 for value in counts.values()),
        stores_failed=len(failed), failed_stores=failed,
        fully_restored=not failed and not skipped,
        restored_count=sum(counts.values()), skipped_count=skipped_count,
        section_counts=counts, skipped_stores=skipped,
        skipped_reasons=skipped_reasons, failed_reasons=failed_reasons,
        replayed_count=sum(replay_counts.values()), section_replay_counts=replay_counts,
    )
