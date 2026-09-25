"""RV-4 risk-sensitive VLD routing variants.

Creates experiment output only. Existing SDK/app/test sources are not modified.
"""

from __future__ import annotations

import json
import sys
from math import floor, log2
from pathlib import Path
import random
import sqlite3
from typing import Any

import numpy as np

from copilot_sdk.scoring.investigation import KUtilityStore

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k_learning_curve_cross_copilot as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "vld" / "rv4_risk_sensitive_results.json"

COPILOTS = ("soc", "dataops", "s2p", "purchasing", "trading")
PENALTY = {"soc": 20.0, "dataops": 10.0, "s2p": 5.0, "purchasing": 3.0, "trading": 2.0}
SEEDS = [20260912, 20260913, 20260914, 20260915, 20260916]
TOTAL_DECISIONS = 500
CHECKPOINT_INTERVAL = 50
EVAL_SCENARIOS = 50
S1_EVAL_SCENARIOS = 20
S1_MARGIN = 0.70


class Store:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")


def adaptive_budget(copilot: str) -> int:
    return floor(log2(PENALTY[copilot])) + 1


def geometry(copilot: str) -> dict[str, Any]:
    info = base.load_export()[copilot]
    categories = list(info.get("category_names") or info["all_category_mu"].keys())
    factors = list(info["factor_names"])
    sigma = np.asarray(info.get("sigma") or [1.0] * len(factors), dtype=np.float64)
    if sigma.shape != (len(factors),):
        sigma = np.ones(len(factors), dtype=np.float64)
    return {
        "info": info,
        "categories": categories,
        "factors": factors,
        "actions": list(info["action_names"]),
        "sigma": sigma,
        "tau": float(info.get("tau", 0.1)),
        "mu": {category: np.asarray(info["all_category_mu"][category], dtype=np.float64) for category in categories},
    }


def easy_case(rng: random.Random, category: str, mu: np.ndarray, investigator: base.VLDInvestigator) -> dict[str, Any]:
    action = rng.randrange(mu.shape[0])
    full = np.clip(mu[action] + np.asarray([rng.gauss(0.0, 0.01) for _ in range(mu.shape[1])]), 0.02, 0.98)
    correct, _p, _m = base.score(investigator, full)
    return {
        "category": category,
        "surface": full.copy(),
        "full": full.copy(),
        "correct_action": int(correct),
        "surface_action": int(correct),
        "informative": set(),
        "s1": True,
    }


def choose_budget(copilot: str, variant: str, surface_margin: float) -> int:
    if surface_margin >= S1_MARGIN:
        return 0
    if variant == "adaptive_budget":
        return min(adaptive_budget(copilot), 6)
    return 2


def run_variant_case(
    case: dict[str, Any],
    investigator: base.VLDInvestigator,
    k_weights: np.ndarray,
    *,
    copilot: str,
    variant: str,
    rng: random.Random,
) -> dict[str, Any]:
    v = np.asarray(case["surface"], dtype=np.float64).copy()
    full = np.asarray(case["full"], dtype=np.float64)
    informative = set(case["informative"])
    enriched: set[int] = set()
    selected: list[int] = []
    step_records: list[tuple[int, np.ndarray, np.ndarray]] = []
    surface_action, surface_p, surface_margin = base.score(investigator, v)
    budget = choose_budget(copilot, variant, surface_margin)
    risk = PENALTY[copilot]

    for _ in range(min(budget, len(v))):
        _action_before, p_before, _margin_before = base.score(investigator, v)
        q = investigator.compute_Q(v, p_before, enriched, K_weights=k_weights)
        if variant in {"risk_fixed_budget", "adaptive_budget"}:
            q = q * risk
        elif variant == "thompson_risk":
            scale = max(float(np.std(q)), 0.02) * (risk / 20.0)
            q = q + np.asarray([rng.gauss(0.0, scale) for _ in q], dtype=np.float64)
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

    final_action, _final_p, _final_margin = base.score(investigator, v)
    correct = final_action == int(case["correct_action"])
    return {
        "selected": selected,
        "step_records": step_records,
        "final_action": int(final_action),
        "surface_action": int(surface_action),
        "correct": bool(correct),
        "saved": bool(surface_action != int(case["correct_action"]) and correct),
        "hurt": bool(surface_action == int(case["correct_action"]) and not correct),
        "informative_reads": sum(1 for dim in selected if dim in informative),
        "total_reads": len(selected),
        "abstained": budget == 0,
        "s1": bool(case.get("s1", False)),
    }


