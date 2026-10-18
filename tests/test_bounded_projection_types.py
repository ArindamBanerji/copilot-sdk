"""Validation and representation contracts for bounded projection types."""

from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields
from typing import Any, get_args

import pytest

from copilot_sdk.graph import query
from copilot_sdk.graph.query import (
    DecisionAggregate, DecisionChangePage, DecisionCursor, DecisionFilter,
    DecisionGenerationChanged, DecisionGroup, DecisionMetric, DecisionOrder,
    DecisionPageRequest, DecisionPageResult, DecisionProjection,
    ProjectionCardinalityExceeded,
)


def test_filter_defaults_and_empty_collections() -> None:
    value = DecisionFilter()
    collections = (
        "categories", "actions", "statuses", "sources", "regimes",
        "decision_ids", "exclude_decision_ids",
    )
    for name in collections:
        assert getattr(value, name) == ()
    for field in fields(value):
        if field.name not in collections and field.name != "exclude_legacy_signals":
            assert getattr(value, field.name) is None
    assert value.exclude_legacy_signals is False
    assert DecisionFilter(categories=(), decision_ids=()) == value
    assert "Empty tuple collection filters impose no restriction" in (value.__doc__ or "")


def test_single_field_filters() -> None:
    cases: dict[str, Any] = {
        "categories": ("cat1",), "actions": ("approve",), "statuses": ("pending",),
        "sources": ("score",), "regimes": ("normal",), "ticker": "ABC",
        "confidence_min": 0.0, "confidence_max": 1.0, "verified": True,
        "correct": False, "created_from": 1.0, "created_to": 2.0,
        "verified_from": 3.0, "verified_to": 4.0, "decision_ids": ("d1",),
        "exclude_decision_ids": ("d2",), "tenant_id": "tenant1",
        "exclude_legacy_signals": True,
    }
    for name, value in cases.items():
        assert getattr(DecisionFilter(**{name: value}), name) == value


def test_filter_combination_and_equal_confidence() -> None:
    value = DecisionFilter(categories=("cat1", "cat2"), actions=("approve",),
                           verified=True, correct=False, confidence_min=0.5,
                           confidence_max=0.5, created_from=1, created_to=2,
                           verified_from=3, verified_to=4)
    assert value.categories == ("cat1", "cat2")
    assert value.actions == ("approve",)
    assert value.verified is True and value.correct is False
    assert value.confidence_min == value.confidence_max == 0.5


def test_reversed_confidence() -> None:
    with pytest.raises(ValueError, match="confidence_min .* > confidence_max"):
        DecisionFilter(confidence_min=0.8, confidence_max=0.2)


@pytest.mark.parametrize("name", ["confidence_min", "confidence_max"])
@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_nonfinite_confidence(name: str, value: float) -> None:
    kwargs: dict[str, Any] = {name: value}
    with pytest.raises(ValueError, match=f"{name} must be finite"):
        DecisionFilter(**kwargs)


@pytest.mark.parametrize("prefix", ["created", "verified"])
@pytest.mark.parametrize("end", [1.0, 0.0])
def test_invalid_time_interval(prefix: str, end: float) -> None:
    kwargs: dict[str, Any] = {f"{prefix}_from": 1.0, f"{prefix}_to": end}
    with pytest.raises(ValueError, match=f"{prefix}_from must be strictly less"):
        DecisionFilter(**kwargs)


@pytest.mark.parametrize("order", ["created_at", "verified_at"])
def test_cursor(order: DecisionOrder) -> None:
    value = DecisionCursor(order, 0.0, "d1")
    assert (value.order_by, value.value, value.decision_id) == (order, 0.0, "d1")


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_nonfinite_cursor(value: float) -> None:
    with pytest.raises(ValueError, match="cursor value must be finite"):
        DecisionCursor("created_at", value, "d1")


def test_empty_cursor_id() -> None:
    with pytest.raises(ValueError, match="cursor decision_id must be non-empty"):
        DecisionCursor("created_at", 1.0, "")


def test_page_defaults() -> None:
    value = DecisionPageRequest()
    assert (value.limit, value.offset, value.after) == (100, 0, None)
    assert value.order_by == "created_at" and value.descending is True


def test_custom_page() -> None:
    value = DecisionPageRequest(limit=1, offset=20, order_by="verified_at", descending=False)
    assert (value.limit, value.offset, value.order_by, value.descending) == (1, 20, "verified_at", False)


