from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from datetime import datetime
from copy import deepcopy
from typing import Any

import pytest

from copilot_sdk.situation import (
    ContextSnapshot,
    PolicyReference,
    SituationAnalyzer,
    SituationContext,
    SituationSignal,
    TraversalEdge,
    TraversalNode,
    TypedIntent,
)


@dataclass
class FakeGraphStore:
    decision: dict[str, Any]

    def __post_init__(self) -> None:
        self.read_calls: list[str] = []
        self.write_calls: list[str] = []

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        self.read_calls.append(decision_id)
        return self.decision if self.decision.get("decision_id") == decision_id else None

    def write_decision(self, *args: Any, **kwargs: Any) -> str:
        self.write_calls.append("write_decision")
        return "unexpected"


class FakePattern:
    domain = "demo"
    name = "demo_context"
    default_max_depth = 3

    def __init__(self) -> None:
        self.calls: list[tuple[TypedIntent, int]] = []

    def supports(self, intent: TypedIntent) -> bool:
        return intent.domain == self.domain

    def traverse(
        self,
        intent: TypedIntent,
        *,
        graph_store: Any = None,
        max_depth: int = 3,
    ) -> SituationContext:
        self.calls.append((intent, max_depth))
        decision_id = intent.decision_id or str(intent.scope.get("decision_id") or "")
        decision = graph_store.get_decision(decision_id) if graph_store is not None else None
        nodes = [
            TraversalNode(
                id=decision_id or "unknown",
                type="decision",
                label="Decision",
                properties=decision or {},
                depth=0,
                source="fake",
            )
        ]
        edges = [
            TraversalEdge(
                source_id=nodes[0].id,
                target_id="context-1",
                type="HAS_CONTEXT",
                depth=1,
            )
        ]
        return SituationContext(
            domain=intent.domain,
            decision_id=decision_id or None,
            intent=intent,
            pattern_name=self.name,
            nodes=nodes,
            edges=edges,
            evidence_chain=[{"node_id": nodes[0].id, "kind": "decision"}],
            max_depth=max_depth,
        )


class WarningPattern(FakePattern):
    name = "warning_context"

    def traverse(
        self,
        intent: TypedIntent,
        *,
        graph_store: Any = None,
        max_depth: int = 3,
    ) -> SituationContext:
        return SituationContext(
            domain=intent.domain,
            decision_id=intent.decision_id,
            intent=intent,
            pattern_name=self.name,
            max_depth=max_depth,
            truncated=True,
            warnings=["depth limit reached"],
            metadata={"from_pattern": True},
        )


def test_typed_intent_preserves_traceability_fields() -> None:
    snapshot = ContextSnapshot(summary="queued alert", facts={"risk": 0.8}, source="unit")
    policy = PolicyReference(policy_id="POL-1", name="Escalation", version="v1")
    intent = TypedIntent(
        domain="demo",
        intent_type="alert_context",
        verb="explain",
        subject="alert",
        scope={"alert_id": "A1"},
        context_snapshot=snapshot,
        policies=[policy],
        source_event_id="A1",
        decision_id="D1",
        trace_id="TRACE-1",
        metadata={"raw_payload": {"severity": "high"}},
    )

    payload = intent.to_dict()

    assert payload["domain"] == "demo"
    assert payload["verb"] == "explain"
    assert payload["subject"] == "alert"
    assert payload["scope"] == {"alert_id": "A1"}
    assert payload["trace_id"] == "TRACE-1"
    assert payload["source_event_id"] == "A1"
    assert payload["decision_id"] == "D1"
    assert payload["policies"][0]["policy_id"] == "POL-1"
    assert payload["context_snapshot"]["facts"] == {"risk": 0.8}
    assert payload["metadata"]["raw_payload"] == {"severity": "high"}


def test_normalize_signal_generates_non_empty_trace_id_when_missing() -> None:
    analyzer = SituationAnalyzer()
    signal = SituationSignal(
        domain="demo",
        signal_type="alert_context",
        source_event_id="A1",
        subject="alert",
        scope={"alert_id": "A1"},
    )

    intent = analyzer.normalize_signal(signal, verb="explain")

    assert intent.trace_id
    assert intent.trace_id.startswith("sit-")
    assert intent.domain == "demo"
    assert intent.source_event_id == "A1"


