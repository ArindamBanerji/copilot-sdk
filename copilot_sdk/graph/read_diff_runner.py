"""Semantic read comparison for GraphStore migration and dual-write checks."""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from typing import Any

from copilot_sdk.graph.dual_write_store import DualWriteStore
from copilot_sdk.graph.protocol import GraphStore


# These are semantic Decision fields common to SQLite and AGE return values.
# Do not compare storage-format fields (for example ``factors_json``),
# migration bookkeeping, metadata serialization, or timestamps.  AGE may
# return verified_at/context only inside an Outcome container, so those are
# deliberately excluded from this cross-store contract.
ACTIVE_COMPARE_FIELDS = (
    "decision_id",
    "domain",
    "category",
    "category_index",
    "recommended_action",
    "recommended_index",
    "confidence",
    "factor_vector",
    "probabilities",
    "status",
)

VERIFIED_COMPARE_FIELDS = ("actual_action", "actual_index", "is_correct")

HISTORY_COMPARE_FIELDS = (
    "decision_id",
    "domain",
    "category",
    "category_index",
    "recommended_action",
    "recommended_index",
    "confidence",
    "factor_vector",
    "probabilities",
    "created_at",
    "actual_action",
    "actual_index",
    "is_correct",
    "verified_at",
    "archived_at",
    "archive_reason",
)


@dataclass
class DiffReport:
    """Structured result of a primary/secondary GraphStore comparison."""

    domain: str
    mode: str = "active"
    primary_count: int = 0
    secondary_count: int = 0
    count_match: bool = False
    primary_correct: int = 0
    secondary_correct: int = 0
    correct_match: bool = False
    primary_total: int = 0
    secondary_total: int = 0
    total_match: bool = False
    primary_archive_count: int = 0
    secondary_archive_count: int = 0
    archive_count_match: bool = False
    missing_in_secondary: list[str] = field(default_factory=list)
    missing_in_primary: list[str] = field(default_factory=list)
    field_mismatches: list[dict[str, Any]] = field(default_factory=list)
    passed: bool = False

    def summary(self) -> str:
        outcome = "PASS" if self.passed else "FAIL"
        if self.mode == "history":
            return (
                f"{outcome} mode=history domain={self.domain} "
                f"archived={self.primary_archive_count}/{self.secondary_archive_count} "
                f"missing_secondary={len(self.missing_in_secondary)} "
                f"missing_primary={len(self.missing_in_primary)} "
                f"field_mismatches={len(self.field_mismatches)}"
            )
        return (
            f"{outcome} mode=active domain={self.domain} verified={self.primary_count}/{self.secondary_count} "
            f"correct={self.primary_correct}/{self.secondary_correct} "
            f"total={self.primary_total}/{self.secondary_total} "
            f"missing_secondary={len(self.missing_in_secondary)} "
            f"missing_primary={len(self.missing_in_primary)} "
            f"field_mismatches={len(self.field_mismatches)}"
        )


def _decoded_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    # Bare identifiers (especially IDs containing ``e``) must remain strings.
    # Python's JSON decoder accepts values such as ``70584e140919`` as an
    # enormous-exponent float (``inf``), which can make ``inf`` vs ``inf`` fail
    # the numeric tolerance comparison because ``inf - inf`` is ``nan``.
    stripped = value.lstrip()
    if not stripped or stripped[0] not in '{["':
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def _values_match(primary_value: Any, secondary_value: Any) -> bool:
    """Compare values with JSON normalization and a small float tolerance."""
    if isinstance(primary_value, str) and isinstance(secondary_value, str):
        if primary_value == secondary_value:
            return True
    primary_value = _decoded_json(primary_value)
    secondary_value = _decoded_json(secondary_value)
    if primary_value is None and secondary_value is None:
        return True
    if isinstance(primary_value, (int, float)) and not isinstance(primary_value, bool):
        if isinstance(secondary_value, (int, float)) and not isinstance(secondary_value, bool):
            return abs(float(primary_value) - float(secondary_value)) <= 1e-6
    if isinstance(primary_value, dict) and isinstance(secondary_value, dict):
        return primary_value == secondary_value
    if isinstance(primary_value, list) and isinstance(secondary_value, list):
        return len(primary_value) == len(secondary_value) and all(
            _values_match(left, right) for left, right in zip(primary_value, secondary_value)
        )
    return bool(primary_value == secondary_value)


