from __future__ import annotations


def is_sample_data(record: dict) -> bool:
    return record.get("provenance") == "sample"


def assert_no_sample_in_metric(records, metric_name):
    sample_count = sum(1 for r in records if is_sample_data(r))
    if sample_count > 0:
        raise ValueError(
            f"F-26 VIOLATION: {sample_count}/{len(records)} records "
            f"feeding metric '{metric_name}' have provenance='sample'."
        )
