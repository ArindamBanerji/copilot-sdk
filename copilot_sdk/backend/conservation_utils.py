from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable


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


def compute_conservation_status_payload(domain: str, state: Any) -> dict[str, Any]:
    counts = state_counts(state, domain=domain)
    check = conservation_status(
        verified_count=counts["verified_count"],
        correct_count=counts["correct_count"],
        total_decisions=counts["total_decisions"],
        penalty_ratio=counts["penalty_ratio"],
    )
    payload = {
        "engine": ENGINE_STATUS,
        "domain": domain,
        **counts,
        **check_payload(check),
    }
    adjuster = getattr(state, "conservation_status_adjuster", None)
    if callable(adjuster):
        return adjuster(payload)
    return payload


def compute_conservation_metrics(state: Any, domain: str | None = None) -> dict[str, object]:
    store = state_store(state)
    if store is None:
        raise RuntimeError("conservation metrics require a graph store")
    effective_domain = str(domain or store_domain(store, ""))
    if not effective_domain:
        raise RuntimeError("conservation metrics require a domain")

    counts = state_counts(state, domain=effective_domain)
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
        alpha = categories_with_data / categories_total if categories_total > 0 else 0.0
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


def count_categories_with_data(store: _ConservationStore, domain: str) -> int:
    value = int(store.count_categories_with_n(domain, 1))
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
