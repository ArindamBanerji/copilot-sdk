"""RV-1 routing variant experiment: greedy vs Thompson/UCB exploration.

Artifact-only experiment code. It reads exported centroid geometry and writes
experiments/vld/rv1_bandit_results.json. It does not modify production source.
"""

from __future__ import annotations

import json
from pathlib import Path
import random
from statistics import mean, pstdev
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CENTROIDS_PATH = ROOT / "real_centroids_v1.json"
OUT_PATH = ROOT / "experiments" / "vld" / "rv1_bandit_results.json"

COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")
VARIANTS = ("greedy", "thompson", "ucb")
TOTAL_DECISIONS = 500
CHECKPOINT_INTERVAL = 50
EVAL_SCENARIOS = 50
SEEDS = 10
BUDGET = 2
BASE_SEED = 20260912
BASELINE_WEIGHT = 0.5


def load_export() -> dict[str, Any]:
    return json.loads(CENTROIDS_PATH.read_text(encoding="utf-8"))["copilots"]


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
    correct_action, _full_probs, _ = score(mu, sigma, tau, full)
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


def choose_dim(
    variant: str,
    q: np.ndarray,
    sigma: np.ndarray,
    attempts: np.ndarray,
    rng: random.Random,
) -> int:
    valid = np.where(q > 0.0)[0]
    if valid.size == 0:
        return -1
    if variant == "greedy":
        scores = q
    elif variant == "thompson":
        scores = q.copy()
        for dim in valid:
            std = float(sigma[int(dim)] / np.sqrt(float(attempts[int(dim)] + 1)))
            scores[int(dim)] = rng.gauss(float(q[int(dim)]), std)
    elif variant == "ucb":
        scores = q + sigma / np.sqrt(attempts + 1.0)
    else:
        raise ValueError(variant)
    masked = np.full_like(scores, -1.0e9)
    masked[valid] = scores[valid]
    return int(np.argmax(masked))


def run_case(
    variant: str,
    mu: np.ndarray,
    sigma: np.ndarray,
    tau: float,
    case: dict[str, Any],
    k: np.ndarray,
    attempts: np.ndarray,
    rng: random.Random,
    update_attempts: bool,
) -> dict[str, Any]:
    v = np.asarray(case["surface"], dtype=np.float64).copy()
    full = np.asarray(case["full"], dtype=np.float64)
    enriched: set[int] = set()
    selected: list[int] = []
    surface_action, _surface_probs, _surface_margin = score(mu, sigma, tau, v)
    for _ in range(min(BUDGET, len(v))):
        _action, probs, _margin = score(mu, sigma, tau, v)
        q = q_rnn(mu, sigma, v, probs, enriched, k)
        dim = choose_dim(variant, q, sigma, attempts, rng)
        if dim < 0:
            break
        selected.append(dim)
        enriched.add(dim)
        if update_attempts:
            attempts[dim] += 1
        if dim in case["informative"]:
            v[dim] = full[dim]
    final_action, _final_probs, _final_margin = score(mu, sigma, tau, v)
    return {
        "selected": selected,
        "reads": len(selected),
        "informative_reads": sum(1 for dim in selected if dim in case["informative"]),
        "correct": final_action == int(case["correct_action"]),
        "saved": surface_action != int(case["correct_action"]) and final_action == int(case["correct_action"]),
    }


def update_k(weights: np.ndarray, selected: list[int], informative: set[int], correct: bool) -> None:
    for dim in selected:
        if correct and dim in informative:
            weights[dim] = min(3.0, weights[dim] + 0.02)
        else:
            weights[dim] = max(0.1, weights[dim] - 0.005)


def evaluate(
    variant: str,
    categories: list[str],
    mu_by_category: dict[str, np.ndarray],
    sigma: np.ndarray,
    tau: float,
    weights: dict[str, np.ndarray],
    attempts: dict[str, np.ndarray],
    rng: random.Random,
) -> dict[str, float]:
    stats = {"reads": 0, "informative": 0, "correct": 0, "saves": 0}
    for _ in range(EVAL_SCENARIOS):
        category = rng.choice(categories)
        case = make_case(rng, mu_by_category[category], sigma, tau)
        run = run_case(variant, mu_by_category[category], sigma, tau, case, weights[category], attempts[category].copy(), rng, False)
        stats["reads"] += run["reads"]
        stats["informative"] += run["informative_reads"]
        stats["correct"] += int(run["correct"])
        stats["saves"] += int(run["saved"])
    return {
        "routing_quality": stats["informative"] / max(1, stats["reads"]),
        "accuracy": stats["correct"] / EVAL_SCENARIOS,
        "saves": float(stats["saves"]),
    }


