"""Replay ordering survives coarse clocks and legacy event payloads."""
from __future__ import annotations

from freezegun import freeze_time

from copilot_sdk.evolution import GraphVariantStore, VariantSpec
from copilot_sdk.graph import InMemoryGraphStore


def test_post_reset_outcomes_survive_equal_timestamps_and_reopen() -> None:
    graph = InMemoryGraphStore()
    with freeze_time("2026-01-01"):
        writer = GraphVariantStore(graph, "trading")
        writer.register_variant(VariantSpec("v", "family"))
        writer.record_outcome("v", False)
        for success in (True, False):
            writer.reset()
            writer = GraphVariantStore(graph, "trading")
            writer.register_variant(VariantSpec("v", "family"))
            writer.record_outcome("v", success)
            reader = GraphVariantStore(graph, "trading")
            stats = reader.get_global_stats("v")
            assert (stats.total, stats.successes, stats.failures) == (
                1, int(success), int(not success),
            )
            assert reader.get_variant("v") is not None


def _write_legacy_events(graph: InMemoryGraphStore) -> None:
    graph.write_evolution_event(
        "legacy-register", "trading", "variant_registered", "family", "v",
        metadata={"spec": {"id": "v", "family": "family"}},
    )
    graph.write_evolution_event(
        "legacy-outcome", "trading", "variant_outcome", "variant", "v",
        metadata={"success": False, "category": "trend"},
    )


def test_legacy_events_without_replay_sequence_still_replay() -> None:
    graph = InMemoryGraphStore()
    with freeze_time("2026-01-01"):
        _write_legacy_events(graph)
    reader = GraphVariantStore(graph, "trading")
    assert reader.get_variant("v") is not None
    stats = reader.get_global_stats("v")
    assert (stats.total, stats.failures) == (1, 1)
    assert reader.get_category_stats("trend", "v").failures == 1


def test_new_reset_excludes_legacy_outcomes_with_the_same_timestamp() -> None:
    graph = InMemoryGraphStore()
    with freeze_time("2026-01-01"):
        _write_legacy_events(graph)
        writer = GraphVariantStore(graph, "trading")
        writer.reset()
        writer.register_variant(VariantSpec("v", "family"))
        writer.record_outcome("v", True, "trend")
    reader = GraphVariantStore(graph, "trading")
    stats = reader.get_global_stats("v")
    assert (stats.total, stats.successes, stats.failures) == (1, 1, 0)
    assert reader.get_category_stats("trend", "v").successes == 1