def _normalized_decision(decision: dict[str, Any]) -> dict[str, Any]:
    """Flatten optional outcome containers into the common comparison shape."""
    normalized = dict(decision)
    for container_key in ("outcome", "outcome_metadata"):
        container = normalized.get(container_key)
        if isinstance(container, dict):
            for field in ("actual_action", "actual_index", "is_correct", "verified_at"):
                normalized.setdefault(field, container.get(field))
    return normalized


class ReadDiffRunner:
    """Compares read outputs from two GraphStore implementations."""

    def __init__(
        self,
        primary: GraphStore,
        secondary: GraphStore,
        domain: str,
        logger: logging.Logger | None = None,
    ) -> None:
        if isinstance(primary, DualWriteStore) or isinstance(secondary, DualWriteStore):
            raise TypeError(
                "ReadDiffRunner requires two concrete stores, not DualWriteStore. "
                "Pass primary and secondary stores directly."
            )
        self.primary = primary
        self.secondary = secondary
        self.domain = domain
        self.logger = logger or logging.getLogger(__name__)

    def run_diff(self) -> DiffReport:
        """Backward-compatible alias for :meth:`compare_all`."""
        return self.compare_all()

    def compare_all(self, domain: str | None = None) -> DiffReport:
        """Backward-compatible alias for :meth:`compare_active`."""
        return self.compare_active(domain)

    def compare_active(self, domain: str | None = None) -> DiffReport:
        """Compare active count parity and every active Decision in ``domain``."""
        target_domain = domain or self.domain
        return self._compare_active(target_domain)

    def compare_sample(self, domain: str | None = None, n: int = 100) -> DiffReport:
        """Backward-compatible alias for :meth:`compare_active_sample`."""
        return self.compare_active_sample(domain, n=n)

    def compare_active_sample(self, domain: str | None = None, n: int = 100) -> DiffReport:
        """Compare count parity and a random sample of up to ``n`` Decisions."""
        if n < 0:
            raise ValueError("sample size must be non-negative")
        target_domain = domain or self.domain
        return self._compare_active(target_domain, sample_size=n)

    def compare_history(
        self, domain: str | None = None, compare_archived_at: bool = False
    ) -> DiffReport:
        """Compare archive history without invoking active D2 count methods."""
        target_domain = domain or self.domain
        report = DiffReport(domain=target_domain, mode="history")
        primary_archived = self.primary.get_archived_decisions(target_domain)
        secondary_archived = self.secondary.get_archived_decisions(target_domain)
        primary_map = self._decision_map(primary_archived, target_domain)
        secondary_map = self._decision_map(secondary_archived, target_domain)
        report.primary_archive_count = len(primary_archived)
        report.secondary_archive_count = len(secondary_archived)
        report.archive_count_match = (
            report.primary_archive_count == report.secondary_archive_count
        )
        self._populate_id_differences(report, primary_map, secondary_map)
        history_fields = HISTORY_COMPARE_FIELDS if compare_archived_at else tuple(
            field for field in HISTORY_COMPARE_FIELDS if field != "archived_at"
        )
        self._compare_fields(report, primary_map, secondary_map, history_fields)
        report.passed = (
            report.archive_count_match
            and not report.missing_in_secondary
            and not report.missing_in_primary
            and not report.field_mismatches
        )
        self.logger.info(report.summary())
        return report

    def _compare_active(self, domain: str, sample_size: int | None = None) -> DiffReport:
        report = DiffReport(domain=domain, mode="active")
        report.primary_count = self.primary.count_verified(domain)
        report.secondary_count = self.secondary.count_verified(domain)
        report.count_match = report.primary_count == report.secondary_count

        report.primary_correct = self.primary.count_correct(domain)
        report.secondary_correct = self.secondary.count_correct(domain)
        report.correct_match = report.primary_correct == report.secondary_correct

        report.primary_total = self.primary.count_decisions(domain)
        report.secondary_total = self.secondary.count_decisions(domain)
        report.total_match = report.primary_total == report.secondary_total

        if report.count_match:
            primary_map = self._decision_map(self.primary.get_all_decisions(domain), domain)
            secondary_map = self._decision_map(self.secondary.get_all_decisions(domain), domain)
            self._merge_verified_fields(
                primary_map,
                self.primary.get_verified_decisions(domain),
                domain,
            )
            self._merge_verified_fields(
                secondary_map,
                self.secondary.get_verified_decisions(domain),
                domain,
            )

            if sample_size is not None:
                sample_keys = set(random.sample(list(primary_map), min(sample_size, len(primary_map))))
                primary_map = {key: decision for key, decision in primary_map.items() if key in sample_keys}
                secondary_map = {key: decision for key, decision in secondary_map.items() if key in sample_keys}

            self._populate_id_differences(report, primary_map, secondary_map)
            self._compare_fields(report, primary_map, secondary_map, ACTIVE_COMPARE_FIELDS)

            for key, primary_decision in primary_map.items():
                secondary_decision = secondary_map.get(key)
                if secondary_decision is None:
                    continue
                if self._is_verified(primary_decision) or self._is_verified(secondary_decision):
                    for field in VERIFIED_COMPARE_FIELDS:
                        # AGE's optional Outcome merge does not guarantee every
                        # verified field at top level.  Compare only values both
                        # adapters explicitly return.
                        if field not in primary_decision or field not in secondary_decision:
                            continue
                        primary_value = primary_decision[field]
                        secondary_value = secondary_decision[field]
                        if not _values_match(primary_value, secondary_value):
                            report.field_mismatches.append(
                                {
                                    "decision_id": key[1],
                                    "field": field,
                                    "primary": primary_value,
                                    "secondary": secondary_value,
                                }
                            )

        report.passed = (
            report.count_match
            and report.correct_match
            and report.total_match
            and not report.missing_in_secondary
            and not report.missing_in_primary
            and not report.field_mismatches
        )
        self.logger.info(report.summary())
        return report

    @staticmethod
    def _populate_id_differences(
        report: DiffReport,
        primary_map: dict[tuple[str, str], dict[str, Any]],
        secondary_map: dict[tuple[str, str], dict[str, Any]],
    ) -> None:
        report.missing_in_secondary = [
            decision_id
            for domain, decision_id in primary_map
            if (domain, decision_id) not in secondary_map
        ]
        report.missing_in_primary = [
            decision_id
            for domain, decision_id in secondary_map
            if (domain, decision_id) not in primary_map
        ]

    @staticmethod
    def _compare_fields(
        report: DiffReport,
        primary_map: dict[tuple[str, str], dict[str, Any]],
        secondary_map: dict[tuple[str, str], dict[str, Any]],
        fields: tuple[str, ...],
    ) -> None:
        for key, primary_decision in primary_map.items():
            secondary_decision = secondary_map.get(key)
            if secondary_decision is None:
                continue
            for field in fields:
                primary_value = primary_decision.get(field)
                secondary_value = secondary_decision.get(field)
                if not _values_match(primary_value, secondary_value):
                    report.field_mismatches.append(
                        {
                            "decision_id": key[1],
                            "field": field,
                            "primary": primary_value,
                            "secondary": secondary_value,
                        }
                    )

    @staticmethod
    def _decision_map(
        decisions: list[dict[str, Any]], domain: str
    ) -> dict[tuple[str, str], dict[str, Any]]:
        return {
            (str(decision.get("domain", domain)), str(decision["decision_id"])): _normalized_decision(decision)
            for decision in decisions
        }

    @classmethod
    def _merge_verified_fields(
        cls,
        decisions: dict[tuple[str, str], dict[str, Any]],
        verified_decisions: list[dict[str, Any]],
        domain: str,
    ) -> None:
        for verified in verified_decisions:
            key = (str(verified.get("domain", domain)), str(verified["decision_id"]))
            decision = decisions.get(key)
            if decision is None:
                continue
            normalized = _normalized_decision(verified)
            for field in VERIFIED_COMPARE_FIELDS:
                if field in normalized:
                    decision[field] = normalized[field]

    @staticmethod
    def _is_verified(decision: dict[str, Any]) -> bool:
        return decision.get("status") in {"confirmed", "overridden"} or (
            decision.get("status") is None and decision.get("outcome") is not None
        )