def run_seed(
    variant: str,
    categories: list[str],
    mu_by_category: dict[str, np.ndarray],
    sigma: np.ndarray,
    tau: float,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    weights = {category: np.full(len(sigma), BASELINE_WEIGHT, dtype=np.float64) for category in categories}
    attempts = {category: np.zeros(len(sigma), dtype=np.float64) for category in categories}
    checkpoints = []
    for decision in range(1, TOTAL_DECISIONS + 1):
        category = rng.choice(categories)
        case = make_case(rng, mu_by_category[category], sigma, tau)
        run = run_case(variant, mu_by_category[category], sigma, tau, case, weights[category], attempts[category], rng, True)
        update_k(weights[category], run["selected"], set(case["informative"]), bool(run["correct"]))
        if decision % CHECKPOINT_INTERVAL == 0:
            eval_rng = random.Random(seed + 100_000 + decision)
            metrics = evaluate(variant, categories, mu_by_category, sigma, tau, weights, attempts, eval_rng)
            checkpoints.append({"decision_count": decision, **metrics})
    total_cells = len(categories) * len(sigma)
    starved = sum(int(attempts[c][d] == 0) for c in categories for d in range(len(sigma)))
    return {"checkpoints": checkpoints, "starvation_rate": starved / total_cells, "attempts": {c: attempts[c].tolist() for c in categories}}


def decisions_to_90(checkpoints: list[dict[str, float]]) -> int:
    final = float(checkpoints[-1]["routing_mean"])
    target = 0.9 * final
    for row in checkpoints:
        if float(row["routing_mean"]) >= target:
            return int(row["decision_count"])
    return int(checkpoints[-1]["decision_count"])


def aggregate(seed_runs: list[dict[str, Any]]) -> dict[str, Any]:
    checkpoints = []
    for index in range(len(seed_runs[0]["checkpoints"])):
        rows = [run["checkpoints"][index] for run in seed_runs]
        checkpoints.append({
            "decision_count": rows[0]["decision_count"],
            "routing_mean": mean(row["routing_quality"] for row in rows),
            "routing_std": pstdev(row["routing_quality"] for row in rows),
            "accuracy_mean": mean(row["accuracy"] for row in rows),
            "accuracy_std": pstdev(row["accuracy"] for row in rows),
            "saves_mean": mean(row["saves"] for row in rows),
        })
    return {
        "checkpoints": checkpoints,
        "final_routing_mean": checkpoints[-1]["routing_mean"],
        "final_routing_std": checkpoints[-1]["routing_std"],
        "final_accuracy_mean": checkpoints[-1]["accuracy_mean"],
        "starvation": mean(run["starvation_rate"] for run in seed_runs),
        "decisions_to_90pct_asymptote": decisions_to_90(checkpoints),
    }


def run_copilot(copilot: str, info: dict[str, Any]) -> dict[str, Any]:
    categories = list(info.get("category_names") or info["all_category_mu"].keys())
    factor_names = list(info["factor_names"])
    sigma = np.asarray(info.get("sigma") or [1.0] * len(factor_names), dtype=np.float64)
    tau = float(info.get("tau", 0.1))
    mu_by_category = {category: np.asarray(info["all_category_mu"][category], dtype=np.float64) for category in categories}
    result = {}
    for variant in VARIANTS:
        seed_runs = [
            run_seed(variant, categories, mu_by_category, sigma, tau, BASE_SEED + seed + sum(ord(ch) for ch in copilot) * 100)
            for seed in range(SEEDS)
        ]
        result[variant] = aggregate(seed_runs)
        print(
            f"{copilot:10s} {variant:8s}: routing={result[variant]['final_routing_mean']:.3f} "
            f"starvation={result[variant]['starvation']:.3f}"
        )
    result["_metadata"] = {"factor_names": factor_names, "category_names": categories}
    return result


def verdict(results: dict[str, Any]) -> tuple[str, str]:
    trading = results["trading"]
    greedy_starvation = float(trading["greedy"]["starvation"])
    candidates = []
    for variant in ("thompson", "ucb"):
        reduction = greedy_starvation - float(trading[variant]["starvation"])
        routing_ok = float(trading[variant]["final_routing_mean"]) >= float(trading["greedy"]["final_routing_mean"])
        speed_ok = int(trading[variant]["decisions_to_90pct_asymptote"]) <= int(trading["greedy"]["decisions_to_90pct_asymptote"])
        if reduction >= 0.10 and routing_ok and speed_ok:
            candidates.append((variant, reduction, float(trading[variant]["final_routing_mean"])))
    if not candidates:
        return "greedy", "No bandit variant met all pre-registered keep criteria on Trading starvation, routing quality, and speed."
    candidates.sort(key=lambda row: (row[1], row[2]), reverse=True)
    winner = candidates[0][0]
    return winner, f"{winner} met the keep criteria with Trading starvation reduction of {candidates[0][1] * 100:.1f}pp."


def main() -> None:
    export = load_export()
    results = {copilot: run_copilot(copilot, export[copilot]) for copilot in COPILOTS}
    starvation_reduction: dict[str, float] = {}
    for copilot in COPILOTS:
        for variant in VARIANTS:
            starvation_reduction[f"{copilot}_{variant}"] = float(results[copilot][variant]["starvation"]) * 100.0
    keep, reason = verdict(results)
    payload = {
        "variants": list(VARIANTS),
        "copilots": list(COPILOTS),
        "budget": BUDGET,
        "seeds": SEEDS,
        "total_decisions": TOTAL_DECISIONS,
        "checkpoint_interval": CHECKPOINT_INTERVAL,
        "evaluation_scenarios_per_checkpoint": EVAL_SCENARIOS,
        "results": results,
        "starvation_reduction": starvation_reduction,
        "kill_keep_verdict": keep,
        "kill_keep_reason": reason,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"RV-1 verdict: {keep} -- {reason}")


if __name__ == "__main__":
    main()
