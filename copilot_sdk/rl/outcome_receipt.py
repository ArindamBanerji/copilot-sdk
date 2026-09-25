"""Immutable RL outcome envelope and atomic persistence contract for SH-06.

This complements, rather than replaces, ``outcome.VerifiedOutcome``. A schema
cannot make an arbitrary scorer callback exactly-once: stores implementing
``OutcomeReceiptStore`` must atomically deduplicate the receipt and its durable
learning intents, and consumers must apply each intent idempotently.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import datetime
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("receipt mapping keys must be strings")
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise TypeError("receipt values must be finite JSON data")


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class OutcomeReceipt:
    """One domain-scoped decision's verified RL result and learning intent.

``verification`` requires verified=True and a stable verification_id.
``learning_effect`` describes intent, never proof that learning has committed.
Reward is the computed normalized value; raw value/formula belong in provenance.
"""

    domain: str
    decision_id: str
    actor: str
    evidence: Mapping[str, Any]
    verification: Mapping[str, Any]
    learning_effect: Mapping[str, Any]
    reward: float
    provenance: Mapping[str, Any]
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name in ("domain", "decision_id", "actor"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be a nonempty canonical string")
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported receipt schema_version")
        if isinstance(self.reward, bool) or not math.isfinite(float(self.reward)) or not 0 <= float(self.reward) <= 1:
            raise ValueError("computed reward must be finite and in [0, 1]")
        object.__setattr__(self, "reward", float(self.reward))
        for name in ("evidence", "verification", "learning_effect", "provenance"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise TypeError(f"{name} must be a mapping")
            object.__setattr__(self, name, _freeze(value))
        verification_id = self.verification.get("verification_id")
        if self.verification.get("verified") is not True or not isinstance(verification_id, str) or not verification_id.strip():
            raise ValueError("explicit verified=True and verification_id are required")

    @property
    def receipt_id(self) -> str:
        """One learning/ledger identity per domain and decision, including retries."""
        return _digest([self.domain, self.decision_id])

    @property
    def payload_hash(self) -> str:
        """Same identity with a different hash is a conflict, never an overwrite."""
        return _digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {field.name: _thaw(getattr(self, field.name)) for field in fields(self)}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> OutcomeReceipt:
        return cls(**dict(value))


def read_outcome_receipt(
    payload: Mapping[str, Any],
    *,
    now: datetime,
    legacy_until: datetime | None = None,
    legacy_reward_range: tuple[float, float] = (0.0, 1.0),
) -> OutcomeReceipt:
    """Prefer canonical receipt; permit reward_raw only before an explicit cutoff.

Legacy payloads must still supply actor, evidence and explicit verification;
numeric reward alone never establishes verification. A malformed canonical
receipt is rejected, not silently downgraded to legacy data.
"""
    if "outcome_receipt" in payload:
        receipt = OutcomeReceipt.from_dict(payload["outcome_receipt"])
        for key in ("domain", "decision_id"):
            if key in payload and payload[key] != getattr(receipt, key):
                raise ValueError(f"canonical receipt {key} conflicts with envelope")
        return receipt
    if "reward" in payload:
        return OutcomeReceipt.from_dict(payload)
    if now.tzinfo is None or (legacy_until is not None and legacy_until.tzinfo is None):
        raise ValueError("migration timestamps must be timezone-aware")
    if legacy_until is None or now >= legacy_until or "reward_raw" not in payload:
        raise ValueError("legacy receipt read is disabled or expired")
    from .reward_protocol import normalize_reward

    migrated = dict(payload)
    raw = float(migrated.pop("reward_raw"))
    migrated["reward"] = normalize_reward(raw, legacy_reward_range)
    migrated["provenance"] = {
        **dict(migrated["provenance"]),
        "migration": "reward_raw_dual_read_v1",
        "reward_raw": raw,
        "reward_range": list(legacy_reward_range),
    }
    return OutcomeReceipt.from_dict(migrated)


@runtime_checkable
class OutcomeReceiptStore(Protocol):
    """Required atomic boundary for future domain adapters, not generic callbacks.

commit() must durably insert the receipt AND learning/ledger intents in one
transaction. An identical replay returns False; same identity/different hash
raises ValueError. Failure leaves neither receipt nor intents committed.
Learning consumers deduplicate on receipt_id in the same transaction as their
effects. Merely storing a receipt before/after a scorer call does not conform.
"""

    def commit(self, receipt: OutcomeReceipt) -> bool:
        ...

    def get(self, *, domain: str, decision_id: str) -> OutcomeReceipt | None:
        ...
