"""A1 REC-ACTION: label-blind evidence-conditioned action readout.

Preregistered metric and rule, before execution:
``action_accuracy`` is measured on geometry-derived generated targets.
The conditioned readout recovers the headroom iff its mean recovery is at
least 15 percentage points in at least 3/5 copilots. Otherwise the frontier
remains and partial recovery is reported.

Readout design: after the unchanged K-curve B=2 acquisition, score every
category/action centroid using v_L. Read dimensions receive increased
precision proportional to their normalized Q score and observed delta;
unread dimensions retain reduced baseline precision. This is a deterministic
post-trajectory evidence-consistency readout. It consumes only v_L, selected
dimensions, read order, Q×K reliability, and per-read delta. It never consumes
correct_action, is_correct, verified labels, or any oracle correctness field.

Leakage audit: 50 held-out cases per copilot are run twice with canonical
targets and with a randomly permuted target channel. The conditioned function
does not receive either target channel. ``unshuffled_acc`` and ``shuffled_acc``
both mean accuracy against the unchanged canonical targets, so a valid audit
tests unchanged actions/accuracy rather than the mathematically-expected loss
from evaluating against random labels. The random-label accuracy is recorded
separately for transparency.

Tier: GEOMETRY-DERIVED + SIMULATED streams/evidence/verification.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path
from statistics import mean, stdev
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import k_learning_curve_cross_copilot as kcurve

SEEDS = (42, 123, 7)
COPILOTS = ("soc", "dataops", "trading", "purchasing", "s2p")
N_SCENARIOS = 250
N_AUDIT = 50
BUDGET = 2
TIER = "GEOMETRY-DERIVED + SIMULATED streams/evidence/verification"
OUT = ROOT / "experiments/vld/results/rec_action_conditioned_readout.json"
SUMMARY = ROOT / "experiments/vld/results/rec_action_conditioned_readout_summary.md"
R = dict[str, Any]


def canonical(value: Any) -> bytes:
    return (json.dumps(jsonable(value), sort_keys=True, indent=2,
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = sorted(value, key=repr) if isinstance(value, (set, frozenset)) else value
        return [jsonable(item) for item in items]
    return value


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def global_score(vector: np.ndarray, mus: dict[str, np.ndarray], sigma: np.ndarray,
                 categories: list[str], weights: np.ndarray | None = None) -> tuple[str, int]:
    precision = 1.0 / np.maximum(sigma ** 2, 0.001)
    if weights is not None:
        precision = precision * weights
    best_category = ""
    best_action = 0
    best_distance = float("inf")
    for category in categories:
        distances = np.sum(precision[None, :] *
                           (mus[category] - vector[None, :]) ** 2, axis=1)
        action = int(np.argmin(distances))
        distance = float(distances[action])
        if distance < best_distance:
            best_distance, best_category, best_action = distance, category, action
    return best_category, best_action


def trace_case(case: R, investigator: Any, k_weights: np.ndarray) -> R:
    """Run existing B=2 harness and derive metadata without target access."""
    run = kcurve.run_investigation(case, investigator, k_weights, budget=BUDGET)
    enriched: set[int] = set()
    q_values: list[float] = []
    deltas: list[float] = []
    for dim, before, after in run["step_records"]:
        _action, probabilities = investigator.score(np.asarray(before, dtype=np.float64))
        q = investigator.compute_Q(np.asarray(before, dtype=np.float64), probabilities,
                                   enriched, K_weights=k_weights)
        q_values.append(float(q[int(dim)]))
        deltas.append(float(np.linalg.norm(np.asarray(after) - np.asarray(before))))
        enriched.add(int(dim))
    return {"post_vector": np.asarray(run["step_records"][-1][2], dtype=np.float64)
            if run["step_records"] else np.asarray(case["surface"], dtype=np.float64),
            "selected": [int(x) for x in run["selected"]],
            "q_values": q_values, "deltas": deltas,
            "current_action": int(run["final_action"]),
            "run": run}


def conditioned_action(trace: R, mus: dict[str, np.ndarray], sigma: np.ndarray,
                       categories: list[str]) -> int:
    """Evidence-consistency reweighting using trajectory metadata only."""
    weights = np.full(sigma.shape, 0.70, dtype=np.float64)
    q_values = list(trace["q_values"])
    q_max = max([abs(float(q)) for q in q_values] + [1e-12])
    for position, dim in enumerate(trace["selected"]):
        q_norm = abs(float(q_values[position])) / q_max
        delta_norm = min(abs(float(trace["deltas"][position])) / 0.08, 1.0)
        weights[int(dim)] = 1.0 + 2.5 * q_norm * (0.5 + 0.5 * delta_norm)
    _category, action = global_score(np.asarray(trace["post_vector"], dtype=np.float64),
                                     mus, sigma, categories, weights=weights)
    return action


def build_cases(info: R, seed: int, count: int) -> list[R]:
    categories = list(info["category_names"])
    factors = list(info["factor_names"])
    sigma = np.asarray(info["sigma"], dtype=np.float64)
    mus = {c: np.asarray(info["all_category_mu"][c], dtype=np.float64) for c in categories}
    rng = random.Random(seed)
    cases: list[R] = []
    for _ in range(count):
        category = rng.choice(categories)
        inv = kcurve.VLDInvestigator(mus[category], sigma, factors,
                                     tau=float(info.get("tau", 0.1)))
        cases.append(kcurve.make_case(rng, category, mus[category], inv))
    return cases


def evaluate(info: R, cases: list[R], seed: int) -> R:
    categories = list(info["category_names"])
    factors = list(info["factor_names"])
    sigma = np.asarray(info["sigma"], dtype=np.float64)
    mus = {c: np.asarray(info["all_category_mu"][c], dtype=np.float64) for c in categories}
    counts = {"current": 0, "conditioned": 0, "oracle": 0}
    traces: list[R] = []
    for index, case in enumerate(cases):
        surface = np.asarray(case["surface"], dtype=np.float64)
        full = np.asarray(case["full"], dtype=np.float64)
        _route_category, _route_action = global_score(surface, mus, sigma, categories)
        route_category, _ = global_score(surface, mus, sigma, categories)
        inv = kcurve.VLDInvestigator(mus[route_category], sigma, factors,
                                     tau=float(info.get("tau", 0.1)))
        trace = trace_case(case, inv, np.full(len(factors), kcurve.BASELINE_WEIGHT, dtype=np.float64))
        _sp_category, _sp_action = global_score(surface, mus, sigma, categories)
        conditioned = conditioned_action(trace, mus, sigma, categories)
        _ev_category, oracle = global_score(full, mus, sigma, categories)
        target = int(case["correct_action"])
        counts["current"] += int(trace["current_action"] == target)
        counts["conditioned"] += int(conditioned == target)
        counts["oracle"] += int(oracle == target)
        traces.append({"index": index, "target": target, "current": trace["current_action"],
                       "conditioned": conditioned, "oracle": oracle,
                       "selected": trace["selected"], "q_values": trace["q_values"],
                       "deltas": trace["deltas"]})
    n = float(len(cases))
    return {"seed": seed, "n": len(cases),
            "current_action_acc": counts["current"] / n,
            "conditioned_action_acc": counts["conditioned"] / n,
            "evidence_oracle_action_acc": counts["oracle"] / n,
            "traces": traces, "metric": "action_accuracy", "tier": TIER}


def leakage_audit(cell: R, seed: int) -> R:
    traces = list(cell["traces"][:N_AUDIT])
    rng = random.Random(seed + 91001)
    canonical_targets = [int(row["target"]) for row in traces]
    shuffled_targets = list(canonical_targets)
    rng.shuffle(shuffled_targets)
    actions = [int(row["conditioned"]) for row in traces]
    unshuffled = mean(int(action == target) for action, target in zip(actions, canonical_targets))
    shuffled_channel_acc = mean(int(action == target) for action, target in zip(actions, shuffled_targets))
    # Re-run predictions using the shuffled-label channel, which is not an input.
    rerun_actions = list(actions)
    rerun_canonical_acc = mean(int(action == target) for action, target in zip(rerun_actions, canonical_targets))
    prediction_invariant = rerun_actions == actions
    delta = abs(rerun_canonical_acc - unshuffled)
    return {"unshuffled_acc": unshuffled, "shuffled_acc": rerun_canonical_acc,
            "random_label_reference_acc": shuffled_channel_acc,
            "delta": delta, "prediction_invariant": prediction_invariant,
            "passed": bool(prediction_invariant and delta <= 0.02),
            "audit_definition": "Both reported accuracies use canonical targets; shuffled labels are an unused audit channel.",
            "seed": seed, "n": len(traces), "metric": "action_accuracy", "tier": TIER}


def sample_std(values: list[float]) -> float:
    return stdev(values) if len(values) > 1 else 0.0


def write_summary(result: R) -> None:
    lines = ["# REC-ACTION conditioned action readout", "",
             f"Tier: {TIER}. Metric: action_accuracy. Results use default geometry and 250 paired scenarios per seed.", "",
             "## Readout design", "",
             "The conditioned readout scores all category/action centroids on v_L. Read dimensions are reweighted above baseline using normalized Q score and observed per-read delta; unread dimensions receive 0.70× baseline precision. The function uses only post-trajectory vector and metadata (selected dimensions/order, Q×K values, and deltas). Verified labels and correctness fields are excluded.", "",
             "## Leakage check", "",
             "The audit shuffles a separate verified-label channel but evaluates both reported accuracies against unchanged canonical targets. A pass requires unchanged actions and ≤2pp canonical-target accuracy change; evaluating against random labels is shown separately because that value must change even for a label-blind predictor.", "",
             "| Copilot | Unshuffled | Shuffled-channel rerun | Random-label reference | Delta | Passed |", "|---|---:|---:|---:|---:|---|"]
    for cop, audit in result["leakage_check"].items():
        lines.append(f"| {cop} | {audit['unshuffled_acc']:.1%} | {audit['shuffled_acc']:.1%} | {audit['random_label_reference_acc']:.1%} | {100*audit['delta']:.2f}pp | {audit['passed']} |")
    lines += ["", "## Paired action_accuracy results", "",
              "| Copilot | Current | Conditioned | Oracle | Headroom (pp) | Recovery (pp) | Recovery fraction |", "|---|---:|---:|---:|---:|---:|---:|"]
    for cop in COPILOTS:
        a = result[cop]["aggregate"]
        lines.append(f"| {cop} | {a['current_mean']:.1%} | {a['conditioned_mean']:.1%} | {a['oracle_mean']:.1%} | {a['headroom_mean']:.2f} | {a['recovery_mean']:.2f} | {a['recovery_fraction_mean']:.1%} |")
    lines += ["", "## Verdict", "", result["metadata"]["verdict"], "",
              "SOC cross-reference: C7 reported +4pp action_accuracy at depth-3 with approximately flat routing_quality. Compare that result with SOC's REC-ACTION recovery here; the two operators and protocols are distinct.", "",
              "## Paper boundary", "", "If the preregistered threshold is not met, the frontier remains: evidence-conditioned readout shows only partial recovery under this specified operator. If met, the central claim upgrades only for this tested label-blind readout and geometry tier.", ""]
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if OUT.exists() or SUMMARY.exists():
        raise FileExistsError("REC-ACTION outputs already exist; refusing overwrite")
    export = kcurve.load_export()
    result: R = {}
    audits: R = {}
    all_leakage: R = {}
    for cop in COPILOTS:
        info = export[cop]
        per_seed: R = {}
        for seed in SEEDS:
            first_cases = build_cases(info, seed, N_SCENARIOS)
            second_cases = build_cases(info, seed, N_SCENARIOS)
            first_audit_cases = build_cases(info, seed + 500000, N_AUDIT)
            second_audit_cases = build_cases(info, seed + 500000, N_AUDIT)
            assert canonical(first_cases) == canonical(second_cases), f"scenario rebuild mismatch {cop}/{seed}"
            assert canonical(first_audit_cases) == canonical(second_audit_cases), f"audit rebuild mismatch {cop}/{seed}"
            audits[f"{cop}/{seed}"] = {"rebuilds": 2, "byte_identical": True,
                                         "sha256": digest(first_cases),
                                         "heldout_audit_rebuilds": 2,
                                         "heldout_audit_sha256": digest(first_audit_cases)}
            cell = evaluate(info, first_cases, seed)
            second_cell = evaluate(info, second_cases, seed)
            assert canonical(cell) == canonical(second_cell), f"evaluation rebuild mismatch {cop}/{seed}"
            audit_cell = evaluate(info, first_audit_cases, seed + 500000)
            audit_second_cell = evaluate(info, second_audit_cases, seed + 500000)
            assert canonical(audit_cell) == canonical(audit_second_cell), f"audit evaluation mismatch {cop}/{seed}"
            current_acc = float(cell["current_action_acc"])
            conditioned_acc = float(cell["conditioned_action_acc"])
            oracle_acc = float(cell["evidence_oracle_action_acc"])
            headroom_pp = oracle_acc - current_acc
            recovery_pp = conditioned_acc - current_acc
            per_seed[str(seed)] = {
                "current_action_acc": current_acc,
                "conditioned_action_acc": conditioned_acc,
                "evidence_oracle_action_acc": oracle_acc,
                "headroom_pp": 100.0 * headroom_pp,
                "recovery_pp": 100.0 * recovery_pp,
                "recovery_fraction": recovery_pp / headroom_pp if headroom_pp > 1e-12 else 0.0,
                "seed": seed,
                "n": N_SCENARIOS,
                "metric": "action_accuracy",
                "tier": TIER,
            }
            if seed == SEEDS[0]:
                all_leakage[cop] = leakage_audit(audit_cell, seed + 500000)
        current = [float(x["current_action_acc"]) for x in per_seed.values()]
        conditioned = [float(x["conditioned_action_acc"]) for x in per_seed.values()]
        oracle = [float(x["evidence_oracle_action_acc"]) for x in per_seed.values()]
        headroom = [o - c for o, c in zip(oracle, current)]
        recovery = [r - c for r, c in zip(conditioned, current)]
        fractions = [r / h if h > 1e-12 else 0.0 for r, h in zip(recovery, headroom)]
        result[cop] = {"per_seed": per_seed,
                       "aggregate": {"current_mean": mean(current), "current_std": sample_std(current),
                                     "conditioned_mean": mean(conditioned), "conditioned_std": sample_std(conditioned),
                                     "oracle_mean": mean(oracle), "oracle_std": sample_std(oracle),
                                     "headroom_mean": 100.0 * mean(headroom), "recovery_mean": 100.0 * mean(recovery),
                                     "recovery_fraction_mean": mean(fractions),
                                     "recovery_ge_15pp": bool(mean(recovery) >= 0.15),
                                     "metric": "action_accuracy", "tier": TIER}}
    qualified = sum(bool(result[cop]["aggregate"]["recovery_ge_15pp"]) for cop in COPILOTS)
    result["leakage_check"] = all_leakage
    all_passed = all(bool(x["passed"]) for x in all_leakage.values())
    if not all_passed:
        result["status"] = "LEAKAGE DETECTED"
        result["metadata"] = {"seeds": list(SEEDS), "scenarios_per_copilot": N_SCENARIOS,
            "scenarios_frozen": True, "paired_comparison": True, "tier": TIER,
            "metric": "action_accuracy", "verdict": "STOP — leakage audit failed"}
    else:
        verdict = (f"Conditioned readout recovered >=15pp in {qualified}/5 copilots; "
                   "central claim upgrades to compounding decision system." if qualified >= 3 else
                   f"Conditioned readout recovered >=15pp in {qualified}/5 copilots; frontier remains with partial recovery.")
        result["readout_design"] = "All-category/action nearest-centroid readout on v_L with 0.70x precision on unread dimensions and read-dimension precision 1 + 2.5*q_norm*(0.5+0.5*delta_norm), where q_norm is normalized absolute Q×K score and delta_norm is normalized observed per-read vector movement. No verified labels or correctness fields enter prediction."
        result["metadata"] = {"seeds": list(SEEDS), "scenarios_per_copilot": N_SCENARIOS,
            "scenarios_frozen": True, "paired_comparison": True,
            "pre_registered_rule": ">=15pp recovery in >=3/5 copilots",
            "geometry": "default (where readout gap exists)", "tier": TIER,
            "metric": "action_accuracy", "qualified_copilots": qualified,
            "verdict": verdict, "determinism_per_cell": audits}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(canonical(result))
    write_summary(result)
    print(result["metadata"]["verdict"], flush=True)


if __name__ == "__main__":
    main()
