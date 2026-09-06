"""Evolution inventory should not issue one history query per variant."""
from pathlib import Path

from copilot_sdk.evolution.graph_store import GraphVariantStore
from copilot_sdk.evolution.prompt_evolver import PromptVariantEvolver
from copilot_sdk.evolution.variant_store import InMemoryVariantStore, VariantSpec
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


def test_summary_uses_two_fresh_stream_reads(tmp_path: Path) -> None:
    graph = SQLiteGraphStore(tmp_path / "summary.db")
    writer_graph = SQLiteGraphStore(tmp_path / "summary.db")
    durable = GraphVariantStore(graph, "purchasing")
    writer = GraphVariantStore(writer_graph, "purchasing")
    reference = InMemoryVariantStore()
    for index in range(12):
        spec = VariantSpec(id=f"v{index}", family="orders", status="active" if index < 6 else "shadow")
        durable.register_variant(spec)
        reference.register_variant(spec)
    actual, expected = PromptVariantEvolver(store=durable), PromptVariantEvolver(store=reference)
    statements: list[str] = []
    graph.connection.set_trace_callback(statements.append)
    try:
        for success in (True, False):
            writer.record_outcome("v1", success, category="protein")
            reference.record_outcome("v1", success, category="protein")
            statements.clear()
            assert actual.get_summary() == expected.get_summary()
            queries = [sql for sql in statements if "SELECT" in sql.upper() and "evolution_events" in sql]
            assert len(queries) == 2, queries
    finally:
        graph.connection.set_trace_callback(None)
        graph.close()
        writer_graph.close()
