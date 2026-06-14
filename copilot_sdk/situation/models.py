"""Domain-agnostic situation and typed-intent models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _trace_id() -> str:
    return f"sit-{uuid4().hex}"


def _json_safe(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


@dataclass(frozen=True)
class PolicyReference:
    """Policy or guardrail reference attached to a typed intent."""

    policy_id: str
    name: str = ""
    version: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "version": self.version,
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class ContextSnapshot:
    """Small, replayable context snapshot captured at normalization time."""

    summary: str = ""
    facts: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    captured_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "facts": _json_safe(self.facts),
            "source": self.source,
            "captured_at": self.captured_at.isoformat(),
        }


@dataclass(frozen=True)
class SituationSignal:
    """Raw normalized signal before it becomes a typed intent."""

    domain: str
    signal_type: str
    source_event_id: str | None = None
    decision_id: str | None = None
    subject: str = ""
    scope: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None
    created_at: datetime = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "signal_type": self.signal_type,
            "source_event_id": self.source_event_id,
            "decision_id": self.decision_id,
            "subject": self.subject,
            "scope": _json_safe(self.scope),
            "payload": _json_safe(self.payload),
            "trace_id": self.trace_id,
            "created_at": self.created_at.isoformat(),
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class TypedIntent:
    """Schema-stable intent used by analyzers and future Control Tower routing."""

    domain: str
    intent_type: str
    verb: str
    subject: str
    scope: dict[str, Any] = field(default_factory=dict)
    context_snapshot: ContextSnapshot | None = None
    policies: list[PolicyReference] = field(default_factory=list)
    source_event_id: str | None = None
    decision_id: str | None = None
    trace_id: str = field(default_factory=_trace_id)
    created_at: datetime = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_signal(
        cls,
        signal: SituationSignal,
        *,
        intent_type: str | None = None,
        verb: str = "analyze",
        subject: str | None = None,
        scope: dict[str, Any] | None = None,
        context_snapshot: ContextSnapshot | None = None,
        policies: list[PolicyReference] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "TypedIntent":
        merged_scope = dict(signal.scope)
        if scope:
            merged_scope.update(scope)
        merged_metadata = dict(signal.metadata)
        merged_metadata.setdefault("raw_payload", dict(signal.payload))
        if metadata:
            merged_metadata.update(metadata)
        return cls(
            domain=signal.domain,
            intent_type=intent_type or signal.signal_type,
            verb=verb,
            subject=subject if subject is not None else signal.subject,
            scope=merged_scope,
            context_snapshot=context_snapshot,
            policies=list(policies or []),
            source_event_id=signal.source_event_id,
            decision_id=signal.decision_id,
            trace_id=signal.trace_id or _trace_id(),
            created_at=signal.created_at,
            metadata=merged_metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "intent_type": self.intent_type,
            "verb": self.verb,
            "subject": self.subject,
            "scope": _json_safe(self.scope),
            "context_snapshot": (
                self.context_snapshot.to_dict() if self.context_snapshot is not None else None
            ),
            "policies": [policy.to_dict() for policy in self.policies],
            "source_event_id": self.source_event_id,
            "decision_id": self.decision_id,
            "trace_id": self.trace_id,
            "created_at": self.created_at.isoformat(),
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class TraversalNode:
    """A bounded context node returned by a traversal pattern."""

    id: str
    type: str
    label: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    depth: int = 0
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "properties": _json_safe(self.properties),
            "depth": self.depth,
            "source": self.source,
        }


@dataclass(frozen=True)
class TraversalEdge:
    """A bounded context relationship returned by a traversal pattern."""

    source_id: str
    target_id: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)
    depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "properties": _json_safe(self.properties),
            "depth": self.depth,
        }


@dataclass(frozen=True)
class SituationContext:
    """Structured situation context suitable for replay, audit, and NL templates."""

    domain: str
    decision_id: str | None = None
    intent: TypedIntent | None = None
    pattern_name: str | None = None
    nodes: list[TraversalNode] = field(default_factory=list)
    edges: list[TraversalEdge] = field(default_factory=list)
    evidence_chain: list[dict[str, Any]] = field(default_factory=list)
    max_depth: int = 3
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "decision_id": self.decision_id,
            "intent": self.intent.to_dict() if self.intent is not None else None,
            "pattern_name": self.pattern_name,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "evidence_chain": _json_safe(self.evidence_chain),
            "max_depth": self.max_depth,
            "truncated": self.truncated,
            "warnings": list(self.warnings),
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class TraversalResult:
    """Traversal result wrapper for callers that need pattern-level metadata."""

    context: SituationContext
    pattern_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "pattern_name": self.pattern_name,
            "metadata": _json_safe(self.metadata),
        }
