from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest


_SCRIPT = Path(__file__).parents[1] / "scripts" / "backfill_d_correct.py"
_SPEC = importlib.util.spec_from_file_location("backfill_d_correct", _SCRIPT)
assert _SPEC and _SPEC.loader
backfill = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(backfill)


class _Rows:
    def __init__(self, value: int) -> None:
        self.value = value

    def fetchall(self) -> list[tuple[int]]:
        return [(self.value,)]


class RecordingConnection:
    """Stateful connection double that records the generated AGE SQL."""

    def __init__(self, *, unclassifiable: int = 0, backfilled: int = 0, pending: int = 0) -> None:
        self.unclassifiable = unclassifiable
        self.backfilled = backfilled
        self.pending = pending
        self.calls: list[str] = []

    def execute(self, sql: str) -> _Rows:
        self.calls.append(sql)
        if "unclassifiable agtype" in sql:
            return _Rows(self.unclassifiable)
        if "backfilled agtype" in sql:
            return _Rows(self.backfilled)
        if "pending agtype" in sql:
            return _Rows(self.pending)
        raise AssertionError(f"unexpected SQL: {sql}")


def test_backfill_query_has_explicit_true_and_false_cases() -> None:
    query = backfill._backfill_query("trading")

    assert "o.is_correct = false THEN false" in query
    assert "o.is_correct = 0 THEN false" in query
    assert "o.is_correct = 'false' THEN false" in query
    assert "ELSE false" not in query


def test_dry_run_reports_unclassifiable_values() -> None:
    connection = RecordingConnection(unclassifiable=2, pending=5)

    report = backfill.run_backfill(connection, "soc_graph", domains=("trading",))

    assert report == {"trading_unclassifiable": 2, "trading": 5}
    assert all("SET d.correct" not in call for call in connection.calls)


def test_apply_refuses_unclassifiable_values_before_mutation() -> None:
    connection = RecordingConnection(unclassifiable=1, backfilled=4)

    with pytest.raises(ValueError, match="Found 1 decisions with unclassifiable"):
        backfill.run_backfill(connection, "soc_graph", apply=True, domains=("trading",))

    assert len(connection.calls) == 1
    assert all("SET d.correct" not in call for call in connection.calls)


def test_force_apply_leaves_unclassifiable_values_null() -> None:
    connection = RecordingConnection(unclassifiable=1, backfilled=4)

    report = backfill.run_backfill(
        connection,
        "soc_graph",
        apply=True,
        force=True,
        domains=("trading",),
    )

    assert report == {"trading_unclassifiable": 1, "trading": 4}
    assert len(connection.calls) == 2
    assert "SET d.correct" in connection.calls[1]
    assert "ELSE false" not in connection.calls[1]
    assert "d.correct IS NULL" in connection.calls[1]
