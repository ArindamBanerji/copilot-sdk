"""Evolution inventory should not issue one history query per variant."""
from unittest.mock import Mock

from copilot_sdk.evolution.graph_store import GraphVariantStore
from copilot_sdk.evolution.prompt_evolver import PromptVariantEvolver
from copilot_sdk.evolution.variant_store import InMemoryVariantStore, VariantSpec


def test_summary_uses_two_fresh_stream_reads(disposable_age, monkeypatch) -> None:
    graph = disposable_age.store("purchasing")
    writer_graph = disposable_age.store("purchasing")
    durable = GraphVariantStore(graph, "purchasing")
    writer = GraphVariantStore(writer_graph, "purchasing")
    reference = InMemoryVariantStore()
    for index in range(12):
        spec = VariantSpec(id=f"v{index}", family="orders", status="active" if index < 6 else "shadow")
        durable.register_variant(spec)
        reference.register_variant(spec)
    actual, expected = PromptVariantEvolver(store=durable), PromptVariantEvolver(store=reference)
    # MOCK-OK: count calls while executing every read on the real AGE connection.
    reads = Mock(wraps=graph.get_evolution_events)
    monkeypatch.setattr(graph, "get_evolution_events", reads)
    try:
        for success in (True, False):
            writer.record_outcome("v1", success, category="protein")
            reference.record_outcome("v1", success, category="protein")
            reads.reset_mock()
            assert actual.get_summary() == expected.get_summary()
            assert reads.call_count == 2
    finally:
        graph.close()
        writer_graph.close()
