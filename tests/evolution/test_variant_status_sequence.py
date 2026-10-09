"""Status replay honors write sequences and legacy status precedence."""
from __future__ import annotations

from freezegun import freeze_time

from copilot_sdk.evolution import GraphVariantStore, VariantSpec
from copilot_sdk.evolution.graph_store import _latest_variant_specs
from copilot_sdk.graph import InMemoryGraphStore


def test_latest_sequence_can_reactivate_a_variant_at_the_same_timestamp() -> None:
    graph = InMemoryGraphStore()
    with freeze_time("2026-01-01"):
        writer = GraphVariantStore(graph, "trading")
        writer.register_variant(VariantSpec("v", "family", status="active"))
        writer.update_variant_status("v", "retired")
        writer.update_variant_status("v", "active")
    events = graph.get_evolution_events("trading", limit=None)
    assert sorted(event["metadata"]["replay_sequence"] for event in events) == [1, 2, 3]
    assert len({event["timestamp"] for event in events}) == 1
    for rows in (events, list(reversed(events))):
        assert _latest_variant_specs(rows)[0].status == "active"
    reader = GraphVariantStore(graph, "trading")
    variant = reader.get_variant("v")
    assert variant is not None and variant.status == "active"
    assert [v.id for v in reader.get_active_variants()] == ["v"]


def test_legacy_status_ties_still_use_status_rank() -> None:
    graph = InMemoryGraphStore()
    with freeze_time("2026-01-01"):
        for index, status in enumerate(("active", "retired", "active")):
            graph.write_evolution_event(
                f"legacy-{index}", "trading", "variant_registered", "family", "v",
                metadata={"spec": {"id": "v", "family": "family", "status": status}},
            )
    events = graph.get_evolution_events("trading", limit=None)
    for rows in (events, list(reversed(events))):
        assert _latest_variant_specs(rows)[0].status == "retired"
    variant = GraphVariantStore(graph, "trading").get_variant("v")
    assert variant is not None and variant.status == "retired"


def test_sequenced_status_supersedes_legacy_rank_at_the_same_timestamp() -> None:
    graph = InMemoryGraphStore()
    with freeze_time("2026-01-01"):
        graph.write_evolution_event(
            "legacy-retired", "trading", "variant_registered", "family", "v",
            metadata={"spec": {"id": "v", "family": "family", "status": "retired"}},
        )
        GraphVariantStore(graph, "trading").update_variant_status("v", "active")
    variant = GraphVariantStore(graph, "trading").get_variant("v")
    assert variant is not None and variant.status == "active"

