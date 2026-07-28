"""Day-zero measurement state for honest fresh-tenant reporting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


DEFAULT_K_MIN = 30


class MeasurementState(str, Enum):
    INSTRUMENT_VALIDATED = "instrument_validated"
    ACCUMULATING = "accumulating"
    MEASURED = "measured"


@dataclass(frozen=True)
class MeasurementStatus:
    state: MeasurementState
    decisions_verified: int
    decisions_needed: int
    arms_measured: int
    arms_total: int
    accuracy: float | None
    iks: float | None
    message: str
    provenance: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        return payload


def compute_measurement_state(
    scorer: Any,
    *,
    k_min: int | None = None,
) -> MeasurementStatus:
    """Compute measurement readiness from the scorer's verified decisions."""

    threshold = _resolve_k_min(scorer, k_min)
    decisions = _verified_decisions(scorer)
    verified = len(decisions)
    arms_total = _arms_total(scorer)
    arm_counts = _arm_counts(scorer, decisions)
    arms_measured = sum(1 for count in arm_counts.values() if count >= threshold)
    min_arm_count = min(arm_counts.values(), default=verified)
    decisions_needed = max(threshold - min_arm_count, 0)

    if verified <= 0:
        return MeasurementStatus(
            state=MeasurementState.INSTRUMENT_VALIDATED,
            decisions_verified=0,
            decisions_needed=threshold,
            arms_measured=0,
            arms_total=arms_total,
            accuracy=None,
            iks=None,
            message="Instrument calibrated. Awaiting first verified decision.",
            provenance="instrument",
        )

    if decisions_needed > 0:
        return MeasurementStatus(
            state=MeasurementState.ACCUMULATING,
            decisions_verified=verified,
            decisions_needed=decisions_needed,
            arms_measured=arms_measured,
            arms_total=arms_total,
            accuracy=None,
            iks=None,
            message=(
                f"Accumulating: {arms_measured}/{arms_total} arms measured. "
                f"Magnitude will be available when every arm reaches {threshold} verified decisions."
            ),
            provenance="accumulating",
        )

    accuracy = _accuracy(decisions)
    iks = _current_iks(scorer)
    return MeasurementStatus(
        state=MeasurementState.MEASURED,
        decisions_verified=verified,
        decisions_needed=0,
        arms_measured=arms_measured,
        arms_total=arms_total,
        accuracy=accuracy,
        iks=iks,
        message=f"Measured: {accuracy * 100:.1f}% accuracy across {verified} decisions.",
        provenance="real_measured",
    )


def _resolve_k_min(scorer: Any, k_min: int | None) -> int:
    if k_min is not None:
        return max(int(k_min), 1)
    for attr in ("measurement_k_min", "_measurement_k_min"):
        value = getattr(scorer, attr, None)
        if value is not None:
            return max(int(value), 1)
    preset = getattr(scorer, "_preset", None)
    value = getattr(preset, "measurement_k_min", None)
    if value is not None:
        return max(int(value), 1)
    return DEFAULT_K_MIN


def _verified_decisions(scorer: Any) -> list[dict[str, Any]]:
    store = _graph_store(scorer)
    domain = _domain(scorer, store)
    if store is not None:
        return [dict(row) for row in store.get_verified_decisions(domain)]
    get_verified_count = getattr(scorer, "get_verified_count", None)
    if callable(get_verified_count):
        return [{} for _ in range(max(int(get_verified_count()), 0))]
    return []


def _graph_store(scorer: Any) -> Any | None:
    for attr in ("graph_store", "_graph_store"):
        value = getattr(scorer, attr, None)
        if value is not None:
            return value
    return None


def _domain(scorer: Any, store: Any | None) -> str:
    value = getattr(scorer, "_domain", None)
    if value:
        return str(value)
    if store is not None:
        return str(getattr(store, "domain", "") or "default")
    return "default"


def _arms_total(scorer: Any) -> int:
    shape = getattr(getattr(scorer, "_preset", None), "shape", None)
    n_categories = int(getattr(shape, "n_categories", 0) or len(getattr(shape, "category_names", ()) or ()))
    n_actions = int(getattr(shape, "n_actions", 0) or len(getattr(shape, "action_names", ()) or ()))
    return max(n_categories * n_actions, 0)


def _arm_counts(scorer: Any, decisions: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    counts = {key: 0 for key in _arm_keys(scorer)}
    for decision in decisions:
        category = str(decision.get("category") or "")
        action = str(decision.get("actual_action") or decision.get("recommended_action") or decision.get("action") or "")
        if not category or not action:
            continue
        key = (category, action)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _arm_keys(scorer: Any) -> list[tuple[str, str]]:
    shape = getattr(getattr(scorer, "_preset", None), "shape", None)
    categories = tuple(getattr(shape, "category_names", ()) or ())
    actions = tuple(getattr(shape, "action_names", ()) or ())
    return [(str(category), str(action)) for category in categories for action in actions]


def _accuracy(decisions: list[dict[str, Any]]) -> float:
    if not decisions:
        return 0.0
    correct = sum(1 for decision in decisions if bool(decision.get("is_correct")))
    return correct / len(decisions)


def _current_iks(scorer: Any) -> float | None:
    trajectory = getattr(scorer, "trajectory", None)
    if not callable(trajectory):
        return None
    try:
        result = trajectory()
    except Exception:
        return None
    if isinstance(result, dict):
        value = result.get("current_iks")
    else:
        value = getattr(result, "current_iks", None)
    if value is None:
        return None
    return float(value)
