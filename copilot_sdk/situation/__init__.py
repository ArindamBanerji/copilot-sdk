"""Situation Analyzer foundation for typed-intent context traversal."""

from copilot_sdk.situation.analyzer import SituationAnalyzer
from copilot_sdk.situation.models import (
    ContextSnapshot,
    PolicyReference,
    SituationContext,
    SituationSignal,
    TraversalEdge,
    TraversalNode,
    TraversalResult,
    TypedIntent,
)
from copilot_sdk.situation.patterns import TraversalPattern
from copilot_sdk.situation.templates import SafeTemplateRenderer, TemplateRenderResult

__all__ = [
    "ContextSnapshot",
    "PolicyReference",
    "SituationAnalyzer",
    "SituationContext",
    "SituationSignal",
    "SafeTemplateRenderer",
    "TemplateRenderResult",
    "TraversalEdge",
    "TraversalNode",
    "TraversalPattern",
    "TraversalResult",
    "TypedIntent",
]
