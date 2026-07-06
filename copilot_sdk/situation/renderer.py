"""Domain-neutral natural-language renderer for situation contexts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from copilot_sdk.situation.templates import SafeTemplateRenderer


@dataclass(frozen=True)
class NLRenderResult:
    """Rendered NL explanation plus template diagnostics."""

    rendered: str
    missing_variables: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.rendered

    def __contains__(self, value: object) -> bool:
        return str(value) in self.rendered

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.rendered == other
        return super().__eq__(other)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rendered": self.rendered,
            "missing_variables": list(self.missing_variables),
            "variables": dict(self.variables),
        }


class NLRenderer:
    """Render category-selected NL output without executing template content."""

    def __init__(self, templates: dict[str, str] | None = None) -> None:
        self._templates = dict(templates or {})
        self._renderer = SafeTemplateRenderer()

    def render(
        self,
        category: str,
        template_vars: dict[str, Any],
        dk_weights: dict[str, Any] | None = None,
    ) -> NLRenderResult:
        """Render NL explanation from template variables."""
        variables = dict(template_vars or {})
        if dk_weights is not None:
            variables["dk_weights"] = dk_weights
            variables["dk_weights_available"] = True
        else:
            variables.setdefault("dk_weights_available", False)
        template = self._templates.get(str(category)) or (
            "Situation {category}: {summary}. -> {action}. Confidence: {confidence_pct}."
        )
        variables.setdefault("category", str(category or "unknown"))
        variables.setdefault("summary", "context requires review")
        variables.setdefault("action", "unknown")
        variables.setdefault("confidence_pct", _confidence_pct(variables.get("confidence")))
        result = self._renderer.render(template, variables, defaults=_defaults())
        return NLRenderResult(
            rendered=result.rendered,
            missing_variables=list(result.missing_variables),
            variables=dict(result.variables),
        )


def _defaults() -> dict[str, Any]:
    return {
        "unknown": "unknown",
        "category": "unknown",
        "summary": "context requires review",
        "action": "unknown",
        "confidence_pct": "0%",
    }


def _confidence_pct(value: Any) -> str:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(confidence, 1.0))
    return f"{round(confidence * 100.0):.0f}%"