def test_normalize_raw_dict_preserves_vendor_extra_fields() -> None:
    analyzer = SituationAnalyzer()
    raw = {
        "domain": "s2p",
        "intent_type": "kpi_breach",
        "verb": "investigate",
        "subject": "invoice",
        "scope": {"invoice_id": "INV-1"},
        "severity": "high",
        "vendor_payload_type": "sap_alert",
        "amount": 123.45,
    }

    intent = analyzer.normalize_signal(raw)
    payload = intent.to_dict()

    assert intent.domain == "s2p"
    assert intent.intent_type == "kpi_breach"
    assert intent.verb == "investigate"
    assert intent.scope["invoice_id"] == "INV-1"
    assert intent.metadata["raw_payload"] == raw
    assert intent.metadata["raw_payload"]["severity"] == "high"
    assert intent.metadata["raw_payload"]["vendor_payload_type"] == "sap_alert"
    assert intent.metadata["raw_payload"]["amount"] == 123.45
    assert payload["metadata"]["raw_payload"]["severity"] == "high"


def test_normalize_raw_dict_coerces_iso_created_at() -> None:
    analyzer = SituationAnalyzer()

    intent = analyzer.normalize_signal(
        {
            "domain": "soc",
            "intent_type": "alert_context",
            "subject": "alert",
            "created_at": "2026-06-13T12:34:56+00:00",
        }
    )

    assert isinstance(intent.created_at, datetime)
    assert intent.to_dict()["created_at"] == "2026-06-13T12:34:56+00:00"


def test_normalize_raw_dict_coerces_epoch_created_at() -> None:
    analyzer = SituationAnalyzer()

    intent = analyzer.normalize_signal(
        {
            "domain": "soc",
            "intent_type": "alert_context",
            "subject": "alert",
            "created_at": 1780000000,
        }
    )

    assert isinstance(intent.created_at, datetime)
    assert intent.to_dict()["created_at"].startswith("2026-05-28T")


def test_normalize_raw_dict_preserves_explicit_payload_and_raw_event() -> None:
    analyzer = SituationAnalyzer()
    raw = {
        "domain": "dataops",
        "intent_type": "schema_drift",
        "subject": "table",
        "scope": {"table": "orders"},
        "payload": {"column": "total_amount"},
        "severity": "medium",
    }

    intent = analyzer.normalize_signal(raw)

    assert intent.metadata["raw_payload"] == raw
    assert intent.metadata["raw_payload"]["severity"] == "medium"
    assert intent.metadata["raw_payload"]["payload"] == {"column": "total_amount"}


def test_normalize_raw_dict_does_not_mutate_input() -> None:
    analyzer = SituationAnalyzer()
    raw = {
        "domain": "soc",
        "intent_type": "alert_context",
        "subject": "alert",
        "scope": {"alert_id": "A1"},
        "payload": {"nested": {"value": 1}},
        "created_at": "2026-06-13T12:34:56Z",
    }
    original = deepcopy(raw)

    analyzer.normalize_signal(raw)

    assert raw == original


def test_normalize_raw_dict_coerces_policy_and_context_snapshot_dicts() -> None:
    analyzer = SituationAnalyzer()

    intent = analyzer.normalize_signal(
        {
            "domain": "soc",
            "intent_type": "alert_context",
            "subject": "alert",
            "policies": [{"policy_id": "POL-1", "name": "Escalation"}],
            "context_snapshot": {
                "summary": "high-risk alert",
                "facts": {"risk": 0.9},
                "source": "test",
                "captured_at": "2026-06-13T12:34:56Z",
            },
        }
    )
    payload = intent.to_dict()

    assert payload["policies"][0]["policy_id"] == "POL-1"
    assert payload["context_snapshot"]["summary"] == "high-risk alert"
    assert payload["context_snapshot"]["captured_at"] == "2026-06-13T12:34:56+00:00"


