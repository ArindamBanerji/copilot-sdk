"""Fixed-read budget/accuracy frontier on exported geometry.

Writes only new experiment outputs. The production investigator executes every
read. Its optional early halts are continued under a frozen episode until the
requested read quota is consumed. No production file or global is patched.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import random
import statistics
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np

from copilot_sdk.scoring.investigation import KUtilityStore, VLDInvestigator
from k_learning_curve_experiment import SQLiteDecisionStore, geometry_hash, scenario

OUT = ROOT / "experiments/vld/budget_accuracy_frontier.json"
CSV = OUT.with_suffix(".csv")
COPILOTS = ("soc", "dataops", "s2p", "purchasing", "trading")
BUDGETS = (0, 1, 2, 3, 4, "exhaustive")
POLICIES = ("vld", "single_pass", "random")
SEEDS = tuple(20260913 + 1009 * i for i in range(5))
FIELDS = ("copilot", "budget", "policy", "accuracy_mean", "accuracy_std",
          "routing_quality_mean", "reads_mean")
CORE = ("copilot_sdk/scoring/investigation.py",
        "copilot_sdk/backend/investigation_router.py",
        "copilot_sdk/scoring/scorer.py")
SOURCE_FILES = CORE + ("scripts/k_learning_curve_experiment.py",
                      "real_centroids_v1.json",
                      "scripts/budget_accuracy_frontier.py",
                      "scripts/generate_budget_frontier_charts.py")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCE_FILES}


class FrontierInvestigator(VLDInvestigator):
    """Only policy selection/masking varies; production investigate executes reads."""

    def begin(self, policy, permutation):
        self.policy = policy
        self.prior_attempts = set()
        self.random_priorities = np.zeros(len(self.factor_names))
        for rank, dim in enumerate(permutation):
            self.random_priorities[dim] = len(permutation) - rank

    def compute_Q(self, v, P, enriched_set=None, K_weights=None):
        attempted = self.prior_attempts | set(enriched_set or ())
        if self.policy != "random":
            return super().compute_Q(v, P, attempted, K_weights)
        priorities = self.random_priorities.copy()
        for dim in attempted:
            priorities[dim] = -1.0
        return priorities


class FullVectorEvidence:
    """All coordinates are available, independent of oracle usefulness labels."""

    def __init__(self, case):
        self.full = np.asarray(case["full"])
        self.requested = []

    def read_evidence(self, decision_id, dimension, factor_name):
        self.requested.append(int(dimension))
        return {"value": float(self.full[dimension]), "confidence": 1.0,
                "source": "synthetic_full_coordinate"}


def investigators(info):
    return {c: FrontierInvestigator(info["all_category_mu"][c], info["sigma"],
            info["factor_names"], tau=info["tau"], action_names=info["action_names"])
            for c in info["category_names"]}


def cases_for(info, invs, seed, n, namespace):
    # Neither routing choices nor training updates consume this generator RNG.
    rng = random.Random(seed + namespace)
    shuffle_rng = random.Random(seed + namespace + 70000001)
    result = []
    for i in range(n):
        category = rng.choice(info["category_names"])
        inv = invs[category]
        case = scenario(rng, category, inv.mu, inv)
        permutation = list(range(len(info["factor_names"])))
        shuffle_rng.shuffle(permutation)
        case["random_order"] = permutation
        case["id"] = f"{namespace}-{i}"
        # Independent nearest-centroid oracle; no routing outcome enters this.
        distance = np.sum((np.asarray(case["full"]) - inv.mu) ** 2
                          / np.maximum(inv.sigma ** 2, .001), axis=1)
        assert int(np.argmin(distance)) == case["correct_action"]
        result.append(case)
    return result


def serialize_case(case):
    return {k: v.tolist() if isinstance(v, np.ndarray)
            else sorted(int(i) for i in v) if isinstance(v, set)
            else int(v) if isinstance(v, np.integer) else v
            for k, v in case.items()}


def episode(case, inv, weights, policy, budget):
    inv.begin(policy, case["random_order"])
    provider = FullVectorEvidence(case)
    actual_budget = 0 if policy == "single_pass" else int(budget)
    vector = np.asarray(case["surface"]).copy()
    original_weights = weights.copy()
    traces = []
    all_steps = []
    halted_segments = []
    # A fixed-budget frontier must not label an early stop "exhaustive".
    # Continue production segments after an oscillation stop; delta=0 disables
    # residual stopping. Mask previous segments, while each segment tracks its
    # own attempted dimensions. The Q formula and evidence update stay unchanged.
    while len(all_steps) < actual_budget or not traces:
        remaining = actual_budget - len(all_steps)
        trace = inv.investigate(case["id"], case["category"], vector, provider,
                    budget=remaining, K_weights=weights, gated_sources=set(),
                    delta=0.0, max_flips=len(inv.factor_names) + 1)
        traces.append(trace)
        if remaining:
            assert trace.steps, "Unconsumed budget without a selectable dimension"
        for step in trace.steps:
            assert step.status == "acquired"
            assert step.dimension not in inv.prior_attempts
            inv.prior_attempts.add(step.dimension)
            all_steps.append(step)
        if trace.steps:
            vector = np.asarray(trace.steps[-1].v_after).copy()
        if len(all_steps) < actual_budget:
            halted_segments.append(trace.halt_reason)
        if remaining == 0:
            break
    chosen = [int(s.dimension) for s in all_steps]
    assert len(chosen) == actual_budget == len(set(chosen))
    assert chosen == provider.requested
    assert np.array_equal(weights, original_weights)
    if policy == "random":
        assert chosen == case["random_order"][:actual_budget]
    if actual_budget == len(inv.factor_names):
        np.testing.assert_array_equal(vector, case["full"])
        assert traces[-1].final_action == case["correct_action"]
    correct = traces[-1].final_action == case["correct_action"]
    surface_correct = case["surface_action"] == case["correct_action"]
    row = {"case_id": case["id"], "category": case["category"],
           "oracle_action": int(case["correct_action"]),
           "surface_action": int(case["surface_action"]),
           "final_action": int(traces[-1].final_action),
           "selected": chosen, "reads": len(chosen),
           "informative_reads": sum(d in case["informative"] for d in chosen),
           "correct": bool(correct), "saves": int(correct and not surface_correct),
           "hurts": int(surface_correct and not correct),
           "continued_halts": halted_segments}
    # Preserve the real per-step flip metadata for the inherited K update.
    combined = replace(traces[0], budget=actual_budget, steps=all_steps,
                       final_action=traces[-1].final_action,
                       final_margin=traces[-1].final_margin)
    return row, combined


def reward(store, trace, case, final_correct):
    # Matches k_learning_curve_experiment.reward_learning_store, including the
    # production +.04 flip bonus for a correct informative action-flipping step.
    # Unlike the old provider, reads themselves are NOT filtered by this label.
    for step in trace.steps:
        helpful = step.dimension in case["informative"] and final_correct
        store.update_weights(case["category"], replace(trace, steps=[step]),
                             correct=bool(helpful), lr_pos=.02, lr_neg=.005)


def k_snapshot(store, categories):
    return {c: store.get_weights(c).tolist() for c in categories}


def metrics(rows):
    reads = sum(r["reads"] for r in rows)
    return {"accuracy": sum(r["correct"] for r in rows) / len(rows),
            "routing_quality": (sum(r["informative_reads"] for r in rows) / reads
                                if reads else None),
            "reads": reads / len(rows),
            "saves": sum(r["saves"] for r in rows),
            "hurts": sum(r["hurts"] for r in rows),
            "continued_halts": sum(len(r["continued_halts"]) for r in rows)}


def run_arm(info, invs, train, evaluation, policy, budget, seed):
    memory = SQLiteDecisionStore()
    store = KUtilityStore(memory, d=len(info["factor_names"]))
    train_rows = []
    checkpoints = []
    try:
        for i, case in enumerate(train, 1):
            row, trace = episode(case, invs[case["category"]],
                                 store.get_weights(case["category"]), policy, budget)
            train_rows.append(row)
            reward(store, trace, case, row["correct"])
            if i % 50 == 0:
                checkpoints.append({"decision_count": i,
                                    "k_by_category": k_snapshot(store, info["category_names"])})
        frozen = k_snapshot(store, info["category_names"])
        assert all(.1 <= k <= 3.0 for values in frozen.values() for k in values)
        before_sql = list(store.conn.execute(
            "SELECT category,dimension,weight,n_updates FROM k_utility ORDER BY category,dimension"))
        eval_rows = []
        examples = []
        for case in evaluation:
            row, trace = episode(case, invs[case["category"]],
                np.asarray(frozen[case["category"]]), policy, budget)
            eval_rows.append(row)
            if len(examples) < 2:
                examples.append({"case_id": case["id"],
                                 "vectors_after_reads": [s.v_after for s in trace.steps],
                                 "flips": [s.flipped for s in trace.steps]})
        assert before_sql == list(store.conn.execute(
            "SELECT category,dimension,weight,n_updates FROM k_utility ORDER BY category,dimension"))
        assert frozen == k_snapshot(store, info["category_names"])
        return {"seed": seed, "metrics": metrics(eval_rows),
                "training_metrics": metrics(train_rows), "k_by_category": frozen,
                "training_checkpoints": checkpoints,
                "k_update_counts": [{"category": c, "dimension": d, "updates": n}
                                   for c, d, w, n in before_sql],
                "training_routes_sha256": digest([r["selected"] for r in train_rows]),
                "evaluation_rows": eval_rows, "trace_examples": examples,
                "evaluation_frozen": True}
    finally:
        memory.conn.close()


def summarize(runs):
    result = {}
    for name in ("accuracy", "routing_quality", "reads"):
        values = [r["metrics"][name] for r in runs]
        result[name + "_mean"] = None if values[0] is None else statistics.mean(values)
        result[name + "_std"] = None if values[0] is None else statistics.stdev(values)
    result["saves"] = sum(r["metrics"]["saves"] for r in runs)
    result["hurts"] = sum(r["metrics"]["hurts"] for r in runs)
    result["seed_runs"] = runs
    return result


def validation(payload):
    assert len(payload["rows"]) == 90
    for copilot, result in payload["copilots"].items():
        ndim = result["ndim"]
        base_runs = result["results"]["0"]["single_pass"]["seed_runs"]
        for label, arms in result["results"].items():
            budget = ndim if label == "exhaustive" else int(label)
            for policy, aggregate in arms.items():
                runs = aggregate["seed_runs"]
                assert len(runs) == 5
                for i, run in enumerate(runs):
                    rows = run["evaluation_rows"]
                    assert len(rows) == 200 and run["evaluation_frozen"]
                    assert run["metrics"] == metrics(rows)
                    expected_reads = 0 if policy == "single_pass" else budget
                    for row in rows:
                        assert len(row["selected"]) == row["reads"] == expected_reads
                        assert len(set(row["selected"])) == expected_reads
                        assert 0 <= row["informative_reads"] <= expected_reads
                    if policy == "single_pass" or budget == 0:
                        assert rows == base_runs[i]["evaluation_rows"]
                    if expected_reads == ndim:
                        assert all(r["correct"] for r in rows)
                    assert all(.1 <= k <= 3 for v in run["k_by_category"].values() for k in v)
                independent = summarize(runs)
                for key in ("accuracy_mean", "accuracy_std", "routing_quality_mean", "reads_mean"):
                    assert aggregate[key] == independent[key]
        efficiency = result["b2_efficiency"]
        assert efficiency["fraction_of_exhaustive_accuracy"] == (
            result["results"]["2"]["vld"]["accuracy_mean"]
            / result["results"]["exhaustive"]["vld"]["accuracy_mean"])
    return {"aggregate_rows": 90, "seed_arm_rows": 450,
            "evaluation_rows_in_grid": 90000,
            "unique_evaluation_cases": 5000, "unique_training_cases": 12500,
            "actual_read_quotas": "PASS", "full_vector_exhaustive": "PASS",
            "single_pass_consistency": "PASS", "frozen_evaluation": "PASS",
            "k_bounds": "PASS", "independent_aggregation": "PASS"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        data = json.loads(OUT.read_text(encoding="utf-8"))
        print(json.dumps(validation(data), indent=2))
        assert data["source_hashes_before"] == data["source_hashes_after"] == source_hashes()
        return
    for path in (OUT, CSV):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
    before = source_hashes()
    export = json.loads((ROOT / "real_centroids_v1.json").read_text(encoding="utf-8"))
    payload = {
        "protocol": {
            "date": "2026-09-13", "training_decisions": 500,
            "evaluation_decisions": 200, "seeds": list(SEEDS), "budget_labels": list(BUDGETS),
            "policies": list(POLICIES), "evidence_tier": "REAL_COMPONENT geometry + SYNTHETIC verification",
            "generator": "k_learning_curve_experiment.scenario",
            "evidence": "Every read reveals full[dimension], independent of informative labels",
            "difference_from_legacy_provider": "Legacy restores only informative dimensions; this study restores every selected dimension",
            "oracle": "Full-vector nearest-centroid action; exhaustive accuracy is 100% by construction",
            "routing_quality": "Informative reads / actual reads; undefined at zero reads (JSON null / CSV blank)",
            "informative_label_limit": "Inherited counterfactual label may count unchanged coordinates informative on surface-correct cases",
            "k": {"initial": .5, "bounds": [.1, 3], "positive": .02, "negative": .005,
                  "correct_informative_flip_bonus": 2,
                  "credit": "Selected informative dimension AND final action correct",
                  "training": "Separate category K per budget/policy, paired 500 training cases",
                  "random": "K is updated but cannot affect a uniformly shuffled order"},
            "budget_semantics": "Fixed read quota; production early halts continued with cumulative masking; not default early-stop deployment behavior",
            "single_pass": "Actual budget zero; one baseline per copilot/seed reused at every displayed budget",
            "pairing": "Same pre-generated train/eval vectors for every policy/budget; per-case random shuffle shared across budgets",
            "evaluation": "Fresh disjoint evaluation RNG; no K/count/geometry updates",
            "uncertainty": "Sample SD over five seeds; ratio of means plus per-seed ratios; descriptive paired t CI",
            "cost_scope": "Reads only, no measured provider or wall-clock latency",
        },
        "source_hashes_before": before, "copilots": {}, "rows": []}
    for copilot in COPILOTS:
        info = export["copilots"][copilot]
        ndim = len(info["factor_names"])
        result = {"ndim": ndim, "factor_names": info["factor_names"],
                  "action_names": info["action_names"], "category_names": info["category_names"],
                  "geometry_hash": geometry_hash(info), "sigma": info["sigma"], "tau": info["tau"],
                  "results": {str(b): {p: [] for p in POLICIES} for b in BUDGETS},
                  "cohorts": []}
        for seed in SEEDS:
            invs = investigators(info)
            domain_seed = seed + 100000 * (COPILOTS.index(copilot) + 1)
            train = cases_for(info, invs, domain_seed, 500, 1000000)
            evaluation = cases_for(info, invs, domain_seed, 200, 9000000)
            train_serial = [serialize_case(c) for c in train]
            eval_serial = [serialize_case(c) for c in evaluation]
            result["cohorts"].append({"seed": seed, "generator_seed": domain_seed,
                "training_sha256": digest(train_serial), "evaluation_sha256": digest(eval_serial),
                "training_count": 500, "evaluation_count": 200,
                "evaluation_cases": eval_serial})
            baseline = run_arm(info, invs, train, evaluation, "single_pass", 0, seed)
            for label in BUDGETS:
                budget = ndim if label == "exhaustive" else label
                result["results"][str(label)]["single_pass"].append(baseline)
                for policy in ("vld", "random"):
                    run = baseline if budget == 0 else run_arm(
                        info, invs, train, evaluation, policy, budget, seed)
                    result["results"][str(label)][policy].append(run)
            print(f"{copilot}: seed {seed} complete", flush=True)
        for label in BUDGETS:
            for policy in POLICIES:
                aggregate = summarize(result["results"][str(label)][policy])
                result["results"][str(label)][policy] = aggregate
                payload["rows"].append({"copilot": copilot, "budget": label, "policy": policy,
                    **{key: aggregate[key] for key in FIELDS[3:]}})
        b2 = result["results"]["2"]["vld"]
        exhaustive = result["results"]["exhaustive"]["vld"]
        baseline = result["results"]["0"]["single_pass"]
        ratios = [a["metrics"]["accuracy"] / e["metrics"]["accuracy"]
                  for a, e in zip(b2["seed_runs"], exhaustive["seed_runs"])]
        mean, sd = statistics.mean(ratios), statistics.stdev(ratios)
        result["b2_efficiency"] = {
            "vld_b2_accuracy": b2["accuracy_mean"],
            "exhaustive_accuracy": exhaustive["accuracy_mean"],
            "single_pass_accuracy": baseline["accuracy_mean"],
            "fraction_of_exhaustive_accuracy": b2["accuracy_mean"] / exhaustive["accuracy_mean"],
            "per_seed_ratios": ratios, "per_seed_ratio_mean": mean, "per_seed_ratio_std": sd,
            "paired_t95_ci": [mean - 2.776445105 * sd / np.sqrt(5),
                              mean + 2.776445105 * sd / np.sqrt(5)],
            "fraction_of_exhaustive_incremental_gain": (
                (b2["accuracy_mean"] - baseline["accuracy_mean"])
                / (exhaustive["accuracy_mean"] - baseline["accuracy_mean"]))
        }
        payload["copilots"][copilot] = result
        print(f"{copilot}: B2/exhaustive = {100 * mean:.2f}%", flush=True)
    payload["checks"] = validation(payload)
    payload["source_hashes_after"] = source_hashes()
    assert payload["source_hashes_after"] == before, "An input source changed during execution"
    text = json.dumps(payload, indent=2, allow_nan=False) + "\n"
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(payload["rows"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    with CSV.open("x", encoding="utf-8", newline="") as stream:
        stream.write(buffer.getvalue())
    print(f"Saved {OUT}\nSaved {CSV}", flush=True)


if __name__ == "__main__":
    main()

