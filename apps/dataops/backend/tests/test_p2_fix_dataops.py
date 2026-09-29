from __future__ import annotations

import pytest

from app import ae_router
from app.routers import di_gateway_router


@pytest.mark.parametrize("value", [None, "not-a-timestamp"])
def test_di_timestamp_substitution_is_labelled(value: object) -> None:
    timestamp, available, source = di_gateway_router._timestamp(value)
    assert isinstance(timestamp, str)
    assert timestamp
    assert available is False
    assert source in {"generated", "invalid"}


@pytest.mark.parametrize("bad_timestamp", [None, "not-a-timestamp"])
def test_ae_malformed_timestamp_sorts_last_and_is_flagged(bad_timestamp: object) -> None:
    events = [
        {
            "event_type": "variant_proposed",
            "rule_name": "rule",
            "variant_id": "v1",
            "timestamp": bad_timestamp,
        },
        {
            "event_type": "variant_promoted",
            "rule_name": "rule",
            "variant_id": "v1",
            "timestamp": "2026-01-01T00:00:00+00:00",
        },
    ]
    rules = ae_router._persisted_rule_lifecycles(events)
    transitions = rules[0]["lifecycle_events"]
    assert transitions[-1]["timestamp_available"] is False
    assert transitions[0]["type"] == "promoted"
