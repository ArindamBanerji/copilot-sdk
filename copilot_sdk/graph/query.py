"""Bounded projection query types for BoundedProjectionStore.

These types define the filter, pagination, aggregation, and change-feed
contracts for bounded graph queries. They are re-exported from
copilot_sdk.graph.protocol and copilot_sdk.graph.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

# === Literal aliases ===

DecisionOrder = Literal["created_at", "verified_at"]
DecisionProjection = Literal["summary", "scoring", "journal", "full"]
DecisionGroup = Literal["category", "action", "status", "regime"]
DecisionMetric = Literal["count", "correct_count", "avg_confidence"]

# Shared normalization manifests. Import these directly from query.py; the
# package-level __all__ below remains the shipped query-type re-export contract.
SUMMARY_FIELDS = (
    "decision_id", "domain", "category", "recommended_action",
    "status", "confidence", "created_at", "verified_at", "is_correct", "correct",
)
SCORING_FIELDS = SUMMARY_FIELDS + (
    "category_index", "recommended_index", "factor_vector", "factor_names",
    "factors", "probabilities", "actual_action", "actual_index", "source",
    "scorer_version", "preset_version", "factor_schema_version", "outcome",
    "verified_at_epoch", "quality_signal", "was_override", "analyst_action",
    "final_action", "learning_metadata",
)
JOURNAL_FIELDS = SUMMARY_FIELDS + (
    "trade_id", "entry_id", "ticker", "regime", "entry_time", "exit_time",
    "entry_price", "exit_price", "size", "pnl", "strategy_tag", "tags",
    "source", "reflection", "notes", "factors", "options_factors",
)
LEARNING_METADATA_FIELDS = (
    "reward", "verifier", "override_reason", "variant_id", "regime_tag",
)
IMPLEMENTATION_ONLY_FIELDS = ("_sequence", "_generation")

# === Dataclasses ===

@dataclass(frozen=True, slots=True)
class DecisionFilter:
    """Predicate set for bounded decision queries.

    Empty tuple collection filters impose no restriction.
    Multiple nonempty predicates combine with AND.
    Collection values use IN.
    """
    categories: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    regimes: tuple[str, ...] = ()
    ticker: str | None = None
    confidence_min: float | None = None
    confidence_max: float | None = None
    verified: bool | None = None
    correct: bool | None = None
    created_from: float | None = None
    created_to: float | None = None
    verified_from: float | None = None
    verified_to: float | None = None
    decision_ids: tuple[str, ...] = ()
    exclude_decision_ids: tuple[str, ...] = ()
    tenant_id: str | None = None
    exclude_legacy_signals: bool = False

    def __post_init__(self) -> None:
        if self.confidence_min is not None:
            if not math.isfinite(self.confidence_min):
                raise ValueError(
                    f"confidence_min must be finite, got {self.confidence_min}"
                )
        if self.confidence_max is not None:
            if not math.isfinite(self.confidence_max):
                raise ValueError(
                    f"confidence_max must be finite, got {self.confidence_max}"
                )
        if (
            self.confidence_min is not None
            and self.confidence_max is not None
            and self.confidence_min > self.confidence_max
        ):
            raise ValueError(
                f"confidence_min ({self.confidence_min}) > "
                f"confidence_max ({self.confidence_max})"
            )
        if self.created_from is not None and self.created_to is not None:
            if self.created_from >= self.created_to:
                raise ValueError(
                    "created_from must be strictly less than created_to"
                )
        if self.verified_from is not None and self.verified_to is not None:
            if self.verified_from >= self.verified_to:
                raise ValueError(
                    "verified_from must be strictly less than verified_to"
                )


@dataclass(frozen=True, slots=True)
class DecisionCursor:
    """Keyset pagination cursor for decision queries.

    Encodes the sort value and decision_id of the last returned row.
    Callers receive this from DecisionPageResult.next_cursor and pass
    it back to get the next page. Never construct from raw values.
    """
    order_by: DecisionOrder
    value: float
    decision_id: str

    def __post_init__(self) -> None:
        if not math.isfinite(self.value):
            raise ValueError(f"cursor value must be finite, got {self.value}")
        if not self.decision_id:
            raise ValueError("cursor decision_id must be non-empty")


@dataclass(frozen=True, slots=True)
class DecisionPageRequest:
    """Pagination parameters for query_decisions.

    cursor (via after) and offset are mutually exclusive.
    When after is provided, order_by must match the cursor's order_by.
    """
    limit: int = 100
    after: DecisionCursor | None = None
    offset: int = 0
    order_by: DecisionOrder = "created_at"
    descending: bool = True

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError(f"limit must be >= 1, got {self.limit}")
        if self.offset < 0:
            raise ValueError(f"offset must be >= 0, got {self.offset}")
        if self.after is not None and self.offset != 0:
            raise ValueError(
                "cursor (after) and offset are mutually exclusive"
            )
        if self.after is not None and self.after.order_by != self.order_by:
            raise ValueError(
                f"cursor order_by ({self.after.order_by}) does not match "
                f"page order_by ({self.order_by})"
            )


@dataclass(frozen=True, slots=True)
class DecisionPageResult:
    """Result of a paginated decision query.

    items contains at most `limit` projected decision dicts.
    next_cursor is set only when has_more is True.
    """
    items: tuple[dict[str, Any], ...]
    next_cursor: DecisionCursor | None
    has_more: bool


@dataclass(frozen=True, slots=True)
class DecisionAggregate:
    """One group from an aggregate decision query.

    dimensions: the group-by dimension values for this row.
        Missing dimension values are represented by absence of
        that key (distinguishing null from empty string).
    values: the metric values. avg_confidence is omitted when
        undefined (zero-count group).
    """
    dimensions: dict[str, str]
    values: dict[str, float]


@dataclass(frozen=True, slots=True)
class DecisionChangePage:
    """Result of a change-feed query.

    events: tuple of change event dicts with projected decision data.
    next_generation: the generation to pass as after_generation for
        the next page. When has_more is False, this is the committed
        upper watermark H.
    current_generation: the committed upper watermark H at read time.
    has_more: whether more events exist beyond this page.
    """
    events: tuple[dict[str, Any], ...]
    next_generation: int
    current_generation: int
    has_more: bool

    def __post_init__(self) -> None:
        if self.next_generation < 0:
            raise ValueError(
                f"next_generation must be >= 0, got {self.next_generation}"
            )
        if self.current_generation < 0:
            raise ValueError(
                f"current_generation must be >= 0, got {self.current_generation}"
            )


# Not a @dataclass — frozen+slots incompatible with Exception base class
class DecisionGenerationChanged(Exception):
    """Raised when as_of_generation does not match the current domain generation.

    The caller should discard partial results and retry with the
    current generation, within a bounded retry budget.
    """

    def __init__(self, expected: int, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Domain generation changed: expected {expected}, actual {actual}"
        )


class ProjectionCardinalityExceeded(Exception):
    """Raised when an aggregate query exceeds the 1000-group limit."""

    def __init__(self, count: int, limit: int = 1000) -> None:
        self.count = count
        self.limit = limit
        super().__init__(
            f"Aggregate produced {count} groups, exceeding limit of {limit}"
        )


__all__ = [
    "DecisionOrder",
    "DecisionProjection",
    "DecisionGroup",
    "DecisionMetric",
    "DecisionFilter",
    "DecisionCursor",
    "DecisionPageRequest",
    "DecisionPageResult",
    "DecisionAggregate",
    "DecisionChangePage",
    "DecisionGenerationChanged",
    "ProjectionCardinalityExceeded",
]
