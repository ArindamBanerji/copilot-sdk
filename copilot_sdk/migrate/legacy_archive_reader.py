"""Read-only access to historical decision archives during AGE cutover."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArchivedDecision:
    """A historical archived decision read from the cutover source."""

    decision_id: str
    domain: str
    properties: Mapping[str, Any]


class LegacySQLiteArchiveReader:
    """Read archived rows without presenting the source as a graph backend."""

    def __init__(self, source_path: str | Path) -> None:
        self.source_path = Path(source_path)

    def iter_decisions(self, domain: str) -> Iterator[ArchivedDecision]:
        """Yield one domain's archive in deterministic historical order."""
        uri = f"file:{self.source_path.resolve().as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            connection.row_factory = sqlite3.Row
            columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(decisions_archive)")
            }
            if not columns:
                return
            required = {"decision_id", "domain", "created_at"}
            missing = required - columns
            if missing:
                raise ValueError(
                    "decisions_archive is missing required columns: "
                    + ", ".join(sorted(missing))
                )
            rows = connection.execute(
                """
                SELECT * FROM decisions_archive
                WHERE domain = ?
                ORDER BY created_at ASC, decision_id ASC
                """,
                (str(domain),),
            )
            for row in rows:
                properties = dict(row)
                yield ArchivedDecision(
                    decision_id=str(properties["decision_id"]),
                    domain=str(properties["domain"]),
                    properties=properties,
                )
