"""Domain-neutral shared pattern registry."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field, replace
from typing import Any

from copilot_sdk.timestamps import normalize_timestamp
from copilot_sdk.graph.protocol import GraphStore


@dataclass(frozen=True)
class TransferPattern:
    pattern_id: str
    source_copilot: str
    pattern_type: str
    category: str
    action: str
    win_rate: float
    centroid_delta: list[float]
    confidence: float
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    source_domain: str = ""
    target_domain: str = ""
    similarity_score: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "pattern_id", str(self.pattern_id or ""))
        object.__setattr__(self, "source_copilot", str(self.source_copilot or ""))
        object.__setattr__(self, "pattern_type", str(self.pattern_type or ""))
        object.__setattr__(self, "category", str(self.category or ""))
        object.__setattr__(self, "action", str(self.action or ""))
        object.__setattr__(self, "win_rate", float(self.win_rate))
        object.__setattr__(
            self,
            "centroid_delta",
            [float(value) for value in self.centroid_delta],
        )
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(self, "created_at", float(self.created_at))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        object.__setattr__(self, "source_domain", str(self.source_domain or self.source_copilot))
        object.__setattr__(self, "target_domain", str(self.target_domain or self.metadata.get("target_domain") or ""))
        object.__setattr__(
            self,
            "similarity_score",
            float(self.similarity_score or self.metadata.get("similarity_score") or self.confidence),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TransferPattern":
        return cls(
            pattern_id=str(payload.get("pattern_id") or ""),
            source_copilot=str(payload.get("source_copilot") or ""),
            pattern_type=str(payload.get("pattern_type") or ""),
            category=str(payload.get("category") or ""),
            action=str(payload.get("action") or ""),
            win_rate=float(payload.get("win_rate") or 0.0),
            centroid_delta=list(payload.get("centroid_delta") or []),
            confidence=float(payload.get("confidence") or 0.0),
            created_at=normalize_timestamp(payload.get("created_at") or time.time()),
            metadata=dict(payload.get("metadata") or {}),
            source_domain=str(payload.get("source_domain") or payload.get("source_copilot") or ""),
            target_domain=str(payload.get("target_domain") or ""),
            similarity_score=float(payload.get("similarity_score") or payload.get("confidence") or 0.0),
        )


class SharedPatternRegistry:
    """Shared patterns read directly from domain-scoped graph state."""

    def __init__(self, graph_store: GraphStore, domain: str) -> None:
        self.graph_store = graph_store
        self.domain = domain

    def _patterns(self) -> list[TransferPattern]:
        return [TransferPattern.from_dict(state["pattern"])
                for state in self.graph_store.list_governance(self.domain)
                if state.get("kind") == "transfer_pattern"]

    @property
    def count(self) -> int:
        return len(self._patterns())

    def register(
        self,
        pattern: TransferPattern,
        graph_store: GraphStore | None = None,
    ) -> TransferPattern:
        if graph_store is not None:
            source_artifact_id = str(pattern.metadata.get("source_artifact_id") or "").strip()
            source_domain = str(pattern.source_domain or pattern.source_copilot).strip()
            if (
                not source_artifact_id
                or not source_domain
                or graph_store.get_governance(source_domain, source_artifact_id) is None
            ):
                raise ValueError("Source artifact not registered")
        pattern_id = pattern.pattern_id or self._new_pattern_id(pattern.source_copilot)
        stored = replace(pattern, pattern_id=pattern_id)
        self.graph_store.save_governance(self.domain, f"transfer_pattern:{pattern_id}",
                                         {"kind": "transfer_pattern", "pattern": stored.to_dict()})
        return stored

    def get_patterns(
        self,
        source_copilot: str | None = None,
        min_confidence: float = 0.5,
        min_win_rate: float = 0.6,
    ) -> list[TransferPattern]:
        patterns = [
            pattern
            for pattern in self._patterns()
            if (source_copilot is None or pattern.source_copilot == source_copilot)
            and pattern.confidence >= float(min_confidence)
            and pattern.win_rate >= float(min_win_rate)
        ]
        return sorted(
            patterns,
            key=lambda pattern: (pattern.confidence, pattern.win_rate, pattern.created_at),
            reverse=True,
        )

    def get_patterns_for_warm_start(
        self,
        target_copilot: str,
        category_mapping: dict[str, str] | None = None,
    ) -> list[TransferPattern]:
        mapped_patterns: list[TransferPattern] = []
        mapping = dict(category_mapping or {})
        for pattern in self.get_patterns():
            if pattern.source_copilot == target_copilot:
                continue
            target_category = mapping.get(pattern.category, pattern.category)
            confidence = pattern.confidence
            if target_category != pattern.category:
                confidence *= 0.8
            mapped_patterns.append(
                replace(
                    pattern,
                    category=target_category,
                    confidence=confidence,
                    metadata={
                        **pattern.metadata,
                        "original_category": pattern.category,
                        "target_copilot": target_copilot,
                    },
                )
            )
        return sorted(
            mapped_patterns,
            key=lambda pattern: (pattern.confidence, pattern.win_rate, pattern.created_at),
            reverse=True,
        )

    def _new_pattern_id(self, source_copilot: str) -> str:
        source = "".join(ch for ch in source_copilot.upper() if ch.isalnum()) or "UNKNOWN"
        return f"XC-{source}-{uuid.uuid4().hex[:8]}"
