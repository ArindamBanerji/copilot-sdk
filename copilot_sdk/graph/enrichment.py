"""Entity enrichment value models for GraphStore implementations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

PROTECTED_ENTITY_FIELDS = frozenset(
    {
        "id",
        "entity_id",
        "supplier_id",
        "canonical_id",
        "domain",
        "entity_type",
        "source_system",
        "created_at",
        "updated_at",
        "name",
        "supplier_name",
        "label",
        "labels",
        "source_id",
        "target_id",
        "edge_id",
        "relationship_id",
    }
)


def utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def is_protected_metric_name(metric_name: str) -> bool:
    return str(metric_name) in PROTECTED_ENTITY_FIELDS


@dataclass(frozen=True)
class ProvenancedValue:
    value: Any
    source: str
    provenance_tier: str
    source_count: int = 0
    factor_eligible: bool = False
    provenance_label: str = ""
    measured: bool = False
    verified: bool = False
    computed_at: str = ""
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.source_count < 0:
            raise ValueError("source_count must be non-negative")
        if self.source == "fixture" and self.verified:
            raise ValueError("fixture values cannot claim verified=True")
        if self.source == "fixture" and self.measured:
            raise ValueError("fixture values cannot claim measured=True")
        if self.source == "unavailable" and self.factor_eligible:
            raise ValueError("unavailable values cannot be factor_eligible")
        if self.source == "verified_outcomes" and not self.verified:
            raise ValueError("verified_outcomes values require verified=True")
        if self.source == "verified_outcomes" and not self.measured:
            raise ValueError("verified_outcomes values require measured=True")
        if self.provenance_tier == "learned" and not self.verified:
            raise ValueError("learned provenance requires verified=True")

    @classmethod
    def from_verified(
        cls,
        value: Any,
        source_count: int,
        n_min: int = 20,
        label: str = "",
        computed_at: str | None = None,
        **kwargs: Any,
    ) -> "ProvenancedValue":
        factor_eligible = source_count >= n_min
        return cls(
            value=value,
            source="verified_outcomes",
            provenance_tier="learned",
            source_count=source_count,
            factor_eligible=factor_eligible,
            provenance_label=label or f"computed from {source_count} verified decisions",
            measured=True,
            verified=True,
            computed_at=computed_at or utc_iso_now(),
            **kwargs,
        )

    @classmethod
    def from_fixture(
        cls,
        value: Any,
        label: str = "integration pending",
        computed_at: str | None = None,
        **kwargs: Any,
    ) -> "ProvenancedValue":
        return cls(
            value=value,
            source="fixture",
            provenance_tier="context",
            source_count=0,
            factor_eligible=False,
            provenance_label=f"supplier context · {label}",
            measured=False,
            verified=False,
            computed_at=computed_at or utc_iso_now(),
            **kwargs,
        )

    @classmethod
    def unavailable(
        cls,
        label: str = "unavailable",
        computed_at: str | None = None,
        **kwargs: Any,
    ) -> "ProvenancedValue":
        return cls(
            value=None,
            source="unavailable",
            provenance_tier="unavailable",
            source_count=0,
            factor_eligible=False,
            provenance_label=label,
            measured=False,
            verified=False,
            computed_at=computed_at or utc_iso_now(),
            **kwargs,
        )

    def to_display(self):
        from copilot_sdk.evidence.provenance import Provenanced

        return Provenanced(
            value=self.value,
            source=self.source,
            label=self.provenance_label or self.provenance_tier,
        )

    def to_storage_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("value", None)
        return payload

    @classmethod
    def from_storage_dict(cls, value: Any, metadata: dict[str, Any]) -> "ProvenancedValue":
        return cls(value=value, **dict(metadata))


@dataclass(frozen=True)
class EnrichmentSourceSet:
    verified_decision_count: int = 0
    unverified_decision_count: int = 0
    decision_ids: list[str] = field(default_factory=list)
    outcome_ids: list[str] = field(default_factory=list)
    fixture_sources: list[str] = field(default_factory=list)
    integration_sources: list[str] = field(default_factory=list)
    computation_version: str = ""

    def __post_init__(self) -> None:
        if self.verified_decision_count < 0:
            raise ValueError("verified_decision_count must be non-negative")
        if self.unverified_decision_count < 0:
            raise ValueError("unverified_decision_count must be non-negative")


@dataclass(frozen=True)
class EntityEnrichmentReceipt:
    domain: str
    entity_type: str
    entity_id: str
    namespace: str
    persisted: bool
    dry_run: bool
    metrics_written: list[str]
    metrics_rejected: list[str]
    protected_fields_rejected: list[str]
    idempotency_key: str = ""
    computed_at: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EntityEnrichmentRecord:
    domain: str
    entity_type: str
    entity_id: str
    namespace: str
    metric_name: str
    value: ProvenancedValue
    computed_from: EnrichmentSourceSet
    computed_at: str
    idempotency_key: str = ""
