"""Primary-authoritative GraphStore wrapper with best-effort secondary writes."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar, cast

from copilot_sdk.graph.enrichment import (
    EnrichmentSourceSet,
    EntityEnrichmentReceipt,
    EntityEnrichmentRecord,
    ProvenancedValue,
)
from copilot_sdk.graph.protocol import GraphStore, ProtocolV2GraphStore


_T = TypeVar("_T")


class DualWriteStore(GraphStore):
    """Read from primary; write primary first and quarantine secondary failures."""

    def __init__(
        self,
        primary: GraphStore,
        secondary: GraphStore,
        logger: logging.Logger | None = None,
    ) -> None:
        # The wrapper exposes Protocol V2 writes as well as GraphStore.  Keep
        # the public constructor GraphStore-compatible for factory callers.
        self.primary = cast(ProtocolV2GraphStore, primary)
        self.secondary = cast(ProtocolV2GraphStore, secondary)
        self.logger = logger or logging.getLogger(__name__)
        self._secondary_failures: list[dict[str, Any]] = []

    @property
    def secondary_failures(self) -> list[dict[str, Any]]:
        return list(self._secondary_failures)

    @property
    def secondary_failure_count(self) -> int:
        return len(self._secondary_failures)

    def flush_secondary_failures(self) -> list[dict[str, Any]]:
        failures = list(self._secondary_failures)
        self._secondary_failures.clear()
        return failures

    @staticmethod
    def _args_summary(args: tuple[object, ...], kwargs: dict[str, object]) -> dict[str, object]:
        summary: dict[str, object] = {"arg_count": len(args), "keyword_names": sorted(kwargs)}
        for key in ("domain", "decision_id", "observation_id", "receipt_intent_id", "checkpoint_id", "event_id"):
            if key in kwargs:
                summary[key] = str(kwargs[key])
        return summary

    def _record_secondary_failure(
        self,
        operation: str,
        args: tuple[object, ...],
        kwargs: dict[str, object],
        error: Exception,
    ) -> None:
        unsupported = isinstance(error, NotImplementedError)
        entry: dict[str, object] = {
            "operation": operation,
            "status": "UNSUPPORTED" if unsupported else "SECONDARY_WRITE_FAILURE",
            "reason": "not_implemented" if unsupported else "secondary_exception",
            "error": f"{type(error).__name__}: {error}",
            "args": self._args_summary(args, kwargs),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._secondary_failures.append(entry)
        self.logger.warning("%s operation=%s error=%s", entry["status"], operation, entry["error"])

    def _write(
        self,
        operation: str,
        primary_call: Callable[[], _T],
        secondary_call: Callable[[], object],
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> _T:
        result = primary_call()
        try:
            secondary_call()
        except Exception as exc:  # Secondary is intentionally best-effort.
            self._record_secondary_failure(operation, args, kwargs, exc)
        return result

    def write_decision(self, domain: str, category: str, action: str, confidence: float, factors: dict[str, Any], metadata: dict[str, Any] | None = None) -> str:
        return self._write(
            "write_decision",
            lambda: self.primary.write_decision(domain, category, action, confidence, factors, metadata),
            lambda: self.secondary.write_decision(domain, category, action, confidence, factors, metadata),
            (domain, category, action, confidence, factors),
            {"metadata": metadata},
        )

    def write_outcome(self, decision_id: str, actual_action: str, is_correct: bool, metadata: dict[str, Any] | None = None) -> None:
        self._write("write_outcome", lambda: self.primary.write_outcome(decision_id, actual_action, is_correct, metadata), lambda: self.secondary.write_outcome(decision_id, actual_action, is_correct, metadata), (decision_id, actual_action, is_correct), {"metadata": metadata})

    def write_governed_decision(self, decision_id: str, domain: str, category: str, category_index: int, recommended_action: str, recommended_index: int, confidence: float, probabilities: list[float], factor_vector: list[float], factor_names: list[str], source: str = "score", scorer_version: str = "", preset_version: str = "", factor_schema_version: str = "", metadata: dict[str, Any] | None = None) -> None:
        self._write("write_governed_decision", lambda: self.primary.write_governed_decision(decision_id, domain, category, category_index, recommended_action, recommended_index, confidence, probabilities, factor_vector, factor_names, source, scorer_version, preset_version, factor_schema_version, metadata), lambda: self.secondary.write_governed_decision(decision_id, domain, category, category_index, recommended_action, recommended_index, confidence, probabilities, factor_vector, factor_names, source, scorer_version, preset_version, factor_schema_version, metadata), (decision_id, domain, category, category_index, recommended_action, recommended_index, confidence, probabilities, factor_vector, factor_names), {"source": source, "scorer_version": scorer_version, "preset_version": preset_version, "factor_schema_version": factor_schema_version, "metadata": metadata})

    def write_observation(self, observation_id: str, domain: str, category: str, recommended_action: str, confidence: float, source_route: str, scorer_version: str, factor_schema_version: str, entity_id: str | None = None, factor_vector: list[float] | None = None, factor_names: list[str] | None = None, metadata: dict[str, Any] | None = None) -> None:
        self._write("write_observation", lambda: self.primary.write_observation(observation_id, domain, category, recommended_action, confidence, source_route, scorer_version, factor_schema_version, entity_id, factor_vector, factor_names, metadata), lambda: self.secondary.write_observation(observation_id, domain, category, recommended_action, confidence, source_route, scorer_version, factor_schema_version, entity_id, factor_vector, factor_names, metadata), (observation_id, domain, category, recommended_action, confidence, source_route, scorer_version, factor_schema_version), {"entity_id": entity_id, "factor_vector": factor_vector, "factor_names": factor_names, "metadata": metadata})

    def save_centroids(self, domain: str, category: str, centroids: Any, metadata: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self._write("save_centroids", lambda: self.primary.save_centroids(domain, category, centroids, metadata, **kwargs), lambda: self.secondary.save_centroids(domain, category, centroids, metadata, **kwargs), (domain, category, centroids), {"metadata": metadata, **kwargs})

    def write_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str, metrics: dict[str, ProvenancedValue], computed_from: EnrichmentSourceSet, dry_run: bool = False, idempotency_key: str | None = None) -> EntityEnrichmentReceipt:
        return self._write("write_entity_enrichment", lambda: self.primary.write_entity_enrichment(domain=domain, entity_type=entity_type, entity_id=entity_id, namespace=namespace, metrics=metrics, computed_from=computed_from, dry_run=dry_run, idempotency_key=idempotency_key), lambda: self.secondary.write_entity_enrichment(domain=domain, entity_type=entity_type, entity_id=entity_id, namespace=namespace, metrics=metrics, computed_from=computed_from, dry_run=dry_run, idempotency_key=idempotency_key), (), {"domain": domain, "entity_type": entity_type, "entity_id": entity_id, "namespace": namespace, "metrics": metrics, "computed_from": computed_from, "dry_run": dry_run, "idempotency_key": idempotency_key})

    def write_conservation_status(self, status_id: str, domain: str, V: int, q: float, alpha: float, theta_min: float, verified_count: int, correct_count: int, status: str, policy_version: str) -> None:
        self._write("write_conservation_status", lambda: self.primary.write_conservation_status(status_id, domain, V, q, alpha, theta_min, verified_count, correct_count, status, policy_version), lambda: self.secondary.write_conservation_status(status_id, domain, V, q, alpha, theta_min, verified_count, correct_count, status, policy_version), (status_id, domain, V, q, alpha, theta_min, verified_count, correct_count, status, policy_version), {})

    def write_fingerprint(self, fingerprint_id: str, domain: str, factor_names: list[str], factor_stats: dict[str, Any], skipped_incompatible: int, window: int, metadata: dict[str, Any] | None = None) -> None:
        self._write("write_fingerprint", lambda: self.primary.write_fingerprint(fingerprint_id, domain, factor_names, factor_stats, skipped_incompatible, window, metadata), lambda: self.secondary.write_fingerprint(fingerprint_id, domain, factor_names, factor_stats, skipped_incompatible, window, metadata), (fingerprint_id, domain, factor_names, factor_stats, skipped_incompatible, window), {"metadata": metadata})

    def write_centroid_checkpoint(self, checkpoint_id: str, domain: str, category: str, action: str, centroids: Any, decisions_count: int, verified_count: int, iks: float, shape: list[int], factor_names_hash: str, metadata: dict[str, Any] | None = None) -> None:
        self._write("write_centroid_checkpoint", lambda: self.primary.write_centroid_checkpoint(checkpoint_id, domain, category, action, centroids, decisions_count, verified_count, iks, shape, factor_names_hash, metadata), lambda: self.secondary.write_centroid_checkpoint(checkpoint_id, domain, category, action, centroids, decisions_count, verified_count, iks, shape, factor_names_hash, metadata), (checkpoint_id, domain, category, action, centroids, decisions_count, verified_count, iks, shape, factor_names_hash), {"metadata": metadata})

    def write_evolution_event(self, event_id: str, domain: str, event_type: str, rule_name: str, variant_id: str, source_copilot: str | None = None, source_rule: str | None = None, metric: float | None = None, shadow_batch_size: int | None = None, min_shadow_batches: int | None = None, metadata: dict[str, Any] | None = None) -> None:
        self._write("write_evolution_event", lambda: self.primary.write_evolution_event(event_id, domain, event_type, rule_name, variant_id, source_copilot, source_rule, metric, shadow_batch_size, min_shadow_batches, metadata), lambda: self.secondary.write_evolution_event(event_id, domain, event_type, rule_name, variant_id, source_copilot, source_rule, metric, shadow_batch_size, min_shadow_batches, metadata), (event_id, domain, event_type, rule_name, variant_id), {"source_copilot": source_copilot, "source_rule": source_rule, "metric": metric, "shadow_batch_size": shadow_batch_size, "min_shadow_batches": min_shadow_batches, "metadata": metadata})

    def link_entity(self, decision_id: str, entity_id: str, entity_type: str, domain: str) -> None:
        self._write("link_entity", lambda: self.primary.link_entity(decision_id, entity_id, entity_type, domain), lambda: self.secondary.link_entity(decision_id, entity_id, entity_type, domain), (decision_id, entity_id, entity_type, domain), {})

    def append_evidence_receipt(self, receipt_intent_id: str, domain: str, decision_id: str, canonical_payload: dict[str, Any], actor: str, source_route: str, metadata: dict[str, Any] | None = None) -> tuple[int, str]:
        return self._write("append_evidence_receipt", lambda: self.primary.append_evidence_receipt(receipt_intent_id, domain, decision_id, canonical_payload, actor, source_route, metadata), lambda: self.secondary.append_evidence_receipt(receipt_intent_id, domain, decision_id, canonical_payload, actor, source_route, metadata), (receipt_intent_id, domain, decision_id, canonical_payload, actor, source_route), {"metadata": metadata})

    # Reads are intentionally primary-only.
    def get_decision(self, decision_id: str) -> dict[str, Any] | None: return self.primary.get_decision(decision_id)
    def get_decisions(self, domain: str, category: str | None = None, limit: int = 400) -> list[dict[str, Any]]: return self.primary.get_decisions(domain, category, limit)
    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]: return self.primary.get_all_decisions(domain)
    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]: return self.primary.get_verified_decisions(domain)
    def count_verified(self, domain: str) -> int: return self.primary.count_verified(domain)
    def count_correct(self, domain: str) -> int: return self.primary.count_correct(domain)
    def count_decisions(self, domain: str) -> int: return self.primary.count_decisions(domain)
    def load_latest_centroids(self, domain: str) -> Any | None: return self.primary.load_latest_centroids(domain)
    def get_centroid_checkpoints(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]: return self.primary.get_centroid_checkpoints(domain, **kwargs)
    def count_archived(self, domain: str) -> int: return self.primary.count_archived(domain)
    def read_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str | None = None) -> dict[str, ProvenancedValue]: return self.primary.read_entity_enrichment(domain=domain, entity_type=entity_type, entity_id=entity_id, namespace=namespace)
    def list_entity_enrichments(self, *, domain: str, entity_type: str | None = None, namespace: str | None = None, limit: int = 500) -> list[EntityEnrichmentRecord]: return self.primary.list_entity_enrichments(domain=domain, entity_type=entity_type, namespace=namespace, limit=limit)
    def count_verified_decisions(self, domain: str) -> int: return self.primary.count_verified_decisions(domain)

    def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int:
        return self._write("archive_old_decisions", lambda: self.primary.archive_old_decisions(domain, keep_recent), lambda: self.secondary.archive_old_decisions(domain, keep_recent), (domain,), {"keep_recent": keep_recent})

    def archive_decisions(self, domain: str, before: float, status_filter: str = "pending", confirm_verified: bool = False) -> int:
        return self._write("archive_decisions", lambda: self.primary.archive_decisions(domain, before, status_filter, confirm_verified), lambda: self.secondary.archive_decisions(domain, before, status_filter, confirm_verified), (domain, before), {"status_filter": status_filter, "confirm_verified": confirm_verified})

    def domain_scoped_reset(self, domain: str) -> None:
        self._write("domain_scoped_reset", lambda: self.primary.domain_scoped_reset(domain), lambda: self.secondary.domain_scoped_reset(domain), (domain,), {})

    def close(self) -> None:
        primary_error: Exception | None = None
        try:
            self.primary.close()
        except Exception as exc:
            primary_error = exc
        try:
            self.secondary.close()
        except Exception as exc:
            self._record_secondary_failure("close", (), {}, exc)
        if primary_error is not None:
            raise primary_error