def test_register_pattern() -> None:
    analyzer = SituationAnalyzer()
    pattern = FakePattern()

    analyzer.register_pattern(pattern)

    assert analyzer.patterns == (pattern,)


def test_analyzer_dispatches_by_domain_support() -> None:
    pattern = FakePattern()
    analyzer = SituationAnalyzer([pattern])
    intent = TypedIntent(
        domain="demo",
        intent_type="decision_context",
        verb="explain",
        subject="decision",
        decision_id="D1",
    )

    context = analyzer.analyze_intent(intent, graph_store=FakeGraphStore({"decision_id": "D1"}))

    assert context.pattern_name == "demo_context"
    assert pattern.calls[0][0] is intent


def test_analyze_intent_returns_structured_context() -> None:
    analyzer = SituationAnalyzer([FakePattern()])
    intent = TypedIntent(
        domain="demo",
        intent_type="decision_context",
        verb="explain",
        subject="decision",
        decision_id="D1",
    )

    context = analyzer.analyze_intent(intent, graph_store=FakeGraphStore({"decision_id": "D1"}))
    payload = context.to_dict()

    assert payload["nodes"][0]["id"] == "D1"
    assert payload["edges"][0]["type"] == "HAS_CONTEXT"
    assert payload["evidence_chain"] == [{"node_id": "D1", "kind": "decision"}]


def test_default_max_depth_is_three() -> None:
    pattern = FakePattern()
    analyzer = SituationAnalyzer([pattern])

    analyzer.analyze_intent(
        TypedIntent(domain="demo", intent_type="x", verb="explain", subject="thing")
    )

    assert pattern.calls[0][1] == 3


def test_max_depth_override_within_bounds() -> None:
    pattern = FakePattern()
    analyzer = SituationAnalyzer([pattern])

    context = analyzer.analyze_intent(
        TypedIntent(domain="demo", intent_type="x", verb="explain", subject="thing"),
        max_depth=2,
    )

    assert context.max_depth == 2
    assert pattern.calls[0][1] == 2


def test_excessive_depth_raises_value_error() -> None:
    analyzer = SituationAnalyzer(max_allowed_depth=5)

    with pytest.raises(ValueError, match="max_depth 6 exceeds"):
        analyzer.analyze_intent(
            TypedIntent(domain="demo", intent_type="x", verb="explain", subject="thing"),
            max_depth=6,
        )


def test_no_matching_pattern_returns_empty_context_with_warning() -> None:
    analyzer = SituationAnalyzer([FakePattern()])
    intent = TypedIntent(domain="other", intent_type="x", verb="explain", subject="thing")

    context = analyzer.analyze_intent(intent)

    assert context.nodes == []
    assert context.edges == []
    assert context.warnings == ["no traversal pattern registered for domain='other'"]


def test_pattern_truncation_and_warnings_preserved() -> None:
    analyzer = SituationAnalyzer([WarningPattern()])
    intent = TypedIntent(domain="demo", intent_type="x", verb="explain", subject="thing")

    context = analyzer.analyze_intent(intent)

    assert context.truncated is True
    assert context.warnings == ["depth limit reached"]
    assert context.metadata["from_pattern"] is True


def test_analyze_decision_does_not_mutate_graph_store() -> None:
    analyzer = SituationAnalyzer([FakePattern()])
    store = FakeGraphStore({"decision_id": "D1", "domain": "demo"})

    context = analyzer.analyze_decision("D1", domain="demo", graph_store=store)

    assert context.decision_id == "D1"
    assert store.read_calls == ["D1"]
    assert store.write_calls == []


def test_s2p_specific_traversal_not_implemented_in_sdk_p33() -> None:
    import copilot_sdk.situation as situation_pkg

    names: list[str] = []
    for module_info in pkgutil.iter_modules(situation_pkg.__path__):
        module = importlib.import_module(f"copilot_sdk.situation.{module_info.name}")
        names.extend(dir(module))

    forbidden_terms = ("S2P", "Invoice", "Supplier", "Contract")
    assert not any(any(term in name for term in forbidden_terms) for name in names)
