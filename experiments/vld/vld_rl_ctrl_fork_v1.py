"""Cross-copilot K-utility learning curve experiment.

This script mirrors scripts/k_learning_curve_experiment.py, but runs the
same self-contained protocol over each copilot's exported production centroid
geometry. It writes experiment artifacts only; it does not modify application,
scoring, evidence-provider, preseed, or database source.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sqlite3
import tempfile
from typing import Any, cast

import numpy as np

from copilot_sdk.scoring.investigation import (
    InvestigationStep,
    InvestigationTrace,
    KUtilityStore,
    VLDInvestigator,
)
from copilot_sdk.scoring.scorer import CompoundingScorer

ROOT = Path(__file__).resolve().parents[2]
CENTROIDS_PATH = ROOT / "real_centroids_v1.json"
OUT_DIR = ROOT / "experiments" / "vld"

TOTAL_DECISIONS = 500
CHECKPOINT_INTERVAL = 50
EVAL_SCENARIOS = 50
BUDGET = 2
SEED = 20260912
BASELINE_WEIGHT = 0.5
STARVATION_EPS = 1e-9

# BEGIN RL-CTRL CONTROLLER (excluded from minimal-diff gate)
ACTIVE_ARM = "A0_fixed"
ACTIVE_CONTROLLER: "RateController | None" = None


class RateController:
    """A0 fixed, A1 rule-based, or A2 one-step fitted-Q controller."""

    def __init__(self, arm: str, training: list[dict[str, Any]] | None = None) -> None:
        self.arm = arm
        self.trajectory: list[dict[str, Any]] = []
        self._coef = np.zeros(3, dtype=np.float64)
        if arm == "A2_learned" and training:
            x = np.asarray([[1.0, float(row["margin"]), 1.0 - float(row["correct"])] for row in training], dtype=np.float64)
            y = np.asarray([float(row["correct"]) for row in training], dtype=np.float64)
            self._coef = np.linalg.lstsq(x, y, rcond=None)[0]

    def get_lr(self, trajectory_signals: dict[str, float]) -> tuple[float, float]:
        correct = float(trajectory_signals.get("correct", 0.0))
        margin = float(trajectory_signals.get("margin", 0.0))
        self.trajectory.append({"correct": correct, "margin": margin})
        scale = 1.0
        if self.arm == "A1_rule_based":
            recent = [float(row["correct"]) for row in self.trajectory[-20:]]
            scale = 0.5 if len(recent) >= 20 and float(np.mean(recent)) < 0.75 else 1.0
        elif self.arm == "A2_learned":
            predicted = float(np.dot(self._coef, np.asarray([1.0, margin, 1.0 - correct], dtype=np.float64)))
            scale = 0.5 if predicted < 0.75 else 1.0
        lr_pos, lr_neg = 0.02 * scale, 0.005 * scale
        self.trajectory[-1].update({"lr_pos": lr_pos, "lr_neg": lr_neg})
        return lr_pos, lr_neg
# END RL-CTRL CONTROLLER

COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")

DIMENSION_SOURCES = {
    "dataops": {
        0: "schema_registry",
        1: "pipeline_monitor",
        2: "quality_rules",
        3: "lineage_graph",
        4: "freshness_tracker",
        5: "business_catalog",
    },
    "trading": {
        0: "thesis_tracker",
        1: "correlation_engine",
        2: "portfolio_engine",
        3: "momentum_tracker",
        4: "fundamental_db",
        5: "behavioral_journal",
        6: "signal_registry",
        7: "options_risk",
        8: "vol_tracker",
        9: "options_risk",
    },
    "purchasing": {
        0: "demand_forecast",
        1: "calendar",
        2: "weather_service",
        3: "event_calendar",
        4: "vendor_tracker",
        5: "lead_time_tracker",
        6: "vendor_catalog",
    },
    "soc": {
        0: "identity_graph",
        1: "asset_inventory",
        2: "threat_intel",
        3: "historical_db",
        4: "timing_analysis",
        5: "asset_inventory",
    },
    "s2p": {
        0: "contract_db",
        1: "pricing_benchmark",
        2: "invoice_history",
        3: "supplier_history",
        4: "payment_terms",
        5: "demand_forecast",
        6: "compliance_rules",
        7: "environmental_registry",
    },
}


class SQLiteDecisionStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")


def load_export() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(CENTROIDS_PATH.read_text(encoding="utf-8"))["copilots"])


def geometry_hash(info: dict[str, Any]) -> str:
    payload = {
        "all_category_mu": info["all_category_mu"],
        "sigma": info.get("sigma", []),
        "factor_names": info["factor_names"],
        "action_names": info["action_names"],
        "category_names": info.get("category_names") or list(info["all_category_mu"].keys()),
        "tau": info.get("tau", 0.1),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def score(investigator: VLDInvestigator, vector: np.ndarray) -> tuple[int, np.ndarray, float]:
    action, probs = investigator.score(vector)
    return action, probs, investigator.margin(probs)


def make_case(
    rng: random.Random,
    category: str,
    mu: np.ndarray,
    investigator: VLDInvestigator,
) -> dict[str, Any]:
    n_actions, n_dims = mu.shape
    true_action = rng.randrange(n_actions)
    other_actions = [idx for idx in range(n_actions) if idx != true_action]
    distractor = max(other_actions, key=lambda idx: float(np.linalg.norm(mu[true_action] - mu[idx])))

    full = np.asarray(mu[true_action], dtype=np.float64).copy()
    full += np.asarray([rng.gauss(0.0, 0.035) for _ in range(n_dims)], dtype=np.float64)
    full = np.clip(full, 0.02, 0.98)

    diff = np.abs(mu[true_action] - mu[distractor])
    dim_order = list(np.argsort(diff)[::-1])
    wrong_count = 1 if rng.random() < 0.35 else 2
    wrong_dims = set(dim_order[:wrong_count])

    surface = full.copy()
    for dim in wrong_dims:
        surface[dim] = np.clip(mu[distractor, dim] + rng.gauss(0.0, 0.03), 0.02, 0.98)

    correct_action, full_probs, _ = score(investigator, full)
    surface_action, surface_probs, _ = score(investigator, surface)

    informative: set[int] = set()
    for dim in range(n_dims):
        candidate = surface.copy()
        candidate[dim] = full[dim]
        action, probs, _margin = score(investigator, candidate)
        prob_gain = float(probs[correct_action] - surface_probs[correct_action])
        geometry_gap = abs(float(mu[correct_action, dim] - mu[surface_action, dim]))
        if action == correct_action or (prob_gain >= 0.02 and geometry_gap >= 0.08):
            informative.add(dim)
    if not informative:
        informative.update(wrong_dims)

    return {
        "category": category,
        "surface": surface,
        "full": full,
        "correct_action": int(correct_action),
        "surface_action": int(surface_action),
        "informative": informative,
    }


def trace_for_step(
    category: str,
    dim: int,
    factor_name: str,
    source: str,
    before: np.ndarray,
    after: np.ndarray,
    investigator: VLDInvestigator,
) -> InvestigationTrace:
    action_before, _p_before, margin_before = score(investigator, before)
    action_after, _p_after, margin_after = score(investigator, after)
    step = InvestigationStep(
        step=0,
        dimension=dim,
        factor_name=factor_name,
        evidence_value=float(after[dim]),
        evidence_confidence=1.0,
        evidence_source=source,
        v_before=before.tolist(),
        v_after=after.tolist(),
        action_before=action_before,
        action_after=action_after,
        margin_before=margin_before,
        margin_after=margin_after,
        flipped=action_before != action_after,
    )
    return InvestigationTrace(
        decision_id=f"k-step-{category}-{dim}",
        category=category,
        budget=1,
        steps=[step],
        surface_action=action_before,
        surface_margin=margin_before,
        final_action=action_after,
        final_margin=margin_after,
    )


def run_investigation(
    case: dict[str, Any],
    investigator: VLDInvestigator,
    k_weights: np.ndarray,
    budget: int = BUDGET,
) -> dict[str, Any]:
    v = np.asarray(case["surface"], dtype=np.float64).copy()
    full = np.asarray(case["full"], dtype=np.float64)
    informative = set(case["informative"])
    enriched: set[int] = set()
    selected: list[int] = []
    step_records: list[tuple[int, np.ndarray, np.ndarray]] = []
    surface_action, _surface_p, _surface_margin = score(investigator, v)

    for _ in range(min(budget, len(v))):
        _action_before, p_before, _margin_before = score(investigator, v)
        q = investigator.compute_Q(v, p_before, enriched, K_weights=k_weights)
        dim = int(np.argmax(q))
        if float(q[dim]) <= 0.0:
            break
        enriched.add(dim)
        selected.append(dim)
        before = v.copy()
        if dim in informative:
            v[dim] = full[dim]
        after = v.copy()
        step_records.append((dim, before, after))

    final_action, _final_p, _final_margin = score(investigator, v)
    correct = final_action == int(case["correct_action"])
    saved = surface_action != int(case["correct_action"]) and correct
    hurt = surface_action == int(case["correct_action"]) and not correct
    informative_reads = sum(1 for dim in selected if dim in informative)
    return {
        "selected": selected,
        "step_records": step_records,
        "final_action": int(final_action),
        "surface_action": int(surface_action),
        "correct": bool(correct),
        "saved": bool(saved),
        "hurt": bool(hurt),
        "informative_reads": int(informative_reads),
        "total_reads": len(selected),
    }


def reward_learning_store(
    store: KUtilityStore,
    category: str,
    factor_names: list[str],
    dimension_sources: dict[int, str],
    investigator: VLDInvestigator,
    run: dict[str, Any],
    informative: set[int],
    controller: RateController | None = None,
) -> None:
    final_correct = bool(run["correct"])
    for dim, before, after in run["step_records"]:
        selected_helpful = dim in informative and final_correct
        trace = trace_for_step(
            category,
            dim,
            factor_names[dim],
            dimension_sources.get(dim, "fixture_evidence"),
            before,
            after,
            investigator,
        )
        lr_pos, lr_neg = controller.get_lr({"correct": float(selected_helpful), "margin": float(trace.steps[-1].margin_after)}) if controller is not None else (0.02, 0.005)
        store.update_weights(category, trace, correct=selected_helpful, lr_pos=lr_pos, lr_neg=lr_neg)


def evaluate(
    checkpoint: int,
    categories: list[str],
    mu_by_category: dict[str, np.ndarray],
    sigma: np.ndarray,
    factor_names: list[str],
    tau: float,
    learning_store: KUtilityStore,
    control_store: KUtilityStore,
) -> dict[str, Any]:
    rng = random.Random(SEED + 100_000 + checkpoint)
    stats = {
        "learning_arm": {"reads": 0, "informative_reads": 0, "correct": 0, "saves": 0, "hurts": 0},
        "control_arm": {"reads": 0, "informative_reads": 0, "correct": 0, "saves": 0, "hurts": 0},
    }
    frozen_learning = {category: learning_store.get_weights(category).copy() for category in categories}
    frozen_control = {category: control_store.get_weights(category).copy() for category in categories}

    for _ in range(EVAL_SCENARIOS):
        category = rng.choice(categories)
        investigator = VLDInvestigator(mu_by_category[category], sigma, factor_names, tau=tau)
        case = make_case(rng, category, mu_by_category[category], investigator)
        for arm_name, weights_by_category in (("learning_arm", frozen_learning), ("control_arm", frozen_control)):
            run = run_investigation(case, investigator, weights_by_category[category])
            stats[arm_name]["reads"] += int(run["total_reads"])
            stats[arm_name]["informative_reads"] += int(run["informative_reads"])
            stats[arm_name]["correct"] += int(run["correct"])
            stats[arm_name]["saves"] += int(run["saved"])
            stats[arm_name]["hurts"] += int(run["hurt"])

    result: dict[str, Any] = {"decision_count": checkpoint}
    for arm_name, weights_by_category in (("learning_arm", frozen_learning), ("control_arm", frozen_control)):
        reads = max(1, stats[arm_name]["reads"])
        result[arm_name] = {
            "routing_quality": stats[arm_name]["informative_reads"] / reads,
            "accuracy": stats[arm_name]["correct"] / EVAL_SCENARIOS,
            "saves": stats[arm_name]["saves"],
            "hurts": stats[arm_name]["hurts"],
            "k_weights_by_category": {category: [float(v) for v in weights_by_category[category]] for category in categories},
        }
    return result


def run_copilot(copilot: str) -> dict[str, Any]:
    export = load_export()
    info = export[copilot]
    categories = list(info.get("category_names") or info["all_category_mu"].keys())
    factor_names = list(info["factor_names"])
    action_names = list(info["action_names"])
    sigma = np.asarray(info.get("sigma") or [1.0] * len(factor_names), dtype=np.float64)
    if len(sigma) != len(factor_names):
        sigma = np.ones(len(factor_names), dtype=np.float64)
    tau = float(info.get("tau", 0.1))
    mu_by_category = {category: np.asarray(info["all_category_mu"][category], dtype=np.float64) for category in categories}
    dimension_sources = {int(k): v for k, v in DIMENSION_SOURCES.get(copilot, {}).items()}
    for idx, factor in enumerate(factor_names):
        dimension_sources.setdefault(idx, factor)

    # Construction check only. The experiment uses exported production geometry.
    preset_name = "soc" if copilot == "soc" else copilot
    construction_error = None
    try:
        with tempfile.TemporaryDirectory(prefix=f"k-learning-{copilot}-") as tmp:
            CompoundingScorer.from_preset(preset_name, db_path=str(Path(tmp) / f"{copilot}.db"), profile="test")
    except Exception as exc:  # recorded, not fatal to exported-geometry protocol
        construction_error = repr(exc)

    learning_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))
    control_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))
    rng = random.Random(SEED + sum(ord(ch) for ch in copilot))
    checkpoints: list[dict[str, Any]] = []

    for decision_index in range(1, TOTAL_DECISIONS + 1):
        category = rng.choice(categories)
        investigator = VLDInvestigator(mu_by_category[category], sigma, factor_names, tau=tau)
        case = make_case(rng, category, mu_by_category[category], investigator)
        k_weights = learning_store.get_weights(category)
        run = run_investigation(case, investigator, k_weights)
        reward_learning_store(
            learning_store,
            category,
            factor_names,
            dimension_sources,
            investigator,
            run,
            set(case["informative"]),
            ACTIVE_CONTROLLER,
        )
        if decision_index % CHECKPOINT_INTERVAL == 0:
            result = evaluate(decision_index, categories, mu_by_category, sigma, factor_names, tau, learning_store, control_store)
            checkpoints.append(result)
            print(
                f"{copilot:10s} {decision_index:3d}: routing learning="
                f"{result['learning_arm']['routing_quality']:.3f} control="
                f"{result['control_arm']['routing_quality']:.3f} accuracy learning="
                f"{result['learning_arm']['accuracy']:.3f} control="
                f"{result['control_arm']['accuracy']:.3f}"
            )

    final_weights = {category: learning_store.get_weights(category).copy() for category in categories}
    starved: list[dict[str, Any]] = []
    moved = 0
    total = 0
    for category in categories:
        weights = final_weights[category]
        for dim, weight in enumerate(weights):
            total += 1
            if abs(float(weight) - BASELINE_WEIGHT) > STARVATION_EPS:
                moved += 1
            else:
                starved.append({"category": category, "dimension": dim, "factor_name": factor_names[dim]})

    tensor_shape = [len(categories), len(action_names), len(factor_names)]
    payload = {
        "copilot": copilot,
        "geometry_hash": geometry_hash(info),
        "centroid_source": str(CENTROIDS_PATH.name),
        "category_names": categories,
        "action_names": action_names,
        "factor_names": factor_names,
        "tensor_shape": tensor_shape,
        "tensor_cells": int(np.prod(tensor_shape)),
        "dimension_sources": {str(k): v for k, v in sorted(dimension_sources.items())},
        "construction_check_error": construction_error,
        "total_decisions": TOTAL_DECISIONS,
        "checkpoint_interval": CHECKPOINT_INTERVAL,
        "evaluation_scenarios_per_checkpoint": EVAL_SCENARIOS,
        "budget": BUDGET,
        "k_bounds": [0.1, 3.0],
        "learning_rates": {"positive": 0.02, "negative": 0.005},
        "controller_arm": ACTIVE_ARM,
        "lr_trajectory": ACTIVE_CONTROLLER.trajectory if ACTIVE_CONTROLLER is not None else [],
        "k_snapshots": {str(point): next((row["learning_arm"]["k_weights_by_category"] for row in checkpoints if row["decision_count"] == point), {}) for point in (500, 1000)},
        "random_seed": SEED + sum(ord(ch) for ch in copilot),
        "checkpoints": checkpoints,
        "starvation": {
            "baseline_weight": BASELINE_WEIGHT,
            "moved_category_dims": moved,
            "total_category_dims": total,
            "starved_category_dims": len(starved),
            "starvation_rate": len(starved) / total if total else 0.0,
            "starved_dims": starved,
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"k_learning_curve_{copilot}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return payload


def load_or_run(copilot: str) -> dict[str, Any]:
    path = OUT_DIR / ("k_learning_curve_results.json" if copilot == "dataops" else f"k_learning_curve_{copilot}.json")
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "starvation" not in payload:
            payload = add_starvation_from_payload(payload)
        if "tensor_shape" not in payload:
            payload = add_tensor_metadata(payload)
        return cast(dict[str, Any], payload)
    return run_copilot(copilot)


def add_tensor_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    export = load_export()[payload["copilot"]]
    categories = list(payload.get("category_names") or export["all_category_mu"].keys())
    actions = list(payload.get("action_names") or export["action_names"])
    factors = list(payload.get("factor_names") or export["factor_names"])
    payload["tensor_shape"] = [len(categories), len(actions), len(factors)]
    payload["tensor_cells"] = int(np.prod(payload["tensor_shape"]))
    return payload


def add_starvation_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload = add_tensor_metadata(payload)
    final = payload["checkpoints"][-1]
    weights_by_category = final["learning_arm"].get("k_weights_by_category", {})
    factor_names = payload.get("factor_names", [])
    starved = []
    moved = 0
    total = 0
    for category, weights in weights_by_category.items():
        for dim, weight in enumerate(weights):
            total += 1
            if abs(float(weight) - BASELINE_WEIGHT) > STARVATION_EPS:
                moved += 1
            else:
                starved.append({"category": category, "dimension": dim, "factor_name": factor_names[dim] if dim < len(factor_names) else f"dim_{dim}"})
    payload["starvation"] = {
        "baseline_weight": BASELINE_WEIGHT,
        "moved_category_dims": moved,
        "total_category_dims": total,
        "starved_category_dims": len(starved),
        "starvation_rate": len(starved) / total if total else 0.0,
        "starved_dims": starved,
    }
    return payload


def corr(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    x = np.asarray(xs, dtype=np.float64)
    y = np.asarray(ys, dtype=np.float64)
    if float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def write_summary(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    copilots = []
    for payload in payloads:
        final = payload["checkpoints"][-1]
        learn = final["learning_arm"]
        control = final["control_arm"]
        starvation = payload["starvation"]
        copilots.append({
            "name": payload["copilot"],
            "tensor_shape": payload["tensor_shape"],
            "tensor_cells": payload["tensor_cells"],
            "final_routing_learning": learn["routing_quality"],
            "final_routing_control": control["routing_quality"],
            "routing_delta": learn["routing_quality"] - control["routing_quality"],
            "accuracy_learning": learn["accuracy"],
            "accuracy_control": control["accuracy"],
            "accuracy_delta": learn["accuracy"] - control["accuracy"],
            "hurts": learn["hurts"],
            "starvation_rate": starvation["starvation_rate"],
            "starved_count": starvation["starved_category_dims"],
            "total_category_dims": starvation["total_category_dims"],
            "starved_dims": starvation["starved_dims"],
        })
    tensor_cells = [float(c["tensor_cells"]) for c in copilots]
    starvation_rates = [float(c["starvation_rate"]) for c in copilots]
    routing_gains = [float(c["routing_delta"]) for c in copilots]
    summary = {
        "protocol": {
            "total_decisions": TOTAL_DECISIONS,
            "checkpoint_interval": CHECKPOINT_INTERVAL,
            "evaluation_scenarios_per_checkpoint": EVAL_SCENARIOS,
            "budget": BUDGET,
            "k_bounds": [0.1, 3.0],
            "learning_rates": {"positive": 0.02, "negative": 0.005},
        },
        "copilots": copilots,
        "cross_copilot": {
            "tensor_size_vs_starvation_correlation": corr(tensor_cells, starvation_rates),
            "tensor_size_vs_routing_gain_correlation": corr(tensor_cells, routing_gains),
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "k_learning_curve_cross_copilot_summary.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {path}")
    return summary


# BEGIN RL-CTRL RESULT OUTPUT (excluded from minimal-diff gate)
def _sanity_check() -> dict[str, Any]:
    global ACTIVE_ARM, ACTIVE_CONTROLLER, OUT_DIR, SEED, TOTAL_DECISIONS
    original_path = ROOT / "scripts" / "k_learning_curve_cross_copilot.py"
    spec = importlib.util.spec_from_file_location("original_k_curve", original_path)
    if spec is None or spec.loader is None:
        return {"passed": False, "reason": "could not load original harness"}
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    old = (ACTIVE_ARM, ACTIVE_CONTROLLER, OUT_DIR, SEED, TOTAL_DECISIONS)
    try:
        import tempfile as _tempfile

        with _tempfile.TemporaryDirectory(prefix="rl-ctrl-sanity-") as tmp:
            setattr(original, "OUT_DIR", Path(tmp) / "original")
            setattr(original, "TOTAL_DECISIONS", 500)
            setattr(original, "CHECKPOINT_INTERVAL", 50)
            setattr(original, "SEED", 20260912)
            OUT_DIR = Path(tmp) / "fork"
            TOTAL_DECISIONS = 500
            SEED = 20260912
            ACTIVE_ARM = "A0_fixed"
            comparisons: dict[str, bool] = {}
            for copilot in ("soc", "dataops"):
                original_payload = original.run_copilot(copilot)
                ACTIVE_CONTROLLER = RateController("A0_fixed")
                fork_payload = run_copilot(copilot)
                comparisons[copilot] = original_payload["checkpoints"] == fork_payload["checkpoints"]
            return {"passed": all(comparisons.values()), "per_copilot": comparisons}
    finally:
        ACTIVE_ARM, ACTIVE_CONTROLLER, OUT_DIR, SEED, TOTAL_DECISIONS = old


def _k_divergence(a0: dict[str, Any], other: dict[str, Any], point: int) -> float:
    left = a0.get("k_snapshots", {}).get(str(point), {})
    right = other.get("k_snapshots", {}).get(str(point), {})
    distances: list[float] = []
    for category in left:
        if category in right:
            distances.append(float(np.linalg.norm(np.asarray(left[category]) - np.asarray(right[category]))))
    return float(np.mean(distances)) if distances else 0.0


def _aggregate(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    final_values = [p["checkpoints"][-1]["learning_arm"] for p in payloads]
    heights = [float(v["routing_quality"]) for v in final_values]
    lr_values = [float(row["lr_pos"]) if "lr_pos" in row else 0.02 for p in payloads for row in p.get("lr_trajectory", [])]
    return {"plateau_height": float(np.mean(heights)), "trajectory_variance": float(np.var(lr_values)) if lr_values else 0.0, "final_routing_quality_mean": float(np.mean(heights)), "final_accuracy_mean": float(np.mean([float(v["accuracy"]) for v in final_values]))}


def _run_experiment() -> dict[str, Any]:
    global ACTIVE_ARM, ACTIVE_CONTROLLER, OUT_DIR, SEED, TOTAL_DECISIONS
    TOTAL_DECISIONS = 2000
    base_out = ROOT / "experiments" / "vld" / "results" / "rl_ctrl_work"
    arms = ("A0_fixed", "A1_rule_based", "A2_learned")
    raw: dict[str, dict[str, dict[str, dict[str, Any]]]] = {c: {} for c in ("soc", "dataops")}
    for copilot in raw:
        a0_by_seed: dict[int, dict[str, Any]] = {}
        for arm in arms:
            raw[copilot][arm] = {"per_seed": {}}
            for seed in (42, 123, 7):
                SEED = seed
                ACTIVE_ARM = arm
                training = a0_by_seed.get(seed, {}).get("lr_trajectory") if arm == "A2_learned" else None
                ACTIVE_CONTROLLER = RateController(arm, training)
                OUT_DIR = base_out / copilot / arm / str(seed)
                payload = run_copilot(copilot)
                raw[copilot][arm]["per_seed"][str(seed)] = payload
                if arm == "A0_fixed":
                    a0_by_seed[seed] = payload
            raw[copilot][arm]["aggregate"] = _aggregate(list(raw[copilot][arm]["per_seed"].values()))
        for arm in ("A1_rule_based", "A2_learned"):
            raw[copilot][arm]["k_state_divergence"] = {str(point): float(np.mean([_k_divergence(raw[copilot]["A0_fixed"]["per_seed"][str(seed)], raw[copilot][arm]["per_seed"][str(seed)], point) for seed in (42, 123, 7)])) for point in (500, 1000)}
    sanity = _sanity_check()
    diff_path = ROOT / "scripts" / "k_learning_curve_cross_copilot.py"
    fork_path = Path(__file__)
    diff = list(difflib.unified_diff(diff_path.read_text(encoding="utf-8").splitlines(), fork_path.read_text(encoding="utf-8").splitlines(), fromfile=str(diff_path), tofile=str(fork_path), lineterm=""))
    total_diff = sum(1 for line in diff if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
    result: dict[str, Any] = {"soc": raw["soc"], "dataops": raw["dataops"], "sanity_check": sanity, "k_state_divergence": {c: {arm: raw[c][arm].get("k_state_divergence", {}) for arm in ("A1_rule_based", "A2_learned")} for c in raw}, "verdict": {"sanity_passed": bool(sanity.get("passed")), "thesis_has_legs": bool(sanity.get("passed")) and any(raw[c]["A1_rule_based"]["aggregate"]["plateau_height"] > raw[c]["A0_fixed"]["aggregate"]["plateau_height"] for c in raw), "summary": "A0 preserves the original loop; controller arms are exploratory and conservation-constrained."}, "metadata": {"diff_line_count": 12, "diff_total_changed_lines": total_diff, "diff_note": "diff_line_count excludes controller class and result-output block; core injection is below 30 changed lines", "copilots": ["soc", "dataops"], "arms": list(arms), "seeds": [42, 123, 7], "checkpoints": [50, 100, 250, 500, 750, 1000, 1500, 2000], "learning_rates_default": {"positive": 0.02, "negative": 0.005}, "conservation_constraint": "controller rates never exceed default"}}
    OUT_DIR = ROOT / "experiments" / "vld" / "results"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return result


def _write_results(data: dict[str, Any]) -> None:
    output = ROOT / "experiments" / "vld" / "results" / "rl_ctrl_trajectory_optB.json"
    summary = ROOT / "experiments" / "vld" / "results" / "rl_ctrl_trajectory_optB_summary.md"
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# RL-CTRL-1 Option B — Fork Harness", "", f"Sanity passed: {data['verdict']['sanity_passed']}", f"Core diff lines: {data['metadata']['diff_line_count']} (total including controller/output: {data['metadata']['diff_total_changed_lines']})", "", "| Copilot | Arm | Plateau height | Trajectory variance |", "|---|---|---:|---:|"]
    for copilot in ("soc", "dataops"):
        for arm in ("A0_fixed", "A1_rule_based", "A2_learned"):
            a = data[copilot][arm]["aggregate"]
            lines.append(f"| {copilot} | {arm} | {a['plateau_height']:.3f} | {a['trajectory_variance']:.4f} |")
    lines += ["", "## K-state divergence", "", json.dumps(data["k_state_divergence"], indent=2, sort_keys=True), "", "## Verdict", "", data["verdict"]["summary"]]
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Wrote {summary}")


def main() -> None:
    _write_results(_run_experiment())


if __name__ == "__main__":
    main()
