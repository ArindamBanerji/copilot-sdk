from __future__ import annotations

from copilot_sdk.evolution import EvolutionStore, VariantSelector
from copilot_sdk.graph import GraphStore, InMemoryGraphStore, SQLiteGraphStore


class SampleVariantSelector:
    def select(self, category, variants, context=None):
        return variants[0]

    def update(self, variant_id, category, reward):
        return None


def test_evolution_store_protocol_importable():
    assert EvolutionStore


def test_variant_selector_protocol_importable_and_runtime_checkable():
    assert isinstance(SampleVariantSelector(), VariantSelector)


def test_evolution_store_is_separate_from_graph_store_protocol():
    assert not hasattr(GraphStore, "save_evolution_event")
    assert not hasattr(GraphStore, "get_evolution_events")
    assert hasattr(EvolutionStore, "save_evolution_event")
    assert hasattr(EvolutionStore, "get_evolution_events")


def test_inmemory_graph_store_structurally_satisfies_evolution_store():
    assert isinstance(InMemoryGraphStore(), EvolutionStore)


def test_sqlite_graph_store_structurally_satisfies_evolution_store(tmp_path):
    assert isinstance(SQLiteGraphStore(tmp_path / "graph.sqlite"), EvolutionStore)
