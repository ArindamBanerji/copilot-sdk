"""Advisory discovery alert primitives."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiscoveryAlert:
    """Advisory-only cross-system discovery alert."""

    alert_id: str = ""
    pattern_type: str = ""
    source_copilots: list[str] = field(default_factory=list)
    title: str = ""
    description: str = ""
    confidence: float = 0.0
    evidence: dict[str, Any] = field(default_factory=dict)
    status: str = "advisory"
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.alert_id:
            self.alert_id = f"DISC-{uuid.uuid4().hex[:8]}"
        self.pattern_type = str(self.pattern_type or "")
        self.source_copilots = [str(name) for name in list(self.source_copilots or [])]
        self.title = str(self.title or "")
        self.description = str(self.description or "")
        self.confidence = _bounded_confidence(self.confidence)
        self.evidence = dict(self.evidence or {})
        self.status = str(self.status or "advisory")
        self.created_at = float(self.created_at)
        self.metadata = dict(self.metadata or {})


def _bounded_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    if confidence != confidence:
        return 0.0
    return max(0.0, min(confidence, 1.0))
