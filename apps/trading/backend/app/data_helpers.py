"""Trading data provenance helpers."""

from __future__ import annotations

from typing import Any


def is_sample_data(record: dict[str, Any]) -> bool:
    """Check if a record is K3 demo-fixture data (Rule 67)."""
    return record.get("provenance") == "sample"


def assert_no_sample_in_metric(records: list[dict[str, Any]], metric_name: str) -> None:
    """F-26 gate: raise if sample data feeds a computed metric."""
    sample_count = sum(1 for record in records if is_sample_data(record))
    if sample_count > 0:
        raise ValueError(
            f"F-26 VIOLATION: {sample_count}/{len(records)} records "
            f"feeding metric '{metric_name}' have provenance='sample'. "
            "K3 demo-fixture data must not feed computed metrics."
        )
