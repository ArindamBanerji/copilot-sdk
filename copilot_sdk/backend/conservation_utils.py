from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, TypedDict, cast, runtime_checkable


def _ensure_gae_path() -> None:
    try:
        import gae  # noqa: F401
    except ModuleNotFoundError:
        import sys

        workspace = Path(__file__).resolve().parents[3]
        candidate = workspace / "graph-attention-engine-v50"
        if candidate.exists():
            sys.path.insert(0, str(candidate))


_ensure_gae_path()

from gae.calibration import check_conservation, compute_theta_min, conservation_status  # noqa: E402
from copilot_sdk.scoring.composite_gate import chronological_decisions


ENGINE_STATUS = {"gae": "gae.calibration", "component": "conservation_status"}
ENGINE_WHAT_IF = {"gae": "gae.calibration", "component": "check_conservation"}
L5_BASELINE_PRODUCT_FALLBACK = 0.0
QUALITY_WINDOW_SIZE = 400


def _is_verified_decision(decision: Mapping[str, Any]) -> bool:
    outcome = decision.get("outcome")
    if outcome is not None:
        return str(outcome).strip().lower() in {"confirmed", "overridden"}
    return decision.get("is_correct") is not None


def _is_benchmark_decision(decision: Mapping[str, Any]) -> bool:
    context = decision.get("context")
    if isinstance(context, dict) and context.get("benchmark") is True:
        return True
    metadata = decision.get("outcome_metadata")
    if isinstance(metadata, dict):
        nested = metadata.get("context")
        if isinstance(nested, dict) and nested.get("benchmark") is True:
            return True
    return False


def _is_correct_decision(decision: Mapping[str, Any]) -> bool:
    outcome = str(decision.get("outcome") or "").strip().lower()
    return outcome == "confirmed" or bool(decision.get("is_correct"))


def _eligible_decisions(
    decisions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in decisions
        if _is_verified_decision(row) and not _is_benchmark_decision(row)
    ]


def _rolling_q(
    decisions: Sequence[Mapping[str, Any]],
    *,
    window_size: int = QUALITY_WINDOW_SIZE,
) -> float | None:
    """Return quality over the most recent ordered, eligible decisions."""
    if window_size < 1:
        raise ValueError("window_size must be positive")
    verified = _eligible_decisions(decisions)
    if not verified:
        return None
    # When fewer than window_size verified decisions exist, use all of them.
    # This is the bootstrap/warm-up case; the gate may return calibration state.
    recent = verified[-window_size:] if len(verified) > window_size else verified
    return sum(_is_correct_decision(row) for row in recent) / len(recent)


