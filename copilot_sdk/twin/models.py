"""Immutable artifacts and comparison results for the shared Frozen Twin."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any

import numpy as np


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default)


def _snapshot_payload(
    scorer_state: dict[str, Any],
    kernel_state: dict[str, Any],
    conservation_state: dict[str, Any],
    iks_value: float,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "scorer_state": scorer_state,
        "kernel_state": kernel_state,
        "conservation_state": conservation_state,
        "iks_value": iks_value,
        "metadata": metadata,
    }


@dataclass(frozen=True)
class FrozenSnapshot:
    """Day-0 scorer state and its integrity digest.

    The dataclass prevents replacement of top-level fields.  Mutable inputs are
    deep-copied at construction and every serialized load is checksum-checked;
    callers should treat the nested state as an immutable artifact as well.
    """

    scorer_state: dict[str, Any]
    kernel_state: dict[str, Any]
    conservation_state: dict[str, Any]
    iks_value: float
    metadata: dict[str, Any]
    checksum: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "scorer_state", copy.deepcopy(self.scorer_state))
        object.__setattr__(self, "kernel_state", copy.deepcopy(self.kernel_state))
        object.__setattr__(self, "conservation_state", copy.deepcopy(self.conservation_state))
        object.__setattr__(self, "metadata", copy.deepcopy(self.metadata))
        object.__setattr__(self, "iks_value", float(self.iks_value))

    @classmethod
    def create(
        cls,
        *,
        scorer_state: dict[str, Any],
        kernel_state: dict[str, Any],
        conservation_state: dict[str, Any],
        iks_value: float,
        metadata: dict[str, Any],
    ) -> "FrozenSnapshot":
        payload = _snapshot_payload(
            scorer_state,
            kernel_state,
            conservation_state,
            float(iks_value),
            metadata,
        )
        checksum = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        return cls(checksum=checksum, **payload)

    def _payload(self) -> dict[str, Any]:
        return _snapshot_payload(
            self.scorer_state,
            self.kernel_state,
            self.conservation_state,
            self.iks_value,
            self.metadata,
        )

    def to_json(self) -> str:
        """Serialize the snapshot deterministically for persistence or transport."""
        return _canonical_json({**self._payload(), "checksum": self.checksum})

    @classmethod
    def from_json(cls, json_str: str) -> "FrozenSnapshot":
        """Load and verify a snapshot, rejecting malformed or altered state."""
        try:
            raw = json.loads(json_str)
        except json.JSONDecodeError as error:
            raise ValueError("Frozen Twin snapshot is not valid JSON") from error
        if not isinstance(raw, dict):
            raise ValueError("Frozen Twin snapshot must be a JSON object")
        required = {
            "scorer_state",
            "kernel_state",
            "conservation_state",
            "iks_value",
            "metadata",
            "checksum",
        }
        if not required.issubset(raw):
            missing = sorted(required.difference(raw))
            raise ValueError(f"Frozen Twin snapshot is missing fields: {missing}")
        snapshot = cls(
            scorer_state=raw["scorer_state"],
            kernel_state=raw["kernel_state"],
            conservation_state=raw["conservation_state"],
            iks_value=float(raw["iks_value"]),
            metadata=raw["metadata"],
            checksum=str(raw["checksum"]),
        )
        if not snapshot.verify_integrity():
            raise ValueError("Frozen Twin snapshot checksum verification failed")
        return snapshot

    def verify_integrity(self) -> bool:
        expected = hashlib.sha256(_canonical_json(self._payload()).encode("utf-8")).hexdigest()
        return expected == self.checksum


@dataclass(frozen=True)
class ParallelResult:
    """Live and day-0 scores for one decision."""

    live_result: Any
    frozen_result: Any
    delta: float


@dataclass(frozen=True)
class DriftReport:
    """Measured divergence between live scorer state and the day-0 twin."""

    centroid_drift: float
    weight_drift: float
    conservation_drift: float
    iks_delta: float
    decision_count_since_freeze: int

