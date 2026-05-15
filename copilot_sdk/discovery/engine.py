"""In-memory cross-system discovery engine."""

from __future__ import annotations

import logging
from typing import Any, Sequence

from copilot_sdk.discovery.alerts import DiscoveryAlert
from copilot_sdk.discovery.patterns import (
    AnomalyCoOccurrencePattern,
    CentroidCorrelationPattern,
    ConservationAlignmentPattern,
    CrossSystemPattern,
    TransferOpportunityPattern,
)

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Advisory-only discovery engine for registered copilots."""

    def __init__(self, patterns: Sequence[CrossSystemPattern] | None = None) -> None:
        self._copilots: dict[str, Any] = {}
        self._patterns = list(patterns) if patterns is not None else [
            CentroidCorrelationPattern(),
            ConservationAlignmentPattern(),
            TransferOpportunityPattern(),
            AnomalyCoOccurrencePattern(),
        ]
        self._alerts: list[DiscoveryAlert] = []

    @property
    def alert_count(self) -> int:
        return len(self._alerts)

    def register_copilot(self, name: str, scorer: Any) -> None:
        normalized = str(name or "").strip()
        if not normalized:
            raise ValueError("copilot name is required")
        self._copilots[normalized] = scorer

    def sweep(
        self,
        category_mappings: dict[str, dict[str, str]] | None = None,
    ) -> list[DiscoveryAlert]:
        new_alerts: list[DiscoveryAlert] = []
        for pattern in self._patterns:
            try:
                discovered = pattern.discover(
                    dict(self._copilots),
                    category_mappings=category_mappings,
                )
            except Exception as exc:
                logger.warning("Discovery pattern %s failed: %s", pattern, exc)
                continue
            new_alerts.extend(discovered)
        self._alerts.extend(new_alerts)
        return new_alerts

    def get_digest(self, min_confidence: float = 0.5) -> list[DiscoveryAlert]:
        threshold = float(min_confidence)
        return [alert for alert in self._alerts if alert.confidence >= threshold]

    def clear(self) -> None:
        self._alerts.clear()
