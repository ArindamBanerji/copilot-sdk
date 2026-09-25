from datetime import datetime, timezone

from copilot_sdk.backend.switching_cost_router import _timestamp


def test_epoch_timestamp_converted() -> None:
    parsed = _timestamp(1_700_000_000)
    assert parsed == datetime.fromtimestamp(1_700_000_000, tz=timezone.utc)


def test_iso_timestamp_preserved() -> None:
    parsed = _timestamp("2023-11-14T22:13:20+00:00")
    assert parsed == datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)


def test_none_timestamp_handled() -> None:
    assert _timestamp(None) is None
