"""AGE-backed persistence adapters for evolution and authority state."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from copilot_sdk.graph.protocol import ProtocolV2GraphStore
from copilot_sdk.evolution.variant_store import (
    CategoryVariantStats,
    InMemoryVariantStore,
    VariantSpec,
    VariantStats,
    VARIANT_STATUSES,
)
from copilot_sdk.promotion.core import PromotionRecord
from copilot_sdk.outcome.models import VerifiedOutcome


def _events(
    store: ProtocolV2GraphStore, domain: str, event_type: str | None = None
) -> list[dict[str, Any]]:
    kwargs = {} if event_type is None else {"event_type": event_type}
    return [dict(row) for row in store.get_evolution_events(domain, limit=10_000, **kwargs)]


def create_variant_store(
    graph_store: ProtocolV2GraphStore, domain: str, *, test_mode: bool = False
) -> GraphVariantStore | InMemoryVariantStore:
    """Select AGE evolution storage, allowing only explicit test doubles in tests."""
    if isinstance(graph_store, ProtocolV2GraphStore):
        return GraphVariantStore(graph_store, domain)
    if test_mode:
        return InMemoryVariantStore()
    raise RuntimeError("AGE GraphStore does not expose evolution-event persistence")


def _metadata(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("metadata") or event.get("metadata_json") or "{}"
    if isinstance(raw, dict):
        return dict(raw)
    try:
        value = json.loads(str(raw))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return dict(value) if isinstance(value, dict) else {}


class GraphVariantStore:
    """VariantStore implementation whose source of truth is AGE events."""

    def __init__(self, graph_store: ProtocolV2GraphStore, domain: str) -> None:
        self.graph_store = graph_store
        self.domain = str(domain)

    def _variant_events(self) -> list[dict[str, Any]]:
        return _events(self.graph_store, self.domain, "variant_registered")

    def _outcome_events(self) -> list[dict[str, Any]]:
        return _events(self.graph_store, self.domain, "variant_outcome")

    def register_variant(self, spec: VariantSpec) -> None:
        if not isinstance(spec, VariantSpec):
            raise TypeError("spec must be a VariantSpec")
        existing = self.get_variant(spec.id)
        if existing is not None:
            if existing.family != spec.family or existing.version != spec.version:
                raise ValueError(f"Variant already registered: {spec.id}")
            return
        self.graph_store.write_evolution_event(
            event_id=f"variant:{self.domain}:{spec.id}",
            domain=self.domain,
            event_type="variant_registered",
            rule_name=spec.family,
            variant_id=spec.id,
            metadata={"spec": {"id": spec.id, "family": spec.family, "version": spec.version, "template": spec.template, "status": spec.status, "metadata": spec.metadata}},
        )

    def _specs(self) -> list[VariantSpec]:
        latest: dict[str, VariantSpec] = {}
        for event in self._variant_events():
            spec_data = _metadata(event).get("spec")
            if not isinstance(spec_data, dict):
                continue
            spec = VariantSpec(
                id=str(spec_data["id"]), family=str(spec_data["family"]),
                version=int(spec_data.get("version", 1)), template=str(spec_data.get("template", "")),
                status=str(spec_data.get("status", "active")), metadata=dict(spec_data.get("metadata", {})),
            )
            latest[spec.id] = spec
        return list(latest.values())

    def get_variant(self, variant_id: str) -> VariantSpec | None:
        return next((s for s in self._specs() if s.id == variant_id), None)

    def get_variants_by_family(self, family: str) -> list[VariantSpec]:
        return [s for s in self._specs() if s.family == family]

    def get_all_variants(self) -> list[VariantSpec]:
        return self._specs()

    def get_active_variants(self) -> list[VariantSpec]:
        return [s for s in self._specs() if s.status == "active"]

    def _stats(self, variant_id: str, category: str | None = None) -> VariantStats:
        rows = [e for e in self._outcome_events() if str(e.get("variant_id")) == variant_id]
        if category is not None:
            rows = [e for e in rows if _metadata(e).get("category") == category]
        successes = sum(bool(_metadata(e).get("success")) for e in rows)
        return VariantStats(successes=successes, total=len(rows), failures=len(rows) - successes)

    def get_global_stats(self, variant_id: str) -> VariantStats:
        return self._stats(variant_id)

    def get_category_stats(self, category: str, variant_id: str) -> CategoryVariantStats:
        stats = self._stats(variant_id, str(category))
        return CategoryVariantStats(category=str(category), variant_id=variant_id, successes=stats.successes, total=stats.total, failures=stats.failures)

    def get_all_category_stats(self, category: str) -> dict[str, CategoryVariantStats]:
        return {s.id: self.get_category_stats(category, s.id) for s in self._specs() if self.get_category_stats(category, s.id).total}

    def record_outcome(self, variant_id: str, success: bool, category: str | None = None) -> None:
        if self.get_variant(variant_id) is None:
            raise ValueError(f"Unknown variant: {variant_id}")
        self.graph_store.write_evolution_event(
            event_id=f"variant-outcome:{self.domain}:{uuid4().hex}", domain=self.domain,
            event_type="variant_outcome", rule_name="variant", variant_id=variant_id,
            metadata={"success": bool(success), "category": category, "recorded_at": datetime.now(timezone.utc).isoformat()},
        )

    def record_category_outcome(self, category: str, variant_id: str, success: bool) -> None:
        self.record_outcome(variant_id, success, category)

    def update_variant_status(self, variant_id: str, new_status: str) -> None:
        if new_status not in VARIANT_STATUSES:
            raise ValueError(f"Unsupported variant status: {new_status}")
        spec = self.get_variant(variant_id)
        if spec is None:
            raise ValueError(f"Unknown variant: {variant_id}")
        self.graph_store.write_evolution_event(
            event_id=f"variant-status:{self.domain}:{uuid4().hex}", domain=self.domain,
            event_type="variant_registered", rule_name=spec.family, variant_id=variant_id,
            metadata={"spec": {"id": spec.id, "family": spec.family, "version": spec.version, "template": spec.template, "status": new_status, "metadata": spec.metadata}},
        )

    def reset(self) -> None:
        raise RuntimeError("AGE evolution history is append-only; reset is not supported")

    def reset_stats_only(self) -> None:
        raise RuntimeError("AGE evolution history is append-only; reset is not supported")


class GraphPromotionStore:
    """PromotionStore-compatible adapter backed by domain-scoped AGE state."""

    def __init__(self, graph_store: ProtocolV2GraphStore, domain: str) -> None:
        self.graph_store = graph_store
        self.domain = str(domain)

    def save(self, record: PromotionRecord) -> None:
        self.graph_store.save_promotion(
            self.domain, record.record_id, {"record": record.to_dict()}
        )

    def _records(self) -> dict[str, PromotionRecord]:
        result: dict[str, PromotionRecord] = {}
        for event in self.graph_store.list_promotions(self.domain):
            raw = event.get("record")
            if isinstance(raw, dict):
                record = PromotionRecord.from_dict(raw)
                result[record.record_id] = record
        return result

    def load(self, record_id: str) -> PromotionRecord | None:
        return self._records().get(record_id)

    def load_by_class(self, copilot: str, decision_class: str) -> PromotionRecord | None:
        return next((r for r in self._records().values() if r.copilot == copilot and r.decision_class == decision_class), None)

    def list_all(self, copilot: str) -> list[PromotionRecord]:
        return [r for r in self._records().values() if r.copilot == copilot]

    def close(self) -> None:
        return None


class GraphOutcomeLedger:
    """OutcomeLedger-compatible AGE event adapter."""

    def __init__(self, graph_store: ProtocolV2GraphStore, domain: str) -> None:
        self.graph_store = graph_store
        self.domain = str(domain)

    def append(self, outcome: VerifiedOutcome) -> bool:
        receipt_id = outcome.receipt_id()
        if self.get(receipt_id) is not None:
            return False
        self.graph_store.write_evolution_event(
            event_id=f"verified-outcome:{self.domain}:{receipt_id}",
            domain=self.domain, event_type="verified_outcome", rule_name=outcome.category,
            variant_id=outcome.decision_id, metadata={"receipt": outcome.to_dict()},
        )
        return True

    def _receipts(self) -> list[VerifiedOutcome]:
        result: list[VerifiedOutcome] = []
        for event in _events(self.graph_store, self.domain, "verified_outcome"):
            raw = _metadata(event).get("receipt")
            if isinstance(raw, dict):
                result.append(VerifiedOutcome.from_dict(raw))
        return result

    def get(self, receipt_id: str) -> VerifiedOutcome | None:
        return next((item for item in self._receipts() if item.receipt_id() == receipt_id), None)

    def exists(self, receipt_id: str) -> bool:
        return self.get(receipt_id) is not None

    def count(self, copilot: str, category: str | None = None) -> int:
        return sum(item.copilot == copilot and (category is None or item.category == category) for item in self._receipts())

    def list_recent(self, copilot: str, limit: int = 100) -> list[VerifiedOutcome]:
        rows = [item for item in self._receipts() if item.copilot == copilot]
        return rows[-max(1, min(int(limit), 10_000)) :][::-1]

    def close(self) -> None:
        return None


class GraphProofLedger:
    """Small append-only proof ledger stored as AGE evidence events."""

    def __init__(self, graph_store: ProtocolV2GraphStore, domain: str) -> None:
        self.graph_store = graph_store
        self.domain = str(domain)

    def record(self, kind: str, payload: dict[str, Any]) -> None:
        stable = json.dumps([kind, payload], sort_keys=True, default=str)
        self.graph_store.write_evolution_event(
            event_id=f"proof:{self.domain}:{uuid4().hex}", domain=self.domain,
            event_type="proof_record", rule_name=str(kind), variant_id="proof",
            metadata={"kind": kind, "payload": dict(payload), "stable": stable},
        )

    def list_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = _events(self.graph_store, self.domain, "proof_record")
        entries = [{"kind": _metadata(row).get("kind"), "payload": _metadata(row).get("payload", {}), "created_at": row.get("created_at")} for row in rows]
        return entries[-max(1, min(int(limit), 1000)) :][::-1]

    def close(self) -> None:
        return None
