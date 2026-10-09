from __future__ import annotations

import inspect
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.graph import InMemoryGraphStore
from tests.graph_store_test_helpers import make_memory_store
from copilot_sdk.graph.protocol import L5LearningStore


def _welford_state(n_all: int = 4) -> dict[str, object]:
    return {
        "confirmed_mean": [0.1, 0.2, 0.3],
        "confirmed_m2": [1.0, 1.1, 1.2],
        "overridden_mean": [0.4, 0.5, 0.6],
        "overridden_m2": [2.0, 2.1, 2.2],
        "all_mean": [0.7, 0.8, 0.9],
        "all_m2": [3.0, 3.1, 3.2],
        "n_all": n_all,
    }


@pytest.fixture(params=["memory"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Any:
    if request.param == "memory":
        return InMemoryGraphStore()
    return make_memory_store(tmp_path / "l5-dk-welford.sqlite")


def test_update_dk_weights_accepts_old_positional_signature(store: Any) -> None:
    store.update_dk_weights("s2p", [[1.0, 2.0]], 3, 12.5)

    row = store.get_dk_weights("s2p")
    assert row is not None
    assert row["weight_json"] == [[1.0, 2.0]]
    assert row["n_decisions_used"] == 3
    assert row["welford_state"] is None
    assert row["n_confirmed"] is None
    assert row["n_overridden"] is None
    assert row["entity_group"] is None


def test_dk_weights_welford_roundtrip_sqlite_and_memory(store: Any) -> None:
    state = _welford_state(n_all=4)

    store.update_dk_weights(
        "s2p",
        [[0.1, 0.2], [0.3, 0.4]],
        4,
        99.5,
        welford_state=state,
        n_confirmed=3,
        n_overridden=1,
        entity_group="supplier",
    )

    row = store.get_dk_weights("s2p")
    assert row is not None
    assert row["welford_state"] == state
    assert row["n_confirmed"] == 3
    assert row["n_overridden"] == 1
    assert row["entity_group"] == "supplier"


def test_dk_weights_welford_copy_safety(store: Any) -> None:
    state = _welford_state(n_all=2)
    store.update_dk_weights("s2p", [[1.0]], 2, 10.0, welford_state=state)
    original_confirmed_mean = state["confirmed_mean"]
    assert isinstance(original_confirmed_mean, list)
    original_confirmed_mean.append(99.0)

    first = store.get_dk_weights("s2p")
    assert first is not None
    first_state = first["welford_state"]
    assert isinstance(first_state, dict)
    confirmed_mean = first_state["confirmed_mean"]
    assert isinstance(confirmed_mean, list)
    confirmed_mean.append(42.0)

    second = store.get_dk_weights("s2p")
    assert second is not None
    assert second["welford_state"] == _welford_state(n_all=2)


def test_dk_weights_welford_partial_state_rejected(store: Any) -> None:
    state = _welford_state(n_all=1)
    del state["all_m2"]

    with pytest.raises((TypeError, ValueError)):
        store.update_dk_weights("s2p", [[1.0]], 1, 1.0, welford_state=state)


@pytest.mark.parametrize(
    "bad_state",
    [
        {**_welford_state(n_all=1), "all_m2": [1.0, 2.0]},
        {**_welford_state(n_all=1), "all_m2": ["bad"]},
        {**_welford_state(n_all=2), "n_all": 3},
    ],
)
def test_dk_weights_welford_vector_dimension_validation(
    store: Any,
    bad_state: dict[str, object],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        store.update_dk_weights("s2p", [[1.0]], 2, 1.0, welford_state=bad_state)






def test_l5_learning_store_signature_backward_compatible() -> None:
    signature = inspect.signature(L5LearningStore.update_dk_weights)
    params = signature.parameters
    assert list(params) == [
        "self",
        "domain",
        "weight_tensor",
        "n_decisions_used",
        "computed_at",
        "welford_state",
        "n_confirmed",
        "n_overridden",
        "entity_group",
    ]
    assert params["computed_at"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    for name in ["welford_state", "n_confirmed", "n_overridden", "entity_group"]:
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY


