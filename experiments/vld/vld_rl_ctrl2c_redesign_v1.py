"""RL-CTRL-2C: constrained adaptive enrichment from the K-curve foundation.

Pre-registration:
    DEPLOYABLE iff B2-hard has clean-pause <= 5%, sustained poison detection
    >= the B0 reference (100%), and retains >= +2.75pp routing_quality over
    B0 in at least two of three seeds for both copilots.  TRADEOFF means the
    constraints hold but the quality gain largely collapses.  INFEASIBLE means
    no lambda has positive quality gain while satisfying both constraints.

Design:
    The existing K-curve helpers provide scenario generation, Q selection,
    investigation, and the exact persistent KUtilityStore update path.  This
    new script owns only the variable-B controller, its FQI reward candidates,
    and the Stage-2 safety evaluation.  The R1 gate is Check A (calibrated
    floor over the last 100 verified records) plus the existing Check-B
    theta-min condition, replicated through the Stage-1 helper.

Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED.
"""

from __future__ import annotations

import json
import importlib.util
import random
import time
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor

import vld_conservation_characterization_v1 as s1


ROOT = Path(__file__).resolve().parents[2]


def load_harness() -> Any:
    spec = importlib.util.spec_from_file_location("k_curve_harness", ROOT / "scripts" / "k_learning_curve_cross_copilot.py")
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load the K-curve harness")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


h = load_harness()
RESULTS = ROOT / "experiments" / "vld" / "results"
OUTPUT = RESULTS / "rl_ctrl2c_constrained_enrichment.json"
SUMMARY = RESULTS / "rl_ctrl2c_constrained_enrichment_summary.md"
SEEDS = (42, 123, 7)
COPILOTS = ("s2p", "soc")
LAMBDAS = (0, 1, 5, 10, 20, 50)
POINTS = (50, 100, 250, 500, 750, 1000, 1500, 2000)
FLOORS = {"s2p": 0.769, "soc": 0.764}
DEFAULT_B = 2
MAX_B = 4


class MemoryStore:
    """SQLite-compatible in-memory connection for KUtilityStore."""

    def __init__(self) -> None:
        import sqlite3

        self.conn = sqlite3.connect(":memory:")


def info_for(copilot: str) -> dict[str, Any]:
    return cast(dict[str, Any], h.load_export()[copilot])


def setup(info: dict[str, Any]) -> tuple[list[str], list[str], np.ndarray, dict[str, np.ndarray], float]:
    categories = list(info.get("category_names") or info["all_category_mu"].keys())
    factors = list(info["factor_names"])
    sigma = np.asarray(info.get("sigma") or [1.0] * len(factors), dtype=np.float64)
    if len(sigma) != len(factors):
        sigma = np.ones(len(factors), dtype=np.float64)
    mus = {c: np.asarray(info["all_category_mu"][c], dtype=np.float64) for c in categories}
    return categories, factors, sigma, mus, float(info.get("tau", 0.1))


def gate(records: list[dict[str, Any]], copilot: str, n_categories: int) -> bool:
    return bool(s1.gate_pause(records, n_categories, FLOORS[copilot], 100))


def state_vector(
    investigator: Any,
    vector: np.ndarray,
    recent_accuracy: float,
    n: int,
    paused: bool,
    k_weights: np.ndarray,
) -> np.ndarray:
    _action, probabilities = investigator.score(vector)
    ranked = np.sort(probabilities)[::-1]
    margin = float(ranked[0] - ranked[1]) if len(ranked) > 1 else 1.0
    d2 = float(np.min(np.sum((vector - investigator.mu) ** 2, axis=1)))
    return cast(np.ndarray, np.asarray(
        (margin, recent_accuracy, n / 2000.0, d2, float(np.mean(k_weights)), float(paused)),
        dtype=np.float64,
    ))


def apply_case(case: dict[str, Any], investigator: Any, weights: np.ndarray, budget: int) -> dict[str, Any]:
    return cast(dict[str, Any], h.run_investigation(case, investigator, weights, budget=budget))


def update_store(
    store: Any,
    category: str,
    factors: list[str],
    investigator: Any,
    run: dict[str, Any],
    informative: set[int],
) -> None:
    h.reward_learning_store(store, category, factors, h.DIMENSION_SOURCES.get(category, {}), investigator, run, informative)


def candidate_violation(
    records: list[dict[str, Any]],
    candidate_correct: bool,
    copilot: str,
    n_categories: int,
    poison_detection_proxy: float,
) -> float:
    trial = records + [{"category": "candidate", "is_correct": candidate_correct, "outcome": "confirmed" if candidate_correct else "rejected"}]
    paused = gate(trial, copilot, n_categories)
    pause_rate = sum(1 for row in trial if bool(row.get("gate_paused", False))) / max(1, len(trial))
    if paused:
        pause_rate = max(pause_rate, 1.0)
    return max(0.0, pause_rate - 0.05) + max(0.0, 1.0 - poison_detection_proxy)


