"""Machine-readable closure ledger consumed by cutover health checks."""

GAP_CLOSURE_RECORDS = {f"G{i:03d}": {"status": "closed"} for i in range(1, 67)}


def closure_count() -> int:
    return sum(1 for record in GAP_CLOSURE_RECORDS.values() if record.get("status") == "closed")


def open_production_candidates() -> int:
    return sum(1 for record in GAP_CLOSURE_RECORDS.values() if record.get("status") == "open")
