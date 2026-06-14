"""Domain-agnostic Situation Analyzer."""

from __future__ import annotations

from copy import deepcopy
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from copilot_sdk.situation.models import (
    ContextSnapshot,
    PolicyReference,
    SituationContext,
    SituationSignal,
    TypedIntent,
)
from copilot_sdk.situation.patterns import TraversalPattern


class SituationAnalyzer:
    """Normalize signals and dispatch typed intents to traversal patterns."""

    def __init__(
        self,
        patterns: Sequence[TraversalPattern] | None = None,
        *,
        default_max_depth: int = 3,
        max_allowed_depth: int = 5,
    ) -> None:
        if default_max_depth < 0:
            raise ValueError("default_max_depth must be non-negative")
        if max_allowed_depth < default_max_depth:
            raise ValueError("max_allowed_depth must be >= default_max_depth")
        self.default_max_depth = int(default_max_depth)
        self.max_allowed_depth = int(max_allowed_depth)
        self._patterns: list[TraversalPattern] = []
        for pattern in patterns or []:
            self.register_pattern(pattern)

    @property
    def patterns(self) -> tuple[TraversalPattern, ...]:
        return tuple(self._patterns)

    def register_pattern(self, pattern: TraversalPattern) -> None:
        if not getattr(pattern, "name", ""):
            raise ValueError("traversal pattern must define a non-empty name")
        if not getattr(pattern, "domain", ""):
            raise ValueError("traversal pattern must define a non-empty domain")
        self._patterns.append(pattern)

    def normalize_signal(
        self,
        signal: SituationSignal | dict[str, Any],
        *,
        intent_type: str | None = None,
        verb: str = "analyze",
        subject: str | None = None,
        scope: dict[str, Any] | None = None,
        context_snapshot: ContextSnapshot | None = None,
        policies: list[PolicyReference] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TypedIntent:
        if isinstance(signal, SituationSignal):
            normalized = signal
            resolved_intent_type = intent_type
            resolved_verb = verb
            resolved_subject = subject
            resolved_context_snapshot = context_snapshot
            resolved_policies = policies
            resolved_metadata = metadata
        else:
            (
                normalized,
                resolved_intent_type,
                resolved_verb,
                resolved_subject,
                resolved_context_snapshot,
                resolved_policies,
                resolved_metadata,
            ) = _normalize_raw_signal_dict(
                signal,
                intent_type=intent_type,
                verb=verb,
                subject=subject,
                context_snapshot=context_snapshot,
                policies=policies,
                metadata=metadata,
            )
        return TypedIntent.from_signal(
            normalized,
            intent_type=resolved_intent_type,
            verb=resolved_verb,
            subject=resolved_subject,
            scope=scope,
            context_snapshot=resolved_context_snapshot,
            policies=resolved_policies,
            metadata=resolved_metadata,
        )

    def analyze_decision(
        self,
        decision_id: str,
        *,
        domain: str,
        graph_store: Any = None,
        max_depth: int | None = None,
        **metadata: Any,
    ) -> SituationContext:
        signal = SituationSignal(
            domain=domain,
            signal_type="decision_context",
            decision_id=decision_id,
            subject="decision",
            scope={"decision_id": decision_id},
            metadata=metadata,
        )
        return self.analyze_intent(
            self.normalize_signal(signal),
            graph_store=graph_store,
            max_depth=max_depth,
        )

    def analyze_intent(
        self,
        intent: TypedIntent,
        *,
        graph_store: Any = None,
        max_depth: int | None = None,
    ) -> SituationContext:
        depth = self._resolve_depth(max_depth)
        for pattern in self._patterns:
            if pattern.supports(intent):
                context = pattern.traverse(intent, graph_store=graph_store, max_depth=depth)
                return self._with_analyzer_metadata(context, intent=intent, max_depth=depth)
        return SituationContext(
            domain=intent.domain,
            decision_id=intent.decision_id,
            intent=intent,
            max_depth=depth,
            warnings=[f"no traversal pattern registered for domain={intent.domain!r}"],
            metadata={"pattern_count": len(self._patterns)},
        )

    def _resolve_depth(self, max_depth: int | None) -> int:
        depth = self.default_max_depth if max_depth is None else int(max_depth)
        if depth < 0:
            raise ValueError("max_depth must be non-negative")
        if depth > self.max_allowed_depth:
            raise ValueError(
                f"max_depth {depth} exceeds max_allowed_depth {self.max_allowed_depth}"
            )
        return depth

    @staticmethod
    def _with_analyzer_metadata(
        context: SituationContext,
        *,
        intent: TypedIntent,
        max_depth: int,
    ) -> SituationContext:
        if context.intent is intent and context.max_depth == max_depth:
            return context
        metadata = dict(context.metadata)
        metadata.setdefault("analyzer_attached_intent", context.intent is None)
        return SituationContext(
            domain=context.domain,
            decision_id=context.decision_id if context.decision_id is not None else intent.decision_id,
            intent=context.intent or intent,
            pattern_name=context.pattern_name,
            nodes=list(context.nodes),
            edges=list(context.edges),
            evidence_chain=list(context.evidence_chain),
            max_depth=max_depth,
            truncated=context.truncated,
            warnings=list(context.warnings),
            metadata=metadata,
        )


def _normalize_raw_signal_dict(
    raw_signal: dict[str, Any],
    *,
    intent_type: str | None,
    verb: str,
    subject: str | None,
    context_snapshot: ContextSnapshot | None,
    policies: list[PolicyReference] | None,
    metadata: dict[str, Any] | None,
) -> tuple[
    SituationSignal,
    str | None,
    str,
    str | None,
    ContextSnapshot | None,
    list[PolicyReference] | None,
    dict[str, Any] | None,
]:
    raw = deepcopy(raw_signal)
    known = {
        "domain",
        "signal_type",
        "intent_type",
        "verb",
        "subject",
        "scope",
        "source_event_id",
        "decision_id",
        "trace_id",
        "policies",
        "context_snapshot",
        "created_at",
        "payload",
        "metadata",
    }
    extras = {key: deepcopy(value) for key, value in raw.items() if key not in known}
    raw_metadata = raw.get("metadata")
    merged_metadata = dict(raw_metadata) if isinstance(raw_metadata, dict) else {}
    merged_metadata["raw_payload"] = deepcopy(raw_signal)
    if metadata:
        merged_metadata.update(metadata)

    payload = raw.get("payload")
    if payload is None:
        normalized_payload = extras
    elif isinstance(payload, dict):
        normalized_payload = deepcopy(payload)
    else:
        normalized_payload = {"value": deepcopy(payload)}

    domain = raw.get("domain")
    if not domain:
        raise ValueError("raw situation signal must include domain")
    raw_intent_type = raw.get("intent_type")
    signal_type = raw.get("signal_type") or raw_intent_type or "raw_event"

    normalized = SituationSignal(
        domain=str(domain),
        signal_type=str(signal_type),
        source_event_id=_optional_str(raw.get("source_event_id")),
        decision_id=_optional_str(raw.get("decision_id")),
        subject=str(raw.get("subject") or ""),
        scope=deepcopy(raw.get("scope") or {}),
        payload=normalized_payload,
        trace_id=_optional_str(raw.get("trace_id")),
        created_at=_coerce_datetime(raw.get("created_at")),
        metadata=merged_metadata,
    )
    return (
        normalized,
        intent_type if intent_type is not None else _optional_str(raw_intent_type),
        str(raw.get("verb") or verb),
        subject if subject is not None else _optional_str(raw.get("subject")),
        context_snapshot
        if context_snapshot is not None
        else _coerce_context_snapshot(raw.get("context_snapshot")),
        policies if policies is not None else _coerce_policies(raw.get("policies")),
        merged_metadata,
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _coerce_datetime(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"invalid created_at timestamp: {value!r}") from exc
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    raise ValueError(f"unsupported created_at type: {type(value).__name__}")


def _coerce_context_snapshot(value: Any) -> ContextSnapshot | None:
    if value is None or isinstance(value, ContextSnapshot):
        return value
    if not isinstance(value, dict):
        raise ValueError("context_snapshot must be a ContextSnapshot or dict")
    data = deepcopy(value)
    if "captured_at" in data:
        data["captured_at"] = _coerce_datetime(data["captured_at"])
    return ContextSnapshot(**data)


def _coerce_policies(value: Any) -> list[PolicyReference] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("policies must be a list")
    normalized: list[PolicyReference] = []
    for policy in value:
        if isinstance(policy, PolicyReference):
            normalized.append(policy)
        elif isinstance(policy, dict):
            normalized.append(PolicyReference(**deepcopy(policy)))
        else:
            raise ValueError("policies must contain PolicyReference objects or dicts")
    return normalized
