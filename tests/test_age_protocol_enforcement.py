from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from copilot_sdk.backend.health_builder import build_graph_health
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.graph.factory import assert_production_graph
from copilot_sdk.graph.production import GraphStoreWrapper
from copilot_sdk.graph.protocol import GraphStore


class ProductionV2Store(InMemoryGraphStore):
    @property
    def production_ready(self) -> bool:
        return True


class PlainV1Store:
    def count_decisions(self, domain: str) -> int:
        return 0


class ProductionV1Store(PlainV1Store):
    @property
    def production_ready(self) -> bool:
        return True


def test_production_assertion_accepts_store_with_both_protocols() -> None:
    store = ProductionV2Store(domain="trading")
    try:
        assert_production_graph(store, "production")
    finally:
        store.close()


def test_production_assertion_rejects_in_memory_store() -> None:
    store = InMemoryGraphStore(domain="trading")
    try:
        with pytest.raises(RuntimeError, match="ProductionReadyStore") as error:
            assert_production_graph(store, "production")
        assert "ProtocolV2GraphStore" not in str(error.value)
    finally:
        store.close()


def test_production_assertion_rejects_marker_without_protocol_v2() -> None:
    store = cast(GraphStore, ProductionV1Store())
    with pytest.raises(RuntimeError, match="ProtocolV2GraphStore") as error:
        assert_production_graph(store, "production")
    assert "ProductionReadyStore" not in str(error.value)


@pytest.mark.parametrize("profile", ["test", "offline", "development"])
def test_production_assertion_is_noop_outside_production(profile: str) -> None:
    store = InMemoryGraphStore(domain="dataops")
    try:
        assert_production_graph(store, profile)
    finally:
        store.close()


def test_memory_health_reports_v2_non_production() -> None:
    store = InMemoryGraphStore(domain="trading")
    try:
        payload = build_graph_health(store, SimpleNamespace(graph="soc_graph"), "trading")
    finally:
        store.close()
    assert payload["protocol_version"] == "v2"
    assert payload["production_ready"] is False


def test_production_health_reports_v2_and_ready() -> None:
    store = ProductionV2Store(domain="purchasing")
    try:
        payload = build_graph_health(store, SimpleNamespace(graph="soc_graph"), "purchasing")
    finally:
        store.close()
    assert payload["protocol_version"] == "v2"
    assert payload["production_ready"] is True


def test_plain_store_health_reports_v1_non_production() -> None:
    payload = build_graph_health(
        cast(GraphStore, PlainV1Store()), SimpleNamespace(graph="soc_graph"), "dataops"
    )
    assert payload["protocol_version"] == "v1"
    assert payload["production_ready"] is False


def test_marker_only_health_reports_v1_and_ready() -> None:
    payload = build_graph_health(
        cast(GraphStore, ProductionV1Store()), SimpleNamespace(graph="soc_graph"), "dataops"
    )
    assert payload["protocol_version"] == "v1"
    assert payload["production_ready"] is True


def test_missing_store_health_reports_v1_non_production() -> None:
    payload = build_graph_health(None, SimpleNamespace(graph="soc_graph"), "trading")
    assert payload["protocol_version"] == "v1"
    assert payload["production_ready"] is False


def test_health_classifies_declared_wrapper_primary() -> None:
    primary = InMemoryGraphStore(domain="s2p")
    wrapper = GraphStoreWrapper()
    wrapper._store = primary
    try:
        payload = build_graph_health(wrapper, SimpleNamespace(graph="soc_graph"), "s2p")
    finally:
        primary.close()
    assert payload["protocol_version"] == "v2"
    assert payload["production_ready"] is False


@pytest.mark.parametrize(
    ("relative_path", "assignment", "assertion"),
    [
        (
            "apps/trading/backend/app/main.py",
            "app.state.graph_store = scorer_proxy.graph_store",
            "assert_production_graph(app.state.graph_store, resolved_profile)",
        ),
        (
            "apps/purchasing/backend/app/main.py",
            "app.state.graph_store = scorer_proxy.graph_store",
            "assert_production_graph(app.state.graph_store, resolved_profile)",
        ),
        (
            "apps/dataops/backend/app/main.py",
            "app.state.graph_store = selected_graph_store",
            "assert_production_graph(app.state.graph_store, graph_config.profile)",
        ),
    ],
)
def test_copilot_wires_assertion_immediately_after_store_assignment(
    relative_path: str, assignment: str, assertion: str
) -> None:
    source = (Path(__file__).resolve().parents[1] / relative_path).read_text(encoding="utf-8")
    lines = [line.strip() for line in source.splitlines()]
    assignment_index = lines.index(assignment)
    assert lines[assignment_index + 1] == assertion
    assert (
        "from copilot_sdk.graph.factory import assert_production_graph, create_graph_store"
        in source
    )
