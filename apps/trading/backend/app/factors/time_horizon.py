"""Time horizon factor computer."""

from __future__ import annotations

from typing import Any

from app.factors.base import clamp, mean_or_neutral


SESSIONS = {
    "premarket": range(4, 10),
    "morning": range(9, 13),
    "midday": range(11, 15),
    "afternoon": range(13, 17),
    "afterhours": range(16, 21),
}


class TimeHorizonFactor:
    factor_name = "risk_reward_actual"
    factor_index = 4

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        if not ctx:
            return 0.5

        components: list[float] = []

        if "planned_hold_hours" in ctx and "actual_hold_hours" in ctx:
            score = _plan_adherence_score(
                ctx.get("planned_hold_hours"),
                ctx.get("actual_hold_hours"),
            )
            if score is not None:
                components.append(score)

        if "exit_reason" in ctx:
            components.append(_exit_reason_score(ctx.get("exit_reason")))

        if "entry_hour" in ctx and "preferred_session" in ctx:
            components.append(
                _session_alignment_score(
                    ctx.get("entry_hour"),
                    ctx.get("preferred_session"),
                )
            )

        return mean_or_neutral(components)


def _plan_adherence_score(planned_value: Any, actual_value: Any) -> float | None:
    try:
        planned = float(planned_value)
        actual = float(actual_value)
    except (TypeError, ValueError):
        return None
    if planned <= 0:
        return None
    ratio = actual / planned
    if 0.7 <= ratio <= 1.5:
        return 1.0
    if ratio < 0.7:
        return clamp(ratio / 0.7)
    return clamp(max(0.2, 1.0 - min((ratio - 1.5) / 2.0, 0.8)))


def _exit_reason_score(value: Any) -> float:
    scores = {
        "target": 1.0,
        "stop": 0.8,
        "time": 0.7,
        "impulse": 0.2,
    }
    return scores.get(str(value or "").lower(), 0.5)


def _session_alignment_score(entry_value: Any, session_value: Any) -> float:
    try:
        entry_hour = int(entry_value)
    except (TypeError, ValueError):
        return 0.5
    preferred_session = str(session_value or "").lower()
    if preferred_session not in SESSIONS:
        return 0.5
    return 1.0 if entry_hour in SESSIONS[preferred_session] else 0.4
