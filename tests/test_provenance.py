from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from copilot_sdk.evidence.provenance import Provenanced


def test_construction_retains_all_fields() -> None:
    item = Provenanced(
        value={"score": 0.9},
        source="graph_store",
        label="Observed score",
        as_of="2026-09-29T12:00:00Z",
    )
    assert item.value == {"score": 0.9}
    assert item.source == "graph_store"
    assert item.label == "Observed score"
    assert item.as_of == "2026-09-29T12:00:00Z"


def test_frozen_instances_are_immutable() -> None:
    item = Provenanced(value=1, source="learned")
    with pytest.raises(FrozenInstanceError):
        item.value = 2


def test_generic_values_retain_runtime_types() -> None:
    number: Provenanced[int] = Provenanced(7, "computed")
    text: Provenanced[str] = Provenanced("ready", "live_api")
    values: Provenanced[list[int]] = Provenanced([1, 2], "fixture")
    assert isinstance(number.value, int)
    assert isinstance(text.value, str)
    assert values.value == [1, 2]


def test_optional_fields_default_to_none() -> None:
    item = Provenanced(value=False, source="live")
    assert item.label is None
    assert item.as_of is None


@pytest.mark.parametrize("source", ["learned", "graph_store", "fixture", "live_api", "vendor_feed"])
def test_source_accepts_any_string(source: str) -> None:
    assert Provenanced(value=1, source=source).source == source
