"""A2: adversarial evidence stress test for saves/hurts.

Pre-registration: under adversarial construction VLD will produce some hurts;
the adversarial saves:hurts ratio will be lower than Astra's favorable 57:0.
The result is reported regardless of whether that expectation is met.

Metric definitions:
* action_accuracy is final action == nearest-centroid target from truth.
* save is pre-investigation wrong -> post-investigation right.
* hurt is pre-investigation right -> post-investigation wrong.

This is a new experiment-only harness.  It reuses VLDInvestigator and its Q
function, but keeps ``truth`` separate from ``evidence`` so an acquired read
can be actively misleading without changing the geometry-derived target.
Tier: GEOMETRY-DERIVED + SIMULATED.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, cast

import numpy as np

from copilot_sdk.scoring.investigation import VLDInvestigator


ROOT = Path(__file__).resolve().parents[2]
CENTROIDS = ROOT / "real_centroids_v1.json"
RESULT = ROOT / "experiments" / "vld" / "results" / "adversarial_saves_hurts.json"
SEEDS = (42, 123, 7)
COPILOTS = ("soc", "dataops", "trading", "purchasing", "s2p")
COUNTS = {"boundary": 80, "misleading": 100, "adversarial_q": 70}
BUDGET = 2


def load_geometry() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(CENTROIDS.read_text(encoding="utf-8"))["copilots"])


def investigator_for(info: dict[str, Any], category: str) -> VLDInvestigator:
    mu = np.asarray(info["all_category_mu"][category], dtype=np.float64)
    return VLDInvestigator(mu, np.asarray(info["sigma"], dtype=np.float64),
                           list(info["factor_names"]), tau=float(info.get("tau", 0.1)))


def score(inv: VLDInvestigator, vector: np.ndarray) -> int:
    return int(inv.score(vector)[0])


def closest_pair(mu: np.ndarray) -> tuple[int, int]:
    best: tuple[float, int, int] | None = None
    for left in range(mu.shape[0]):
        for right in range(left + 1, mu.shape[0]):
            distance = float(np.linalg.norm(mu[left] - mu[right]))
            candidate = (distance, left, right)
            if best is None or candidate < best:
                best = candidate
    if best is None:
        raise ValueError("at least two actions are required")
    return best[1], best[2]


def top_q(inv: VLDInvestigator, vector: np.ndarray, weights: np.ndarray) -> list[int]:
    action, probabilities = inv.score(vector)
    _ = action
    q = inv.compute_Q(vector, probabilities, set(), K_weights=weights)
    return [int(index) for index in np.argsort(q)[::-1][:BUDGET]]


def noisy_centroid(rng: random.Random, centroid: np.ndarray, scale: float = 0.012) -> np.ndarray:
    noise = np.asarray([rng.gauss(0.0, scale) for _ in range(centroid.size)], dtype=np.float64)
    return cast(np.ndarray, np.clip(centroid + noise, 0.02, 0.98))


def make_case(rng: random.Random, tier: str, info: dict[str, Any], category: str) -> dict[str, Any]:
    mu = np.asarray(info["all_category_mu"][category], dtype=np.float64)
    n_actions, n_dims = mu.shape
    weights = np.full(n_dims, 0.5, dtype=np.float64)
    left, right = closest_pair(mu)
    true_action = left if rng.random() < 0.5 else right
    wrong_action = right if true_action == left else left

    if tier == "boundary":
        midpoint = (mu[true_action] + mu[wrong_action]) / 2.0
        direction = mu[true_action] - mu[wrong_action]
        truth = np.clip(midpoint + direction * rng.uniform(0.015, 0.045), 0.02, 0.98)
        surface = truth.copy()
        changed = int(np.argmax(np.abs(direction)))
        surface[changed] = np.clip(mu[wrong_action, changed] + rng.gauss(0.0, 0.01), 0.02, 0.98)
        evidence = truth.copy()
        spec = "closest action-pair midpoint with small truth-side perturbation; one partial dimension is wrong"
    else:
        truth = noisy_centroid(rng, mu[true_action], 0.018)
        surface = truth.copy()
        initial_q = top_q(investigator_for(info, category), surface, weights)
        if tier == "misleading":
            # The surface is initially complete-looking; the provider's acquired
            # values on Q-selected dimensions are then wrong-action values.
            evidence = truth.copy()
            for dim in initial_q:
                evidence[dim] = np.clip(mu[wrong_action, dim] + rng.gauss(0.0, 0.008), 0.02, 0.98)
            spec = "initial Q top-2 dimensions receive wrong-action evidence; remaining acquired values are truthful"
        else:
            # Severe tier makes every potentially selected read align to the
            # wrong action, including after the first read changes Q rankings.
            evidence = noisy_centroid(rng, mu[wrong_action], 0.008)
            spec = "all acquired values are aligned to the wrong action, targeting the Q-ranked dimensions"

    inv = investigator_for(info, category)
    target = score(inv, truth)
    return {"category": category, "truth": truth, "surface": surface,
            "evidence": evidence, "target": target, "construction": spec,
            "n_actions": n_actions, "n_dims": n_dims}


def run_case(case: dict[str, Any], info: dict[str, Any]) -> dict[str, Any]:
    category = str(case["category"])
    inv = investigator_for(info, category)
    weights = np.full(int(case["n_dims"]), 0.5, dtype=np.float64)
    vector = np.asarray(case["surface"], dtype=np.float64).copy()
    evidence = np.asarray(case["evidence"], dtype=np.float64)
    target = int(case["target"])
    pre = score(inv, vector)
    selected: list[int] = []
    enriched: set[int] = set()
    for _ in range(min(BUDGET, vector.size)):
        before_action, probabilities = inv.score(vector)
        _ = before_action
        q = inv.compute_Q(vector, probabilities, enriched, K_weights=weights)
        dim = int(np.argmax(q))
        if dim in enriched or float(q[dim]) <= 0.0:
            break
        enriched.add(dim)
        selected.append(dim)
        vector[dim] = evidence[dim]
    post = score(inv, vector)
    return {"pre": pre, "post": post, "target": target, "selected": selected,
            "pre_correct": pre == target, "post_correct": post == target,
            "saved": pre != target and post == target,
            "hurt": pre == target and post != target}


def build_cases(info: dict[str, Any], copilot: str, seed: int) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(seed)
    categories = list(info["all_category_mu"].keys())
    result: dict[str, list[dict[str, Any]]] = {}
    for tier, count in COUNTS.items():
        result[tier] = [make_case(rng, tier, info, categories[index % len(categories)])
                        for index in range(count)]
    _ = copilot
    return result


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    saves = sum(int(run["saved"]) for run in runs)
    hurts = sum(int(run["hurt"]) for run in runs)
    neutral_correct = sum(int(run["pre_correct"] and run["post_correct"]) for run in runs)
    neutral_wrong = sum(int(not run["pre_correct"] and not run["post_correct"]) for run in runs)
    return {"saves": saves, "hurts": hurts, "neutral_correct": neutral_correct,
            "neutral_wrong": neutral_wrong, "ratio": f"{saves}:{hurts}",
            "action_accuracy": sum(int(run["post_correct"]) for run in runs) / len(runs),
            "pre_action_accuracy": sum(int(run["pre_correct"]) for run in runs) / len(runs),
            "n_scenarios": len(runs)}


def evaluate_once(geometry: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for copilot in COPILOTS:
        info = geometry[copilot]
        copilot_result: dict[str, Any] = {}
        total_runs: list[dict[str, Any]] = []
        for tier in COUNTS:
            per_seed: dict[str, Any] = {}
            aggregate_runs: list[dict[str, Any]] = []
            for seed in SEEDS:
                cases = build_cases(info, copilot, seed)[tier]
                runs = [run_case(case, info) for case in cases]
                aggregate_runs.extend(runs)
                per_seed[str(seed)] = summarize(runs)
            copilot_result[tier] = {"per_seed": per_seed, "aggregate": summarize(aggregate_runs)}
            total_runs.extend(aggregate_runs)
        copilot_result["all_tiers"] = summarize(total_runs)
        output[copilot] = copilot_result
    return output


def canonical_payload(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def write_summary(data: dict[str, Any]) -> None:
    lines = ["# A2 — Adversarial saves:hurts", "", "Tier: GEOMETRY-DERIVED + SIMULATED.",
             "", "## Construction", "",
             "Boundary uses closest action-pair midpoints with a small truth-side perturbation and one wrong partial dimension. Misleading cases make the initial Q top-2 acquired values align with a wrong action while the latent truth remains geometry-derived. Adversarial-Q cases align all acquired values with the wrong action so Q cannot recover through a second read. Truth and acquired evidence are separate by design.", "",
             "## Results", "", "| Copilot | Tier | Saves | Hurts | Ratio | Pre action_accuracy | Post action_accuracy |", "|---|---|---:|---:|---|---:|---:|"]
    all_saves = all_hurts = 0
    for copilot in COPILOTS:
        for tier in COUNTS:
            row = data[copilot][tier]["aggregate"]
            lines.append(f"| {copilot} | {tier} | {row['saves']} | {row['hurts']} | {row['ratio']} | {row['pre_action_accuracy']:.1%} | {row['action_accuracy']:.1%} |")
        row = data[copilot]["all_tiers"]
        all_saves += int(row["saves"])
        all_hurts += int(row["hurts"])
        lines.append(f"| **{copilot}** | **all tiers** | **{row['saves']}** | **{row['hurts']}** | **{row['ratio']}** | {row['pre_action_accuracy']:.1%} | {row['action_accuracy']:.1%} |")
    most = max(COUNTS, key=lambda tier: sum(int(data[c][tier]["aggregate"]["hurts"]) for c in COPILOTS))
    lines += ["", "## Interpretation", "",
              f"Across all 5 copilots × 3 seeds, adversarial construction produced {all_saves}:{all_hurts} saves:hurts; Astra's favorable paper-sourced reference is 57:0. The tier with the most hurts is **{most}**.",
              "", "Paper sentence: On favorable scenarios, VLD achieved 57:0 saves:hurts. On adversarial-constructed scenarios with misleading evidence, the ratio was " + f"{all_saves}:{all_hurts} — the favorable result does not establish robustness to actively incorrect evidence." ,
              "", "No labels or verified outcomes are used by the action/read pipeline; they are used only for post hoc geometry-derived scoring."]
    (RESULT.parent / "adversarial_saves_hurts_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    geometry = load_geometry()
    first = evaluate_once(geometry)
    second = evaluate_once(geometry)
    if canonical_payload(first) != canonical_payload(second):
        raise RuntimeError("determinism self-test failed")
    payload: dict[str, Any] = dict(first)
    payload["metadata"] = {
        "seeds": list(SEEDS), "scenarios_per_copilot": 250,
        "tier_counts": COUNTS,
        "construction_spec": {
            "boundary": "closest action-pair midpoint plus small truth-side perturbation; one partial dimension set toward the competing action",
            "misleading": "initial Q top-2 dimensions receive wrong-action acquired evidence; all other acquired dimensions are truthful",
            "adversarial_q": "all acquired values are generated from the wrong action, targeting dimensions selected by Q",
        },
        "pre_registered_rule": "report honestly; hurts expected and should reduce the favorable 57:0 ratio",
        "tier": "GEOMETRY-DERIVED + SIMULATED",
        "comparison": "Astra 57:0 was favorable construction; this is adversarial",
        "determinism_two_rebuilds": True,
        "source": "scripts/k_learning_curve_cross_copilot.py VLDInvestigator Q-selection reused in standalone experiment script",
    }
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(payload)
    print(f"wrote {RESULT}")
    for copilot in COPILOTS:
        row = payload[copilot]["all_tiers"]
        print(f"{copilot}: saves={row['saves']} hurts={row['hurts']} ratio={row['ratio']} action_accuracy={row['action_accuracy']:.3f}")
    print("payload_sha256=" + hashlib.sha256(canonical_payload(first).encode()).hexdigest())


if __name__ == "__main__":
    main()
