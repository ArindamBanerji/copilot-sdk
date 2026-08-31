"""Contract tests for the domain-scoped GraphStore state extension."""

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore


@pytest.mark.parametrize(
    ("save", "get", "list_name", "delete"),
    [
        ("save_evolution", "get_evolution", "list_evolutions", "delete_evolution"),
        ("save_posterior", "get_posterior", "list_posteriors", "delete_posterior"),
        ("save_promotion", "get_promotion", "list_promotions", "delete_promotion"),
        ("save_ledger", "get_ledger", "list_ledgers", "delete_ledger"),
        ("save_governance", "get_governance", "list_governance", "delete_governance"),
    ],
)
def test_domain_scoped_state_round_trip(save: str, get: str, list_name: str, delete: str) -> None:
    store = InMemoryGraphStore(domain="soc")
    state = {"generation": 3, "fitness": 0.91}

    getattr(store, save)("soc", "record-1", state)

    assert getattr(store, get)("soc", "record-1") == state
    assert getattr(store, get)("trading", "record-1") is None
    assert getattr(store, list_name)("soc") == [{"key": "record-1", **state}]

    getattr(store, delete)("soc", "record-1")
    assert getattr(store, get)("soc", "record-1") is None


def test_domain_scoped_state_rejects_blank_identity() -> None:
    store = InMemoryGraphStore(domain="soc")
    with pytest.raises(ValueError):
        store.save_evolution("", "record-1", {})
    with pytest.raises(ValueError):
        store.save_evolution("soc", "", {})
