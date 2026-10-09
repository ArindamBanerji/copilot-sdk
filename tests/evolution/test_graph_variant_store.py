"""Variant persistence contracts using the injected graph backend."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import pytest
from copilot_sdk.graph import InMemoryGraphStore

from copilot_sdk.evolution import (
    InMemoryVariantStore,
    PromptEvolverConfig,
    PromptVariantEvolver,
    GraphVariantStore,
    VariantSpec,
)


@pytest.fixture
def graph() -> InMemoryGraphStore:
    return InMemoryGraphStore()


def _spec(variant_id: str = "variant-a") -> VariantSpec:
    return VariantSpec(
        id=variant_id,
        family="family-a",
        version=1,
        template="prompt",
        metadata={"owner": "test"},
    )


def test_graph_store_register_and_retrieve(graph: InMemoryGraphStore) -> None:
    store = GraphVariantStore(graph, "test")
    store.register_variant(_spec())

    loaded = store.get_variant("variant-a")

    assert loaded is not None
    assert loaded.family == "family-a"
    assert loaded.metadata == {"owner": "test"}
    assert store.get_all_variants()[0].id == "variant-a"
    store.close()


def test_graph_store_update_stats(graph: InMemoryGraphStore) -> None:
    store = GraphVariantStore(graph, "test")
    store.register_variant(_spec())
    store.record_outcome("variant-a", True, category="soc")
    store.record_outcome("variant-a", False, category="soc")

    global_stats = store.get_global_stats("variant-a")
    category_stats = store.get_category_stats("soc", "variant-a")

    assert (global_stats.total, global_stats.successes, global_stats.failures) == (2, 1, 1)
    assert (category_stats.total, category_stats.successes, category_stats.failures) == (2, 1, 1)
    store.close()


def test_graph_store_survives_reconnect(graph: InMemoryGraphStore) -> None:
    first = GraphVariantStore(graph, "test")
    first.register_variant(_spec())
    first.record_outcome("variant-a", True)
    first.close()

    second = GraphVariantStore(graph, "test")

    assert second.get_global_stats("variant-a").successes == 1
    assert second.get_variant("variant-a") is not None
    second.close()


def test_graph_store_idempotent_register_preserves_stats(graph: InMemoryGraphStore) -> None:
    store = GraphVariantStore(graph, "test")
    store.register_variant(_spec())
    store.record_outcome("variant-a", True)
    store.register_variant(VariantSpec(id="variant-a", family="family-a", status="shadow"))

    assert len(store.get_all_variants()) == 1
    assert store.get_global_stats("variant-a").total == 1
    # Existing persisted lifecycle status is not reset by boot registration.
    loaded = store.get_variant("variant-a")
    assert loaded is not None
    assert loaded.status == "active"
    store.close()


def test_graph_store_domain_isolation(graph: InMemoryGraphStore) -> None:
    soc = GraphVariantStore(graph, "soc")
    trading = GraphVariantStore(graph, "trading")
    soc.register_variant(_spec())
    soc.record_outcome("variant-a", True)

    assert trading.get_variant("variant-a") is None
    assert trading.get_global_stats("variant-a").total == 0
    soc.close()
    trading.close()


def test_graph_store_concurrent_writes(graph: InMemoryGraphStore) -> None:
    store = GraphVariantStore(graph, "test")
    store.register_variant(_spec())

    def write_outcome(index: int) -> None:
        store.record_outcome("variant-a", index % 2 == 0)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(write_outcome, range(100)))

    stats = store.get_global_stats("variant-a")
    assert stats.total == 100
    assert stats.successes == 50
    assert stats.failures == 50
    store.close()


def test_graph_store_empty_start(graph: InMemoryGraphStore) -> None:
    store = GraphVariantStore(graph, "test")

    assert store.get_all_variants() == []
    assert store.get_global_stats("missing").total == 0
    store.close()


def test_evolver_with_graph_store_survives_restart(graph: InMemoryGraphStore) -> None:
    first = PromptVariantEvolver(store=GraphVariantStore(graph, "test"))
    first.register_variants([_spec()])
    first.record_outcome("variant-a", True)
    first.store.close()

    second = PromptVariantEvolver(store=GraphVariantStore(graph, "test"))

    assert second.store.get_global_stats("variant-a").successes == 1
    assert second.get_summary()["variants"][0]["total"] == 1
    second.store.close()


def test_in_memory_store_and_default_evolver_still_work() -> None:
    evolver = PromptVariantEvolver(config=PromptEvolverConfig(default_variant_id="variant-a"))
    assert isinstance(evolver.store, InMemoryVariantStore)
    evolver.register_variants([_spec()])
    evolver.record_outcome("variant-a", True)
    assert evolver.store.get_global_stats("variant-a").success_rate == 1.0

