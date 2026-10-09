"""AGE-backed persistence adapters for evolution and authority state."""

from __future__ import annotations

import hashlib
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
from copilot_sdk.promotion.core import PromotionStore
from copilot_sdk.outcome.ledger import OutcomeLedger

_STATUS_ORDER = {"shadow": 0, "active": 1, "promoted": 2, "retired": 3}


def _events(
    store: ProtocolV2GraphStore, domain: str, event_type: str | None = None
) -> list[dict[str, Any]]:
    kwargs = {} if event_type is None else {"event_type": event_type}
    return [dict(row) for row in store.get_evolution_events(domain, limit=None, **kwargs)]


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


def _event_epoch(event: dict[str, Any]) -> float | None:
    value = event.get("timestamp", event.get("created_at"))
    try:
        return float(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).timestamp()
        except ValueError:
            return None


def _event_sequence(event: dict[str, Any]) -> int | None:
    value = _metadata(event).get("replay_sequence")
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _ordered_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def order(item: tuple[int, dict[str, Any]]) -> tuple[bool, float, bool, int, str]:
        index, event = item
        epoch = _event_epoch(event)
        sequence = _event_sequence(event)
        # Legacy ties retain their incoming order, before newly sequenced writes.
        return (epoch is None, epoch if epoch is not None else float(index),
                sequence is not None, sequence if sequence is not None else index,
                str(event.get("event_id") or ""))

    return [event for _index, event in sorted(enumerate(events), key=order)]


