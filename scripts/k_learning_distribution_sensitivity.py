"""KE-4 decision distribution sensitivity for DataOps K learning."""

from __future__ import annotations

import json
import sys
from pathlib import Path
import random
import sqlite3
from typing import Any

import numpy as np

from copilot_sdk.scoring.investigation import KUtilityStore

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k_learning_curve_cross_copilot as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "vld" / "ke4_distribution_sensitivity_results.json"

SEEDS = [20260912, 20260913, 20260914, 20260915, 20260916]
TOTAL_DECISIONS = 500
CHECKPOINT_INTERVAL = 50
EVAL_SCENARIOS = 50
DISTRIBUTIONS = ("uniform", "clustered", "adversarial")


class Store:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")


def dataops_geometry() -> dict[str, Any]:
    info = base.load_export()["dataops"]
    categories = list(info["category_names"])
    factors = list(info["factor_names"])
    return {
        "info": info,
        "categories": categories,
        "factors": factors,
        "actions": list(info["action_names"]),
        "sigma": np.asarray(info.get("sigma") or [1.0] * len(factors), dtype=np.float64),
        "tau": float(info.get("tau", 0.1)),
        "mu": {category: np.asarray(info["all_category_mu"][category], dtype=np.float64) for category in categories},
    }


def choose_category(rng: random.Random, categories: list[str], distribution: str) -> str:
    if distribution == "clustered" and rng.random() < 0.60:
        return rng.choice(categories[:2])
    return rng.choice(categories)


def adversarial_case(
    rng: random.Random,
    category: str,
    mu: np.ndarray,
    investigator: base.VLDInvestigator,
) -> dict[str, Any]:
    n_actions, n_dims = mu.shape
    true_action = rng.randrange(n_actions)
    distractor = max(
        [idx for idx in range(n_actions) if idx != true_action],
        key=lambda idx: float(np.linalg.norm(mu[true_action] - mu[idx])),
    )
    full = np.clip(mu[true_action] + np.asarray([rng.gauss(0.0, 0.025) for _ in range(n_dims)]), 0.02, 0.98)
    surface = np.clip((mu[true_action] + mu[distractor]) / 2.0, 0.02, 0.98)
    hard_dims = list(np.argsort(np.abs(mu[true_action] - mu[distractor]))[::-1][:2])
    for dim in hard_dims:
        surface[dim] = np.clip(0.35 * mu[true_action, dim] + 0.65 * mu[distractor, dim], 0.02, 0.98)
    correct_action, _full_p, _ = base.score(investigator, full)
    surface_action, surface_p, _ = base.score(investigator, surface)
    informative: set[int] = set()
    for dim in range(n_dims):
        candidate = surface.copy()
        candidate[dim] = full[dim]
        action, probs, _margin = base.score(investigator, candidate)
        if action == correct_action or float(probs[correct_action] - surface_p[correct_action]) >= 0.015:
            informative.add(dim)
    if not informative:
        informative.update(hard_dims)
    return {
        "category": category,
        "surface": surface,
        "full": full,
        "correct_action": int(correct_action),
        "surface_action": int(surface_action),
        "informative": informative,
    }


def make_train_case(rng: random.Random, geom: dict[str, Any], distribution: str) -> tuple[str, dict[str, Any], base.VLDInvestigator]:
    category = choose_category(rng, geom["categories"], distribution)
    investigator = base.VLDInvestigator(geom["mu"][category], geom["sigma"], geom["factors"], tau=geom["tau"])
    if distribution == "adversarial":
        case = adversarial_case(rng, category, geom["mu"][category], investigator)
    else:
        case = base.make_case(rng, category, geom["mu"][category], investigator)
    return category, case, investigator


def evaluate(seed: int, checkpoint: int, geom: dict[str, Any], store: KUtilityStore) -> dict[str, Any]:
    rng = random.Random(seed + 200_000 + checkpoint)
    stats = {"reads": 0, "informative": 0, "correct": 0, "saves": 0, "hurts": 0}
    frozen = {category: store.get_weights(category).copy() for category in geom["categories"]}
    for _ in range(EVAL_SCENARIOS):
        category = rng.choice(geom["categories"])
        investigator = base.VLDInvestigator(geom["mu"][category], geom["sigma"], geom["factors"], tau=geom["tau"])
        case = base.make_case(rng, category, geom["mu"][category], investigator)
        run = base.run_investigation(case, investigator, frozen[category])
        stats["reads"] += run["total_reads"]
        stats["informative"] += run["informative_reads"]
        stats["correct"] += int(run["correct"])
        stats["saves"] += int(run["saved"])
        stats["hurts"] += int(run["hurt"])
    return {
        "decision_count": checkpoint,
        "routing_quality": stats["informative"] / max(1, stats["reads"]),
        "accuracy": stats["correct"] / EVAL_SCENARIOS,
        "saves": stats["saves"],
        "hurts": stats["hurts"],
        "k_weights_by_category": {category: [float(v) for v in frozen[category]] for category in geom["categories"]},
    }


def starvation(geom: dict[str, Any], store: KUtilityStore) -> dict[str, Any]:
    starved = 0
    total = 0
    for category in geom["categories"]:
        for weight in store.get_weights(category):
            total += 1
            starved += int(abs(float(weight) - 0.5) <= 1e-9)
    return {"starved_category_dims": starved, "total_category_dims": total, "starvation_rate": starved / total}


def run_distribution(distribution: str, seed: int) -> dict[str, Any]:
    geom = dataops_geometry()
    rng = random.Random(seed + len(distribution))
    store = KUtilityStore(Store(), d=len(geom["factors"]))
    checkpoints = []
    sources = {int(k): v for k, v in base.DIMENSION_SOURCES["dataops"].items()}
    for decision in range(1, TOTAL_DECISIONS + 1):
        category, case, investigator = make_train_case(rng, geom, distribution)
        run = base.run_investigation(case, investigator, store.get_weights(category))
        base.reward_learning_store(store, category, geom["factors"], sources, investigator, run, set(case["informative"]))
        if decision % CHECKPOINT_INTERVAL == 0:
            checkpoints.append(evaluate(seed, decision, geom, store))
    return {"seed": seed, "checkpoints": checkpoints, "starvation": starvation(geom, store)}


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def main() -> None:
    results = {}
    for distribution in DISTRIBUTIONS:
        print(distribution)
        results[distribution] = [run_distribution(distribution, seed) for seed in SEEDS]
    summary = {}
    for distribution, runs in results.items():
        finals = [run["checkpoints"][-1] for run in runs]
        summary[distribution] = {
            "final_routing_quality": mean([f["routing_quality"] for f in finals]),
            "final_accuracy": mean([f["accuracy"] for f in finals]),
            "hurts": sum(f["hurts"] for f in finals),
            "starvation_rate": mean([run["starvation"]["starvation_rate"] for run in runs]),
        }
    robust = all(item["final_routing_quality"] > 0.44 and item["hurts"] == 0 for item in summary.values())
    fragile = summary["adversarial"]["final_routing_quality"] <= 0.45
    payload = {
        "protocol": {
            "copilot": "dataops",
            "distributions": list(DISTRIBUTIONS),
            "total_decisions": TOTAL_DECISIONS,
            "checkpoint_interval": CHECKPOINT_INTERVAL,
            "evaluation_scenarios": EVAL_SCENARIOS,
            "eval_distribution": "uniform",
            "seeds": SEEDS,
        },
        "results": results,
        "summary": summary,
        "verdict": "ROBUST" if robust else ("FRAGILE" if fragile else "DISTRIBUTION_DEPENDENT"),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