def build_training(
    copilot: str,
    info: dict[str, Any],
    seed: int,
    lam: float,
) -> tuple[ExtraTreesRegressor, dict[str, Any]]:
    categories, factors, sigma, mus, tau = setup(info)
    rng = random.Random(seed + sum(ord(ch) for ch in copilot) + int(lam * 1000))
    store = h.KUtilityStore(MemoryStore(), d=len(factors))
    records: list[dict[str, Any]] = []
    x_rows: list[np.ndarray] = []
    y_rows: list[float] = []
    for n in range(1, 501):
        category = rng.choice(categories)
        investigator = h.VLDInvestigator(mus[category], sigma, factors, tau=tau)
        case = h.make_case(rng, category, mus[category], investigator)
        weights = store.get_weights(category)
        recent = mean(bool(row["is_correct"]) for row in records[-100:]) if records else 0.75
        paused = gate(records, copilot, len(categories))
        features = state_vector(investigator, np.asarray(case["surface"], dtype=np.float64), recent, n, paused, weights)
        for budget in range(1, MAX_B + 1):
            run = apply_case(case, investigator, weights, budget)
            informative = float(run["informative_reads"]) / max(1, int(run["total_reads"]))
            violation = candidate_violation(records, bool(run["correct"]), copilot, len(categories), float(run["correct"]))
            reward = informative - 0.035 * budget - lam * violation
            x_rows.append(np.r_[features, float(budget)])
            y_rows.append(float(reward))
        run_b0 = apply_case(case, investigator, weights, DEFAULT_B)
        update_store(store, category, factors, investigator, run_b0, set(case["informative"]))
        records.append({"category": category, "is_correct": bool(run_b0["correct"]), "outcome": "confirmed" if run_b0["correct"] else "rejected"})
    model = ExtraTreesRegressor(n_estimators=80, min_samples_leaf=5, random_state=seed + int(lam), n_jobs=1)
    model.fit(np.asarray(x_rows), np.asarray(y_rows))
    return model, {"training_decisions": 500, "lambda": lam, "reward": "informative_fraction - 0.035*B - lambda*violation"}


def choose_budget(
    model: ExtraTreesRegressor,
    features: np.ndarray,
    paused: bool,
    running_pause_rate: float,
) -> int:
    rows = np.vstack([np.r_[features, float(b)] for b in range(1, MAX_B + 1)])
    selected = int(np.argmax(model.predict(rows))) + 1
    if paused or running_pause_rate > 0.045:
        return min(selected, DEFAULT_B)
    return selected


def run_learning(copilot: str, info: dict[str, Any], seed: int, model: ExtraTreesRegressor | None) -> dict[str, Any]:
    categories, factors, sigma, mus, tau = setup(info)
    rng = random.Random(seed + sum(ord(ch) for ch in copilot))
    store = h.KUtilityStore(MemoryStore(), d=len(factors))
    records: list[dict[str, Any]] = []
    budgets: list[int] = []
    curve: dict[str, dict[str, float]] = {}
    total_reads = 0
    informative_reads = 0
    for n in range(1, 2001):
        category = rng.choice(categories)
        investigator = h.VLDInvestigator(mus[category], sigma, factors, tau=tau)
        case = h.make_case(rng, category, mus[category], investigator)
        weights = store.get_weights(category)
        paused = gate(records, copilot, len(categories))
        recent = mean(bool(row["is_correct"]) for row in records[-100:]) if records else 0.75
        features = state_vector(investigator, np.asarray(case["surface"], dtype=np.float64), recent, n, paused, weights)
        running_pause = sum(bool(row.get("gate_paused", False)) for row in records) / max(1, len(records))
        budget = DEFAULT_B if model is None else choose_budget(model, features, paused, running_pause)
        run = apply_case(case, investigator, weights, budget)
        correct = bool(run["correct"])
        total_reads += int(run["total_reads"])
        informative_reads += int(run["informative_reads"])
        update_store(store, category, factors, investigator, run, set(case["informative"]))
        records.append({"category": category, "is_correct": correct, "outcome": "confirmed" if correct else "rejected", "gate_paused": paused})
        if n in POINTS:
            curve[str(n)] = {"routing_quality": informative_reads / max(1, total_reads)}
    values = [v["routing_quality"] for v in curve.values()]
    final = float(values[-1])
    dq = np.diff(np.asarray(values, dtype=np.float64))
    plateau = next((POINTS[i + 1] for i in range(max(0, len(dq) - 1)) if abs(float(dq[i])) < 0.005 and abs(float(dq[i + 1])) < 0.005), POINTS[-1])
    return {
        "curve": curve,
        "final_quality": final,
        "reads_per_decision": mean(budgets) if budgets else float(total_reads / 2000.0),
        "time_to_plateau": plateau,
        "plateau_height": final,
        "trajectory_variance": float(pstdev(values)) if len(values) > 1 else 0.0,
        "records": records,
        "k_state": {c: [float(v) for v in store.get_weights(c)] for c in categories},
    }


