from __future__ import annotations

from pathlib import Path
from typing import Any


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


def compute_conservation_status_payload(domain: str, state: Any) -> dict[str, Any]:
    counts = state_counts(state)
    check = conservation_status(
        verified_count=counts["verified_count"],
        correct_count=counts["correct_count"],
        total_decisions=counts["total_decisions"],
        penalty_ratio=counts["penalty_ratio"],
    )
    return {
        "engine": ENGINE_STATUS,
        "domain": domain,
        **counts,
        **check_payload(check),
    }


def compute_conservation_metrics(state: Any, domain: str | None = None) -> dict[str, object]:
    store = state_store(state)
    if store is None:
        raise RuntimeError("conservation metrics require a graph store")
    effective_domain = str(domain or store_domain(store, ""))
    if not effective_domain:
        raise RuntimeError("conservation metrics require a domain")

    counts = state_counts(state)
    categories_total = category_count(state)
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
        )
    else:
        alpha = verified_count / total_decisions
        q = correct_count / verified_count
        V = verified_count
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


def state_counts(state: Any) -> dict[str, Any]:
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
        domain = store_domain(store, getattr(state, "domain", ""))
        verified = _call_count(store, "count_verified", domain)
        correct = _call_count(store, "count_correct", domain)
        total = _call_count_optional(store, "count_verified_decisions", domain)
        if total is None:
            total = max(verified, correct)

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


def state_store(state: Any) -> Any | None:
    if isinstance(state, dict):
        return None
    direct_count_verified = getattr(state, "count_verified", None)
    direct_count_correct = getattr(state, "count_correct", None)
    if callable(direct_count_verified) and callable(direct_count_correct):
        return state
    return getattr(state, "graph_store", None) or getattr(state, "_graph_store", None)


def store_domain(store: Any, fallback: str) -> str:
    return str(getattr(store, "domain", fallback) or fallback)


def category_count(state: Any) -> int:
    preset = preset_for_state(state)
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


def count_categories_with_data(store: Any, domain: str) -> int:
    method = getattr(store, "count_categories_with_n", None)
    if not callable(method):
        raise RuntimeError("categories_with_data unavailable")
    value = int(method(domain, 1))
    if value < 0:
        raise ValueError("categories_with_data must be non-negative")
    return value


def _call_count(store: Any, method_name: str, domain: str) -> int:
    method = getattr(store, method_name, None)
    if not callable(method):
        return 0
    try:
        return int(method(domain))
    except TypeError:
        return int(method())


def _call_count_optional(store: Any, method_name: str, domain: str) -> int | None:
    method = getattr(store, method_name, None)
    if not callable(method):
        return None
    try:
        return int(method(domain))
    except TypeError:
        return int(method())


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