@pytest.mark.parametrize("limit", [0, -1])
def test_invalid_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="limit must be >= 1"):
        DecisionPageRequest(limit=limit)


def test_negative_offset() -> None:
    with pytest.raises(ValueError, match="offset must be >= 0"):
        DecisionPageRequest(offset=-1)


def test_cursor_and_offset() -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        DecisionPageRequest(after=DecisionCursor("created_at", 1, "d1"), offset=1)


def test_cursor_order_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match"):
        DecisionPageRequest(after=DecisionCursor("verified_at", 1, "d1"))


def test_cursor_with_zero_offset() -> None:
    cursor = DecisionCursor("verified_at", 1, "d1")
    assert DecisionPageRequest(after=cursor, offset=0, order_by="verified_at").after is cursor


def test_page_result() -> None:
    cursor = DecisionCursor("created_at", 1, "d1")
    value = DecisionPageResult(({"decision_id": "d1"},), cursor, True)
    assert value.items == ({"decision_id": "d1"},)
    assert value.next_cursor is cursor and value.has_more is True


def test_empty_page_result() -> None:
    value = DecisionPageResult((), None, False)
    assert value.items == () and value.next_cursor is None and value.has_more is False


def test_aggregate() -> None:
    value = DecisionAggregate({"category": "cat1"}, {"count": 2.0, "avg_confidence": 0.5})
    assert value.dimensions == {"category": "cat1"}
    assert value.values == {"count": 2.0, "avg_confidence": 0.5}


def test_ungrouped_aggregate() -> None:
    value = DecisionAggregate({}, {"count": 0.0})
    assert value.dimensions == {} and value.values == {"count": 0.0}
    assert "avg_confidence" not in value.values


def test_change_page() -> None:
    value = DecisionChangePage(({"decision_id": "d1"},), 1, 2, True)
    assert value.events == ({"decision_id": "d1"},)
    assert (value.next_generation, value.current_generation, value.has_more) == (1, 2, True)
    empty = DecisionChangePage((), 0, 0, False)
    assert (empty.events, empty.next_generation, empty.current_generation, empty.has_more) == ((), 0, 0, False)


@pytest.mark.parametrize("name", ["next_generation", "current_generation"])
def test_negative_generation(name: str) -> None:
    kwargs: dict[str, Any] = {"events": (), "next_generation": 0, "current_generation": 0, "has_more": False}
    kwargs[name] = -1
    with pytest.raises(ValueError, match=f"{name} must be >= 0"):
        DecisionChangePage(**kwargs)


def test_generation_exception() -> None:
    error = DecisionGenerationChanged(3, 4)
    assert (error.expected, error.actual) == (3, 4)
    assert str(error) == "Domain generation changed: expected 3, actual 4"
    with pytest.raises(DecisionGenerationChanged):
        raise error


def test_cardinality_exception() -> None:
    default = ProjectionCardinalityExceeded(1001)
    assert (default.count, default.limit) == (1001, 1000)
    assert str(default) == "Aggregate produced 1001 groups, exceeding limit of 1000"
    custom = ProjectionCardinalityExceeded(11, 10)
    assert (custom.count, custom.limit) == (11, 10)
    assert str(custom) == "Aggregate produced 11 groups, exceeding limit of 10"


@pytest.mark.parametrize("value", [
    DecisionFilter(), DecisionCursor("created_at", 1, "d1"), DecisionPageRequest(),
    DecisionPageResult((), None, False), DecisionAggregate({}, {}),
    DecisionChangePage((), 0, 0, False),
])
def test_frozen_and_slots(value: Any) -> None:
    assert not hasattr(value, "__dict__")
    name = fields(value)[0].name
    with pytest.raises(FrozenInstanceError):
        setattr(value, name, getattr(value, name))


def test_literal_aliases() -> None:
    assert get_args(DecisionOrder) == ("created_at", "verified_at")
    assert get_args(DecisionProjection) == ("summary", "scoring", "journal", "full")
    assert get_args(DecisionGroup) == ("category", "action", "status", "regime")
    assert get_args(DecisionMetric) == ("count", "correct_count", "avg_confidence")


def test_query_import_isolation() -> None:
    tree = ast.parse(inspect.getsource(query))
    modules: list[str | None] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module)
    assert set(modules) == {"__future__", "math", "dataclasses", "typing"}
