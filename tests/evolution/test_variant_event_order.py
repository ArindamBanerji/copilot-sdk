from datetime import datetime
from pathlib import Path

from copilot_sdk.evolution.graph_store import GraphVariantStore, _latest_variant_specs
from copilot_sdk.evolution.variant_store import VariantSpec
from copilot_sdk.graph.memory_store import InMemoryGraphStore


def test_latest_variant_status_is_independent_of_adapter_order(tmp_path: Path) -> None:
    graph = InMemoryGraphStore()
    variants = GraphVariantStore(graph, "purchasing")
    try:
        variants.register_variant(VariantSpec(id="candidate", family="orders", status="shadow"))
        variants.update_variant_status("candidate", "active")
        variants.update_variant_status("candidate", "retired")
        events = graph.get_evolution_events("purchasing", event_type="variant_registered", limit=100)
        assert len(events) == 3
        # AGE exposes event timestamps as ISO strings; the reducer also accepts
        # legacy epoch values. No store method is replaced.
        assert all(isinstance(event["timestamp"], str) for event in events)
        epoch_events = [
            {
                **event,
                "timestamp": datetime.fromisoformat(
                    event["timestamp"].replace("Z", "+00:00")
                ).timestamp(),
            }
            for event in events
        ]
        for rows in (events, list(reversed(events)), epoch_events, list(reversed(epoch_events))):
            specs = _latest_variant_specs(rows)
            assert len(specs) == 1
            assert specs[0].status == "retired"
        assert variants.get_active_variants() == []
    finally:
        graph.close()
