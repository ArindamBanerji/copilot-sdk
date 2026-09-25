"""RV-0 routing variant experiment: static/RNN/GRU/LSTM.

Artifact-only experiment code. It reads exported centroid geometry and writes
experiments/vld/rv0_gru_ablation_results.json. It does not modify production
scoring, investigation, router, app, preseed, evidence, or test source.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import random
from statistics import mean, pstdev
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CENTROIDS_PATH = ROOT / "real_centroids_v1.json"
OUT_PATH = ROOT / "experiments" / "vld" / "rv0_gru_ablation_results.json"

VARIANTS = ("static", "rnn", "gru", "lstm")
TOTAL_DECISIONS = 500
CHECKPOINT_INTERVAL = 50
EVAL_SCENARIOS = 50
SEEDS = 10
BUDGET = 2
BUDGETS = (1, 2, 3, 4)
BASE_SEED = 20260912
BASELINE_WEIGHT = 0.5


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def load_geometry() -> dict[str, Any]:
    return json.loads(CENTROIDS_PATH.read_text(encoding="utf-8"))["copilots"]["dataops"]


def score(mu: np.ndarray, sigma: np.ndarray, tau: float, v: np.ndarray) -> tuple[int, np.ndarray, float]:
    precision = 1.0 / np.maximum(sigma**2, 0.001)
    dists = np.sum(precision.reshape(1, -1) * (v.reshape(1, -1) - mu) ** 2, axis=1)
    logits = -dists / tau
    logits -= np.max(logits)
    probs = np.exp(logits)
    probs = probs / np.sum(probs)
    ranked = np.sort(probs)[::-1]
    margin = float(ranked[0] - ranked[1]) if ranked.size > 1 else 1.0
    return int(np.argmax(probs)), probs, margin


def q_rnn(mu: np.ndarray, sigma: np.ndarray, v: np.ndarray, probs: np.ndarray, enriched: set[int], k: np.ndarray) -> np.ndarray:
    ranked = np.argsort(probs)[::-1]
    a1 = int(ranked[0])
    a2 = int(ranked[1]) if ranked.size > 1 else a1
    q = np.zeros(mu.shape[1], dtype=np.float64)
    for dim in range(mu.shape[1]):
        if dim in enriched:
            q[dim] = -1.0
            continue
        precision = (1.0 / max(float(sigma[dim] ** 2), 0.001)) / 100.0
        discriminative = abs(float(mu[a1, dim] - mu[a2, dim]))
        leverage = abs(float((v[dim] - mu[a1, dim]) ** 2 - (v[dim] - mu[a2, dim]) ** 2))
        q[dim] = (precision + discriminative + leverage) * float(k[dim])
    return q


def geometry_signal(mu: np.ndarray, sigma: np.ndarray, probs: np.ndarray) -> np.ndarray:
    ranked = np.argsort(probs)[::-1]
    a1 = int(ranked[0])
    a2 = int(ranked[1]) if ranked.size > 1 else a1
    sep = np.abs(mu[a1] - mu[a2])
    sig = sigma / max(float(np.max(sigma)), 1.0e-8)
    raw = sep * sig
    return raw / max(float(np.max(raw)), 1.0e-8)


def q_gru(
    mu: np.ndarray,
    sigma: np.ndarray,
    tau: float,
    v: np.ndarray,
    probs: np.ndarray,
    enriched: set[int],
    k: np.ndarray,
    hidden: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    geom = geometry_signal(mu, sigma, probs)
    x = np.clip(0.55 * v + 0.45 * geom, 0.0, 1.0)
    z = sigmoid(1.2 * x + 0.35 * hidden - 0.55)
    r = sigmoid(0.8 * x - 0.25 * hidden)
    h_hat = np.tanh(1.1 * x + 0.6 * r * hidden - 0.45)
    next_hidden = (1.0 - z) * hidden + z * np.abs(h_hat)
    q = next_hidden * sigma * geom * k / max(tau, 1.0e-8)
    for dim in enriched:
        q[dim] = -1.0
    return q, next_hidden


def q_lstm(
    mu: np.ndarray,
    sigma: np.ndarray,
    tau: float,
    v: np.ndarray,
    probs: np.ndarray,
    enriched: set[int],
    k: np.ndarray,
    hidden: np.ndarray,
    cell: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    geom = geometry_signal(mu, sigma, probs)
    x = np.clip(0.55 * v + 0.45 * geom, 0.0, 1.0)
    forget = sigmoid(0.9 * x + 0.2 * hidden)
    input_gate = sigmoid(1.0 * x + 0.35 * hidden - 0.35)
    candidate = np.tanh(1.15 * x + 0.45 * hidden - 0.45)
    next_cell = forget * cell + input_gate * candidate
    output_gate = sigmoid(0.9 * x + 0.25 * hidden)
    next_hidden = np.abs(output_gate * np.tanh(next_cell))
    q = next_hidden * sigma * geom * k / max(tau, 1.0e-8)
    for dim in enriched:
        q[dim] = -1.0
    return q, next_hidden, next_cell


def make_case(rng: random.Random, mu: np.ndarray, sigma: np.ndarray, tau: float) -> dict[str, Any]:
    n_actions, n_dims = mu.shape
    true_action = rng.randrange(n_actions)
    distractor = max((a for a in range(n_actions) if a != true_action), key=lambda a: float(np.linalg.norm(mu[true_action] - mu[a])))
    full = np.clip(mu[true_action] + np.array([rng.gauss(0.0, 0.035) for _ in range(n_dims)]), 0.02, 0.98)
    diff = np.abs(mu[true_action] - mu[distractor])
    wrong_dims = set(np.argsort(diff)[::-1][: 1 if rng.random() < 0.35 else 2])
    surface = full.copy()
    for dim in wrong_dims:
        surface[int(dim)] = np.clip(mu[distractor, int(dim)] + rng.gauss(0.0, 0.03), 0.02, 0.98)
    correct_action, full_probs, _ = score(mu, sigma, tau, full)
    surface_action, surface_probs, _ = score(mu, sigma, tau, surface)
    informative: set[int] = set()
    for dim in range(n_dims):
        candidate = surface.copy()
        candidate[dim] = full[dim]
        action, probs, _margin = score(mu, sigma, tau, candidate)
        gain = float(probs[correct_action] - surface_probs[correct_action])
        gap = abs(float(mu[correct_action, dim] - mu[surface_action, dim]))
        if action == correct_action or (gain >= 0.02 and gap >= 0.08):
            informative.add(dim)
    if not informative:
        informative.update(int(d) for d in wrong_dims)
    return {"surface": surface, "full": full, "correct_action": int(correct_action), "informative": informative}


def select_dims(
    variant: str,
    mu: np.ndarray,
    sigma: np.ndarray,
    tau: float,
    case: dict[str, Any],
    k: np.ndarray,
    budget: int,
) -> dict[str, Any]:
    v = np.asarray(case["surface"], dtype=np.float64).copy()
    full = np.asarray(case["full"], dtype=np.float64)
    enriched: set[int] = set()
    selected: list[int] = []
    evals = 1
    hidden = np.zeros(mu.shape[1], dtype=np.float64)
    cell = np.zeros(mu.shape[1], dtype=np.float64)

    if variant == "static":
        _action, probs, _margin = score(mu, sigma, tau, v)
        q = q_rnn(mu, sigma, v, probs, set(), k)
        planned = [int(d) for d in np.argsort(q)[::-1] if float(q[int(d)]) > 0.0][:budget]
        for dim in planned:
            selected.append(dim)
            enriched.add(dim)
            if dim in case["informative"]:
                v[dim] = full[dim]
        evals += 1
    else:
        for _ in range(min(budget, mu.shape[1])):
            _action, probs, _margin = score(mu, sigma, tau, v)
            evals += 1
            if variant == "rnn":
                q = q_rnn(mu, sigma, v, probs, enriched, k)
            elif variant == "gru":
                q, hidden = q_gru(mu, sigma, tau, v, probs, enriched, k, hidden)
            elif variant == "lstm":
                q, hidden, cell = q_lstm(mu, sigma, tau, v, probs, enriched, k, hidden, cell)
            else:
                raise ValueError(variant)
            dim = int(np.argmax(q))
            if float(q[dim]) <= 0.0:
                break
            selected.append(dim)
            enriched.add(dim)
            if dim in case["informative"]:
                v[dim] = full[dim]
    final_action, _probs, _margin = score(mu, sigma, tau, v)
    evals += 1
    informative_reads = sum(1 for dim in selected if dim in case["informative"])
    return {
        "selected": selected,
        "informative_reads": informative_reads,
        "reads": len(selected),
        "correct": final_action == int(case["correct_action"]),
        "scorer_evals": evals,
    }


def update_k(weights: np.ndarray, selected: list[int], informative: set[int], correct: bool) -> None:
    for dim in selected:
        if correct and dim in informative:
            weights[dim] = min(3.0, weights[dim] + 0.02)
        else:
            weights[dim] = max(0.1, weights[dim] - 0.005)


def evaluate_variant(
    variant: str,
    categories: list[str],
    mu_by_category: dict[str, np.ndarray],
    sigma: np.ndarray,
    tau: float,
    weights_by_category: dict[str, np.ndarray],
    budget: int,
    rng: random.Random,
) -> dict[str, float]:
    stats = {"reads": 0, "informative": 0, "correct": 0, "evals": 0}
    for _ in range(EVAL_SCENARIOS):
        category = rng.choice(categories)
        case = make_case(rng, mu_by_category[category], sigma, tau)
        run = select_dims(variant, mu_by_category[category], sigma, tau, case, weights_by_category[category], budget)
        stats["reads"] += run["reads"]
        stats["informative"] += run["informative_reads"]
        stats["correct"] += int(run["correct"])
        stats["evals"] += run["scorer_evals"]
    reads = max(1, stats["reads"])
    evals = max(1, stats["evals"])
    return {
        "routing_quality": stats["informative"] / reads,
        "accuracy": stats["correct"] / EVAL_SCENARIOS,
        "accuracy_per_scorer_eval": stats["correct"] / evals,
        "scorer_evals_per_decision": stats["evals"] / EVAL_SCENARIOS,
    }


def run_seed(
    variant: str,
    categories: list[str],
    mu_by_category: dict[str, np.ndarray],
    sigma: np.ndarray,
    tau: float,
    budget: int,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    weights = {category: np.full(len(sigma), BASELINE_WEIGHT, dtype=np.float64) for category in categories}
    checkpoints = []
    selected_counts = {category: np.zeros(len(sigma), dtype=np.int64) for category in categories}
    for decision in range(1, TOTAL_DECISIONS + 1):
        category = rng.choice(categories)
        case = make_case(rng, mu_by_category[category], sigma, tau)
        run = select_dims(variant, mu_by_category[category], sigma, tau, case, weights[category], budget)
        for dim in run["selected"]:
            selected_counts[category][dim] += 1
        update_k(weights[category], run["selected"], set(case["informative"]), bool(run["correct"]))
        if decision % CHECKPOINT_INTERVAL == 0:
            eval_rng = random.Random(seed + 100_000 + decision)
            learned = evaluate_variant(variant, categories, mu_by_category, sigma, tau, weights, budget, eval_rng)
            control_weights = {category: np.full(len(sigma), BASELINE_WEIGHT, dtype=np.float64) for category in categories}
            control = evaluate_variant(variant, categories, mu_by_category, sigma, tau, control_weights, budget, eval_rng)
            checkpoints.append({
                "decision_count": decision,
                "routing_quality": learned["routing_quality"],
                "routing_quality_no_k": control["routing_quality"],
                "accuracy": learned["accuracy"],
                "accuracy_per_scorer_eval": learned["accuracy_per_scorer_eval"],
                "scorer_evals_per_decision": learned["scorer_evals_per_decision"],
            })
    total_cells = len(categories) * len(sigma)
    starved = sum(int(selected_counts[c][d] == 0) for c in categories for d in range(len(sigma)))
    return {"checkpoints": checkpoints, "starvation_rate": starved / total_cells}


def aggregate(seed_runs: list[dict[str, Any]]) -> dict[str, Any]:
    checkpoints = []
    for index in range(len(seed_runs[0]["checkpoints"])):
        rows = [run["checkpoints"][index] for run in seed_runs]
        checkpoints.append({
            "decision_count": rows[0]["decision_count"],
            "routing_mean": mean(row["routing_quality"] for row in rows),
            "routing_std": pstdev(row["routing_quality"] for row in rows),
            "routing_no_k_mean": mean(row["routing_quality_no_k"] for row in rows),
            "accuracy_mean": mean(row["accuracy"] for row in rows),
            "accuracy_std": pstdev(row["accuracy"] for row in rows),
            "accuracy_per_scorer_eval_mean": mean(row["accuracy_per_scorer_eval"] for row in rows),
            "scorer_evals_per_decision_mean": mean(row["scorer_evals_per_decision"] for row in rows),
        })
    final = checkpoints[-1]
    return {
        "checkpoints": checkpoints,
        "final_routing_mean": final["routing_mean"],
        "final_routing_std": final["routing_std"],
        "final_accuracy_mean": final["accuracy_mean"],
        "final_accuracy_std": final["accuracy_std"],
        "final_accuracy_per_scorer_eval": final["accuracy_per_scorer_eval_mean"],
        "starvation_rate": mean(run["starvation_rate"] for run in seed_runs),
        "scorer_evals_per_decision": final["scorer_evals_per_decision_mean"],
        "m_gov_interpretable_hidden_state": True,
    }


def run_budget(categories: list[str], mu_by_category: dict[str, np.ndarray], sigma: np.ndarray, tau: float, budget: int) -> dict[str, Any]:
    result = {}
    for variant in VARIANTS:
        runs = [
            run_seed(variant, categories, mu_by_category, sigma, tau, budget, BASE_SEED + budget * 10_000 + seed)
            for seed in range(SEEDS)
        ]
        result[variant] = aggregate(runs)
        print(f"budget={budget} {variant}: routing={result[variant]['final_routing_mean']:.3f}")
    return result


def main() -> None:
    info = load_geometry()
    categories = list(info.get("category_names") or info["all_category_mu"].keys())
    factor_names = list(info["factor_names"])
    sigma = np.asarray(info.get("sigma") or [1.0] * len(factor_names), dtype=np.float64)
    tau = float(info.get("tau", 0.1))
    mu_by_category = {category: np.asarray(info["all_category_mu"][category], dtype=np.float64) for category in categories}

    budget_sweep = {str(budget): run_budget(categories, mu_by_category, sigma, tau, budget) for budget in BUDGETS}
    results = budget_sweep[str(BUDGET)]
    gru = results["gru"]["final_routing_mean"]
    lstm = results["lstm"]["final_routing_mean"]
    if lstm - gru >= 0.02:
        verdict = "LSTM"
        reason = f"LSTM exceeded GRU by {(lstm - gru) * 100:.2f}pp at matched budget/cost."
    else:
        verdict = "GRU"
        reason = f"LSTM margin over GRU was {(lstm - gru) * 100:.2f}pp, below the pre-registered 2pp keep threshold."

    payload = {
        "variants": list(VARIANTS),
        "copilot": "dataops",
        "budget": BUDGET,
        "seeds": SEEDS,
        "total_decisions": TOTAL_DECISIONS,
        "checkpoint_interval": CHECKPOINT_INTERVAL,
        "evaluation_scenarios_per_checkpoint": EVAL_SCENARIOS,
        "factor_names": factor_names,
        "results": results,
        "budget_sweep": budget_sweep,
        "kill_keep_verdict": verdict,
        "kill_keep_reason": reason,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"RV-0 verdict: {verdict} -- {reason}")


if __name__ == "__main__":
    main()
