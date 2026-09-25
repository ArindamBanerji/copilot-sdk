"""GAP2: empirical surface-confidence risk/coverage on exported geometry.

Run with python -B scripts/gap2_abstention_curve.py. Only GAP2 JSON/CSV
artifacts are written. No fitting or monotonic smoothing uses evaluation labels.
This is a synthetic ranking experiment, not probability calibration or a
production abstention implementation.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/vld"
sys.path.insert(0, str(ROOT / "scripts"))
from routing_variant_bandit import make_case, score as harness_score, update_k

COPILOTS = ("dataops", "purchasing", "soc")
SIGNALS = ("margin", "d_min", "entropy")
COVERAGES = (1., .95, .90, .85, .80, .75, .70, .60, .50, .40, .30, .20, .10)
N_TRAIN, N_EVAL, N_SEEDS, BUDGET = 500, 500, 5, 2
BASE_SEED = 20260913
CORE = ("copilot_sdk/scoring/investigation.py",
        "copilot_sdk/backend/investigation_router.py",
        "copilot_sdk/scoring/scorer.py",
        "copilot_sdk/scoring/situation_classifier.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    # Include all repository Python source outside dependencies/caches.
    import os
    result = {}
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {
            "node_modules", ".git", ".venv", "venv", "__pycache__",
            "graphify-out", "dist", "build", ".mypy_cache", ".pytest_cache"}]
        for name in files:
            if name.endswith(".py"):
                p = Path(directory) / name
                result[p.relative_to(ROOT).as_posix()] = sha(p)
    return result


def load_investigator():
    # Direct module loading avoids application initialization/database writes.
    spec = importlib.util.spec_from_file_location(
        "gap2_investigation", ROOT / "copilot_sdk/scoring/investigation.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.VLDInvestigator


def confidence(investigator, vector, category):
    action, probs, _ = investigator.predict(vector, category)
    ranked = np.sort(probs)[::-1]
    margin = float(ranked[0] - ranked[1])
    distance = np.sum((vector[None, :] - investigator.mu)**2 /
                      np.maximum(investigator.sigma**2, .001)[None, :], axis=1)
    positive = probs[probs > 0]
    return action, probs, {
        "margin": margin, "d_min": float(np.min(distance)),
        "entropy": float(-np.sum(positive * np.log(positive))),
    }


def investigate_fixed_b2(investigator, category, case, k):
    """Standard fixed-budget recurrence; no production early-halting policy.

    Selection uses only current evidence, frozen geometry and K. The inherited
    synthetic provider restores latent values for designated informative reads;
    it is explicitly an oracle-coupled evidence model, not a live graph.
    """
    v = case["surface"].copy()
    selected = []
    for _ in range(BUDGET):
        _, probs, _ = investigator.predict(v, category)
        q = investigator.compute_Q(v, probs, set(selected), k)
        dim = int(np.argmax(q))
        assert dim not in selected and q[dim] >= 0
        selected.append(dim)
        if dim in case["informative"]:
            v[dim] = case["full"][dim]
    action, _, _ = investigator.predict(v, category)
    return int(action), selected


def monotonicity(curve):
    # Curve order is decreasing coverage. Desired accuracy direction is UP.
    acc = [r["accuracy_on_acted"] for r in curve]
    drops = [max(0., a-b) for a, b in zip(acc, acc[1:])]
    global_drop = max((a-b for i,a in enumerate(acc) for b in acc[i+1:]), default=0.)
    legacy = acc[1:]
    return {
        "strict": all(d <= 1e-12 for d in drops),
        "within_2pp": all(d <= .02 + 1e-12 for d in drops),
        "largest_adjacent_drop": max(drops, default=0.),
        "largest_drop_from_any_higher_coverage": max(0., global_drop),
        "globally_within_2pp": global_drop <= .02 + 1e-12,
        "lift_at_10pct_coverage": acc[-1]-acc[0],
        "violations_over_2pp": [
            {"from_coverage": curve[i]["coverage"],
             "to_coverage": curve[i+1]["coverage"], "drop": d}
            for i, d in enumerate(drops) if d > .02 + 1e-12],
        "user_snippet_reversed_direction_result": all(
            legacy[i] >= legacy[i+1] - .02 for i in range(len(legacy)-1)),
    }


def curve_for(rows, signal, signal_field="signals"):
    # Pre-generated tie keys never depend on truth or correctness.
    direction = -1 if signal == "margin" else 1
    ranked = sorted(rows, key=lambda r: (direction*r[signal_field][signal], r["tie_key"]))
    baseline = sum(r["correct"] for r in rows) / len(rows)
    curve = []
    for coverage in COVERAGES:
        count = round(coverage * len(rows))
        retained = ranked[:count]
        correct = sum(r["correct"] for r in retained)
        accuracy = correct / count
        threshold = retained[-1][signal_field][signal]
        curve.append({
            "coverage": count / len(rows), "accuracy_on_acted": accuracy,
            "risk": 1-accuracy, "baseline_accuracy_all": baseline,
            "accuracy_lift_vs_baseline": accuracy-baseline,
            "n_acted": count, "n_abstained": len(rows)-count,
            "n_correct_acted": correct, "threshold_raw": threshold,
            "boundary_ties_total": sum(r[signal_field][signal] == threshold for r in ranked),
            "boundary_ties_retained": sum(r[signal_field][signal] == threshold for r in retained),
        })
    return curve


def run_seed(copilot, info, seed, investigator_type):
    categories = list(info.get("category_names") or info["all_category_mu"])
    factors = info["factor_names"]
    sigma = np.asarray(info["sigma"], dtype=float)
    tau = float(info["tau"])
    investigators = {c: investigator_type(info["all_category_mu"][c], sigma, factors, tau=tau)
                     for c in categories}
    k = {c: np.full(len(factors), .5) for c in categories}
    attempts = {c: np.zeros(len(factors), dtype=int) for c in categories}
    train_rng, eval_rng, tie_rng = (random.Random(seed+x) for x in (0, 1000000, 2000000))
    train_vectors = set()
    for _ in range(N_TRAIN):
        cat = train_rng.choice(categories)
        inv = investigators[cat]
        case = make_case(train_rng, inv.mu, sigma, tau)
        train_vectors.add((cat, case["surface"].tobytes()))
        action, selected = investigate_fixed_b2(inv, cat, case, k[cat])
        update_k(k[cat], selected, case["informative"], action == case["correct_action"])
        attempts[cat][selected] += 1
    frozen = {c: weights.copy() for c, weights in k.items()}
    rows = []
    for index in range(N_EVAL):
        cat = eval_rng.choice(categories)
        inv = investigators[cat]
        case = make_case(eval_rng, inv.mu, sigma, tau)
        assert (cat, case["surface"].tobytes()) not in train_vectors
        surface_action, probs, signals = confidence(inv, case["surface"], cat)
        # Meaningful parity check against the inherited generator's scorer.
        ha, hp, hm = harness_score(inv.mu, sigma, tau, case["surface"])
        assert ha == surface_action and np.allclose(hp, probs, rtol=0, atol=1e-12)
        assert abs(hm - signals["margin"]) < 1e-12
        action, selected = investigate_fixed_b2(inv, cat, case, k[cat])
        final_vector = case["surface"].copy()
        for dim in selected:
            if dim in case["informative"]:
                final_vector[dim] = case["full"][dim]
        final_action, final_probs, final_signals = confidence(inv, final_vector, cat)
        assert final_action == action
        rows.append({
            "decision_index": index, "category": cat, "tie_key": tie_rng.random(),
            "signals": signals, "surface_vector": case["surface"].tolist(),
            "final_signals": final_signals, "final_probabilities": final_probs.tolist(),
            "full_vector": case["full"].tolist(), "surface_probabilities": probs.tolist(),
            "surface_action": int(surface_action), "vld_action": action,
            "oracle_action": case["correct_action"],
            "correct": int(action == case["correct_action"]),
            "selected_dimensions": selected,
            "informative_dimensions": sorted(int(x) for x in case["informative"]),
        })
    assert all(np.array_equal(k[c], frozen[c]) for c in categories)
    curves = {s: curve_for(rows, s) for s in SIGNALS}
    final_curves = {s: curve_for(rows, s, "final_signals") for s in SIGNALS}
    return {
        "seed": seed, "evaluation_seed": seed+1000000,
        "n_training": N_TRAIN, "n_evaluation": N_EVAL,
        "baseline_accuracy_all": sum(r["correct"] for r in rows)/N_EVAL,
        "k_after_training": {c: v.tolist() for c, v in frozen.items()},
        "training_read_counts": {c: v.tolist() for c, v in attempts.items()},
        "training_starvation": float(np.mean([v == 0 for v in attempts.values()])),
        "checks": {"evaluation_k_frozen": True, "no_train_eval_surface_overlap": True,
                   "scorer_probability_parity": True},
        "curves": curves, "monotonicity": {s: monotonicity(curves[s]) for s in SIGNALS},
        "final_curves": final_curves,
        "final_monotonicity": {s: monotonicity(final_curves[s]) for s in SIGNALS},
        "decisions": rows,
    }


def aggregate_signal(signal, runs, stage="surface"):
    baseline = float(np.mean([r["baseline_accuracy_all"] for r in runs]))
    bootstrap = np.random.default_rng(BASE_SEED).integers(0, len(runs), (10000, len(runs)))
    curve = []
    for i, coverage in enumerate(COVERAGES):
        points = [r["curves" if stage == "surface" else "final_curves"][signal][i] for r in runs]
        accs = np.array([r["accuracy_on_acted"] for r in points])
        lifts = np.array([r["accuracy_lift_vs_baseline"] for r in points])
        accuracy = float(accs.mean())
        curve.append({
            "coverage": coverage, "accuracy_on_acted": accuracy, "risk": 1-accuracy,
            "baseline_accuracy_all": baseline, "accuracy_lift_vs_baseline": float(lifts.mean()),
            "n_acted": sum(r["n_acted"] for r in points),
            "n_abstained": sum(r["n_abstained"] for r in points),
            "n_correct_acted": sum(r["n_correct_acted"] for r in points),
            "accuracy_seed_sd": float(accs.std(ddof=1)),
            "accuracy_bootstrap_95_ci": np.quantile(accs[bootstrap].mean(axis=1), [.025,.975]).tolist(),
            "lift_bootstrap_95_ci": np.quantile(lifts[bootstrap].mean(axis=1), [.025,.975]).tolist(),
            "thresholds_by_seed": [r["threshold_raw"] for r in points],
        })
    values = list(reversed(curve))
    partial_area = sum((b["coverage"]-a["coverage"])*(a["risk"]+b["risk"])/2
                       for a,b in zip(values, values[1:]))/.9
    return {"signal": signal, "baseline_accuracy": baseline, "curve": curve,
            "monotonicity": monotonicity(curve),
            "seed_monotonic_within_2pp_count": sum(r["monotonicity" if stage == "surface" else "final_monotonicity"][signal]["within_2pp"] for r in runs),
            "normalized_partial_aurc_10_to_100": partial_area}


def main():
    before = source_hashes()
    export_path = ROOT / "real_centroids_v1.json"
    export_hash = sha(export_path)
    export = json.loads(export_path.read_text(encoding="utf-8"))
    investigator_type = load_investigator()
    result = {
        "experiment": "VLD-GAP2", "evidence_tier": "REAL_COMPONENT_WITH_SYNTHETIC_LABELS",
        "protocol": {
            "copilots": COPILOTS, "signals": SIGNALS, "seeds_per_copilot": N_SEEDS,
            "training_decisions_per_seed": N_TRAIN, "fresh_evaluation_decisions_per_seed": N_EVAL,
            "budget": BUDGET, "confidence_timing": "surface, before investigation",
            "signal_direction": {"margin": "higher is more confident", "d_min": "lower is more confident", "entropy": "lower is more confident"},
            "coverage_order": "descending; desired accuracy is nondecreasing",
            "coverage_selection": "top fraction within each seed; equal-size seed means; CSV counts pooled over five seeds",
            "k_protocol": "per-category K=.5; correct informative read +.02, otherwise -.005; clip [.1,3]; frozen for evaluation",
            "paired_signals": "one shared trained K and identical 500 evaluation cases per seed; signals do not change investigation",
            "case_generator": "unchanged scripts/routing_variant_bandit.py:make_case",
            "oracle": "argmax scorer on latent full vector; geometry-derived synthetic truth, not independent outcomes",
            "evidence": "inherited synthetic informative-set provider; noninformative reads return unchanged values",
            "scorer": "VLDInvestigator.predict without score_fn: exported-geometry fallback, not full CompoundingScorer runtime",
            "routing": "production compute_Q, fixed B=2 recurrence; prior experiment K updates; no production early halt/flip bonus",
            "uncertainty": "sample SD and paired-seed percentile bootstrap (10000 resamples); 5 seeds, descriptive, no multiple-comparison correction",
            "best_signal": "highest aggregate accuracy at 75% on evaluation data; exploratory selection, not independent validation",
            "calibration_scope": "empirical confidence ranking only; no claim that raw signals are calibrated correctness probabilities",
            "monotonicity_note": "user snippet inequality is reversed for descending coverage; correct and verbatim-direction results both retained",
            "b7_comparison": "different fixture/geometry/evidence protocol; not a matched causal test of B7's failure",
            "secondary_diagnostic": "After observing primary surface failures, additionally rank on final B=2 geometry; same seeds, cases, K and actions. Exploratory. All decisions have already paid for two reads; this does not save investigation cost.",
        },
        "export_provenance": {k:v for k,v in export.items() if k != "copilots"},
        "centroid_sha256": export_hash, "source_hashes_before": before,
        "expected_hash_note": "Prompt investigation.py prefix 3441dcdb is transposed; observed preexisting prefix is 3441dcbd, preserved.",
        "copilots": [],
    }
    for copilot in COPILOTS:
        info = export["copilots"][copilot]
        seeds = [BASE_SEED + sum(map(ord,copilot))*100 + i for i in range(N_SEEDS)]
        runs = []
        for seed in seeds:
            run = run_seed(copilot, info, seed, investigator_type)
            runs.append(run)
            print(f"{copilot} seed={seed}: baseline={run['baseline_accuracy_all']:.3f}", flush=True)
        signals = [aggregate_signal(s, runs) for s in SIGNALS]
        final_signals = [aggregate_signal(s, runs, "final") for s in SIGNALS]
        best = max(signals, key=lambda s: next(r["accuracy_on_acted"] for r in s["curve"] if r["coverage"] == .75))
        final_best = max(final_signals, key=lambda s: next(r["accuracy_on_acted"] for r in s["curve"] if r["coverage"] == .75))
        result["copilots"].append({
            "copilot": copilot, "seeds": seeds,
            "geometry": {"categories": list(info["all_category_mu"]), "factors": info["factor_names"],
                         "sigma": info["sigma"], "tau": info["tau"]},
            "baseline_accuracy_all": signals[0]["baseline_accuracy"],
            "signals": signals, "best_signal_at_75": best["signal"], "seed_runs": runs,
            "post_investigation_diagnostic": {"signals": final_signals, "best_signal_at_75": final_best["signal"]},
        })
        for sig in signals:
            for row in sig["curve"]:
                if row["coverage"] in (.9,.75,.5):
                    print(f"{copilot}/{sig['signal']} {row['coverage']:.0%}: acted={row['accuracy_on_acted']:.1%} baseline={sig['baseline_accuracy']:.1%} lift={row['accuracy_lift_vs_baseline']:+.1%}")
            print(f"  monotonic strict={sig['monotonicity']['strict']} within2pp={sig['monotonicity']['within_2pp']}")
        for sig in final_signals:
            row = next(r for r in sig["curve"] if r["coverage"] == .75)
            print(f"SECONDARY final/{copilot}/{sig['signal']} 75%: acted={row['accuracy_on_acted']:.1%} lift={row['accuracy_lift_vs_baseline']:+.1%} strict={sig['monotonicity']['strict']} global2pp={sig['monotonicity']['globally_within_2pp']}")
    after = source_hashes()
    assert before == after, "Existing Python source changed during experiment"
    assert export_hash == sha(export_path), "Centroid export changed"
    result["source_hashes_after"] = after
    result["post_checks"] = {
        "all_python_source_hashes_unchanged": True, "centroid_export_unchanged": True,
        "at_least_one_monotonic_within_2pp": any(s["monotonicity"]["within_2pp"] for c in result["copilots"] for s in c["signals"]),
        "at_least_one_strictly_monotonic": any(s["monotonicity"]["strict"] for c in result["copilots"] for s in c["signals"]),
        "primary_at_least_one_globally_within_2pp": any(s["monotonicity"]["globally_within_2pp"] for c in result["copilots"] for s in c["signals"]),
        "secondary_at_least_one_strictly_monotonic": any(s["monotonicity"]["strict"] for c in result["copilots"] for s in c["post_investigation_diagnostic"]["signals"]),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gap2_abstention_curve.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    columns = ["copilot", "signal", "coverage", "accuracy_on_acted", "baseline_accuracy_all",
               "accuracy_lift_vs_baseline", "n_acted", "n_abstained"]
    with (OUT / "gap2_abstention_curve.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for cop in result["copilots"]:
            for sig in cop["signals"]:
                for row in sig["curve"]:
                    writer.writerow({key: cop["copilot"] if key=="copilot" else sig["signal"] if key=="signal" else row[key] for key in columns})
    print("POST CHECKS", result["post_checks"])
    for p in CORE:
        print(f"{p}: {after[p][:16]}... unchanged")


if __name__ == "__main__":
    main()
