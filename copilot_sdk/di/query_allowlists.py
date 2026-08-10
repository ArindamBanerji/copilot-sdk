"""Allowlisted DI-3 metrics, dimensions, and validation helpers."""

from __future__ import annotations

from collections.abc import Iterable


SUPPORTED_METRICS = frozenset(
    {
        "revenue",
        "invoice_total",
        "unmatched_invoice_count",
        "unmatched_invoice_rate",
        "decision_count",
        "accuracy",
        "confidence",
        "exception_count",
        "exception_rate",
        "conservation_status",
        "source_trust",
        "data_freshness",
    }
)

SUPPORTED_DIMENSIONS = frozenset(
    {"category", "source", "supplier", "system", "region", "action", "month", "week"}
)


def validate_metric(metric: str | None) -> str | None:
    """Return a normalized metric or ``None`` when it is not allowlisted."""

    if metric is None:
        return None
    normalized = str(metric).strip().lower().replace(" ", "_")
    return normalized if normalized in SUPPORTED_METRICS else None


def validate_dimension(dimension: str) -> str:
    """Validate one dimension and raise ``ValueError`` when unsupported."""

    normalized = str(dimension).strip().lower().replace(" ", "_")
    if normalized not in SUPPORTED_DIMENSIONS:
        raise ValueError(f"Unsupported query dimension: {dimension}")
    return normalized


def validate_dimensions(dimensions: Iterable[str]) -> list[str]:
    """Validate and normalize a collection of dimensions."""

    return [validate_dimension(dimension) for dimension in dimensions]


def validate_domain(domain: str) -> str:
    """Allow only a non-empty domain identifier for governed reads."""

    normalized = str(domain).strip().lower()
    if not normalized or any(char in normalized for char in " ;'\"\n\r"):
        raise ValueError("Invalid query domain")
    return normalized
