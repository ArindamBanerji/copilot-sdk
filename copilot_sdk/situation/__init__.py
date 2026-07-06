"""Situation Analyzer foundation for typed-intent context traversal."""

from copilot_sdk.situation.analyzer import SituationAnalyzer
from copilot_sdk.situation.models import (
    ContextSnapshot,
    ContextChain,
    PolicyReference,
    SituationContext,
    SituationSignal,
    TraversalEdge,
    TraversalNode,
    TraversalResult,
    TypedIntent,
)
from copilot_sdk.situation.patterns import TraversalPattern
from copilot_sdk.situation.renderer import NLRenderer, NLRenderResult
from copilot_sdk.situation.templates import SafeTemplateRenderer, TemplateRenderResult

__all__ = [
    "ContextChain",
    "ContextSnapshot",
    "NLRenderer",
    "NLRenderResult",
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