def eval_checkpoint(
    copilot: str,
    variant: str,
    seed: int,
    checkpoint: int,
    geom: dict[str, Any],
    store: KUtilityStore,
) -> dict[str, Any]:
    rng = random.Random(seed + 100_000 + checkpoint)
    stats = {"reads": 0, "informative": 0, "correct": 0, "saves": 0, "hurts": 0, "s1": 0, "s1_abstain": 0}
    frozen = {category: store.get_weights(category).copy() for category in geom["categories"]}
    for _ in range(EVAL_SCENARIOS):
        category = rng.choice(geom["categories"])
        investigator = base.VLDInvestigator(geom["mu"][category], geom["sigma"], geom["factors"], tau=geom["tau"])
        case = base.make_case(rng, category, geom["mu"][category], investigator)
        run = run_variant_case(case, investigator, frozen[category], copilot=copilot, variant=variant, rng=rng)
        stats["reads"] += run["total_reads"]
        stats["informative"] += run["informative_reads"]
        stats["correct"] += int(run["correct"])
        stats["saves"] += int(run["saved"])
        stats["hurts"] += int(run["hurt"])
    for _ in range(S1_EVAL_SCENARIOS):
        category = rng.choice(geom["categories"])
        investigator = base.VLDInvestigator(geom["mu"][category], geom["sigma"], geom["factors"], tau=geom["tau"])
        case = easy_case(rng, category, geom["mu"][category], investigator)
        run = run_variant_case(case, investigator, frozen[category], copilot=copilot, variant=variant, rng=rng)
        stats["s1"] += 1
        stats["s1_abstain"] += int(run["abstained"])
    reads = max(1, stats["reads"])
    return {
        "decision_count": checkpoint,
        "routing_quality": stats["informative"] / reads,
        "accuracy": stats["correct"] / EVAL_SCENARIOS,
        "saves": stats["saves"],
        "hurts": stats["hurts"],
        "mean_reads": stats["reads"] / EVAL_SCENARIOS,
        "s1_abstain_calibration": stats["s1_abstain"] / max(1, stats["s1"]),
        "k_weights_by_category": {category: [float(v) for v in frozen[category]] for category in geom["categories"]},
    }


def run_arm(copilot: str, variant: str, seed: int) -> dict[str, Any]:
    geom = geometry(copilot)
    rng = random.Random(seed + sum(ord(ch) for ch in copilot) + len(variant))
    store = KUtilityStore(Store(), d=len(geom["factors"]))
    checkpoints = []
    sources = {int(k): v for k, v in base.DIMENSION_SOURCES.get(copilot, {}).items()}
    for idx, factor in enumerate(geom["factors"]):
        sources.setdefault(idx, factor)
    for decision in range(1, TOTAL_DECISIONS + 1):
        category = rng.choice(geom["categories"])
        investigator = base.VLDInvestigator(geom["mu"][category], geom["sigma"], geom["factors"], tau=geom["tau"])
        case = base.make_case(rng, category, geom["mu"][category], investigator)
        run = run_variant_case(case, investigator, store.get_weights(category), copilot=copilot, variant=variant, rng=rng)
        base.reward_learning_store(store, category, geom["factors"], sources, investigator, run, set(case["informative"]))
        if decision % CHECKPOINT_INTERVAL == 0:
            checkpoints.append(eval_checkpoint(copilot, variant, seed, decision, geom, store))
    return {"seed": seed, "checkpoints": checkpoints}


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def summarize(results: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for copilot, variants in results.items():
        summary[copilot] = {"penalty_ratio": PENALTY[copilot], "adaptive_budget": adaptive_budget(copilot)}
        for variant, seed_runs in variants.items():
            finals = [run["checkpoints"][-1] for run in seed_runs]
            summary[copilot][variant] = {
                "routing_quality": mean([f["routing_quality"] for f in finals]),
                "accuracy": mean([f["accuracy"] for f in finals]),
                "mean_reads": mean([f["mean_reads"] for f in finals]),
                "saves": mean([f["saves"] for f in finals]),
                "hurts": mean([f["hurts"] for f in finals]),
                "s1_abstain_calibration": mean([f["s1_abstain_calibration"] for f in finals]),
            }
        adaptive_gain = summary[copilot]["adaptive_budget"]["routing_quality"] - summary[copilot]["uniform_fixed_budget"]["routing_quality"]
        summary[copilot]["adaptive_routing_gain"] = adaptive_gain
    high_gain = mean([summary[c]["adaptive_routing_gain"] for c in ("soc", "dataops")])
    low_ok = all(summary[c]["adaptive_routing_gain"] >= -0.001 for c in ("s2p", "purchasing", "trading"))
    abstain_ok = all(
        summary[c]["adaptive_budget"]["s1_abstain_calibration"] >= summary[c]["uniform_fixed_budget"]["s1_abstain_calibration"] - 0.001
        for c in COPILOTS
    )
    return {
        "by_copilot": summary,
        "kill_keep": {
            "high_penalty_mean_gain": high_gain,
            "low_penalty_no_degradation": low_ok,
            "abstain_calibration_not_degraded": abstain_ok,
            "verdict": "KEEP" if high_gain >= 0.05 and low_ok and abstain_ok else "KILL_OR_QUALIFY",
        },
    }


def main() -> None:
    variants = ("uniform_fixed_budget", "risk_fixed_budget", "adaptive_budget", "thompson_risk")
    results: dict[str, Any] = {}
    for copilot in COPILOTS:
        results[copilot] = {}
        for variant in variants:
            print(f"{copilot} {variant}")
            results[copilot][variant] = [run_arm(copilot, variant, seed) for seed in SEEDS]
    payload = {
        "protocol": {
            "total_decisions": TOTAL_DECISIONS,
            "checkpoint_interval": CHECKPOINT_INTERVAL,
            "evaluation_scenarios": EVAL_SCENARIOS,
            "seeds": SEEDS,
            "penalty_ratios": PENALTY,
            "variants": list(variants),
        },
        "results": results,
        "summary": summarize(results),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
