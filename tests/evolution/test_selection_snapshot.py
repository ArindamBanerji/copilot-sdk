from __future__ import annotations

from pathlib import Path

from copilot_sdk.evolution.graph_store import GraphVariantStore
from copilot_sdk.evolution.prompt_evolver import PromptEvolverConfig, PromptVariantEvolver
from copilot_sdk.evolution.variant_store import InMemoryVariantStore, VariantSpec
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


def test_selection_reads_two_streams_and_observes_new_outcomes(tmp_path: Path) -> None:
    graph = SQLiteGraphStore(tmp_path / "variants.db")
    other_graph = SQLiteGraphStore(tmp_path / "variants.db")
    durable = GraphVariantStore(graph, "purchasing")
    reference = InMemoryVariantStore()
    config = PromptEvolverConfig(default_variant_id="v2")
    evolver = PromptVariantEvolver(config, durable)
    expected = PromptVariantEvolver(config, reference)
    for index in range(6):
        spec = VariantSpec(id=f"v{index}", family="orders")
        durable.register_variant(spec)
        reference.register_variant(spec)
    statements: list[str] = []
    graph.connection.set_trace_callback(statements.append)
    try:
        for category in (None, "protein", "produce"):
            statements.clear()
            assert evolver.get_variant(category=category) == expected.get_variant(category=category)
            reads = [sql for sql in statements if "SELECT" in sql.upper() and "evolution_events" in sql]
            assert len(reads) == 2, reads
        writer = GraphVariantStore(other_graph, "purchasing")
        for index in range(6):
            for success in (True, index == 2):
                writer.record_outcome(f"v{index}", success, category="protein")
                reference.record_outcome(f"v{index}", success, category="protein")
        for category in (None, "protein", "produce"):
            statements.clear()
            assert evolver.get_variant(category=category) == expected.get_variant(category=category)
            assert len([sql for sql in statements if "SELECT" in sql.upper() and "evolution_events" in sql]) == 2
    finally:
        graph.connection.set_trace_callback(None)
        graph.close()
        other_graph.close()
