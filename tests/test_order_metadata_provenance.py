from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ORDER_METADATA = (
    Path(__file__).resolve().parents[1]
    / "apps"
    / "purchasing"
    / "backend"
    / "data"
    / "order_metadata.json"
)


def _records() -> list[dict[str, Any]]:
    payload = json.loads(ORDER_METADATA.read_text(encoding="utf-8"))
    return [record for record in payload.values() if isinstance(record, dict)]


def test_all_order_metadata_records_have_provenance() -> None:
    records = _records()

    assert records
    assert all(
        isinstance(record.get("provenance"), str) and record["provenance"]
        for record in records
    )


def test_provenance_values_are_valid() -> None:
    records = _records()

    assert {record["provenance"] for record in records} <= {"sample", "live", "seed"}
