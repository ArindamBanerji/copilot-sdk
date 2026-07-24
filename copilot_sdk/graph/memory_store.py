"""In-memory GraphStore implementation for tests and demos."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import datetime, timezone
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


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


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
        "canonical_payload": deepcopy(canonical_payload),
        "actor": actor,
        "source_route": source_route,
        "metadata": deepcopy(metadata or {}),
    }
    encoded = json.dumps(
        payload,
        default=_json_default,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class InMemoryGraphStore:
    """Dictionary-backed domain-aware decision and outcome store."""

    def __init__(self, domain: str = "test", decision_id_prefix: str = "") -> None:
        self.domain = str(domain)
        self._decision_id_prefix = str(decision_id_prefix or "")
        self._decisions: dict[str, dict[str, Any]] = {}
        self._outcomes: dict[str, dict[str, Any]] = {}
        self._observations: dict[str, dict[str, Any]] = {}
        self._observation_entity_edges: list[dict[str, Any]] = []
        self._observation_factor_vectors: dict[str, dict[str, Any]] = {}
        self._evidence_receipts: dict[tuple[str, str], dict[str, Any]] = {}
        self._evidence_receipt_chains: dict[str, list[str]] = {}
        self._conservation_snapshots: dict[str, dict[str, Any]] = {}
        self._fingerprints: dict[str, dict[str, Any]] = {}
        self._protocol_centroid_checkpoints: dict[str, dict[str, Any]] = {}
        self._l5_centroids: dict[tuple[str, str, str], dict[str, object]] = {}
        self._l5_dk_weights: dict[str, list[dict[str, object]]] = {}
        self._l5_dk_weight_counter: int = 0
        self._l5_conservation_state: dict[str, dict[str, object]] = {}
        self._l5_conservation_state_counter: int = 0
        self._protocol_evolution_events: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        self._centroid_checkpoints: list[dict[str, Any]] = []
        self._evolution_events: list[dict[str, Any]] = []
        self._rl_state: dict[tuple[str, str], dict[str, Any]] = {}
        self._archive: list[dict[str, Any]] = []
        self._outbox: list[dict[str, Any]] = []
        self._outbox_quarantine: list[dict[str, Any]] = []
        self._entity_enrichments: dict[tuple[str, str, str, str, str], EntityEnrichmentRecord] = {}
        self._outbox_counter = 0
        self._quarantine_counter = 0
        self._sequence = 0

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
        matches = [
            row
            for row in self._outbox
            if row["domain"] == domain
            and row["operation_type"] == operation_type
            and row["target_key"] == target_key
        ]
        for row in matches:
            if row["payload_hash"] == payload_hash:
                return int(row["outbox_id"])
        if matches:
            original = sorted(matches, key=lambda row: int(row["outbox_id"]))[0]
            self._quarantine_counter += 1
            self._outbox_quarantine.append(
                {
                    "quarantine_id": self._quarantine_counter,
                    "domain": domain,
                    "outbox_id": original["outbox_id"],
                    "operation_type": operation_type,
                    "target_key": target_key,
                    "existing_payload_hash": original["payload_hash"],
                    "new_payload_hash": payload_hash,
                    "new_payload_json": payload_json,
                    "reason": "payload_hash_conflict",
                    "quarantined_at": _utc_iso_now(),
                    "resolved_at": None,
                    "resolution": None,
                }
            )
            raise ValueError(
                "outbox payload_hash_conflict quarantined for "
                f"{domain}:{operation_type}:{target_key}"
            )

        now = _utc_iso_now()
        self._outbox_counter += 1
        self._outbox.append(
            {
                "outbox_id": self._outbox_counter,
                "domain": domain,
                "operation_type": operation_type,
                "target_key": target_key,
                "payload_json": payload_json,
                "payload_hash": payload_hash,
                "causal_decision_id": causal_decision_id,
                "status": "pending",
                "attempt_count": 0,
                "last_error_redacted": None,
                "schema_version": 1,
                "created_at": now,
                "updated_at": now,
                "replayed_at": None,
            }
        )
        return self._outbox_counter

    def write_decision(
        self,
        domain: str,
        category: str,
        action: str,
        confidence: float,
        factors: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        self._sequence += 1
        decision_id = str((metadata or {}).get("decision_id") or uuid.uuid4().hex[:12])
        if self._decision_id_prefix and not decision_id.startswith(self._decision_id_prefix):
            decision_id = f"{self._decision_id_prefix}{decision_id}"
        decision_metadata = deepcopy(metadata or {})
        if self._decision_id_prefix or "decision_id" in decision_metadata:
            decision_metadata["decision_id"] = decision_id
        entity_id = str(decision_metadata.get("entity_id") or decision_id)
        if "entity_id" not in decision_metadata:
            decision_metadata["entity_id"] = entity_id
        created_at = float((metadata or {}).get("created_at", time.time()))
        category_index = int((metadata or {}).get("category_index", 0))
        recommended_index = int((metadata or {}).get("recommended_index", 0))
        factor_vector = deepcopy((metadata or {}).get("factor_vector"))
        if factor_vector is None:
            factor_vector = [float(factors[name]) for name in factors]
        probabilities = deepcopy((metadata or {}).get("probabilities"))
        if probabilities is None:
            probabilities = [float(confidence)]
        self._decisions[decision_id] = {
            "decision_id": decision_id,
            "domain": str(domain),
            "entity_id": entity_id,
            "category": category,
            "category_index": category_index,
            "recommended_action": action,
            "recommended_index": recommended_index,
            "confidence": float(confidence),
            "factors": deepcopy(factors),
            "factor_vector": factor_vector,
            "probabilities": probabilities,
            "status": "pending",
            "metadata": decision_metadata,
            "created_at": created_at,
            "_sequence": self._sequence,
        }
        return decision_id

    def generate_decision_id(self, domain: str) -> str:
        """Return a bare unique ID for the in-memory protocol test store."""
        _ = domain
        return uuid.uuid4().hex[:12]

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
        meta = deepcopy(metadata or {})
        meta.update(
            {
                "decision_id": str(decision_id),
                "category_index": int(category_index),
                "recommended_index": int(recommended_index),
                "probabilities": [float(value) for value in probabilities],
                "factor_vector": [float(value) for value in factor_vector],
                "factor_names": list(factor_names),
                "source": source,
                "scorer_version": scorer_version,
                "preset_version": preset_version,
                "factor_schema_version": factor_schema_version,
            }
        )
        factors = {
            name: float(value)
            for name, value in zip(factor_names, factor_vector, strict=False)
        }
        existing = self._decisions.get(str(decision_id))
        if existing is not None:
            proposed = {
                "domain": str(domain),
                "category": category,
                "category_index": int(category_index),
                "recommended_action": recommended_action,
                "recommended_index": int(recommended_index),
                "confidence": float(confidence),
                "factors": factors,
                "factor_vector": meta["factor_vector"],
                "probabilities": meta["probabilities"],
            }
            current = {key: existing.get(key) for key in proposed}
            if current == proposed:
                return None
            raise ValueError(f"conflicting governed decision_id: {decision_id}")
        self.write_decision(
            str(domain),
            category,
            recommended_action,
            float(confidence),
            factors,
            metadata=meta,
        )
        return None

    def write_outcome(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
        domain: str | None = None,
    ) -> None:
        if decision_id not in self._decisions:
            raise KeyError(decision_id)
        if domain is not None and self._decisions[decision_id].get("domain") != domain:
            raise KeyError(decision_id)
        if decision_id in self._outcomes:
            raise ValueError(f"outcome already exists for decision_id: {decision_id}")
        meta = metadata or {}
        self._outcomes[decision_id] = {
            "decision_id": decision_id,
            "domain": self._decisions[decision_id].get("domain", self.domain),
            "actual_action": actual_action,
            "actual_index": int(meta.get("actual_index", 0)),
            "is_correct": bool(is_correct),
            "metadata": deepcopy(meta),
            "context": deepcopy(meta.get("context", {})),
            "verified_at": float(meta.get("verified_at", time.time())),
        }
        self._decisions[decision_id]["status"] = "confirmed" if is_correct else "overridden"

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
        if observation_id in self._observations:
            return None
        created_at = float((metadata or {}).get("created_at", time.time()))
        self._observations[observation_id] = {
            "observation_id": observation_id,
            "domain": str(domain),
            "category": category,
            "recommended_action": recommended_action,
            "confidence": float(confidence),
            "source_route": source_route,
            "scorer_version": scorer_version,
            "factor_schema_version": factor_schema_version,
            "metadata": deepcopy(metadata or {}),
            "created_at": created_at,
        }
        if entity_id is not None:
            self._observation_entity_edges.append(
                {
                    "domain": str(domain),
                    "observation_id": observation_id,
                    "entity_id": str(entity_id),
                    "edge_type": "ABOUT",
                    "created_at": created_at,
                }
            )
        if factor_vector is not None:
            self._observation_factor_vectors[observation_id] = {
                "domain": str(domain),
                "observation_id": observation_id,
                "dimension": len(factor_vector),
                "factor_names": list(factor_names or []),
                "factor_vector": [float(value) for value in factor_vector],
                "created_at": created_at,
            }
        return None

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
        key = (domain, receipt_intent_id)
        payload_hash = _receipt_payload_hash(
            receipt_intent_id,
            domain,
            decision_id,
            canonical_payload,
            actor,
            source_route,
            metadata,
        )
        existing = self._evidence_receipts.get(key)
        if existing is not None:
            if existing["payload_hash"] == payload_hash:
                return int(existing["chain_index"]), str(existing["payload_hash"])
            raise ValueError(f"conflicting evidence receipt_intent_id: {receipt_intent_id}")

        chain = self._evidence_receipt_chains.setdefault(domain, [])
        chain_index = len(chain)
        previous_hash = "GENESIS" if not chain else chain[-1]
        receipt = {
            "receipt_intent_id": receipt_intent_id,
            "domain": domain,
            "decision_id": decision_id,
            "chain_index": chain_index,
            "previous_hash": previous_hash,
            "payload_hash": payload_hash,
            "actor": actor,
            "source_route": source_route,
            "canonical_payload": deepcopy(canonical_payload),
            "metadata": deepcopy(metadata or {}),
            "created_at": time.time(),
        }
        self._evidence_receipts[key] = receipt
        chain.append(payload_hash)
        return chain_index, payload_hash

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
        status_id = str(status_id)
        snapshot_payload = {
            "snapshot_id": status_id,
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
        existing = self._conservation_snapshots.get(status_id)
        if existing is not None:
            existing_payload = {
                key: existing[key]
                for key in snapshot_payload
            }
            if existing_payload == snapshot_payload:
                return None
            raise ValueError(f"conflicting conservation status_id: {status_id}")
        self._conservation_snapshots[status_id] = {
            **snapshot_payload,
            "computed_at": time.time(),
        }
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
        fingerprint_id = str(fingerprint_id)
        fingerprint_payload = {
            "fingerprint_id": fingerprint_id,
            "domain": str(domain),
            "factor_names": list(factor_names),
            "factor_stats": deepcopy(factor_stats),
            "skipped_incompatible": int(skipped_incompatible),
            "window": int(window),
            "metadata": deepcopy(metadata or {}),
        }
        existing = self._fingerprints.get(fingerprint_id)
        if existing is not None:
            existing_payload = {key: existing[key] for key in fingerprint_payload}
            if existing_payload == fingerprint_payload:
                return None
            raise ValueError(f"conflicting fingerprint_id: {fingerprint_id}")
        self._fingerprints[fingerprint_id] = {
            **fingerprint_payload,
            "created_at": time.time(),
        }
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
        checkpoint_id = str(checkpoint_id)
        checkpoint_payload = {
            "checkpoint_id": checkpoint_id,
            "domain": str(domain),
            "category": category,
            "action": action,
            "centroids": deepcopy(centroids),
            "decisions_count": int(decisions_count),
            "verified_count": int(verified_count),
            "iks": float(iks),
            "shape": [int(value) for value in shape],
            "factor_names_hash": str(factor_names_hash),
            "metadata": deepcopy(metadata or {}),
        }
        existing = self._protocol_centroid_checkpoints.get(checkpoint_id)
        if existing is not None:
            existing_payload = {key: existing[key] for key in checkpoint_payload}
            if existing_payload == checkpoint_payload:
                return None
            raise ValueError(f"conflicting checkpoint_id: {checkpoint_id}")
        self._protocol_centroid_checkpoints[checkpoint_id] = {
            **checkpoint_payload,
            "created_at": time.time(),
        }
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
        event_id = str(event_id)
        event_payload = {
            "event_id": event_id,
            "domain": str(domain),
            "event_type": event_type,
            "rule_name": rule_name,
            "variant_id": variant_id,
            "source_copilot": source_copilot,
            "source_rule": source_rule,
            "metric": None if metric is None else float(metric),
            "shadow_batch_size": None if shadow_batch_size is None else int(shadow_batch_size),
            "min_shadow_batches": None if min_shadow_batches is None else int(min_shadow_batches),
            "metadata": deepcopy(metadata or {}),
        }
        existing = self._protocol_evolution_events.get(event_id)
        if existing is not None:
            existing_payload = {key: existing[key] for key in event_payload}
            if existing_payload == event_payload:
                return None
            raise ValueError(f"conflicting evolution event_id: {event_id}")
        self._protocol_evolution_events[event_id] = {
            **event_payload,
            "created_at": time.time(),
        }
        self._evolution_events.append(
            {
                "domain": event_payload["domain"],
                "event_type": event_type,
                "rule_name": rule_name,
                "variant_id": variant_id,
                "metadata": deepcopy(metadata or {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_id": event_id,
                "source_copilot": source_copilot,
                "source_rule": source_rule,
                "metric": event_payload["metric"],
                "shadow_batch_size": event_payload["shadow_batch_size"],
                "min_shadow_batches": event_payload["min_shadow_batches"],
            }
        )
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
        if decision_id not in self._decisions:
            raise KeyError(decision_id)
        if self._decisions[decision_id].get("domain") != domain:
            raise KeyError(decision_id)
        edge = {
            "domain": domain,
            "decision_id": decision_id,
            "entity_id": str(entity_id),
            "entity_type": str(entity_type),
            "edge_type": "DECIDED_ON",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        for existing in self._edges:
            if (
                existing.get("domain") == edge["domain"]
                and existing.get("decision_id") == edge["decision_id"]
                and existing.get("entity_id") == edge["entity_id"]
            ):
                return None
        self._edges.append(edge)
        return None

    def _check_outcome_replay(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Classify future outbox replay without mutating outcome state."""
        if decision_id not in self._decisions:
            return "missing"
        outcome = self._outcomes.get(decision_id)
        if outcome is None:
            return "needs_apply"
        meta = metadata or {}
        if (
            outcome["actual_action"] == actual_action
            and int(outcome["actual_index"]) == int(meta.get("actual_index", 0))
            and bool(outcome["is_correct"]) is bool(is_correct)
        ):
            return "already_applied"
        return "conflict"

    def get_decision(self, decision_id: str, domain: str | None = None) -> dict[str, Any] | None:
        decision = self._decisions.get(decision_id)
        if decision is not None and domain is not None and decision.get("domain") != domain:
            return None
        return deepcopy(decision) if decision is not None else None

    def get_decisions(
        self,
        domain: str,
        category: str | None = None,
        limit: int = 400,
    ) -> list[dict[str, Any]]:
        decisions = [
            decision
            for decision in self._ordered_decisions()
            if decision.get("domain") == domain
            and (category is None or decision["category"] == category)
        ]
        return deepcopy(decisions[: max(int(limit), 0)])

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return self.get_decisions(domain, category=None, limit=len(self._decisions))

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        verified = []
        for decision in self._ordered_decisions():
            if decision.get("domain") != domain:
                continue
            outcome = self._outcomes.get(decision["decision_id"])
            if outcome is None:
                continue
            merged = dict(decision)
            merged.update({
                "actual_action": outcome["actual_action"],
                "actual_index": outcome["actual_index"],
                "is_correct": outcome["is_correct"],
                "verified_at": outcome["verified_at"],
                "context": deepcopy(outcome["context"]),
                "outcome_metadata": deepcopy(outcome["metadata"]),
            })
            verified.append(merged)
        return deepcopy(verified)

    def count_verified(self, domain: str) -> int:
        return len(self.get_verified_decisions(domain))

    def count_verified_decisions(self, domain: str) -> int:
        return sum(
            1
            for decision in self._decisions.values()
            if decision.get("domain") == domain
            and (
                decision.get("status") in {"confirmed", "overridden"}
                or decision.get("decision_id") in self._outcomes
            )
        )

    def count_correct(self, domain: str) -> int:
        return sum(
            1
            for outcome in self._outcomes.values()
            if outcome.get("domain") == domain and outcome["is_correct"]
        )

    def count_decisions(self, domain: str) -> int:
        return sum(1 for decision in self._decisions.values() if decision.get("domain") == domain)

    def update_centroid(
        self,
        domain: str,
        category: str,
        action: str,
        centroid_vector: list[float],
        delta_norm: float,
        caused_by_decision_id: str | None = None,
    ) -> None:
        domain_value = str(domain)
        category_value = str(category)
        action_value = str(action)
        vector = _normalize_centroid_vector(centroid_vector)
        self._l5_centroids[(domain_value, category_value, action_value)] = {
            "category": category_value,
            "action": action_value,
            "vector_json": list(vector),
            "delta_norm": float(delta_norm),
            "caused_by_decision_id": None
            if caused_by_decision_id is None
            else str(caused_by_decision_id),
            "updated_at": _utc_iso_now(),
        }
        return None

    def get_centroids(self, domain: str) -> list[dict[str, object]]:
        domain_value = str(domain)
        rows = [
            row
            for (row_domain, _category, _action), row in self._l5_centroids.items()
            if row_domain == domain_value
        ]
        ordered = sorted(rows, key=lambda row: (str(row["category"]), str(row["action"])))
        return [
            {
                "category": row["category"],
                "action": row["action"],
                "vector_json": list(cast(list[float], row["vector_json"])),
                "delta_norm": row["delta_norm"],
                "caused_by_decision_id": row["caused_by_decision_id"],
                "updated_at": row["updated_at"],
            }
            for row in ordered
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
        domain_value = str(domain)
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
        history = self._l5_dk_weights.setdefault(domain_value, [])
        current = next((row for row in history if row.get("is_current") is True), None)
        old_id = cast(int | None, current.get("id")) if current is not None else None
        if current is not None:
            current["is_current"] = False
        self._l5_dk_weight_counter += 1
        history.append(
            {
                "id": self._l5_dk_weight_counter,
                "domain": domain_value,
                "weight_json": [list(row) for row in tensor],
                "n_decisions_used": decisions_used,
                "computed_at": computed_at_value,
                "supersedes_id": old_id,
                "is_current": True,
                "created_at": _utc_iso_now(),
                "welford_state": deepcopy(normalized_welford),
                "n_confirmed": confirmed_count,
                "n_overridden": overridden_count,
                "entity_group": entity_group_value,
            }
        )
        return None

    def get_dk_weights(self, domain: str) -> dict[str, object] | None:
        history = self._l5_dk_weights.get(str(domain), [])
        current = next((row for row in reversed(history) if row.get("is_current") is True), None)
        if current is None:
            return None
        tensor = cast(list[list[float]], current["weight_json"])
        return {
            "weight_json": [list(row) for row in tensor],
            "n_decisions_used": current["n_decisions_used"],
            "computed_at": current["computed_at"],
            "supersedes_id": current["supersedes_id"],
            "created_at": current["created_at"],
            "domain": current["domain"],
            "welford_state": deepcopy(current.get("welford_state")),
            "n_confirmed": current.get("n_confirmed"),
            "n_overridden": current.get("n_overridden"),
            "entity_group": current.get("entity_group"),
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
        domain_value = cast(str, state["domain"])
        existing = self._l5_conservation_state.get(domain_value)
        if existing is None:
            self._l5_conservation_state_counter += 1
            state_id = str(self._l5_conservation_state_counter)
        else:
            state_id = cast(str, existing["id"])
        self._l5_conservation_state[domain_value] = {
            "id": state_id,
            **state,
            "updated_at": _utc_iso_now(),
        }
        return state_id

    def get_conservation_state(self, domain: str) -> dict[str, object] | None:
        row = self._l5_conservation_state.get(str(domain))
        if row is None:
            return None
        return dict(row)

    def save_centroids(
        self,
        domain: str,
        category: str,
        centroids: Any,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._centroid_checkpoints.append(
            {
                "domain": str(domain),
                "decision_id": kwargs.get("decision_id"),
                "category": category,
                "centroids": deepcopy(centroids),
                "decisions_count": self.count_decisions(str(domain)),
                "iks": float((metadata or {}).get("iks", 0.0)),
                "metadata": deepcopy(metadata or {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "decision_time_start": kwargs.get("decision_time_start"),
                "decision_time_end": kwargs.get("decision_time_end"),
                "checkpoint_time": kwargs.get("checkpoint_time") or _utc_iso_now(),
            }
        )

    def load_latest_centroids(self, domain: str) -> Any | None:
        checkpoints = [
            checkpoint
            for checkpoint in self._centroid_checkpoints
            if checkpoint.get("domain") == domain
        ]
        if not checkpoints:
            return None
        return deepcopy(checkpoints[-1]["centroids"])

    def save_rl_state(self, key: str, data: dict) -> None:
        self._rl_state[(self.domain, str(key))] = deepcopy(dict(data))

    def load_rl_state(self, key: str) -> dict | None:
        data = self._rl_state.get((self.domain, str(key)))
        return deepcopy(data) if data is not None else None

    def get_centroid_checkpoints(
        self,
        domain: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        limit_value = kwargs.get("limit", 50)
        checkpoints = [
            checkpoint
            for checkpoint in self._centroid_checkpoints
            if checkpoint.get("domain") == domain
            and _matches_checkpoint_filters(
                checkpoint,
                checkpoint_time_start=kwargs.get("checkpoint_time_start"),
                checkpoint_time_end=kwargs.get("checkpoint_time_end"),
                decision_time_start=kwargs.get("decision_time_start"),
                decision_time_end=kwargs.get("decision_time_end"),
                category=kwargs.get("category"),
            )
        ]
        if limit_value is None:
            return deepcopy(checkpoints)
        limit_value = max(int(limit_value), 0)
        if limit_value == 0:
            return []
        return deepcopy(checkpoints[-limit_value:])

    def save_evolution_event(
        self,
        domain: str,
        event_type: str,
        rule_name: str = "",
        variant_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._evolution_events.append(
            {
                "domain": str(domain),
                "event_type": event_type,
                "rule_name": rule_name,
                "variant_id": variant_id,
                "metadata": deepcopy(metadata or {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_evolution_events(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]:
        rule_name = kwargs.get("rule_name")
        limit = max(int(kwargs.get("limit", 100)), 0)
        events = [
            event
            for event in self._evolution_events
            if event.get("domain") == domain
            and (rule_name is None or event.get("rule_name") == rule_name)
        ]
        return deepcopy(events[-limit:] if limit else [])

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

        for metric_name, value in allowed.items():
            key = (domain, entity_type, entity_id, namespace, metric_name)
            self._entity_enrichments[key] = EntityEnrichmentRecord(
                domain=domain,
                entity_type=entity_type,
                entity_id=entity_id,
                namespace=namespace,
                metric_name=metric_name,
                value=deepcopy(value),
                computed_from=deepcopy(computed_from),
                computed_at=computed_at,
                idempotency_key=str(idempotency_key or ""),
            )
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
        result: dict[str, ProvenancedValue] = {}
        for (row_domain, row_type, row_id, row_namespace, metric_name), record in sorted(
            self._entity_enrichments.items()
        ):
            if row_domain != str(domain) or row_type != str(entity_type) or row_id != str(entity_id):
                continue
            if namespace is not None and row_namespace != str(namespace):
                continue
            key = metric_name if namespace is not None else f"{row_namespace}.{metric_name}"
            result[key] = deepcopy(record.value)
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
        records = [
            record
            for (row_domain, row_type, _row_id, row_namespace, _metric), record in sorted(
                self._entity_enrichments.items()
            )
            if row_domain == str(domain)
            and (entity_type is None or row_type == str(entity_type))
            and (namespace is None or row_namespace == str(namespace))
        ]
        return deepcopy(records[:limit_value])

    def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int:
        keep_recent = max(int(keep_recent), 0)
        decisions = [
            decision
            for decision in self._ordered_decisions()
            if decision.get("domain") == domain
        ]
        if len(decisions) <= keep_recent:
            return 0
        to_archive = decisions[: len(decisions) - keep_recent]
        archived_at = time.time()
        for decision in to_archive:
            decision_id = decision["decision_id"]
            outcome = self._outcomes.get(decision_id)
            self._archive.append(
                {
                    "decision": deepcopy(decision),
                    "outcome": deepcopy(outcome),
                    "domain": domain,
                    "archived_at": archived_at,
                    "archive_reason": "retention_window",
                }
            )
            self._outcomes.pop(decision_id, None)
            self._decisions.pop(decision_id, None)
            self._edges = [
                edge for edge in self._edges if edge.get("decision_id") != decision_id
            ]
        return len(to_archive)

    def count_archived(self, domain: str) -> int:
        return sum(1 for row in self._archive if row.get("domain") == domain)

    def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for archived in self._archive:
            if archived.get("domain") != str(domain):
                continue
            decision = archived["decision"]
            outcome = archived.get("outcome") or {}
            actual_index = outcome.get("actual_index")
            is_correct = outcome.get("is_correct")
            verified_at = outcome.get("verified_at")
            records.append(
                {
                    "decision_id": decision["decision_id"],
                    "domain": decision["domain"],
                    "category": decision["category"],
                    "category_index": int(decision["category_index"]),
                    "recommended_action": decision["recommended_action"],
                    "recommended_index": int(decision["recommended_index"]),
                    "confidence": float(decision["confidence"]),
                    "factor_vector": [float(value) for value in decision["factor_vector"]],
                    "probabilities": [float(value) for value in decision["probabilities"]],
                    "created_at": float(decision["created_at"]),
                    "actual_action": outcome.get("actual_action"),
                    "actual_index": int(actual_index) if actual_index is not None else None,
                    "is_correct": bool(is_correct) if is_correct is not None else None,
                    "verified_at": float(verified_at) if verified_at is not None else None,
                    "archived_at": float(archived["archived_at"]),
                    "archive_reason": archived["archive_reason"],
                }
            )
        return sorted(records, key=lambda record: (record["created_at"], record["decision_id"]))

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
        to_archive = [
            decision
            for decision in self._ordered_decisions()
            if decision.get("domain") == domain
            and decision.get("status") == status_filter
            and float(decision.get("created_at", 0.0)) < float(before)
        ]
        archived_at = time.time()
        for decision in to_archive:
            decision_id = decision["decision_id"]
            outcome = self._outcomes.get(decision_id)
            self._archive.append(
                {
                    "decision": deepcopy(decision),
                    "outcome": deepcopy(outcome),
                    "domain": domain,
                    "archived_at": archived_at,
                    "archive_reason": f"protocol_v2_{status_filter}",
                }
            )
            self._outcomes.pop(decision_id, None)
            self._decisions.pop(decision_id, None)
            self._edges = [
                edge for edge in self._edges if edge.get("decision_id") != decision_id
            ]
        return len(to_archive)

    def domain_scoped_reset(self, domain: str) -> None:
        domain = str(domain)
        decision_ids = {
            decision_id
            for decision_id, decision in self._decisions.items()
            if decision.get("domain") == domain
        }
        for decision_id in list(decision_ids):
            self._decisions.pop(decision_id, None)
            self._outcomes.pop(decision_id, None)
        self._outcomes = {
            decision_id: outcome
            for decision_id, outcome in self._outcomes.items()
            if outcome.get("domain") != domain
        }
        self._observations = {
            observation_id: observation
            for observation_id, observation in self._observations.items()
            if observation.get("domain") != domain
        }
        self._observation_entity_edges = [
            edge for edge in self._observation_entity_edges if edge.get("domain") != domain
        ]
        self._observation_factor_vectors = {
            observation_id: vector
            for observation_id, vector in self._observation_factor_vectors.items()
            if vector.get("domain") != domain
        }
        self._evidence_receipts = {
            key: receipt
            for key, receipt in self._evidence_receipts.items()
            if receipt.get("domain") != domain
        }
        self._evidence_receipt_chains.pop(domain, None)
        self._conservation_snapshots = {
            snapshot_id: snapshot
            for snapshot_id, snapshot in self._conservation_snapshots.items()
            if snapshot.get("domain") != domain
        }
        self._fingerprints = {
            fingerprint_id: fingerprint
            for fingerprint_id, fingerprint in self._fingerprints.items()
            if fingerprint.get("domain") != domain
        }
        self._protocol_centroid_checkpoints = {
            checkpoint_id: checkpoint
            for checkpoint_id, checkpoint in self._protocol_centroid_checkpoints.items()
            if checkpoint.get("domain") != domain
        }
        self._l5_centroids = {
            key: centroid
            for key, centroid in self._l5_centroids.items()
            if key[0] != domain
        }
        self._l5_dk_weights.pop(domain, None)
        self._l5_conservation_state.pop(domain, None)
        self._centroid_checkpoints = [
            checkpoint
            for checkpoint in self._centroid_checkpoints
            if checkpoint.get("domain") != domain
        ]
        self._protocol_evolution_events = {
            event_id: event
            for event_id, event in self._protocol_evolution_events.items()
            if event.get("domain") != domain
        }
        self._evolution_events = [
            event for event in self._evolution_events if event.get("domain") != domain
        ]
        self._edges = [
            edge
            for edge in self._edges
            if edge.get("domain") != domain and edge.get("decision_id") not in decision_ids
        ]
        self._rl_state = {
            key: value
            for key, value in self._rl_state.items()
            if key[0] != domain
        }
        self._archive = [row for row in self._archive if row.get("domain") != domain]
        self._outbox = [row for row in self._outbox if row.get("domain") != domain]
        self._outbox_quarantine = [
            row for row in self._outbox_quarantine if row.get("domain") != domain
        ]
        self._entity_enrichments = {
            key: record
            for key, record in self._entity_enrichments.items()
            if key[0] != domain
        }
        return None

    def link_decision_to_entity(
        self,
        decision_id: str,
        entity_id: str,
        edge_type: str = "DECIDED_ON",
    ) -> None:
        decision = self._decisions.get(decision_id)
        domain = str((decision or {}).get("domain") or self.domain)
        self._edges.append(
            {
                "domain": domain,
                "decision_id": decision_id,
                "entity_id": entity_id,
                "edge_type": edge_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_decision_links(
        self,
        decision_id: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        limit_value = _bounded_traversal_limit(limit) if limit is not None else None
        links = [
            {
                key: value
                for key, value in edge.items()
                if key != "domain"
            }
            for edge in self._edges
            if edge.get("domain") == self.domain
            and (decision_id is None or edge["decision_id"] == decision_id)
        ]
        if limit_value is not None:
            links = links[:limit_value]
        return deepcopy(links)

    def query_context(self, entity_id: str, max_depth: int) -> list[dict[str, Any]]:
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
        root_links = self._entity_links(root_id, limit=100)
        linked_decision_ids = [str(edge["decision_id"]) for edge in root_links]
        if root_id in self._decisions and root_id not in linked_decision_ids:
            linked_decision_ids.insert(0, root_id)
        seen: set[str] = set()
        seen_entities: set[str] = {root_id}
        for decision_id in linked_decision_ids[:100]:
            if decision_id in seen:
                continue
            seen.add(decision_id)
            decision = self._decisions.get(decision_id)
            if decision is None:
                continue
            rows.append(
                {
                    "node": "decision",
                    "id": decision_id,
                    "depth": 1,
                    "properties": deepcopy(decision),
                }
            )
            if depth < 2:
                continue
            for edge in self.get_decision_links(decision_id, limit=100):
                if edge.get("decision_id") != decision_id:
                    continue
                neighbor_id = str(edge.get("entity_id") or "")
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
                            "edge_type": edge.get("edge_type"),
                            "provenance": "graph_store",
                        },
                    }
                )
                if depth < 3:
                    continue
                for neighbor_edge in self._entity_links(neighbor_id, limit=100):
                    neighbor_decision_id = str(neighbor_edge.get("decision_id") or "")
                    if not neighbor_decision_id or neighbor_decision_id in seen:
                        continue
                    neighbor_decision = self._decisions.get(neighbor_decision_id)
                    if neighbor_decision is None:
                        continue
                    seen.add(neighbor_decision_id)
                    rows.append(
                        {
                            "node": "decision",
                            "id": neighbor_decision_id,
                            "depth": 3,
                            "properties": deepcopy(neighbor_decision),
                        }
                    )
        return deepcopy(rows[:100])

    def _entity_links(self, entity_id: str, limit: int = 100) -> list[dict[str, Any]]:
        limit_value = _bounded_traversal_limit(limit)
        return [
            deepcopy(edge)
            for edge in self._edges
            if edge.get("domain") == self.domain and str(edge.get("entity_id")) == str(entity_id)
        ][:limit_value]

    def query_similar(self, entity_id: str, limit: int) -> list[dict[str, Any]]:
        limit_value = _bounded_traversal_limit(limit)
        source = self._decisions.get(str(entity_id))
        if source is None:
            for edge in self._entity_links(str(entity_id), limit=100):
                if edge.get("domain") == self.domain and str(edge.get("entity_id")) == str(entity_id):
                    source = self._decisions.get(str(edge.get("decision_id")))
                    break
        if source is None:
            return []
        category = str(source.get("category") or "")
        source_supplier = _decision_supplier(source)
        matches: list[dict[str, Any]] = []
        for candidate in self._ordered_decisions():
            if candidate.get("domain") != source.get("domain"):
                continue
            if category and candidate.get("category") != category:
                continue
            if candidate.get("decision_id") == source.get("decision_id"):
                continue
            if source_supplier and _decision_supplier(candidate) != source_supplier:
                continue
            matches.append(deepcopy(candidate))
            if len(matches) >= limit_value:
                break
        return matches

    def reset(self) -> None:
        self._decisions.clear()
        self._outcomes.clear()
        self._edges.clear()
        self._centroid_checkpoints.clear()
        self._protocol_centroid_checkpoints.clear()
        self._l5_centroids.clear()
        self._l5_dk_weights.clear()
        self._l5_conservation_state.clear()
        self._fingerprints.clear()
        self._protocol_evolution_events.clear()
        self._evolution_events.clear()
        self._rl_state.clear()
        self._archive.clear()
        self._outbox.clear()
        self._outbox_quarantine.clear()
        self._outbox_counter = 0
        self._quarantine_counter = 0
        self._l5_dk_weight_counter = 0
        self._l5_conservation_state_counter = 0
        self._sequence = 0

    def close(self) -> None:
        return None

    def _ordered_decisions(self) -> list[dict[str, Any]]:
        return sorted(
            self._decisions.values(),
            key=lambda decision: (decision["created_at"], decision["_sequence"], decision["decision_id"]),
        )


def _matches_checkpoint_filters(
    checkpoint: dict[str, Any],
    *,
    checkpoint_time_start: str | None,
    checkpoint_time_end: str | None,
    decision_time_start: str | None,
    decision_time_end: str | None,
    category: str | None,
) -> bool:
    if category is not None and checkpoint.get("category") != category:
        return False
    checkpoint_time = checkpoint.get("checkpoint_time")
    if checkpoint_time_start is not None:
        if checkpoint_time is None or checkpoint_time < checkpoint_time_start:
            return False
    if checkpoint_time_end is not None:
        if checkpoint_time is None or checkpoint_time > checkpoint_time_end:
            return False
    stored_decision_start = checkpoint.get("decision_time_start")
    if decision_time_start is not None:
        if stored_decision_start is None or stored_decision_start < decision_time_start:
            return False
    stored_decision_end = checkpoint.get("decision_time_end")
    if decision_time_end is not None:
        if stored_decision_end is None or stored_decision_end > decision_time_end:
            return False
    return True


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
