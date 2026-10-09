"""Timestamp comparisons shared by graph consumers and import boundaries."""

from datetime import datetime, timezone


def normalize_timestamp(value: float | int | str | None) -> float:
    """Return epoch seconds for a numeric epoch or an ISO 8601 timestamp.

    Graph records may contain numeric epochs or historical ISO strings. Numeric
    strings remain supported for compatibility with existing float conversions.
    ISO offsets and trailing ``Z`` are honored; naive dates/times mean UTC,
    independent of the host timezone. Missing, blank, or malformed values raise
    ValueError rather than inventing a timestamp.
    """
    if value is None:
        raise ValueError("timestamp must not be None")
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        raise ValueError("timestamp must be a numeric epoch or ISO 8601 string")
    text = value.strip()
    if not text:
        raise ValueError("timestamp must not be empty")
    try:
        return float(text)
    except ValueError:
        pass
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"invalid timestamp: {value!r}; expected epoch seconds or ISO 8601") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()
