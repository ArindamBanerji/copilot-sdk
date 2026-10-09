"""Shared promotion and earned-authority state machine."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Mapping, Protocol, runtime_checkable
from copilot_sdk.graph.protocol import GraphStore


class PromotionStage(str, Enum):
    DISCOVERED = "discovered"
    SHADOWING = "shadowing"
    PROMOTED = "promoted"
    MEASURING = "measuring"
    KEPT = "kept"
    ROLLED_BACK = "rolled_back"
    TRANSFERRED = "transferred"


@runtime_checkable
class PromotionPolicy(Protocol):
    """Policy data injected into the domain-independent state machine."""

    @property
    def stages(self) -> tuple[PromotionStage, ...]: ...

    @property
    def stage_names(self) -> tuple[str, ...]: ...

    @property
    def min_shadow_decisions(self) -> int: ...

    @property
    def min_measurement_decisions(self) -> int: ...

    @property
    def improvement_threshold(self) -> float: ...

    @property
    def conservation_required(self) -> bool: ...

    @property
    def allowed_transitions(self) -> Mapping[PromotionStage, tuple[PromotionStage, ...]]: ...


@dataclass(frozen=True)
class PromotionRecord:
    record_id: str
    copilot: str
    decision_class: str
    current_stage: PromotionStage = PromotionStage.DISCOVERED
    stage_history: list[dict[str, Any]] = field(default_factory=list)
    shadow_decisions: int = 0
    measurement_decisions: int = 0
    improvement_delta: float = 0.0
    conservation_state_at_transition: str = "UNKNOWN"

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise ValueError("record_id must be non-empty")
        if not self.copilot.strip():
            raise ValueError("copilot must be non-empty")
        if not self.decision_class.strip():
            raise ValueError("decision_class must be non-empty")
        object.__setattr__(self, "current_stage", PromotionStage(self.current_stage))
        object.__setattr__(self, "stage_history", [dict(item) for item in self.stage_history])
        object.__setattr__(
            self,
            "conservation_state_at_transition",
            _normalize_status(self.conservation_state_at_transition),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["current_stage"] = self.current_stage.value
        data["stage_history"] = [dict(item) for item in self.stage_history]
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PromotionRecord":
        return cls(
            record_id=str(data["record_id"]),
            copilot=str(data["copilot"]),
            decision_class=str(data["decision_class"]),
            current_stage=PromotionStage(data.get("current_stage", PromotionStage.DISCOVERED.value)),
            stage_history=list(data.get("stage_history", [])),
            shadow_decisions=int(data.get("shadow_decisions", 0)),
            measurement_decisions=int(data.get("measurement_decisions", 0)),
            improvement_delta=float(data.get("improvement_delta", 0.0)),
            conservation_state_at_transition=str(
                data.get("conservation_state_at_transition", "UNKNOWN")
            ),
        )


@dataclass(frozen=True)
class PromotionResult:
    advanced: bool
    new_stage: PromotionStage
    reason: str
    record: PromotionRecord | None = None
    target_record_id: str | None = None


class PromotionStore:
    """PromotionStore-compatible adapter backed by domain-scoped graph state."""

    def __init__(self, graph_store: GraphStore, domain: str) -> None:
        self.graph_store = graph_store
        self.domain = str(domain)

    def save(self, record: PromotionRecord) -> None:
        # Application adapters consume flat records; retain legacy reads below.
        self.graph_store.save_promotion(
            self.domain, record.record_id, record.to_dict()
        )

    @staticmethod
    def _decode_record(state: dict[str, Any]) -> PromotionRecord | None:
        raw = state.get("record")
        if isinstance(raw, dict):
            return PromotionRecord.from_dict(raw)
        if "record_id" in state:
            return PromotionRecord.from_dict(state)
        return None

    def _records(self) -> dict[str, PromotionRecord]:
        result: dict[str, PromotionRecord] = {}
        for event in self.graph_store.list_promotions(self.domain):
            record = self._decode_record(event)
            if record is not None:
                result[record.record_id] = record
        return dict(sorted(result.items()))

    def load(self, record_id: str) -> PromotionRecord | None:
        state = self.graph_store.get_promotion(self.domain, record_id)
        return self._decode_record(state) if state is not None else None

    def load_by_class(self, copilot: str, decision_class: str) -> PromotionRecord | None:
        return next((r for r in self._records().values() if r.copilot == copilot and r.decision_class == decision_class), None)

    def list_all(self, copilot: str) -> list[PromotionRecord]:
        return [r for r in self._records().values() if r.copilot == copilot]

    def close(self) -> None:
        return None


class PromotionEngine:
    """Concurrent-safe lifecycle engine with conservation-gated authority."""

    def __init__(
        self,
        policy: PromotionPolicy,
        store: PromotionStore,
        conservation_provider: Any | None = None,
    ) -> None:
        self.policy = policy
        self.store = store
        self.conservation_provider = conservation_provider
        self._lock = RLock()

    def create(self, copilot: str, decision_class: str, record_id: str | None = None) -> PromotionRecord:
        record = PromotionRecord(
            record_id=record_id or f"promotion-{uuid.uuid4().hex}",
            copilot=copilot,
            decision_class=decision_class,
            stage_history=[_history_entry(PromotionStage.DISCOVERED, "created", "UNKNOWN", {})],
        )
        with self._lock:
            self.store.save(record)
        return record

    def advance(self, record_id: str, evidence: Mapping[str, Any] | None = None) -> PromotionResult:
        evidence_map = dict(evidence or {})
        with self._lock:
            record = self.store.load(record_id)
            if record is None:
                return PromotionResult(False, PromotionStage.DISCOVERED, "record_not_found")
            next_stage = self._next_stage(record.current_stage)
            if next_stage is None:
                return PromotionResult(False, record.current_stage, "no_allowed_transition", record)

            status = self._conservation_status(evidence_map)
            if next_stage in {PromotionStage.PROMOTED, PromotionStage.TRANSFERRED}:
                if self.policy.conservation_required and status != "GREEN":
                    reason = "conservation_red" if status == "RED" else "conservation_unavailable"
                    return PromotionResult(False, record.current_stage, reason, record)

            if next_stage is PromotionStage.PROMOTED:
                shadow_count = _count(evidence_map, "shadow_decisions", record.shadow_decisions)
                if shadow_count < self.policy.min_shadow_decisions:
                    return PromotionResult(False, record.current_stage, "insufficient_shadow_decisions", record)
            if next_stage is PromotionStage.KEPT:
                measurement_count = _count(
                    evidence_map, "measurement_decisions", record.measurement_decisions
                )
                if measurement_count < self.policy.min_measurement_decisions:
                    return PromotionResult(False, record.current_stage, "insufficient_measurement_decisions", record)
                improvement = _float(evidence_map, "improvement", record.improvement_delta)
                if improvement <= self.policy.improvement_threshold:
                    return PromotionResult(False, record.current_stage, "improvement_below_threshold", record)

            updated = self._transition(record, next_stage, evidence_map, status)
            self.store.save(updated)
            return PromotionResult(True, next_stage, "advanced", updated)

    def rollback(self, record_id: str, reason: str) -> PromotionResult:
        with self._lock:
            record = self.store.load(record_id)
            if record is None:
                return PromotionResult(False, PromotionStage.DISCOVERED, "record_not_found")
            status = self._conservation_status({})
            updated = self._transition(
                record,
                PromotionStage.ROLLED_BACK,
                {"reason": reason},
                status,
                force=True,
            )
            self.store.save(updated)
            return PromotionResult(True, PromotionStage.ROLLED_BACK, "rolled_back", updated)

    def veto(self, record_id: str) -> bool:
        with self._lock:
            record = self.store.load(record_id)
            if record is None:
                return True
            return self._conservation_status({}) == "RED"

    def get_authority(self, copilot: str, decision_class: str) -> PromotionStage:
        record = self.store.load_by_class(copilot, decision_class)
        return record.current_stage if record is not None else PromotionStage.DISCOVERED

    def get_all(self, copilot: str) -> list[PromotionRecord]:
        return self.store.list_all(copilot)

    def transfer(
        self,
        record_id: str,
        target_copilot: str,
        target_decision_class: str | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> PromotionResult:
        evidence_map = dict(evidence or {})
        with self._lock:
            record = self.store.load(record_id)
            if record is None:
                return PromotionResult(False, PromotionStage.DISCOVERED, "record_not_found")
            if record.current_stage is not PromotionStage.KEPT:
                return PromotionResult(False, record.current_stage, "transfer_requires_kept", record)
            status = self._conservation_status(evidence_map)
            if self.policy.conservation_required and status != "GREEN":
                reason = "conservation_red" if status == "RED" else "conservation_unavailable"
                return PromotionResult(False, record.current_stage, reason, record)
            transferred = self._transition(
                record, PromotionStage.TRANSFERRED, evidence_map, status, force=True
            )
            self.store.save(transferred)
            target_engine = self
            if target_copilot != record.copilot:
                target_engine = PromotionEngine(
                    self.policy, PromotionStore(self.store.graph_store, target_copilot),
                    self.conservation_provider,
                )
            target = target_engine.create(
                target_copilot,
                target_decision_class or record.decision_class,
            )
            return PromotionResult(True, PromotionStage.TRANSFERRED, "transferred", transferred, target.record_id)

    def _next_stage(self, stage: PromotionStage) -> PromotionStage | None:
        allowed = self.policy.allowed_transitions.get(stage, ())
        return allowed[0] if allowed else None

    def _transition(
        self,
        record: PromotionRecord,
        stage: PromotionStage,
        evidence: Mapping[str, Any],
        status: str,
        force: bool = False,
    ) -> PromotionRecord:
        if not force and stage not in self.policy.allowed_transitions.get(record.current_stage, ()):
            raise ValueError(f"Invalid transition: {record.current_stage.value} -> {stage.value}")
        shadow_count = _count(evidence, "shadow_decisions", record.shadow_decisions)
        measurement_count = _count(evidence, "measurement_decisions", record.measurement_decisions)
        improvement = _float(evidence, "improvement", record.improvement_delta)
        history = [dict(item) for item in record.stage_history]
        history.append(_history_entry(stage, str(evidence.get("reason", "advanced")), status, evidence))
        return PromotionRecord(
            record_id=record.record_id,
            copilot=record.copilot,
            decision_class=record.decision_class,
            current_stage=stage,
            stage_history=history,
            shadow_decisions=shadow_count,
            measurement_decisions=measurement_count,
            improvement_delta=improvement,
            conservation_state_at_transition=status,
        )

    def _conservation_status(self, evidence: Mapping[str, Any]) -> str:
        raw: Any = evidence.get("conservation_state", evidence.get("conservation"))
        if raw is None and self.conservation_provider is not None:
            try:
                getter = getattr(self.conservation_provider, "get_state", None)
                raw = getter() if callable(getter) else self.conservation_provider()
            except Exception:
                return "UNKNOWN"
        return _normalize_status(raw)


def _history_entry(
    stage: PromotionStage,
    reason: str,
    conservation_status: str,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "stage": stage.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "evidence": dict(evidence),
        "conservation_state": conservation_status,
    }


def _normalize_status(raw: Any) -> str:
    if isinstance(raw, Mapping):
        raw = raw.get("status", raw.get("state", "UNKNOWN"))
    status = str(raw or "UNKNOWN").strip().upper()
    return status if status in {"GREEN", "AMBER", "RED"} else "UNKNOWN"


def _count(values: Mapping[str, Any], key: str, fallback: int) -> int:
    try:
        return max(int(values.get(key, fallback)), 0)
    except (TypeError, ValueError):
        return max(int(fallback), 0)


def _float(values: Mapping[str, Any], key: str, fallback: float) -> float:
    try:
        return float(values.get(key, fallback))
    except (TypeError, ValueError):
        return float(fallback)