def _events_after_latest_reset(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = _ordered_events(events)
    reset_index = -1
    for index, event in enumerate(ordered):
        if str(event.get("event_type") or "") == "variant_reset":
            reset_index = index
    return ordered[reset_index + 1 :]


def _latest_reset_epoch_id(events: list[dict[str, Any]]) -> str | None:
    resets = [event for event in _ordered_events(events) if str(event.get("event_type") or "") == "variant_reset"]
    if not resets:
        return None
    metadata = _metadata(resets[-1])
    epoch_id = metadata.get("epoch_id")
    return str(epoch_id) if epoch_id else None


def _latest_variant_specs(events: list[dict[str, Any]]) -> list[VariantSpec]:
    latest: dict[str, VariantSpec] = {}
    times: dict[str, tuple[float | None, bool, int]] = {}
    for event in events:
        spec_data = _metadata(event).get("spec")
        if not isinstance(spec_data, dict):
            continue
        identifier = str(spec_data["id"])
        timestamp = _event_epoch(event)
        status = str(spec_data.get("status", "active"))
        sequence = _event_sequence(event)
        # Sequence orders new writes; status rank only resolves legacy ties.
        current = (timestamp, sequence is not None,
                   sequence if sequence is not None else _STATUS_ORDER.get(status, -1))
        previous = times.get(identifier)
        if (
            timestamp is not None
            and previous is not None
            and previous[0] is not None
            and current < previous
        ):
            continue
        latest[identifier] = VariantSpec(
            id=identifier, family=str(spec_data["family"]),
            version=int(spec_data.get("version", 1)), template=str(spec_data.get("template", "")),
            status=status, metadata=dict(spec_data.get("metadata", {})),
        )
        times[identifier] = current
    return list(latest.values())


class GraphVariantStore:
    """VariantStore implementation whose source of truth is AGE events."""

    def __init__(self, graph_store: ProtocolV2GraphStore, domain: str) -> None:
        self.graph_store = graph_store
        self.domain = str(domain)

    def _all_events(self) -> list[dict[str, Any]]:
        return _events(self.graph_store, self.domain)

    def _next_replay_sequence(self) -> int:
        # Derive from persisted events so ordering survives adapter recreation.
        return max((_event_sequence(event) or 0 for event in self._all_events()), default=0) + 1

    def _active_events(self, event_type: str | None = None) -> list[dict[str, Any]]:
        events = _events_after_latest_reset(self._all_events())
        return [event for event in events
                if event_type is None or event.get("event_type") == event_type]

    def _variant_events(self) -> list[dict[str, Any]]:
        return self._active_events("variant_registered")

    def _outcome_events(self) -> list[dict[str, Any]]:
        return self._active_events("variant_outcome")

    def _epoch_event_prefix(self) -> str:
        epoch_id = _latest_reset_epoch_id(self._all_events())
        if epoch_id is None:
            return f"variant:{self.domain}"
        return f"variant:{self.domain}:{epoch_id}"

    def register_variant(self, spec: VariantSpec) -> None:
        if not isinstance(spec, VariantSpec):
            raise TypeError("spec must be a VariantSpec")
        existing = self.get_variant(spec.id)
        if existing is not None:
            if existing.family != spec.family or existing.version != spec.version:
                raise ValueError(f"Variant already registered: {spec.id}")
            return
        self.graph_store.write_evolution_event(
            event_id=f"{self._epoch_event_prefix()}:{spec.id}",
            domain=self.domain,
            event_type="variant_registered",
            rule_name=spec.family,
            variant_id=spec.id,
            metadata={"replay_sequence": self._next_replay_sequence(), "spec": {"id": spec.id, "family": spec.family, "version": spec.version, "template": spec.template, "status": spec.status, "metadata": spec.metadata}},
        )

    def _specs(self) -> list[VariantSpec]:
        # Reconstruct specifications from graph events in chronological order.
        return _latest_variant_specs(self._variant_events())

    def get_variant(self, variant_id: str) -> VariantSpec | None:
        return next((s for s in self._specs() if s.id == variant_id), None)

    def get_variants_by_family(self, family: str) -> list[VariantSpec]:
        return [s for s in self._specs() if s.family == family]

    def get_all_variants(self) -> list[VariantSpec]:
        return self._specs()

    def get_active_variants(self) -> list[VariantSpec]:
        return [s for s in self._specs() if s.status == "active"]

    def selection_snapshot(self) -> InMemoryVariantStore:
        """Read each event stream once for a single selection; retain no cache."""
        snapshot = InMemoryVariantStore()
        specs = self._specs()
        ids = {spec.id for spec in specs}
        for spec in specs:
            snapshot.register_variant(spec)
        for event in self._outcome_events():
            variant_id = str(event.get("variant_id"))
            if variant_id not in ids:
                continue
            metadata = _metadata(event)
            snapshot.record_outcome(variant_id, bool(metadata.get("success")),
                                    category=metadata.get("category"))
        return snapshot

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
            metadata={"replay_sequence": self._next_replay_sequence(), "success": bool(success), "category": category, "recorded_at": datetime.now(timezone.utc).isoformat()},
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
            metadata={"replay_sequence": self._next_replay_sequence(), "spec": {"id": spec.id, "family": spec.family, "version": spec.version, "template": spec.template, "status": new_status, "metadata": spec.metadata}},
        )

    def reset(self) -> None:
        epoch_id = uuid4().hex
        self.graph_store.write_evolution_event(
            event_id=f"variant-reset:{self.domain}:{epoch_id}",
            domain=self.domain,
            event_type="variant_reset",
            rule_name="variant_epoch",
            variant_id="epoch",
            metadata={"replay_sequence": self._next_replay_sequence(), "epoch_id": epoch_id, "reset_at": datetime.now(timezone.utc).isoformat()},
        )

    def reset_stats_only(self) -> None:
        raise RuntimeError("Evolution history is append-only; reset is not supported")

    def close(self) -> None:
        """The caller owns the injected graph store."""


class GraphPromotionStore(PromotionStore):
    """Compatibility name for graph-only promotion persistence."""


class GraphOutcomeLedger(OutcomeLedger):
    """Compatibility name for graph-only verified outcome persistence."""


class GraphProofLedger:
    """Small append-only proof ledger stored as AGE evidence events."""

    def __init__(self, graph_store: ProtocolV2GraphStore, domain: str) -> None:
        self.graph_store = graph_store
        self.domain = str(domain)

    def record(self, kind: str, payload: dict[str, Any]) -> None:
        stable = json.dumps([kind, payload], sort_keys=True, default=str)
        self.graph_store.write_evolution_event(
            event_id=f"proof:{self.domain}:{hashlib.sha256(stable.encode()).hexdigest()}", domain=self.domain,
            event_type="proof_record", rule_name=str(kind), variant_id="proof",
            metadata={"kind": kind, "payload": dict(payload), "stable": stable},
        )

    def list_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.graph_store.get_evolution_events(
            self.domain, event_type="proof_record", limit=max(1, min(int(limit), 1000))
        )
        entries = [{"kind": _metadata(row).get("kind"), "payload": _metadata(row).get("payload", {}), "created_at": _event_epoch(row)} for row in rows]
        return entries[:max(0, min(int(limit), 1000))]

    def close(self) -> None:
        return None
