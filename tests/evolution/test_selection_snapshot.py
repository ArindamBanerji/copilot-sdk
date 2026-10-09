from __future__ import annotations

from unittest.mock import Mock

from copilot_sdk.evolution.graph_store import GraphVariantStore
from copilot_sdk.evolution.prompt_evolver import PromptEvolverConfig, PromptVariantEvolver
from copilot_sdk.evolution.variant_store import InMemoryVariantStore, VariantSpec


def test_selection_reads_two_streams_and_observes_new_outcomes(disposable_age, monkeypatch) -> None:
    graph = disposable_age.store("purchasing")
    other_graph = disposable_age.store("purchasing")
    durable = GraphVariantStore(graph, "purchasing")
    reference = InMemoryVariantStore()
    config = PromptEvolverConfig(default_variant_id="v2")
    evolver = PromptVariantEvolver(config, durable)
    expected = PromptVariantEvolver(config, reference)
    for index in range(6):
        spec = VariantSpec(id=f"v{index}", family="orders")
        durable.register_variant(spec)
        reference.register_variant(spec)
    # MOCK-OK: count calls while executing every read on the real AGE connection.
    reads = Mock(wraps=graph.get_evolution_events)
    monkeypatch.setattr(graph, "get_evolution_events", reads)
    try:
        for category in (None, "protein", "produce"):
            reads.reset_mock()
            assert evolver.get_variant(category=category) == expected.get_variant(category=category)
            assert reads.call_count == 2
        writer = GraphVariantStore(other_graph, "purchasing")
        for index in range(6):
            for success in (True, index == 2):
                writer.record_outcome(f"v{index}", success, category="protein")
                reference.record_outcome(f"v{index}", success, category="protein")
        for category in (None, "protein", "produce"):
            reads.reset_mock()
            assert evolver.get_variant(category=category) == expected.get_variant(category=category)
            assert reads.call_count == 2
    finally:
        graph.close()
        other_graph.close()
