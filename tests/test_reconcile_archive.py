from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.migrate.reconcile_archive import ArchiveReconciler


class ArchiveSQLiteSource:  # MOCK-OK: isolates AGE reconciliation Cypher boundary without a live AGE service.
    def __init__(self, ids: list[str], data_dir: Path) -> None:
        self.ids = ids
        self.db_path = str(data_dir / "trading.db")

    def get_archived_decisions(self, domain: str) -> list[dict[str, str]]:
        assert domain == "trading"
        return [{"decision_id": decision_id} for decision_id in self.ids]

    def count_verified(self, domain: str) -> int:
        return 0

    def count_correct(self, domain: str) -> int:
        return 0

    def count_decisions(self, domain: str) -> int:
        return 0

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return []

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        return []


class ArchiveAGEStore:  # MOCK-OK: stateful AGE query fixture for reconciliation query and update contracts.
    _S = staticmethod(lambda value: "'" + str(value).replace("'", "\\'") + "'")

    def __init__(self, states: dict[str, bool | None], fail_on_update_number: int | None = None) -> None:
        self.states = dict(states)
        self.fail_on_update_number = fail_on_update_number
        self.update_calls = 0
        self.queries: list[str] = []

    def _domain_clause(self, domain: str) -> str:
        assert domain == "trading"
        return "d.domain = 'trading'"

    def _run_query(self, cypher: str) -> list[dict[str, Any]]:
        self.queries.append(cypher)
        ids = [decision_id for decision_id in self.states if f"'{decision_id}'" in cypher]
        if "RETURN d.decision_id AS decision_id" in cypher:
            return [{"decision_id": decision_id, "archived": self.states[decision_id]} for decision_id in ids]
        if "SET d.archived = true" in cypher:
            self.update_calls += 1
            if self.fail_on_update_number == self.update_calls:
                raise RuntimeError("interrupted")
            for decision_id in ids:
                if self.states[decision_id] is not True:
                    self.states[decision_id] = True
            return [{"cnt": len(ids)}]
        raise AssertionError(f"unexpected query: {cypher}")

    def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]:
        return [
            {"decision_id": decision_id, "domain": domain}
            for decision_id, archived in self.states.items()
            if archived is True
        ]

    def count_verified(self, domain: str) -> int:
        return 0

    def count_correct(self, domain: str) -> int:
        return 0

    def count_decisions(self, domain: str) -> int:
        return 0

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return []

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        return []


def _reconciler(tmp_path: Path, source_ids: list[str], age_states: dict[str, bool | None]) -> ArchiveReconciler:
    return ArchiveReconciler(ArchiveSQLiteSource(source_ids, tmp_path), ArchiveAGEStore(age_states), "trading")


def test_reconcile_marks_active_age_decisions_archived(tmp_path: Path) -> None:
    reconciler = _reconciler(tmp_path, ["d1", "d2", "d3"], {"d1": None, "d2": False, "d3": None})

    report = reconciler.reconcile()

    assert report["status"] == "PASS"
    assert report["reconciled"] == 3
    assert reconciler.age_store.states == {"d1": True, "d2": True, "d3": True}


def test_reconcile_counts_existing_age_archives(tmp_path: Path) -> None:
    reconciler = _reconciler(tmp_path, ["d1", "d2", "d3"], {"d1": True, "d2": True, "d3": True})

    report = reconciler.reconcile()

    assert report["reconciled"] == 0
    assert report["already_archived"] == 3


def test_reconcile_mixed_active_and_existing_archive_states(tmp_path: Path) -> None:
    reconciler = _reconciler(
        tmp_path, ["d1", "d2", "d3", "d4", "d5"], {"d1": None, "d2": False, "d3": None, "d4": True, "d5": True}
    )

    report = reconciler.reconcile()

    assert report["reconciled"] == 3
    assert report["already_archived"] == 2


def test_reconcile_reports_sqlite_ids_missing_from_age(tmp_path: Path) -> None:
    reconciler = _reconciler(tmp_path, ["present", "missing"], {"present": None})

    report = reconciler.reconcile()

    assert report["status"] == "FAIL"
    assert report["reconciled"] == 1
    assert report["not_found_in_age"] == 1


def test_dry_run_leaves_age_unchanged(tmp_path: Path) -> None:
    reconciler = _reconciler(tmp_path, ["d1", "d2"], {"d1": None, "d2": False})

    report = reconciler.reconcile(dry_run=True)

    assert report["reconciled"] == 2
    assert reconciler.age_store.states == {"d1": None, "d2": False}
    assert not reconciler.checkpoint_file.exists()


def test_checkpoint_resume_completes_remaining_batches(tmp_path: Path) -> None:
    source = ArchiveSQLiteSource([f"d{index}" for index in range(5)], tmp_path)
    age = ArchiveAGEStore({f"d{index}": None for index in range(5)}, fail_on_update_number=2)
    reconciler = ArchiveReconciler(source, age, "trading")

    with pytest.raises(RuntimeError, match="interrupted"):
        reconciler.reconcile(batch_size=2)
    checkpoint = json.loads(reconciler.checkpoint_file.read_text(encoding="utf-8"))
    assert checkpoint["processed_ids"] == ["d0", "d1"]

    age.fail_on_update_number = None
    report = reconciler.reconcile(batch_size=2)

    checkpoint = json.loads(reconciler.checkpoint_file.read_text(encoding="utf-8"))
    assert report["reconciled"] == 5
    assert checkpoint["status"] == "complete"
    assert checkpoint["processed_ids"] == ["d0", "d1", "d2", "d3", "d4"]


def test_reconcile_is_idempotent(tmp_path: Path) -> None:
    reconciler = _reconciler(tmp_path, ["d1", "d2"], {"d1": None, "d2": None})
    first = reconciler.reconcile()
    reconciler.checkpoint_file.unlink()
    second = reconciler.reconcile()

    assert first["reconciled"] == 2
    assert second["reconciled"] == 0
    assert second["already_archived"] == 2
    assert second["not_found_in_age"] == 0
    assert reconciler.age_store.states == {"d1": True, "d2": True}


def test_verify_returns_passing_active_and_history_reports_after_reconciliation(tmp_path: Path) -> None:
    reconciler = _reconciler(tmp_path, [], {})
    reports = reconciler.verify()

    assert reports["active"].mode == "active"
    assert reports["history"].mode == "history"
