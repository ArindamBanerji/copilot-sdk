"""Data model builder for the Intelligence Map visualization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MapNode:
    id: str
    label: str
    domain: str
    brightness: float
    size: float
    record_count: int
    quality_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MapEdge:
    source: str
    target: str
    thickness: float
    correlation: float
    label: str
    style: str = "solid"
    color: str = "standard"
    annual_value: float | None = None
    confidence: float | None = None
    narrative: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IKSBadge:
    domain: str
    score: int
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceMapData:
    nodes: list[MapNode]
    edges: list[MapEdge]
    gold_lines: list[MapEdge]
    iks_badges: list[IKSBadge]
    domain_clusters: dict[str, list[str]]
    narrative: str
    websocket_pulsing: str = "deferred to DI-7.1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "gold_lines": [line.to_dict() for line in self.gold_lines],
            "iks_badges": [badge.to_dict() for badge in self.iks_badges],
            "domain_clusters": dict(self.domain_clusters),
            "narrative": self.narrative,
            "websocket_pulsing": self.websocket_pulsing,
        }


class IntelligenceMapBuilder:
    """Build map data from source profiles, relationships, and valuations."""

    def build(
        self,
        sources: list[dict[str, Any]],
        correlations: list[dict[str, Any]] | None = None,
        valuations: list[Any] | None = None,
        iks_by_domain: dict[str, int] | None = None,
    ) -> IntelligenceMapData:
        nodes = [self._node(source, index) for index, source in enumerate(sources)]
        edges = [self._edge(item) for item in correlations or []]
        gold_lines = self.add_suggestions(valuations or [])
        badges = self.add_iks_badges(iks_by_domain or {})
        clusters = self.group_by_domain(nodes)
        narrative = self._narrative(nodes, gold_lines, badges)
        return IntelligenceMapData(nodes, edges, gold_lines, badges, clusters, narrative)

    def add_suggestions(self, valuations: list[Any]) -> list[MapEdge]:
        lines = []
        for valuation in valuations:
            item = _as_dict(valuation)
            value = float(item.get("annual_value") or 0.0)
            factor_a = str(item.get("factor_a") or item.get("source_a") or "source_a")
            factor_b = str(item.get("factor_b") or item.get("source_b") or "source_b")
            lines.append(
                MapEdge(
                    factor_a,
                    factor_b,
                    max(1.0, min(value / 50000.0, 8.0)),
                    float(item.get("confidence") or 0.0),
                    f"${_money(value)}/year",
                    "dotted",
                    "gold",
                    value,
                    float(item.get("confidence") or 0.0),
                    str(item.get("narrative") or f"Connect {factor_b} to improve {factor_a}."),
                )
            )
        return lines

    def add_iks_badges(self, iks_by_domain: dict[str, int]) -> list[IKSBadge]:
        return [
            IKSBadge(domain, int(score), _iks_status(int(score)))
            for domain, score in sorted(iks_by_domain.items())
        ]

    def group_by_domain(self, nodes: list[MapNode]) -> dict[str, list[str]]:
        clusters: dict[str, list[str]] = {}
        for node in nodes:
            clusters.setdefault(node.domain, []).append(node.id)
        return clusters

    def _node(self, source: dict[str, Any], index: int) -> MapNode:
        quality = _optional_float(source.get("quality_score", source.get("overall_quality")))
        trust = _optional_float(source.get("source_reliability", source.get("trust", quality)))
        records = int(source.get("record_count", source.get("records", 0)) or 0)
        label = str(source.get("name", source.get("source_name", f"source-{index + 1}")))
        return MapNode(
            str(source.get("id", label)).replace(" ", "_").lower(),
            label,
            str(source.get("domain", "dataops")),
            max(0.25, min(trust if trust is not None else 0.5, 1.0)),
            max(1.0, min(1.0 + records / 1000.0, 8.0)),
            max(records, 0),
            quality,
        )

    def _edge(self, item: dict[str, Any]) -> MapEdge:
        correlation = abs(float(item.get("correlation", 0.0) or 0.0))
        return MapEdge(
            str(item.get("source", item.get("source_a", ""))),
            str(item.get("target", item.get("source_b", ""))),
            max(1.0, min(correlation * 8.0, 8.0)),
            correlation,
            str(item.get("label", f"{round(correlation * 100)}% relationship")),
        )

    def _narrative(self, nodes: list[MapNode], gold_lines: list[MapEdge], badges: list[IKSBadge]) -> str:
        if gold_lines:
            best = max(gold_lines, key=lambda item: item.annual_value or 0.0)
            return f"Intelligence Map found {len(gold_lines)} suggested data connections. Top value: {best.source} x {best.target}, {best.label}."
        return f"Intelligence Map contains {len(nodes)} source nodes and {len(badges)} IKS badges."


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        result = value.to_dict()
        return result if isinstance(result, dict) else {}
    result = asdict(value) if hasattr(value, "__dataclass_fields__") else {}
    return result if isinstance(result, dict) else {}


def _optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iks_status(score: int) -> str:
    if score >= 70:
        return "mature"
    if score >= 30:
        return "developing"
    return "learning"


def _money(value: float) -> str:
    if abs(value) >= 1000:
        return f"{round(value / 1000)}K"
    return f"{round(value):,}"
