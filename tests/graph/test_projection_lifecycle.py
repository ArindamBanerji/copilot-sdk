from __future__ import annotations

import pytest

from copilot_sdk.graph.projection import AGEProjection


def test_projection_uses_authorized_graph() -> None:
    projection = AGEProjection(
        dsn="host=localhost dbname=test",
        graph_name="soc_graph",
        domain="soc",
    )

    assert projection.graph_name == "soc_graph"
    assert projection.domain == "soc"


def test_projection_rejects_unauthorized_graph() -> None:
    with pytest.raises(ValueError, match="soc_graph"):
        AGEProjection(
            dsn="host=localhost dbname=test",
            graph_name="other_graph",
            domain="soc",
        )


def test_projection_read_only_preserved() -> None:
    projection = AGEProjection(
        dsn="host=localhost dbname=test",
        graph_name="soc_graph",
        domain="soc",
    )

    with pytest.raises(ValueError, match="read-only"):
        projection._query("MATCH (d:Decision) SET d.correct = true RETURN d")


def test_projection_domain_predicate_preserved() -> None:
    projection = AGEProjection(
        dsn="host=localhost dbname=test",
        graph_name="soc_graph",
        domain="soc",
    )

    predicate = projection._d2_where()

    assert "d.domain" in predicate
    assert "soc" in predicate
