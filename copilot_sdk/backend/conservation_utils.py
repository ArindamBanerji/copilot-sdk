from __future__ import annotations

from pathlib import Path
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


ENGINE_STATUS = {"gae": "gae.calibration", "component": "conservation_status"}
ENGINE_WHAT_IF = {"gae": "gae.calibration", "component": "check_conservation"}
L5_BASELINE_PRODUCT_FALLBACK = 0.0


@runtime_checkable
class _DecisionCountStore(Protocol):
    def count_verified(self, domain: str) -> int:
        ...

    def count_verified_decisions(self, domain: str) -> int:
        ...

    def count_correct(self, domain: str) -> int:
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


def compute_conservation_status_payload(domain: str, state: Any) -> dict[str, Any]:
    counts = state_counts(state, domain=domain)
    categories_total = category_count(state, domain=domain)
    store = state_store(state)
    if isinstance(state, dict):
        categories_total = int(
            state.get("total_categories")
            or state.get("categories_total")
            or categories_total
        )
        categories_with_data = int(
            state.get("categories_with_data")
            or state.get("categories_with_data_count")
            or 0
        )
    else:
        categories_with_data = (
            count_categories_with_data(store, domain) if store is not None else 0
        )
    check = conservation_status(
        verified_count=counts["verified_count"],
        correct_count=counts["correct_count"],
        total_decisions=counts["total_decisions"],
        penalty_ratio=counts["penalty_ratio"],
        categories_with_data=categories_with_data,
        total_categories=categories_total,
    )
    verified_count = int(counts["verified_count"])
    correct_count = int(counts["correct_count"])
    alpha = (
        float(categories_with_data / categories_total)
        if categories_total > 0
        else 0.0
    )
    q = float(correct_count / verified_count) if verified_count > 0 else 0.0
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
    payload = {
        "engine": ENGINE_STATUS,
        "domain": domain,
        **counts,
        **check_payload(check),
        # CC-4 panel fields.  Keep the conservation V explicit and use
        # additive headroom (signal - floor); the what-if route retains the
        # legacy ratio returned directly by check_payload().
        "alpha": alpha,
        "q": q,
        "V": verified_count,
        "headroom": headroom,
        "baseline": baseline_q,
        "baseline_q": baseline_q,
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
        ),
    }
    adjuster = getattr(state, "conservation_status_adjuster", None)
    if callable(adjuster):
        return adjuster(payload)
    return payload


def _baseline_q(state: Any, current_q: float) -> float:
    """Resolve a supplied quality baseline, falling back to current quality."""

    candidates: list[Any] = []
    if isinstance(state, dict):
        candidates.extend([state.get("baseline_q"), state.get("baseline")])
    else:
        candidates.extend([
            getattr(state, "baseline_q", None),
            getattr(state, "baseline", None),
        ])
    for candidate in candidates:
        try:
            value = float(candidate)
        except (TypeError, ValueError):
            continue
        if 0.0 <= value <= 1.0:
            return value
    return float(max(0.0, min(1.0, current_q)))


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
) -> str:
    """Return a plain-language, auditable explanation of the gate state."""

    if V <= 0 or signal is None or theta_min is None:
        return "No verified decisions are available; conservation remains RED until evidence accumulates."
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
        q = correct_count / verified_count
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
