"""Deterministic source profiling for Data Intelligence connectors."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from copilot_sdk.di.models import ProfileConfig, SourceProfile

logger = logging.getLogger(__name__)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class BaseSourceProfiler:
    """Profile a SourceConnector-compatible object without domain assumptions."""

    def __init__(self, connector: Any, config: ProfileConfig | None = None) -> None:
        self.connector = connector
        self.config = config or ProfileConfig()

    def profile(self, entity_ids: Iterable[str]) -> SourceProfile:
        now = datetime.now(timezone.utc)
        records: list[dict[str, Any]] = []
        errors: list[str] = []
        validation_results: list[bool] = []

        for entity_id in entity_ids:
            try:
                fetched = self.connector.fetch(str(entity_id))
            except Exception as exc:
                message = f"fetch failed for {entity_id}: {exc.__class__.__name__}: {exc}"
                logger.warning(message)
                errors.append(message)
                continue
            for record in fetched or []:
                if not isinstance(record, dict):
                    errors.append(f"non-dict record ignored for {entity_id}")
                    continue
                records.append(record)
                try:
                    validation_results.append(bool(self.connector.validate(record)))
                except Exception as exc:
                    message = f"validate failed for {entity_id}: {exc.__class__.__name__}: {exc}"
                    logger.warning(message)
                    errors.append(message)
                    validation_results.append(False)

        freshness = self._compute_freshness(records, now)
        completeness = self._compute_completeness(records)
        consistency = 0.5
        validation_pass_rate = (
            sum(1 for result in validation_results if result) / len(validation_results)
            if validation_results
            else 0.0
        )
        overall_quality = _clamp(
            self.config.freshness_weight * freshness
            + self.config.completeness_weight * completeness
            + self.config.consistency_weight * consistency
            + self.config.validation_weight * validation_pass_rate
        )

        return SourceProfile(
            source_name=str(getattr(self.connector, "source_name", "")),
            entity_type=str(getattr(self.connector, "entity_type", "")),
            trust_tier=int(getattr(self.connector, "trust_tier", 3)),
            freshness_score=freshness,
            completeness_score=completeness,
            consistency_score=consistency,
            validation_pass_rate=_clamp(validation_pass_rate),
            record_count=len(records),
            last_profiled=now,
            overall_quality=overall_quality,
            errors=errors,
        )

    def _compute_freshness(self, records: list[dict[str, Any]], now: datetime) -> float:
        if not records:
            return 0.0
        timestamps = [
            _parse_timestamp(record.get("timestamp") or record.get("updated_at") or record.get("created_at"))
            for record in records
        ]
        valid_timestamps = [timestamp for timestamp in timestamps if timestamp is not None]
        if not valid_timestamps:
            return 0.0
        window_seconds = max(float(self.config.freshness_window_hours) * 3600.0, 1.0)
        scores = [
            _clamp(1.0 - max((now - timestamp).total_seconds(), 0.0) / window_seconds)
            for timestamp in valid_timestamps
        ]
        return _clamp(sum(scores) / len(scores))

    def _compute_completeness(self, records: list[dict[str, Any]]) -> float:
        if not records:
            return 0.0
        required = list(self.config.required_fields)
        if not required:
            return 1.0
        total = len(records) * len(required)
        present = sum(
            1
            for record in records
            for field_name in required
            if record.get(field_name) not in (None, "")
        )
        return _clamp(present / total if total else 0.0)


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (int, float)):
        parsed = datetime.fromtimestamp(float(value), tz=timezone.utc)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
