from __future__ import annotations

from typing import Any, Callable, cast

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


@pytest.fixture(params=["memory", "sqlite"])
def store(request: pytest.FixtureRequest, tmp_path: Any) -> Any:
    if request.param == "memory":
        return InMemoryGraphStore(domain="test")
    return SQLiteGraphStore(tmp_path / "domain-required.sqlite", domain="test")


def _decision(store: Any, domain: str, decision_id: str, category: str = "shared") -> str:
    return cast(str, store.write_decision(
        domain,
        category,
        "review",
        0.8,
        {"signal": 0.8},
        metadata={"decision_id": decision_id, "entity_id": f"entity-{decision_id}"},
    ))


def _decisions_by_domain(store: Any) -> tuple[str, str]:
    return _decision(store, "soc", "soc-1"), _decision(store, "trading", "trading-1")


@pytest.mark.parametrize("method", ["get_decision", "get_decision_links"])
def test_decision_reads_require_domain(store: Any, method: str) -> None:
    soc_id, _ = _decisions_by_domain(store)
    if method == "get_decision_links":
        store.link_decision_to_entity(soc_id, "entity-soc", domain="soc")
        args: tuple[Any, ...] = ()
    else:
        args = (soc_id,)
    reader: Callable[..., Any] = getattr(store, method)
    with pytest.raises(TypeError):
        reader(*args)


@pytest.mark.parametrize("method", ["query_context", "query_similar"])
def test_traversal_reads_require_domain(store: Any, method: str) -> None:
    soc_id, _ = _decisions_by_domain(store)
    store.link_decision_to_entity(soc_id, "entity-soc", domain="soc")
    reader: Callable[..., Any] = getattr(store, method)
    args = ("entity-soc", 2) if method == "query_context" else (soc_id, 5)
    with pytest.raises(TypeError):
        reader(*args)


def test_write_outcome_requires_domain(store: Any) -> None:
    decision_id = _decision(store, "soc", "outcome-1")
    with pytest.raises(TypeError):
        store.write_outcome(decision_id, "review", True)


@pytest.mark.parametrize("method", [
    "get_decision",
    "get_decision_links",
    "query_context",
    "query_similar",
    "write_outcome",
])
def test_changed_methods_reject_empty_domain(store: Any, method: str) -> None:
    decision_id = _decision(store, "soc", "empty-domain-1")
    if method == "get_decision":
        args: tuple[Any, ...] = (decision_id,)
    elif method == "get_decision_links":
        args = ()
    elif method == "query_context":
        args = (f"entity-{decision_id}", 2)
    elif method == "query_similar":
        args = (decision_id, 5)
    else:
        args = (decision_id, "review", True)
    reader: Callable[..., Any] = getattr(store, method)
    with pytest.raises(ValueError):
        reader(*args, domain="  ")


def test_get_decision_is_domain_scoped(store: Any) -> None:
    soc_id, trading_id = _decisions_by_domain(store)
    assert store.get_decision(soc_id, domain="soc")["domain"] == "soc"
    assert store.get_decision(trading_id, domain="soc") is None
    assert store.get_decision("missing", domain="unknown") is None


def test_get_decision_links_are_domain_scoped(store: Any) -> None:
    soc_id, trading_id = _decisions_by_domain(store)
    store.link_decision_to_entity(soc_id, "shared-entity", domain="soc")
    store.link_decision_to_entity(trading_id, "shared-entity", domain="trading")

    soc_links = store.get_decision_links(domain="soc")
    assert [link["decision_id"] for link in soc_links] == [soc_id]
    assert store.get_decision_links(domain="unknown") == []


def test_query_context_is_domain_scoped(store: Any) -> None:
    soc_id, trading_id = _decisions_by_domain(store)
    store.link_decision_to_entity(soc_id, "shared-entity", domain="soc")
    store.link_decision_to_entity(trading_id, "shared-entity", domain="trading")

    soc_rows = store.query_context("shared-entity", 2, domain="soc")
    decision_ids = {row["id"] for row in soc_rows if row.get("node") == "decision"}
    assert soc_id in decision_ids
    assert trading_id not in decision_ids
    unknown_rows = store.query_context("shared-entity", 2, domain="unknown")
    assert not any(row.get("node") == "decision" for row in unknown_rows)


def test_query_similar_is_domain_scoped(store: Any) -> None:
    soc_id = _decision(store, "soc", "similar-soc-1", category="shared")
    similar_soc_id = _decision(store, "soc", "similar-soc-2", category="shared")
    trading_id = _decision(store, "trading", "similar-trading-1", category="shared")

    matches = store.query_similar(soc_id, 10, domain="soc")
    match_ids = {match["decision_id"] for match in matches}
    assert similar_soc_id in match_ids
    assert trading_id not in match_ids
    assert store.query_similar(soc_id, 10, domain="unknown") == []


def test_write_outcome_is_domain_scoped(store: Any) -> None:
    decision_id = _decision(store, "soc", "outcome-scope-1")
    store.write_outcome(decision_id, "review", True, domain="soc")
    decision = store.get_decision(decision_id, domain="soc")
    assert decision is not None
    assert decision["correct"] is True
    with pytest.raises(KeyError):
        store.write_outcome("missing", "review", True, domain="soc")
