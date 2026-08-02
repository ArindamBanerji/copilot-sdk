from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.graph.projection import AGEProjection, ProjectionRegistry


class _ProjectionClient:
    """Complete local client double for constructor and Cypher guard tests."""

    def __init__(self) -> None:
        self.queries: list[str] = []

    async def run_query(self, cypher: str, _params: Any = None) -> list[dict[str, Any]]:
        self.queries.append(cypher)
        return []


def _projection() -> AGEProjection:
    return AGEProjection(client=_ProjectionClient(), graph_name="soc_graph", domain="soc")


def test_projection_uses_authorized_graph() -> None:
    projection = _projection()

    assert projection.graph_name == "soc_graph"
    assert projection.domain == "soc"


def test_projection_has_no_direct_age_client_import() -> None:
    source = Path(__file__).resolve().parents[2] / "copilot_sdk" / "graph" / "projection.py"
    text = source.read_text(encoding="utf-8")

    assert "from ci_platform.graph.age_client import AGEClient" not in text
    assert "AGEClient(" not in text


def test_projection_uses_injected_client() -> None:
    client = _ProjectionClient()
    projection = AGEProjection(client=client, graph_name="soc_graph", domain="soc")

    assert projection._query("MATCH (d:Decision) RETURN d") == []
    assert len(client.queries) == 1


def test_projection_rejects_unauthorized_graph() -> None:
    with pytest.raises(ValueError, match="soc_graph"):
        AGEProjection(
            client=_ProjectionClient(),
            graph_name="other_graph",
            domain="soc",
        )


def test_projection_read_only_preserved() -> None:
    projection = _projection()

    with pytest.raises(ValueError, match="read-only"):
        projection._query("MATCH (d:Decision) SET d.correct = true RETURN d")


def test_projection_domain_predicate_preserved() -> None:
    projection = _projection()

    predicate = projection._d2_where()

    assert "d.domain" in predicate
    assert "soc" in predicate


def test_projection_count_correct_requires_verified_status() -> None:
    client = _ProjectionClient()
    projection = AGEProjection(client=client, graph_name="soc_graph", domain="soc")

    projection.count_correct()

    assert "d.status IN ['confirmed', 'overridden']" in client.queries[-1]


def test_render_count_verified_includes_status() -> None:
    rendered = ProjectionRegistry.render("count_verified", domain="soc")

    assert "d.status IN ['confirmed', 'overridden']" in rendered
    assert "<d2>" not in rendered


def test_render_count_correct_includes_status_and_correct() -> None:
    rendered = ProjectionRegistry.render("count_correct", domain="soc")

    assert "d.status IN ['confirmed', 'overridden']" in rendered
    assert "d.correct = true" in rendered
    assert "<d2-correct>" not in rendered


def test_render_no_unsubstituted_tokens() -> None:
    for pattern_name in ProjectionRegistry.PATTERNS:
        rendered = ProjectionRegistry.render(pattern_name, domain="test")

        assert "<d2>" not in rendered
        assert "<d2-correct>" not in rendered
