from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path

import pytest

from copilot_sdk.graph import GraphStore, InMemoryGraphStore, L5LearningStore, ProtocolV2GraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


BASE_STATE = {
    "domain": "s2p",
    "status": "GREEN",
    "alpha": 0.25,
    "q": 0.8,
    "V": 42,
    "theta_min": 23.53,
    "product": 18.824,
    "categories_total": 6,
    "categories_with_data": 4,
    "baseline_product": 20.0,
    "relative_threshold": 0.9412,
    "complacency_flag": "false",
    "caused_by_decision_id": "DEC-1",
    "old_status": "AMBER",
}

PUBLIC_KEYS = {
    "id",
    "domain",
    "status",
    "alpha",
    "q",
    "V",
    "theta_min",
    "product",
    "categories_total",
    "categories_with_data",
    "baseline_product",
    "relative_threshold",
    "complacency_flag",
    "caused_by_decision_id",
    "old_status",
    "updated_at",
}


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    if request.param == "memory":
        yield InMemoryGraphStore()
    else:
        sqlite_store = SQLiteGraphStore(tmp_path / "graph.sqlite")
        try:
            yield sqlite_store
        finally:
            sqlite_store.close()


def _write(store, **overrides):
    payload = {**BASE_STATE, **overrides}
    return store.update_conservation_state(**payload)


def test_protocol_boundary_and_signature() -> None:
    assert not hasattr(GraphStore, "update_conservation_state")
    assert not hasattr(GraphStore, "get_conservation_state")
    assert not hasattr(ProtocolV2GraphStore, "update_conservation_state")
    assert not hasattr(ProtocolV2GraphStore, "get_conservation_state")
    assert hasattr(L5LearningStore, "update_conservation_state")
    assert hasattr(L5LearningStore, "get_conservation_state")
    assert list(inspect.signature(L5LearningStore.update_conservation_state).parameters) == [
        "self",
        "domain",
        "status",
        "alpha",
        "q",
        "V",
        "theta_min",
        "product",
        "categories_total",
        "categories_with_data",
        "baseline_product",
        "relative_threshold",
        "complacency_flag",
        "caused_by_decision_id",
        "old_status",
    ]
    assert inspect.signature(L5LearningStore.update_conservation_state).return_annotation == "str"
    assert list(inspect.signature(L5LearningStore.get_conservation_state).parameters) == [
        "self",
        "domain",
    ]


def test_stores_have_concrete_methods() -> None:
    assert callable(SQLiteGraphStore.update_conservation_state)
    assert callable(SQLiteGraphStore.get_conservation_state)
    assert callable(InMemoryGraphStore.update_conservation_state)
    assert callable(InMemoryGraphStore.get_conservation_state)


def test_basic_write_get_roundtrips_all_fields(store) -> None:
    state_id = _write(store)

    row = store.get_conservation_state("s2p")

    assert isinstance(state_id, str)
    assert row is not None
    assert set(row) == PUBLIC_KEYS
    assert row["id"] == state_id
    for key, value in BASE_STATE.items():
        assert row[key] == value
    datetime.fromisoformat(str(row["updated_at"]).replace("Z", "+00:00"))


def test_upsert_updates_current_domain_without_sqlite_duplicates(store) -> None:
    first_id = _write(store)
    second_id = _write(
        store,
        status="RED",
        alpha=0.9,
        q=0.1,
        product=9.0,
        complacency_flag="true",
        old_status="GREEN",
    )

    row = store.get_conservation_state("s2p")

    assert row is not None
    assert second_id == first_id
    assert row["status"] == "RED"
    assert row["alpha"] == 0.9
    assert row["q"] == 0.1
    assert row["product"] == 9.0
    assert row["complacency_flag"] == "true"
    assert row["old_status"] == "GREEN"
    if isinstance(store, SQLiteGraphStore):
        count = store.connection.execute(
            "SELECT COUNT(*) AS n FROM l5_conservation_state WHERE domain = ?",
            ("s2p",),
        ).fetchone()["n"]
        assert count == 1


def test_unknown_domain_returns_none(store) -> None:
    assert store.get_conservation_state("missing") is None


def test_domain_isolation_and_reset_no_overdelete(store) -> None:
    _write(store, domain="s2p", status="GREEN")
    _write(store, domain="trading", status="AMBER", old_status=None)

    store.domain_scoped_reset("s2p")

    assert store.get_conservation_state("s2p") is None
    assert store.get_conservation_state("trading") is not None


def test_inmemory_get_returns_copy_safe_dict() -> None:
    store = InMemoryGraphStore()
    _write(store)

    row = store.get_conservation_state("s2p")
    assert row is not None
    row["status"] = "RED"

    assert store.get_conservation_state("s2p")["status"] == "GREEN"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("domain", ""),
        ("status", "BLUE"),
        ("alpha", -0.01),
        ("alpha", 1.01),
        ("q", -0.01),
        ("q", 1.01),
        ("V", -1),
        ("theta_min", 0.0),
        ("categories_total", -1),
        ("categories_with_data", -1),
        ("categories_with_data", 7),
        ("complacency_flag", "TRUE"),
        ("complacency_flag", True),
        ("old_status", "BLUE"),
    ],
)
def test_validation_rejects_bad_values(store, field, value) -> None:
    with pytest.raises((TypeError, ValueError)):
        _write(store, **{field: value})


@pytest.mark.parametrize(
    "field",
    ["product", "baseline_product", "relative_threshold"],
)
def test_numeric_fields_reject_non_numeric_values(store, field) -> None:
    with pytest.raises((TypeError, ValueError)):
        _write(store, **{field: "not-numeric"})


def test_formula_inputs_are_stored_exactly_without_recomputation(store) -> None:
    _write(
        store,
        theta_min=12.345,
        product=67.89,
        baseline_product=101.112,
        relative_threshold=0.333,
    )

    row = store.get_conservation_state("s2p")

    assert row is not None
    assert row["theta_min"] == 12.345
    assert row["product"] == 67.89
    assert row["baseline_product"] == 101.112
    assert row["relative_threshold"] == 0.333


def test_no_formula_or_runtime_imports_in_l5_conservation_storage() -> None:
    root = Path(__file__).resolve().parents[1]
    for relative in ["copilot_sdk/graph/sqlite_store.py", "copilot_sdk/graph/memory_store.py"]:
        source = (root / relative).read_text(encoding="utf-8")
        assert "derive_theta_min" not in source
        assert "ConservationStateMachine" not in source
