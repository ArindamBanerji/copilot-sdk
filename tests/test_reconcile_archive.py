from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from ci_platform.graph.age_client import AGEClient

from copilot_sdk.migrate.reconcile_archive import ArchiveReconciler


def _reconciler(tmp_path: Path, source_ids: list[str], age_states: dict[str, bool | None], environment: Any) -> ArchiveReconciler:
    from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
    source = SQLiteGraphStore(tmp_path / "trading.db", domain="trading")
    for decision_id in source_ids:
        source.write_decision("trading", "risk", "buy", 0.8, {"x": 0.5}, metadata={"decision_id": decision_id, "created_at": 1.0})
    source.archive_decisions("trading", before=1e20)
    age = environment.store("trading")
    for decision_id, archived in age_states.items():
        age.write_decision("trading", "risk", "buy", 0.8, {"x": 0.5}, metadata={"decision_id": decision_id})
        if archived is not None:
            age._store._run_query(f"MATCH (d:Decision {{decision_id: {AGEClient.serialize_for_age(decision_id)}}}) SET d.archived = {str(archived).lower()} RETURN d")
    return ArchiveReconciler(source, age, "trading")


def _states(age: Any) -> dict[str, Any]:
    return {row["id"]: row["archived"] for row in age._store._run_query("MATCH (d:Decision) RETURN d.decision_id AS id, d.archived AS archived")}


@pytest.mark.age
def test_reconcile_marks_active_age_decisions_archived(tmp_path: Path, disposable_age: Any) -> None:
    reconciler = _reconciler(tmp_path, ["d1", "d2", "d3"], {"d1": None, "d2": False, "d3": None}, disposable_age)

    report = reconciler.reconcile()

    assert report["status"] == "PASS"
    assert report["reconciled"] == 3
    assert _states(reconciler.age_store) == {"d1": True, "d2": True, "d3": True}


@pytest.mark.age
def test_reconcile_counts_existing_age_archives(tmp_path: Path, disposable_age: Any) -> None:
    reconciler = _reconciler(tmp_path, ["d1", "d2", "d3"], {"d1": True, "d2": True, "d3": True}, disposable_age)

    report = reconciler.reconcile()

    assert report["reconciled"] == 0
    assert report["already_archived"] == 3


@pytest.mark.age
def test_reconcile_mixed_active_and_existing_archive_states(tmp_path: Path, disposable_age: Any) -> None:
    reconciler = _reconciler(
        tmp_path, ["d1", "d2", "d3", "d4", "d5"], {"d1": None, "d2": False, "d3": None, "d4": True, "d5": True}
    , disposable_age)

    report = reconciler.reconcile()

    assert report["reconciled"] == 3
    assert report["already_archived"] == 2


@pytest.mark.age
def test_reconcile_reports_sqlite_ids_missing_from_age(tmp_path: Path, disposable_age: Any) -> None:
    reconciler = _reconciler(tmp_path, ["present", "missing"], {"present": None}, disposable_age)

    report = reconciler.reconcile()

    assert report["status"] == "FAIL"
    assert report["reconciled"] == 1
    assert report["not_found_in_age"] == 1


@pytest.mark.age
def test_dry_run_leaves_age_unchanged(tmp_path: Path, disposable_age: Any) -> None:
    reconciler = _reconciler(tmp_path, ["d1", "d2"], {"d1": None, "d2": False}, disposable_age)

    report = reconciler.reconcile(dry_run=True)

    assert report["reconciled"] == 2
    assert _states(reconciler.age_store) == {"d1": None, "d2": False}
    assert not reconciler.checkpoint_file.exists()


@pytest.mark.age
def test_checkpoint_resume_completes_remaining_batches(tmp_path: Path, disposable_age: Any, monkeypatch: Any) -> None:
    reconciler = _reconciler(tmp_path, [f"d{index}" for index in range(5)], {f"d{index}": None for index in range(5)}, disposable_age)
    age = reconciler.age_store._store
    original = age._run_query
    updates = 0
    def interrupted(query):
        nonlocal updates
        if "SET d.archived = true" in query:
            updates += 1
            if updates == 2:
                raise RuntimeError("interrupted")
        return original(query)
    monkeypatch.setattr(age, "_run_query", interrupted)

    with pytest.raises(RuntimeError, match="interrupted"):
        reconciler.reconcile(batch_size=2)
    checkpoint = json.loads(reconciler.checkpoint_file.read_text(encoding="utf-8"))
    assert checkpoint["processed_ids"] == ["d0", "d1"]

    monkeypatch.setattr(age, "_run_query", original)
    report = reconciler.reconcile(batch_size=2)

    checkpoint = json.loads(reconciler.checkpoint_file.read_text(encoding="utf-8"))
    assert report["reconciled"] == 5
    assert checkpoint["status"] == "complete"
    assert checkpoint["processed_ids"] == ["d0", "d1", "d2", "d3", "d4"]


@pytest.mark.age
def test_reconcile_is_idempotent(tmp_path: Path, disposable_age: Any) -> None:
    reconciler = _reconciler(tmp_path, ["d1", "d2"], {"d1": None, "d2": None}, disposable_age)
    first = reconciler.reconcile()
    reconciler.checkpoint_file.unlink()
    second = reconciler.reconcile()

    assert first["reconciled"] == 2
    assert second["reconciled"] == 0
    assert second["already_archived"] == 2
    assert second["not_found_in_age"] == 0
    assert _states(reconciler.age_store) == {"d1": True, "d2": True}


@pytest.mark.age
def test_verify_returns_passing_active_and_history_reports_after_reconciliation(tmp_path: Path, disposable_age: Any) -> None:
    reconciler = _reconciler(tmp_path, [], {}, disposable_age)
    reports = reconciler.verify()

    assert reports["active"].mode == "active"
    assert reports["history"].mode == "history"


@pytest.mark.parametrize("decision_id", ["it's", "back\\slash", "escape\\' UNION RETURN x //"])
@pytest.mark.age
def test_reconcile_uses_canonical_age_escaping(tmp_path: Path, decision_id: str, disposable_age: Any) -> None:
    reconciler = _reconciler(tmp_path, [decision_id], {decision_id: None}, disposable_age)
    assert reconciler.reconcile()["reconciled"] == 1
    assert _states(reconciler.age_store)[decision_id] is True