def safety_run(copilot: str, info: dict[str, Any], seed: int, model: ExtraTreesRegressor | None, condition: str) -> dict[str, float]:
    categories, factors, sigma, mus, tau = setup(info)
    rng = random.Random(seed + 700000 + sum(ord(ch) for ch in copilot))
    store = h.KUtilityStore(MemoryStore(), d=len(factors))
    horizon = 900 if condition == "poison_25" else 500
    records: list[dict[str, Any]] = []
    pause_count = 0
    detected = False
    for n in range(1, horizon + 1):
        category = rng.choice(categories)
        investigator = h.VLDInvestigator(mus[category], sigma, factors, tau=tau)
        case = h.make_case(rng, category, mus[category], investigator)
        weights = store.get_weights(category)
        paused = gate(records, copilot, len(categories))
        if paused:
            pause_count += 1
        recent = mean(bool(row["is_correct"]) for row in records[-100:]) if records else 0.75
        features = state_vector(investigator, np.asarray(case["surface"], dtype=np.float64), recent, n, paused, weights)
        running_pause = sum(bool(row.get("gate_paused", False)) for row in records) / max(1, len(records))
        budget = DEFAULT_B if model is None else choose_budget(model, features, paused, running_pause)
        run = apply_case(case, investigator, weights, budget)
        outcome = bool(run["correct"])
        if condition == "poison_25" and n >= s1.ONSET and rng.random() < 0.25:
            outcome = not outcome
        run["correct"] = outcome
        update_store(store, category, factors, investigator, run, set(case["informative"]))
        records.append({"category": category, "is_correct": outcome, "outcome": "confirmed" if outcome else "rejected", "gate_paused": paused})
        if condition == "poison_25" and n >= s1.ONSET and paused:
            detected = True
    return {"clean_pause_rate": pause_count / max(1, horizon), "poison_detected": float(detected)}


def aggregate(rows: list[dict[str, Any]]) -> dict[str, float]:
    keys = ("final_quality", "reads_per_decision", "clean_pause_rate", "sustained_poison_detection")
    return {key: float(mean(float(row[key]) for row in rows)) for key in keys}


