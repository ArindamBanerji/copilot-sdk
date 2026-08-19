"""Shared regime detection service."""

from __future__ import annotations

from typing import Any, Mapping

from copilot_sdk.regime.models import RegimeState
from copilot_sdk.regime.policy import RegimePolicy


class RegimeDetector:
    """Classify market or operational indicators without domain side effects."""

    def __init__(self, policy: RegimePolicy | None = None):
        self.policy = policy or RegimePolicy()

    def detect(self, indicators: Mapping[str, Any]) -> RegimeState:
        """Return a state using the injected policy's indicator vocabulary."""
        regime, confidence, normalized = self.policy.classify(indicators)
        return RegimeState.create(regime, confidence, normalized)
