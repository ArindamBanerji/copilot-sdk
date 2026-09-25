"""KE-5 conservation interaction with DataOps K learning."""

from __future__ import annotations

from collections import deque
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
OUT = ROOT / "experiments" / "vld" / "ke5_conservation_interaction_results.json"

SEEDS = [20260912, 20260913, 20260914, 20260915, 20260916]
TOTAL_DECISIONS = 500
CHECKPOINT_INTERVAL = 50
EVAL_SCENARIOS = 50
PENALTY_RATIO = 10.0
THETA_CONSTANT = 23.53
ROLLING_WINDOW = 50


class Store:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")


def dataops_geometry() -> dict[str, Any]:
    info = base.load_export()["dataops"]
    categories = list(info["category_names"])
    factors = list(info["factor_names"])
    return {
        "categories": categories,
        "factors": factors,
        "actions": list(info["action_names"]),
        "sigma": np.asarray(info.get("sigma") or [1.0] * len(factors), dtype=np.float64),
        "tau": float(info.get("tau", 0.1)),
        "mu": {category: np.asarray(info["all_category_mu"][category], dtype=np.float64) for category in categories},
    }


class ConservationState:
    def __init__(self, total_categories: int) -> None:
        self.total_categories = total_categories
        self.seen_categories: set[str] = set()
        self.outcomes: deque[int] = deque(maxlen=ROLLING_WINDOW)
        self.verified = 0
        self.blocked = 0
        self.history: list[dict[str, Any]] = []

    def observe(self, category: str, correct: bool, decision_count: int) -> dict[str, Any]:
        self.verified += 1
        self.seen_categories.add(category)
        self.outcomes.append(1 if correct else 0)
        alpha = len(self.seen_categories) / self.total_categories
        theta_min = THETA_CONSTANT / max(alpha * self.verified, 1e-9)
        q = sum(self.outcomes) / len(self.outcomes)
        if self.verified < ROLLING_WINDOW:
            status = "GREEN"
        elif q < theta_min * 0.90:
            status = "RED"
        elif q < theta_min:
            status = "AMBER"
        else:
            status = "GREEN"
        allowed = status == "GREEN"
        if not allowed:
            self.blocked += 1
        entry = {
            "decision_count": decision_count,
            "status": status,
            "q": q,
            "alpha": alpha,
            "V": self.verified,
            "theta_min": theta_min,
            "allowed": allowed,
            "blocked_cumulative": self.blocked,
        }
        self.history.append(entry)
        return entry


def evaluate(seed: int, checkpoint: int, geom: dict[str, Any], store: KUtilityStore) -> dict[str, Any]:
    rng = random.Random(seed + 300_000 + checkpoint)
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


def run_seed(seed: int) -> dict[str, Any]:
    geom = dataops_geometry()
    rng = random.Random(seed)
    stores = {
        "without_conservation": KUtilityStore(Store(), d=len(geom["factors"])),
        "with_conservation": KUtilityStore(Store(), d=len(geom["factors"])),
    }
    conservation = ConservationState(total_categories=len(geom["categories"]))
    checkpoints: dict[str, list[dict[str, Any]]] = {"without_conservation": [], "with_conservation": []}
    blocked_by_checkpoint = []
    sources = {int(k): v for k, v in base.DIMENSION_SOURCES["dataops"].items()}
    for decision in range(1, TOTAL_DECISIONS + 1):
        category = rng.choice(geom["categories"])
        investigator = base.VLDInvestigator(geom["mu"][category], geom["sigma"], geom["factors"], tau=geom["tau"])
        case = base.make_case(rng, category, geom["mu"][category], investigator)
        for arm, store in stores.items():
            run = base.run_investigation(case, investigator, store.get_weights(category))
            if arm == "without_conservation":
                base.reward_learning_store(store, category, geom["factors"], sources, investigator, run, set(case["informative"]))
            else:
                state = conservation.observe(category, bool(run["correct"]), decision)
                if state["allowed"]:
                    base.reward_learning_store(store, category, geom["factors"], sources, investigator, run, set(case["informative"]))
        if decision % CHECKPOINT_INTERVAL == 0:
            for arm, store in stores.items():
                checkpoints[arm].append(evaluate(seed, decision, geom, store))
            blocked_by_checkpoint.append(
                {
                    "decision_count": decision,
                    "blocked_updates": conservation.blocked,
                    "status": conservation.history[-1]["status"],
                    "q": conservation.history[-1]["q"],
                    "theta_min": conservation.history[-1]["theta_min"],
                }
            )
    return {
        "seed": seed,
        "checkpoints": checkpoints,
        "blocked_by_checkpoint": blocked_by_checkpoint,
        "blocked_updates": conservation.blocked,
        "conservation_history_tail": conservation.history[-10:],
    }


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def dip_magnitude(values: list[float]) -> float:
    worst = 0.0
    for before, after in zip(values, values[1:]):
        worst = min(worst, after - before)
    return abs(worst)


def main() -> None:
    runs = [run_seed(seed) for seed in SEEDS]
    summary: dict[str, Any] = {}
    for arm in ("without_conservation", "with_conservation"):
        final = [run["checkpoints"][arm][-1] for run in runs]
        curves = [[c["routing_quality"] for c in run["checkpoints"][arm]] for run in runs]
        acc_curves = [[c["accuracy"] for c in run["checkpoints"][arm]] for run in runs]
        summary[arm] = {
            "final_routing_quality": mean([f["routing_quality"] for f in final]),
            "final_accuracy": mean([f["accuracy"] for f in final]),
            "mean_routing_dip": mean([dip_magnitude(curve) for curve in curves]),
            "mean_accuracy_dip": mean([dip_magnitude(curve) for curve in acc_curves]),
        }
    summary["blocked_updates_mean"] = mean([run["blocked_updates"] for run in runs])
    summary["final_routing_cost"] = summary["without_conservation"]["final_routing_quality"] - summary["with_conservation"]["final_routing_quality"]
    summary["dip_reduction"] = summary["without_conservation"]["mean_routing_dip"] - summary["with_conservation"]["mean_routing_dip"]
    summary["verdict"] = {
        "helps": summary["dip_reduction"] > 0.0,
        "costs": summary["final_routing_cost"] >= 0.05,
    }
    payload = {
        "protocol": {
            "copilot": "dataops",
            "total_decisions": TOTAL_DECISIONS,
            "checkpoint_interval": CHECKPOINT_INTERVAL,
            "evaluation_scenarios": EVAL_SCENARIOS,
            "seeds": SEEDS,
            "conservation_policy": {
                "theta_min": "23.53/(alpha*V)",
                "theta_constant": THETA_CONSTANT,
                "alpha": "seen_categories/total_categories",
                "V": "verified_decisions",
                "q": f"rolling_accuracy_last_{ROLLING_WINDOW}",
                "penalty_ratio": PENALTY_RATIO,
            },
        },
        "runs": runs,
        "summary": summary,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
