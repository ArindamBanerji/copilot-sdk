"""Extended DataOps K-utility learning curve to 2000 decisions.

This is an additive experiment artifact. It mirrors
scripts/k_learning_curve_experiment.py with a longer horizon and does not
modify scorer, investigation, router, app, fixture, or database source.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import sqlite3
import tempfile
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from copilot_sdk.scoring.investigation import (
    InvestigationStep,
    InvestigationTrace,
    KUtilityStore,
    VLDInvestigator,
)
from copilot_sdk.scoring.scorer import CompoundingScorer

ROOT = Path(__file__).resolve().parents[1]
CENTROIDS_PATH = ROOT / "real_centroids_v1.json"
RESULTS_PATH = ROOT / "experiments" / "vld" / "k_learning_curve_dataops_extended.json"
CHART_DIR = ROOT / "experiments" / "vld" / "charts"

TOTAL_DECISIONS = 2000
CHECKPOINT_INTERVAL = 100
EVAL_SCENARIOS = 50
BUDGET = 2
SEED = 20260912
BASELINE_WEIGHT = 0.5
STARVED_EPS = 0.02

DIMENSION_SOURCES = {
    0: "schema_registry",
    1: "pipeline_monitor",
    2: "quality_rules",
    3: "lineage_graph",
    4: "freshness_tracker",
    5: "business_catalog",
}


class SQLiteDecisionStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")


def load_dataops_geometry() -> dict[str, Any]:
    data = json.loads(CENTROIDS_PATH.read_text(encoding="utf-8"))
    return data["copilots"]["dataops"]


def geometry_hash(info: dict[str, Any]) -> str:
    payload = {
        "all_category_mu": info["all_category_mu"],
        "sigma": info["sigma"],
        "factor_names": info["factor_names"],
        "action_names": info["action_names"],
        "category_names": info["category_names"],
        "tau": info["tau"],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def score(investigator: VLDInvestigator, vector: np.ndarray) -> tuple[int, np.ndarray, float]:
    action, probs = investigator.score(vector)
    return action, probs, investigator.margin(probs)


def scenario(rng: random.Random, category: str, mu: np.ndarray, investigator: VLDInvestigator) -> dict[str, Any]:
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
        "correct_action": correct_action,
        "surface_action": surface_action,
        "informative": informative,
    }


def trace_for_step(category: str, dim: int, factor_name: str, before: np.ndarray, after: np.ndarray, investigator: VLDInvestigator) -> InvestigationTrace:
    action_before, _p_before, margin_before = score(investigator, before)
    action_after, _p_after, margin_after = score(investigator, after)
    step = InvestigationStep(
        step=0,
        dimension=dim,
        factor_name=factor_name,
        evidence_value=float(after[dim]),
        evidence_confidence=1.0,
        evidence_source=DIMENSION_SOURCES.get(dim, "dataops_fixture"),
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


def run_investigation(case: dict[str, Any], investigator: VLDInvestigator, factor_names: list[str], k_weights: np.ndarray, budget: int = BUDGET) -> dict[str, Any]:
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
        "final_action": final_action,
        "surface_action": surface_action,
        "correct": correct,
        "saved": saved,
        "hurt": hurt,
        "informative_reads": informative_reads,
        "total_reads": len(selected),
    }


def reward_learning_store(store: KUtilityStore, category: str, factor_names: list[str], investigator: VLDInvestigator, run: dict[str, Any], informative: set[int]) -> None:
    final_correct = bool(run["correct"])
    for dim, before, after in run["step_records"]:
        selected_helpful = dim in informative and final_correct
        trace = trace_for_step(category, dim, factor_names[dim], before, after, investigator)
        store.update_weights(category, trace, correct=selected_helpful)


def starvation_snapshot(weights_by_category: dict[str, list[float]]) -> dict[str, Any]:
    total = 0
    starved = 0
    starved_dims: list[dict[str, Any]] = []
    for category, weights in weights_by_category.items():
        for dim, weight in enumerate(weights):
            total += 1
            if abs(float(weight) - BASELINE_WEIGHT) < STARVED_EPS:
                starved += 1
                starved_dims.append({"category": category, "dimension": dim})
    return {
        "epsilon": STARVED_EPS,
        "baseline_weight": BASELINE_WEIGHT,
        "starved_category_dims": starved,
        "total_category_dims": total,
        "starvation_rate": starved / total if total else 0.0,
        "starved_dims": starved_dims,
    }


def evaluate(checkpoint: int, categories: list[str], mu_by_category: dict[str, np.ndarray], sigma: np.ndarray, factor_names: list[str], tau: float, learning_store: KUtilityStore, control_store: KUtilityStore) -> dict[str, Any]:
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
        case = scenario(rng, category, mu_by_category[category], investigator)
        for arm_name, weights_by_category in (("learning_arm", frozen_learning), ("control_arm", frozen_control)):
            run = run_investigation(case, investigator, factor_names, weights_by_category[category])
            stats[arm_name]["reads"] += int(run["total_reads"])
            stats[arm_name]["informative_reads"] += int(run["informative_reads"])
            stats[arm_name]["correct"] += int(run["correct"])
            stats[arm_name]["saves"] += int(run["saved"])
            stats[arm_name]["hurts"] += int(run["hurt"])

    result: dict[str, Any] = {"decision_count": checkpoint}
    for arm_name, weights_by_category in (("learning_arm", frozen_learning), ("control_arm", frozen_control)):
        reads = max(1, stats[arm_name]["reads"])
        k_weights = {category: [float(value) for value in weights_by_category[category]] for category in categories}
        result[arm_name] = {
            "routing_quality": stats[arm_name]["informative_reads"] / reads,
            "accuracy": stats[arm_name]["correct"] / EVAL_SCENARIOS,
            "saves": stats[arm_name]["saves"],
            "hurts": stats[arm_name]["hurts"],
            "k_weights_by_category": k_weights,
        }
        if arm_name == "learning_arm":
            result[arm_name]["starvation"] = starvation_snapshot(k_weights)
    return result


def generate_charts(payload: dict[str, Any]) -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    checkpoints = payload["checkpoints"]
    xs = [cp["decision_count"] for cp in checkpoints]
    learn = [cp["learning_arm"]["routing_quality"] for cp in checkpoints]
    control = [cp["control_arm"]["routing_quality"] for cp in checkpoints]
    starvation = [cp["learning_arm"]["starvation"]["starvation_rate"] for cp in checkpoints]

    plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False})

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(xs, learn, marker="o", label="learning")
    ax.plot(xs, control, marker="o", linestyle="--", label="control")
    ax.set_title("Extended DataOps K Routing")
    ax.set_xlabel("Decisions")
    ax.set_ylabel("Routing quality")
    ax.set_xlim(0, TOTAL_DECISIONS)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "pub_k_extended_routing.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(xs, starvation, marker="o", color="#B279A2")
    ax.set_title("Extended DataOps K Starvation")
    ax.set_xlabel("Decisions")
    ax.set_ylabel("Starvation rate")
    ax.set_xlim(0, TOTAL_DECISIONS)
    ax.set_ylim(0, max(0.1, max(starvation) * 1.2))
    fig.tight_layout()
    fig.savefig(CHART_DIR / "pub_k_extended_starvation_evolution.png", dpi=180)
    plt.close(fig)


def main() -> None:
    info = load_dataops_geometry()
    categories = list(info["category_names"])
    factor_names = list(info["factor_names"])
    action_names = list(info["action_names"])
    sigma = np.asarray(info["sigma"], dtype=np.float64)
    tau = float(info["tau"])
    mu_by_category = {category: np.asarray(info["all_category_mu"][category], dtype=np.float64) for category in categories}

    with tempfile.TemporaryDirectory(prefix="k-learning-extended-") as tmp:
        CompoundingScorer.from_preset("dataops", db_path=str(Path(tmp) / "dataops.db"), profile="test")

    learning_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))
    control_store = KUtilityStore(SQLiteDecisionStore(), d=len(factor_names))
    rng = random.Random(SEED)
    checkpoints: list[dict[str, Any]] = []

    for decision_index in range(1, TOTAL_DECISIONS + 1):
        category = rng.choice(categories)
        investigator = VLDInvestigator(mu_by_category[category], sigma, factor_names, tau=tau)
        case = scenario(rng, category, mu_by_category[category], investigator)
        k_weights = learning_store.get_weights(category)
        run = run_investigation(case, investigator, factor_names, k_weights)
        reward_learning_store(learning_store, category, factor_names, investigator, run, set(case["informative"]))

        if decision_index % CHECKPOINT_INTERVAL == 0:
            result = evaluate(decision_index, categories, mu_by_category, sigma, factor_names, tau, learning_store, control_store)
            checkpoints.append(result)
            print(
                f"{decision_index:4d}: routing learning={result['learning_arm']['routing_quality']:.3f} "
                f"control={result['control_arm']['routing_quality']:.3f} accuracy learning={result['learning_arm']['accuracy']:.3f} "
                f"control={result['control_arm']['accuracy']:.3f} starvation={result['learning_arm']['starvation']['starvation_rate']:.3f}"
            )

    payload = {
        "copilot": "dataops",
        "geometry_hash": geometry_hash(info),
        "centroid_source": str(CENTROIDS_PATH.name),
        "category_names": categories,
        "action_names": action_names,
        "factor_names": factor_names,
        "dimension_sources": {str(k): v for k, v in DIMENSION_SOURCES.items()},
        "total_decisions": TOTAL_DECISIONS,
        "checkpoint_interval": CHECKPOINT_INTERVAL,
        "evaluation_scenarios_per_checkpoint": EVAL_SCENARIOS,
        "budget": BUDGET,
        "k_bounds": [0.1, 3.0],
        "learning_rates": {"positive": 0.02, "negative": 0.005},
        "random_seed": SEED,
        "starvation_epsilon": STARVED_EPS,
        "checkpoints": checkpoints,
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    generate_charts(payload)
    print(f"Wrote {RESULTS_PATH}")
    print(f"Wrote {CHART_DIR / 'pub_k_extended_routing.png'}")
    print(f"Wrote {CHART_DIR / 'pub_k_extended_starvation_evolution.png'}")


if __name__ == "__main__":
    main()
