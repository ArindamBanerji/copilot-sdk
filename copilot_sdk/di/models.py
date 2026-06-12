"""Data Intelligence source profiling models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ProfileConfig:
    """Configuration for deterministic source quality scoring."""

    freshness_weight: float = 0.3
    completeness_weight: float = 0.3
    consistency_weight: float = 0.2
    validation_weight: float = 0.2
    freshness_window_hours: float = 24.0
    required_fields: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceProfile:
    """Quality profile for records fetched from one source connector."""

    source_name: str
    entity_type: str
    trust_tier: int
    freshness_score: float
    completeness_score: float
    consistency_score: float
    validation_pass_rate: float
    record_count: int
    last_profiled: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    overall_quality: float = 0.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["last_profiled"] = self.last_profiled.isoformat()
        return payload
