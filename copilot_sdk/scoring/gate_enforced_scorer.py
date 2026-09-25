"""Gate-aware scorer boundary for verified learning."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any, cast

from copilot_sdk.scoring.composite_gate import CompositeGate

logger = logging.getLogger(__name__)


class GateEnforcedScorer:
    """Wrap a scorer and enforce the composite gate before ``learn``.

    The wrapper deliberately keeps the underlying scorer's public surface.
    Verified outcomes attempted while the gate is paused are retained and
    replayed when a subsequent gate evaluation is green.
    """

    def __init__(
        self,
        scorer: Any,
        gate: CompositeGate,
        baseline_provider: Callable[..., float] | None = None,
    ) -> None:
        self._wrapped_scorer = scorer
        self._gate = gate
        self._baseline_provider = baseline_provider
        self._outcome_buffer: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self._last_gate_status: dict[str, Any] | None = None

    def learn(self, *args: Any, **kwargs: Any) -> Any:
        gate_result = self._evaluate_gate()
        self._last_gate_status = gate_result
        # This flag is captured by the real scorer at construction from the
        # server environment, never from request context. The launcher removes
        # it before the normal restart. Preserve the measured gate result: demo
        # initialization must not pretend degraded data is GREEN.
        source = self._wrapped_scorer
        scorer_factory = getattr(source, "_scorer", None)
        if callable(scorer_factory):
            source = scorer_factory()
        if getattr(source, "_preseed_mode", False) is True:
            self._last_gate_status = {**gate_result, "enforcement_mode": "preseed"}
            logger.info("Explicit server-side preseed learning; measured gate status=%s", gate_result.get("status"))
            return self._wrapped_scorer.learn(*args, **kwargs)
        if _gate_is_active(gate_result):
            self._outcome_buffer.append((args, dict(kwargs)))
            return {
                "blocked_by_gate": True,
                "gate_status": gate_result,
                "buffered_outcomes": len(self._outcome_buffer),
            }

        buffered = list(self._outcome_buffer)
        self._outcome_buffer.clear()
        for buffered_args, buffered_kwargs in buffered:
            replay_result = self._wrapped_scorer.learn(*buffered_args, **buffered_kwargs)
            if isinstance(replay_result, dict) and replay_result.get("blocked_by_gate"):
                self._outcome_buffer.append((buffered_args, buffered_kwargs))
        return self._wrapped_scorer.learn(*args, **kwargs)

    def gate_status(self) -> dict[str, Any] | None:
        """Return the last gate evaluation, if a learning call has occurred."""

        return self._last_gate_status

    def _evaluate_gate(self) -> dict[str, Any]:
        state = self._conservation_state()
        outcomes = self._get_recent_outcomes()
        rolling_accuracy = _mean(outcomes) if outcomes else _state_float(state, "q", 0.0)
        baseline = self._baseline(state)
        alpha = _state_float(state, "alpha", 1.0)
        quality = _state_float(state, "q", rolling_accuracy)
        verified_count = _state_float(state, "V", float(len(outcomes)))
        alpha_q_v = _state_float(state, "signal", alpha * quality * verified_count)
        theta_min = _state_optional_float(state, "theta_min")
        # Preserve the scorer's explicit cold-start/bootstrap floor.  The
        # composite gate becomes enforceable once ten verified outcomes exist.
        if verified_count < 10.0:
            theta_min = None
        base_status = str(state.get("status", "GREEN")) if isinstance(state, dict) else "GREEN"
        return cast(
            dict[str, Any],
            self._gate.evaluate(
                alpha_q_v=alpha_q_v,
                theta_min=theta_min,
                rolling_accuracy=rolling_accuracy,
                baseline=baseline,
                verified_outcomes=outcomes,
                base_status=base_status,
            ),
        )

    def _conservation_state(self) -> dict[str, Any]:
        getter = getattr(self._wrapped_scorer, "get_conservation_state", None)
        if not callable(getter):
            return {}
        state = getter()
        return dict(state) if isinstance(state, dict) else {}

    def _baseline(self, state: dict[str, Any]) -> float:
        if self._baseline_provider is not None:
            try:
                value = self._baseline_provider(state)
            except TypeError:
                value = self._baseline_provider()
            try:
                return _clamp(float(value))
            except (TypeError, ValueError):
                pass
        for key in ("baseline_q", "baseline", "baseline_accuracy"):
            if key in state:
                try:
                    return _clamp(float(state[key]))
                except (TypeError, ValueError):
                    continue
        return 0.5

    def _get_recent_outcomes(self) -> list[bool]:
        store = getattr(self._wrapped_scorer, "graph_store", None)
        try:
            getter = store.get_verified_decisions if store is not None else None
        except AttributeError:
            getter = None
        if not callable(getter):
            return []
        domain = str(
            getattr(self._wrapped_scorer, "_domain", None)
            or getattr(self._wrapped_scorer, "domain", None)
            or getattr(self._wrapped_scorer, "_preset_name", "")
        )
        try:
            rows = getter(domain)
        except TypeError:
            rows = getter()
        return [_outcome_value(row) for row in (rows or [])]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped_scorer, name)


def _outcome_value(row: Any) -> bool:
    if isinstance(row, dict):
        value = row.get("is_correct", row.get("correct", row.get("outcome", False)))
    else:
        value = row
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "correct", "confirmed", "success", "passed"}
    return bool(value)


def _state_float(state: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(state.get(key, default))
    except (TypeError, ValueError):
        return default


def _state_optional_float(state: dict[str, Any], key: str) -> float | None:
    value = state.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: list[bool]) -> float:
    return sum(1.0 for value in values if value) / len(values)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _gate_is_active(result: dict[str, Any]) -> bool:
    return any(
        isinstance(details, dict) and details.get("active") is True
        for name, details in result.items()
        if name.startswith("g_")
    )
