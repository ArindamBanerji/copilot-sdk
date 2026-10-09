from __future__ import annotations

import pytest

from copilot_sdk.backend.response_materializer import ResponseMaterializer


class Store:
    def __init__(self) -> None:
        self.value = 1
        self.reads = 0

    def get_all_decisions(self, domain: str):
        self.reads += 1
        return [{"value": self.value}]

    def get_verified_decisions(self, domain: str):
        return []


def test_each_read_uses_fresh_graph_rows() -> None:
    store = Store()
    materializer = ResponseMaterializer(
        "test", lambda: store, {"data": lambda shared: shared["decisions"]}
    )
    assert materializer.get("data") == [{"value": 1}]
    store.value = 2
    assert materializer.get("data") == [{"value": 2}]
    assert store.reads == 2


def test_each_read_returns_an_independent_payload() -> None:
    store = Store()
    materializer = ResponseMaterializer(
        "test", lambda: store, {"data": lambda shared: shared["decisions"]}
    )
    first = materializer.get("data")
    assert isinstance(first, list)
    first[0]["value"] = 99
    assert materializer.get("data") == [{"value": 1}]


def test_refresh_and_invalidate_are_compatibility_noops() -> None:
    store = Store()
    materializer = ResponseMaterializer(
        "test", lambda: store, {"data": lambda shared: shared["decisions"]}
    )
    materializer.refresh()
    materializer.invalidate()
    assert store.reads == 0
    assert materializer.get_or_refresh("data") == [{"value": 1}]


@pytest.mark.parametrize("payload", [{}, [], 0, False])
def test_falsey_payloads_are_returned_fresh(payload) -> None:
    store = Store()
    materializer = ResponseMaterializer("test", lambda: store, {"data": lambda shared: payload})
    assert materializer.get("data") == payload
    assert materializer.get("data") == payload
    assert store.reads == 2


def test_unknown_key_does_not_read_store() -> None:
    store = Store()
    materializer = ResponseMaterializer("test", lambda: store, {})
    assert materializer.get("unknown") is None
    assert store.reads == 0


def test_source_failure_propagates() -> None:
    def unavailable():
        raise ValueError("source offline")

    materializer = ResponseMaterializer("test", unavailable, {"data": lambda shared: shared})
    with pytest.raises(ValueError, match="source offline"):
        materializer.get("data")
