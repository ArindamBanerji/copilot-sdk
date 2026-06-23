"""SDK-level graph enrichment framework for Data Intelligence jobs."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from collections.abc import Callable
from typing import Any

from copilot_sdk.graph.enrichment import (
    EnrichmentSourceSet,
    EntityEnrichmentReceipt,
    ProvenancedValue,
)


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class GraphEnrichmentResult:
    entity_id: str
    entity_type: str
    namespace: str
    sample_count: int
    metrics: dict[str, Any]
    persisted: bool
    receipt: EntityEnrichmentReceipt | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metrics"] = {
            name: asdict(value) if isinstance(value, ProvenancedValue) else value
            for name, value in self.metrics.items()
        }
        payload["receipt"] = asdict(self.receipt) if self.receipt is not None else None
        return payload


@dataclass(frozen=True)
class GraphEnrichmentReport:
    domain: str
    entity_type: str
    namespace: str
    entities_enriched: int
    entities_skipped: int
    total_decisions_used: int
    dry_run: bool
    timestamp: str
    results: list[GraphEnrichmentResult]
    warnings: list[str] = field(default_factory=list)
    skipped_decisions: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["results"] = [result.to_dict() for result in self.results]
        return payload


class BaseGraphEnricher(ABC):
    """Base class for on-demand graph enrichment jobs.

    Subclasses own domain-specific grouping and metric computation. This base
    class owns deterministic grouping, source-set construction, and optional
    persistence through the P39A GraphStore entity enrichment API.
    """

    def __init__(
        self,
        *,
        domain: str,
        entity_type: str,
        namespace: str = "default",
        min_decisions: int = 5,
        computation_version: str = "",
    ) -> None:
        self.domain = str(domain)
        self.entity_type = str(entity_type)
        self.namespace = str(namespace or "default")
        self.min_decisions = max(int(min_decisions), 0)
        self.computation_version = str(computation_version or "")

    @abstractmethod
    def group_key(self, decision: dict[str, Any]) -> str | None:
        """Return the entity identifier for a decision, or None to skip it."""

    @abstractmethod
    def compute_metrics(
        self,
        entity_id: str,
        decisions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compute entity metrics for an already-grouped decision list."""

    def build_source_set(
        self,
        entity_id: str,
        decisions: list[dict[str, Any]],
    ) -> EnrichmentSourceSet:
        return EnrichmentSourceSet(
            verified_decision_count=0,
            unverified_decision_count=len(decisions),
            decision_ids=_decision_ids(decisions),
            computation_version=self.computation_version,
        )

    def normalize_metric(
        self,
        metric_name: str,
        value: Any,
        decisions: list[dict[str, Any]],
    ) -> ProvenancedValue | Any:
        if isinstance(value, ProvenancedValue):
            return value
        return value

    def should_skip_entity(self, entity_id: str, decisions: list[dict[str, Any]]) -> str | None:
        if len(decisions) < self.min_decisions:
            return f"sample_count {len(decisions)} below min_decisions {self.min_decisions}"
        return None

    def enrich(
        self,
        decisions: list[dict[str, Any]],
        *,
        graph_store: Any | None = None,
        dry_run: bool = False,
        verified_source: bool = False,
    ) -> GraphEnrichmentReport:
        warnings: list[str] = []
        groups, skipped_without_group = self._group_decisions(decisions)
        if skipped_without_group:
            warnings.append(f"decisions_skipped_without_group={skipped_without_group}")

        results: list[GraphEnrichmentResult] = []
        entities_skipped = 0
        total_decisions_used = 0

        for entity_id in sorted(groups):
            entity_decisions = groups[entity_id]
            skip_reason = self.should_skip_entity(entity_id, entity_decisions)
            if skip_reason:
                entities_skipped += 1
                warnings.append(f"{entity_id}: {skip_reason}")
                continue

            total_decisions_used += len(entity_decisions)
            raw_metrics = self.compute_metrics(entity_id, list(entity_decisions))
            metrics, metric_warnings = self._normalize_metrics(raw_metrics, entity_decisions)
            source_set = self._build_source_set(
                entity_id,
                entity_decisions,
                verified_source=verified_source,
            )
            receipt, persisted, result_warnings = self._persist_entity_enrichment(
                entity_id=entity_id,
                metrics=metrics,
                source_set=source_set,
                graph_store=graph_store,
                dry_run=dry_run,
            )
            results.append(
                GraphEnrichmentResult(
                    entity_id=entity_id,
                    entity_type=self.entity_type,
                    namespace=self.namespace,
                    sample_count=len(entity_decisions),
                    metrics=metrics,
                    persisted=persisted,
                    receipt=receipt,
                    warnings=[*metric_warnings, *result_warnings],
                )
            )

        return GraphEnrichmentReport(
            domain=self.domain,
            entity_type=self.entity_type,
            namespace=self.namespace,
            entities_enriched=len(results),
            entities_skipped=entities_skipped,
            total_decisions_used=total_decisions_used,
            dry_run=bool(dry_run),
            timestamp=_utc_iso_now(),
            results=results,
            warnings=warnings,
            skipped_decisions=skipped_without_group,
        )

    def enrich_from_store(
        self,
        graph_store: Any,
        *,
        dry_run: bool = False,
    ) -> GraphEnrichmentReport:
        decisions, warnings = self._read_verified_decisions(graph_store)
        report = self.enrich(
            decisions,
            graph_store=graph_store,
            dry_run=dry_run,
            verified_source=True,
        )
        if not warnings:
            return report
        return GraphEnrichmentReport(
            domain=report.domain,
            entity_type=report.entity_type,
            namespace=report.namespace,
            entities_enriched=report.entities_enriched,
            entities_skipped=report.entities_skipped,
            total_decisions_used=report.total_decisions_used,
            dry_run=report.dry_run,
            timestamp=report.timestamp,
            results=report.results,
            warnings=[*warnings, *report.warnings],
            skipped_decisions=report.skipped_decisions,
        )

    def _compute_confidence(self, sample_count: int) -> float:
        if self.min_decisions <= 0:
            return 1.0
        return min(1.0, max(0.0, float(sample_count) / float(self.min_decisions)))

    def _group_decisions(
        self,
        decisions: list[dict[str, Any]],
    ) -> tuple[dict[str, list[dict[str, Any]]], int]:
        groups: dict[str, list[dict[str, Any]]] = {}
        skipped = 0
        for decision in list(decisions or []):
            if not isinstance(decision, dict):
                skipped += 1
                continue
            key = self.group_key(decision)
            if key in (None, ""):
                skipped += 1
                continue
            groups.setdefault(str(key), []).append(decision)
        return groups, skipped

    def _normalize_metrics(
        self,
        metrics: dict[str, Any],
        decisions: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], list[str]]:
        normalized: dict[str, Any] = {}
        warnings: list[str] = []
        for metric_name, value in dict(metrics or {}).items():
            metric_key = str(metric_name)
            normalized_value = self.normalize_metric(metric_key, value, decisions)
            if not isinstance(normalized_value, ProvenancedValue):
                warnings.append(f"raw_metric_without_provenance={metric_key}")
            normalized[metric_key] = normalized_value
        return normalized, warnings

    def _build_source_set(
        self,
        entity_id: str,
        decisions: list[dict[str, Any]],
        *,
        verified_source: bool,
    ) -> EnrichmentSourceSet:
        if type(self).build_source_set is BaseGraphEnricher.build_source_set:
            return EnrichmentSourceSet(
                verified_decision_count=len(decisions) if verified_source else 0,
                unverified_decision_count=0 if verified_source else len(decisions),
                decision_ids=_decision_ids(decisions),
                computation_version=self.computation_version,
            )
        return self.build_source_set(entity_id, decisions)

    def _persist_entity_enrichment(
        self,
        *,
        entity_id: str,
        metrics: dict[str, Any],
        source_set: EnrichmentSourceSet,
        graph_store: Any | None,
        dry_run: bool,
    ) -> tuple[EntityEnrichmentReceipt | None, bool, list[str]]:
        provenanced_metrics = {
            name: value
            for name, value in metrics.items()
            if isinstance(value, ProvenancedValue)
        }
        if not provenanced_metrics:
            return None, False, ["no ProvenancedValue metrics available for persistence"]
        if graph_store is None:
            return None, False, ["graph_store unavailable; computed only"]
        write = getattr(graph_store, "write_entity_enrichment", None)
        if not callable(write):
            return None, False, ["graph_store does not support write_entity_enrichment"]
        try:
            receipt = write(
                domain=self.domain,
                entity_type=self.entity_type,
                entity_id=str(entity_id),
                namespace=self.namespace,
                metrics=provenanced_metrics,
                computed_from=source_set,
                dry_run=bool(dry_run),
                idempotency_key=self._idempotency_key(entity_id, source_set),
            )
        except NotImplementedError as exc:
            return None, False, [str(exc) or "entity enrichment writes unsupported"]
        if not isinstance(receipt, EntityEnrichmentReceipt):
            return None, False, ["write_entity_enrichment returned invalid receipt"]
        persisted = bool(receipt.persisted) and not bool(dry_run)
        return receipt, persisted, list(receipt.warnings)

    def _idempotency_key(self, entity_id: str, source_set: EnrichmentSourceSet) -> str:
        payload = {
            "domain": self.domain,
            "entity_type": self.entity_type,
            "entity_id": str(entity_id),
            "namespace": self.namespace,
            "source_set": asdict(source_set),
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return f"di-enrichment:{digest[:24]}"

    def _read_verified_decisions(self, graph_store: Any) -> tuple[list[dict[str, Any]], list[str]]:
        read = getattr(graph_store, "get_verified_decisions", None)
        if not callable(read):
            return [], ["graph_store does not support get_verified_decisions"]
        try:
            rows = read(self.domain)
        except Exception as exc:
            return [], [f"get_verified_decisions failed: {exc}"]
        if not isinstance(rows, list):
            return [], ["get_verified_decisions returned non-list result"]
        return [row for row in rows if isinstance(row, dict)], []


class GraphEnricher(BaseGraphEnricher):
    """Concrete graph enricher configured with callables."""

    def __init__(
        self,
        *,
        domain: str,
        entity_type: str,
        group_key_fn: Callable[[dict[str, Any]], str | None],
        compute_metrics_fn: Callable[[str, list[dict[str, Any]]], dict[str, Any]],
        namespace: str = "default",
        min_decisions: int = 5,
        computation_version: str = "",
    ) -> None:
        super().__init__(
            domain=domain,
            entity_type=entity_type,
            namespace=namespace,
            min_decisions=min_decisions,
            computation_version=computation_version,
        )
        self._group_key_fn = group_key_fn
        self._compute_metrics_fn = compute_metrics_fn

    def group_key(self, decision: dict[str, Any]) -> str | None:
        return self._group_key_fn(decision)

    def compute_metrics(
        self,
        entity_id: str,
        decisions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return self._compute_metrics_fn(entity_id, decisions)


def _decision_ids(decisions: list[dict[str, Any]]) -> list[str]:
    ids = [
        str(decision.get("decision_id"))
        for decision in decisions
        if decision.get("decision_id") not in (None, "")
    ]
    return sorted(ids)
