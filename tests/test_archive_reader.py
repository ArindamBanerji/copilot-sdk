from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from copilot_sdk.migrate.legacy_archive_reader import LegacySQLiteArchiveReader


DOMAIN = "trading"


def _archive(path: Path, rows: list[tuple[str, str, float]]) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE decisions_archive (
                archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                created_at REAL NOT NULL,
                category TEXT,
                confidence REAL
            )
            """
        )
        connection.executemany(
            "INSERT INTO decisions_archive(decision_id, domain, created_at) VALUES (?, ?, ?)",
            rows,
        )


def test_legacy_archive_reader_filters_domain_and_orders_rows(tmp_path: Path) -> None:
    path = tmp_path / "archive.db"
    _archive(
        path,
        [
            ("d-late", DOMAIN, 2.0),
            ("other", "purchasing", 0.0),
            ("d-early", DOMAIN, 1.0),
        ],
    )

    rows = list(LegacySQLiteArchiveReader(path).iter_decisions(DOMAIN))

    assert [row.decision_id for row in rows] == ["d-early", "d-late"]
    assert all(row.domain == DOMAIN for row in rows)
    assert rows[0].properties["created_at"] == 1.0


def test_legacy_archive_reader_returns_empty_for_missing_table(tmp_path: Path) -> None:
    path = tmp_path / "empty.db"
    with sqlite3.connect(path):
        pass

    assert list(LegacySQLiteArchiveReader(path).iter_decisions(DOMAIN)) == []


def test_legacy_archive_reader_rejects_incompatible_schema(tmp_path: Path) -> None:
    path = tmp_path / "bad.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE decisions_archive (decision_id TEXT)")

    with pytest.raises(ValueError, match="missing required columns"):
        list(LegacySQLiteArchiveReader(path).iter_decisions(DOMAIN))


def test_legacy_archive_reader_is_not_a_graph_store(tmp_path: Path) -> None:
    reader = LegacySQLiteArchiveReader(tmp_path / "absent.db")
    assert not hasattr(reader, "write_decision")
    assert not hasattr(reader, "get_verified_decisions")
