from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.graph.projection import AGEProjection, ProjectionRegistry


def _projection() -> AGEProjection:
    return AGEProjection(client=object(), graph_name="soc_graph", domain="soc")


def test_projection_uses_authorized_graph() -> None:
    projection = _projection()

    assert projection.graph_name == "soc_graph"
    assert projection.domain == "soc"


def test_projection_has_no_direct_age_client_import() -> None:
    source = Path(__file__).resolve().parents[2] / "copilot_sdk" / "graph" / "projection.py"
    text = source.read_text(encoding="utf-8")

    assert "from ci_platform.graph.age_client import AGEClient" not in text
    assert "AGEClient(" not in text


@pytest.mark.age
def test_projection_uses_injected_client(disposable_age, monkeypatch) -> None:
    # Authorization has its own constructor test; isolate the live query in a disposable graph.
    monkeypatch.setattr("copilot_sdk.graph.projection.require_shared_graph", lambda *args, **kwargs: None)
    projection = AGEProjection(client=disposable_age.client(), graph_name=disposable_age.graph, domain="soc")
    store = disposable_age.store("soc")
    decision_id = store.write_decision("soc", "risk", "review", 0.8, {"x": 0.5})
    assert projection._query("MATCH (d:Decision) RETURN d.decision_id AS id") == [{"id": decision_id}]
    store.write_decision("soc", "risk", "review", 0.7, {"x": 0.6})
    assert len(projection._query("MATCH (d:Decision) RETURN d.decision_id AS id")) == 2


def test_projection_rejects_unauthorized_graph() -> None:
    with pytest.raises(ValueError, match="soc_graph"):
        AGEProjection(
            client=object(),
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


@pytest.mark.age
def test_projection_count_correct_requires_verified_status(disposable_age, monkeypatch) -> None:
    monkeypatch.setattr("copilot_sdk.graph.projection.require_shared_graph", lambda *args, **kwargs: None)
    projection = AGEProjection(client=disposable_age.client(), graph_name=disposable_age.graph, domain="soc")
    store = disposable_age.store("soc")
    for domain, correct in [("soc", True), ("soc", False), ("other", True), ("soc", None)]:
        decision_id = store.write_decision(domain, "risk", "review", 0.8, {"x": 0.5})
        if correct is not None:
            store.write_outcome(decision_id, "review", correct, domain=domain)
    assert projection.count_correct() == 1
    assert projection.count_verified() == 2


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