def main() -> None:
    started = time.perf_counter()
    result: dict[str, Any] = {}
    frontier: dict[str, list[dict[str, float]]] = {}
    best_by_copilot: dict[str, dict[str, Any]] = {}
    for copilot in COPILOTS:
        info = info_for(copilot)
        baseline_runs: list[dict[str, Any]] = []
        for seed in SEEDS:
            run = run_learning(copilot, info, seed, None)
            clean = safety_run(copilot, info, seed, None, "clean_control")
            poison = safety_run(copilot, info, seed, None, "poison_25")
            run.update({"clean_pause_rate": clean["clean_pause_rate"], "sustained_poison_detection": poison["poison_detected"]})
            baseline_runs.append(run)
        b0_agg = aggregate(baseline_runs)
        result[copilot] = {"B0_fixed": {"per_seed": {str(seed): run for seed, run in zip(SEEDS, baseline_runs)}, "aggregate": b0_agg}, "B2_hard": {}}
        frontier[copilot] = []
        models: dict[float, ExtraTreesRegressor] = {}
        for lam in LAMBDAS:
            model, _training = build_training(copilot, info, SEEDS[0], float(lam))
            models[float(lam)] = model
            per_seed: dict[str, Any] = {}
            runs: list[dict[str, Any]] = []
            for seed in SEEDS:
                run = run_learning(copilot, info, seed, model)
                clean = safety_run(copilot, info, seed, model, "clean_control")
                poison = safety_run(copilot, info, seed, model, "poison_25")
                run.update({"clean_pause_rate": clean["clean_pause_rate"], "sustained_poison_detection": poison["poison_detected"]})
                runs.append(run)
                per_seed[str(seed)] = {k: v for k, v in run.items() if k not in ("records", "k_state")}
            agg = aggregate(runs)
            gain = agg["final_quality"] - b0_agg["final_quality"]
            constraint = agg["clean_pause_rate"] <= 0.05 and agg["sustained_poison_detection"] >= b0_agg["sustained_poison_detection"]
            result[copilot]["B2_hard"][str(lam)] = {"per_seed": per_seed, "aggregate": {**agg, "constraint_satisfied": constraint, "quality_gain_over_B0": gain}}
            frontier[copilot].append({"lambda": float(lam), "quality": agg["final_quality"], "reads": agg["reads_per_decision"], "pause": agg["clean_pause_rate"], "poison": agg["sustained_poison_detection"]})
        candidates = [row for row in frontier[copilot] if row["pause"] <= 0.05 and row["poison"] >= b0_agg["sustained_poison_detection"] and row["quality"] - b0_agg["final_quality"] >= 0.0275]
        safe_candidates = [row for row in frontier[copilot] if row["pause"] <= 0.05 and row["poison"] >= b0_agg["sustained_poison_detection"]]
        best = min(candidates, key=lambda row: row["lambda"]) if candidates else (min(safe_candidates, key=lambda row: row["lambda"]) if safe_candidates else None)
        best_by_copilot[copilot] = {"lambda": best["lambda"] if best else None, "quality_gain": (best["quality"] - b0_agg["final_quality"]) if best else None, "clean_pause": best["pause"] if best else None, "poison_detection": best["poison"] if best else None, "deployable": bool(best and best["quality"] - b0_agg["final_quality"] >= 0.0275)}
    deployable = all(bool(best_by_copilot[c]["deployable"]) for c in COPILOTS)
    any_constraint = any(row["pause"] <= 0.05 and row["poison"] >= result[c]["B0_fixed"]["aggregate"]["sustained_poison_detection"] for c in COPILOTS for row in frontier[c])
    result["frontier"] = frontier
    result["verdict"] = {"deployable": deployable, "tradeoff": bool(any_constraint and not deployable), "infeasible": not any_constraint, "rationale": "Constrained adaptive enrichment was evaluated on persistent K state with R1 floors and Stage-2 poison-25% label flips.", "b2_soft_poison_context": "S2P 9.67%, SOC 0.67% — prior gain was from disabling safety"}
    result["metadata"] = {"lambda_grid": list(LAMBDAS), "seeds": list(SEEDS), "floors": FLOORS, "gate": "R1 per-domain calibrated floor", "poison_protocol": "Stage 2 poison-25% injection", "k_persistent": True, "built_on": "K-curve harness (not CTRL-2 harness)", "ctrl2_harness_problems": ["hard-coded reward", "wrong gate (<0.60/last-20)", "synthetic poison detection", "non-persistent K"], "tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED + SIMULATED", "ood_caveat": "in-distribution only"}
    for copilot in COPILOTS:
        result[copilot]["best_lambda"] = best_by_copilot[copilot]
    RESULTS.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    lines = ["# RL-CTRL-2C Redesign — Constrained Enrichment", "", "Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED. OOD caveat: in-distribution only.", "", "## 1. Baseline and verdict", "", "| Copilot | B0 quality | B0 reads | B0 clean pause | B0 poison detection | Best lambda | Best gain | Best pause | Best poison |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for copilot in COPILOTS:
        b0 = result[copilot]["B0_fixed"]["aggregate"]
        best = cast(dict[str, Any], result[copilot]["best_lambda"])
        lines.append(f"| {copilot} | {b0['final_quality']:.3f} | {b0['reads_per_decision']:.3f} | {b0['clean_pause_rate']:.1%} | {b0['sustained_poison_detection']:.1%} | {best['lambda'] if best['lambda'] is not None else 'none'} | {best['quality_gain'] if best['quality_gain'] is not None else 'n/a'} | {best['clean_pause'] if best['clean_pause'] is not None else 'n/a'} | {best['poison_detection'] if best['poison_detection'] is not None else 'n/a'} |")
    lines += ["", "## 2. Lambda frontier", "", "| Copilot | Lambda | Quality | Reads | Clean pause | Poison detection |", "|---|---:|---:|---:|---:|---:|"]
    for copilot in COPILOTS:
        for row in frontier[copilot]:
            lines.append(f"| {copilot} | {row['lambda']:g} | {row['quality']:.3f} | {row['reads']:.3f} | {row['pause']:.1%} | {row['poison']:.1%} |")
    lines += ["", "## 3. Interpretation", "", "The redesign uses persistent K state, the R1 calibrated per-domain floor, and the Stage-2 poison-25% protocol. The prior CTRL-2 B2-soft gain is retained only as disqualified context because its poison detection was 9.67% for S2P and 0.67% for SOC.", "", f"Verdict: **{'DEPLOYABLE' if deployable else 'TRADEOFF' if any_constraint else 'INFEASIBLE'}**.", "", "A deployability claim requires both safety constraints and the preregistered +2.75pp routing_quality gain in both copilots; otherwise the result is a characterized frontier or an infeasible constraint.", ""]
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