def _sort_decisions_chronological(
    decisions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return decisions oldest first by canonical timestamp and stable ID."""
    rows = [dict(row) for row in decisions]
    return cast(list[dict[str, Any]], chronological_decisions(rows))


@runtime_checkable
class _DecisionCountStore(Protocol):
    def count_verified(self, domain: str) -> int:
        ...

    def count_verified_decisions(self, domain: str) -> int:
        ...

    def count_correct(self, domain: str) -> int:
        ...


@runtime_checkable
class _VerifiedDecisionStore(_DecisionCountStore, Protocol):
    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        ...


@runtime_checkable
class _ConservationStore(_DecisionCountStore, Protocol):
    def count_categories_with_n(self, domain: str, n: int = 1) -> int:
        ...


class ConservationMetrics(TypedDict):
    status: str
    alpha: float
    q: float
    V: int
    theta_min: float
    product: float
    categories_total: int
    categories_with_data: int
    baseline_product: float
    relative_threshold: float
    complacency_flag: str


def _state_verified_decisions(
    state: Any,
    *,
    domain: str,
) -> list[dict[str, Any]] | None:
    """Read and canonically order the provider's verified-decision projection."""
    if isinstance(state, dict):
        candidate = state.get("verified_decisions")
        if isinstance(candidate, (list, tuple)):
            return _sort_decisions_chronological(
                [row for row in candidate if isinstance(row, Mapping)]
            )
        return None
    store = state_store(state)
    if not isinstance(store, _VerifiedDecisionStore):
        return None
    return _sort_decisions_chronological(store.get_verified_decisions(domain))


def _categories_with_data_from_decisions(
    decisions: Sequence[Mapping[str, Any]],
) -> int:
    return len(
        {
            str(row.get("category"))
            for row in decisions
            if row.get("category") not in (None, "")
        }
    )


def compute_conservation_status_payload(domain: str, state: Any) -> dict[str, Any]:
    counts = state_counts(state, domain=domain)
    categories_total = category_count(state, domain=domain)
    store = state_store(state)
    ordered_decisions = _state_verified_decisions(state, domain=domain)
    eligible_decisions = (
        _eligible_decisions(ordered_decisions)
        if ordered_decisions is not None
        else None
    )
    if eligible_decisions is not None:
        counts = {
            **counts,
            "verified_count": len(eligible_decisions),
            "correct_count": sum(
                _is_correct_decision(row) for row in eligible_decisions
            ),
            "total_decisions": len(eligible_decisions),
        }
    if isinstance(state, dict):
        categories_total = int(
            state.get("total_categories")
            or state.get("categories_total")
            or categories_total
        )
        categories_with_data = (
            _categories_with_data_from_decisions(eligible_decisions)
            if eligible_decisions is not None
            else int(
                state.get("categories_with_data")
                or state.get("categories_with_data_count")
                or 0
            )
        )
    else:
        categories_with_data = (
            _categories_with_data_from_decisions(eligible_decisions)
            if eligible_decisions is not None
            else count_categories_with_data(store, domain)
            if store is not None
            else 0
        )
    verified_count = int(counts["verified_count"])
    correct_count = int(counts["correct_count"])
    alpha = (
        float(categories_with_data / categories_total)
        if categories_total > 0
        else 0.0
    )
    rolling_q = _rolling_q(ordered_decisions) if ordered_decisions is not None else None
    q = float(rolling_q) if rolling_q is not None else 0.0
    theta_for_check = compute_theta_min(alpha, float(verified_count))
    check = check_conservation(
        alpha=alpha,
        q=q,
        V=float(verified_count),
        theta_min=theta_for_check,
    )
    baseline_q = _baseline_q(state, q)
    relative_trigger_ratio = 0.7
    relative_trigger = relative_trigger_ratio * baseline_q
    signal = _finite_or_none(check.signal)
    theta_min = _finite_or_none(check.theta_min)
    headroom = (
        signal - theta_min
        if signal is not None and theta_min is not None
        else None
    )
    status_payload = check_payload(check)
    conservation_mode = (
        "cold_start"
        if verified_count <= 0
        else "unavailable"
        if rolling_q is None
        else "bootstrap"
        if verified_count < 10
        else "normal"
    )
    payload = {
        "engine": ENGINE_STATUS,
        "domain": domain,
        **counts,
        **status_payload,
        # CC-4 panel fields.  Keep the conservation V explicit and use
        # additive headroom (signal - floor); the what-if route retains the
        # legacy ratio returned directly by check_payload().
        "alpha": alpha,
        "q": q,
        "V": verified_count,
        "headroom": headroom,
        "baseline": baseline_q,
        "baseline_q": baseline_q,
        "conservation_mode": conservation_mode,
        "conservation_applicable": conservation_mode == "normal",
        "relative_trigger": relative_trigger,
        "relative_trigger_ratio": relative_trigger_ratio,
        "categories_total": int(categories_total),
        "total_categories": int(categories_total),
        "categories_with_data": int(categories_with_data),
        "reason": _conservation_reason(
            status=str(check.status),
            alpha=alpha,
            q=q,
            V=verified_count,
            signal=signal,
            theta_min=theta_min,
            headroom=headroom,
            baseline_q=baseline_q,
            relative_trigger=relative_trigger,
            quality_available=rolling_q is not None,
        ),
    }
    adjuster = getattr(state, "conservation_status_adjuster", None)
    if callable(adjuster):
        return adjuster(payload)
    return payload


def _baseline_q(state: Any, current_q: float) -> float:
    """Resolve an independent quality baseline for G-REL.

    A current-window accuracy is never used as its own baseline.  When at
    least 200 verified outcomes are available, the first 200 outcomes in the
    rolling 400-outcome window provide the comparison baseline.  During
    bootstrap, an explicit configured baseline is preferred and 0.5 is the
    labeled default.
    """

    del current_q  # The current value must not become a self-comparison.

    outcomes: list[Any] = []
    if isinstance(state, dict):
        for key in ("verified_outcomes", "recent_outcomes", "outcomes"):
            candidate = state.get(key)
            if isinstance(candidate, (list, tuple)):
                outcomes = list(candidate)
                break
    else:
        store = getattr(state, "graph_store", None) or getattr(state, "_graph_store", None)
        try:
            getter = store.get_verified_decisions if store is not None else None
        except AttributeError:
            getter = None
        if callable(getter):
            domain = str(getattr(state, "domain", "") or getattr(store, "domain", ""))
            try:
                outcomes = list(getter(domain))
            except TypeError:
                outcomes = list(getter())

    if len(outcomes) >= 200:
        window = outcomes[-400:]
        baseline_window = window[:200]
        correct = 0
        for outcome in baseline_window:
            if isinstance(outcome, dict):
                value = outcome.get("is_correct", outcome.get("correct"))
            else:
                value = outcome
            correct += int(bool(value))
        return float(correct / len(baseline_window))

    candidates: list[Any] = []
    if isinstance(state, dict):
        candidates.extend(
            [
                state.get("baseline_q"),
                state.get("baseline"),
                state.get("baseline_accuracy"),
                state.get("domain_baseline"),
            ]
        )
    else:
        candidates.extend([
            getattr(state, "baseline_q", None),
            getattr(state, "baseline", None),
            getattr(state, "baseline_accuracy", None),
            getattr(getattr(state, "_preset", None), "baseline_accuracy", None),
        ])
    for candidate in candidates:
        try:
            value = float(candidate)
        except (TypeError, ValueError):
            continue
        if 0.0 <= value <= 1.0:
            return value
    return 0.5


def _conservation_reason(
    *,
    status: str,
    alpha: float,
    q: float,
    V: int,
    signal: float | None,
    theta_min: float | None,
    headroom: float | None,
    baseline_q: float,
    relative_trigger: float,
    quality_available: bool,
) -> str:
    """Return a plain-language, auditable explanation of the gate state."""

    if V <= 0 or signal is None or theta_min is None:
        return "No verified decisions are available; conservation is in explicit COLD_START bootstrap mode."
    if not quality_available:
        return (
            "Ordered verified decisions are unavailable for the rolling 400-decision "
            "quality window; conservation is unavailable and remains fail-closed."
        )
    relation = "exceeds" if signal > theta_min else "meets" if signal == theta_min else "is below"
    quality_relation = "above" if q >= relative_trigger else "below"
    return (
        f"Signal {signal:.2f} {relation} theta_min {theta_min:.4f} with "
        f"headroom {headroom or 0.0:.2f}. Accuracy {q * 100:.1f}% is "
        f"{quality_relation} 70% of baseline ({baseline_q * 100:.1f}%). "
        f"Status is {status} with α={alpha:.2f} across {V} verified decisions."
    )


def compute_conservation_metrics(
    state: Any, domain: str | None = None
) -> ConservationMetrics:
    store = state_store(state)
    if store is None:
        raise RuntimeError("conservation metrics require a graph store")
    effective_domain = str(domain or store_domain(store, ""))
    if not effective_domain:
        raise RuntimeError("conservation metrics require a domain")

    counts = state_counts(state, domain=effective_domain)
    categories_total = category_count(state, domain=effective_domain)
    ordered_decisions = _state_verified_decisions(state, domain=effective_domain)
    eligible_decisions = (
        _eligible_decisions(ordered_decisions)
        if ordered_decisions is not None
        else None
    )
    if eligible_decisions is not None:
        counts = {
            **counts,
            "verified_count": len(eligible_decisions),
            "correct_count": sum(
                _is_correct_decision(row) for row in eligible_decisions
            ),
            "total_decisions": len(eligible_decisions),
        }
        categories_with_data = _categories_with_data_from_decisions(
            eligible_decisions
        )
    else:
        categories_with_data = count_categories_with_data(store, effective_domain)

    verified_count = int(counts["verified_count"])
    correct_count = int(counts["correct_count"])
    total_decisions = int(counts["total_decisions"])
    if total_decisions <= 0 or verified_count <= 0:
        alpha = 0.0
        q = 0.0
        V = 0
        theta_min = float("inf")
        check = conservation_status(
            verified_count=verified_count,
            correct_count=correct_count,
            total_decisions=total_decisions,
            penalty_ratio=float(counts["penalty_ratio"]),
            categories_with_data=categories_with_data,
            total_categories=categories_total,
        )
    else:
        alpha = categories_with_data / categories_total if categories_total > 0 else 0.0
        rolling_q = _rolling_q(ordered_decisions) if ordered_decisions is not None else None
        if rolling_q is None:
            raise RuntimeError(
                "rolling conservation quality requires canonically ordered "
                "verified decisions"
            )
        q = rolling_q
        V = verified_count
        if alpha == 0.0:
            # No category has reached the configured coverage threshold yet.
            # This is a valid calibrating state: persist it, but keep the gate
            # closed until category coverage becomes positive.
            theta_min = float(compute_theta_min(1.0, float(V)))
            return {
                "status": "CALIBRATING",
                "alpha": 0.0,
                "q": float(q),
                "V": int(V),
                "theta_min": theta_min,
                "product": 0.0,
                "categories_total": int(categories_total),
                "categories_with_data": 0,
                "baseline_product": L5_BASELINE_PRODUCT_FALLBACK,
                "relative_threshold": 0.7 * L5_BASELINE_PRODUCT_FALLBACK,
                "complacency_flag": "false",
            }
        theta_min = compute_theta_min(alpha, float(V))
        check = check_conservation(alpha, q, float(V), theta_min)

    baseline_product = L5_BASELINE_PRODUCT_FALLBACK
    return {
        "status": str(check.status),
        "alpha": float(alpha),
        "q": float(q),
        "V": int(V),
        "theta_min": float(check.theta_min),
        "product": float(check.signal),
        "categories_total": int(categories_total),
        "categories_with_data": int(categories_with_data),
        "baseline_product": baseline_product,
        "relative_threshold": 0.7 * baseline_product,
        "complacency_flag": "false",
    }


def state_counts(state: Any, domain: str | None = None) -> dict[str, Any]:
    if isinstance(state, dict):
        verified = max(int(state.get("verified_count") or 0), 0)
        correct = max(int(state.get("correct_count") or 0), 0)
        # Preserve the status endpoint contract: conservation V is verified-only.
        total = verified
        penalty = _positive_float(state.get("penalty_ratio"), default=1.0)
        return {
            "verified_count": verified,
            "correct_count": correct,
            "total_decisions": total,
            "penalty_ratio": penalty,
        }

    store = state_store(state)
    if store is None:
        verified = int(getattr(state, "verified_count", 0) or 0)
        correct = int(getattr(state, "correct_count", 0) or 0)
        total = int(getattr(state, "total_decisions", verified) or verified)
    else:
        effective_domain = str(domain or store_domain(store, getattr(state, "domain", "")))
        verified = int(store.count_verified(effective_domain))
        correct = int(store.count_correct(effective_domain))
        total = int(store.count_verified_decisions(effective_domain))

    preset = preset_for_state(state)
    penalty = _positive_float(
        getattr(state, "penalty_ratio", None)
        or getattr(preset, "penalty_ratio", None),
        default=1.0,
    )
    return {
        "verified_count": verified,
        "correct_count": correct,
        "total_decisions": total,
        "penalty_ratio": penalty,
    }


def check_payload(check: Any) -> dict[str, Any]:
    return {
        "signal": float(check.signal),
        "theta_min": _finite_or_none(check.theta_min),
        "headroom": _finite_or_none(check.headroom),
        "status": str(check.status),
        "passed": bool(check.passed),
    }


def state_store(state: Any) -> _DecisionCountStore | None:
    if isinstance(state, dict):
        return None
    if isinstance(state, _DecisionCountStore):
        return state
    candidate = getattr(state, "graph_store", None) or getattr(state, "_graph_store", None)
    if candidate is None:
        return None
    if not isinstance(candidate, _DecisionCountStore):
        raise RuntimeError("state graph store does not satisfy the Decision count contract")
    return cast(_DecisionCountStore, candidate)


def store_domain(store: Any, fallback: str) -> str:
    return str(getattr(store, "domain", fallback) or fallback)


def category_count(state: Any, domain: str | None = None) -> int:
    preset = preset_for_state(state)
    if preset is None and domain:
        from copilot_sdk.scoring.presets import PRESET_REGISTRY

        preset_cls = PRESET_REGISTRY.get(str(domain))
        preset = preset_cls() if preset_cls is not None else None
    shape = getattr(preset, "shape", None)
    value = getattr(shape, "n_categories", None)
    if value is None:
        names = getattr(shape, "category_names", None)
        if names is not None:
            value = len(tuple(names))
    if value is None:
        raise RuntimeError("conservation metrics require domain category count")
    count = int(value)
    if count < 0:
        raise ValueError("category count must be non-negative")
    return count


def preset_for_state(state: Any) -> Any | None:
    preset = getattr(state, "_preset", None) or getattr(state, "preset", None)
    if preset is not None:
        return preset
    preset_name = getattr(state, "_preset_name", None)
    if not preset_name:
        return None
    from copilot_sdk.scoring.presets import PRESET_REGISTRY

    preset_cls = PRESET_REGISTRY.get(str(preset_name))
    return preset_cls() if preset_cls is not None else None


def count_categories_with_data(store: _ConservationStore, domain: str) -> int:
    counter = getattr(store, "count_categories_with_n", None)
    if not callable(counter):
        # Older GraphStore-compatible adapters expose decision counts but not
        # category coverage. Treat coverage as zero rather than failing the
        # status panel; the resulting state remains conservatively RED.
        return 0
    value = int(counter(domain, 1))
    if value < 0:
        raise ValueError("categories_with_data must be non-negative")
    return value


def _positive_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _finite_or_none(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed == float("inf") or parsed == float("-inf"):
        return None
    return parsed
