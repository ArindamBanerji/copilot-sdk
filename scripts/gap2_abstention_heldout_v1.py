"""Fresh three-way GAP-2 validation: fixed final_d_min, random_state=42.

500 training, 500 threshold-selection, 500 untouched evaluation cases per seed.
Five paired independent replicates per copilot. No evaluation-based selection.
Only this new result is written; original GAP-2 results remain unchanged.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
OUT = ROOT/"experiments/vld/results/gap2_abstention_heldout_v1.json"
COPILOTS = ("dataops", "purchasing", "soc")
COVERAGES = (1., .95, .9, .85, .8, .75, .7, .6, .5, .4, .3, .2, .1)
TIER = "REAL_COMPONENT geometry + SIMULATED decisions/evidence/verification"


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("d3_gap2_original", ROOT/"scripts/gap2_abstention_curve.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_seed(h: Any, info: dict[str, Any], seeds: list[int]) -> dict[str, Any]:
    itype = h.load_investigator()
    categories = list(info.get("category_names") or info["all_category_mu"])
    sigma = np.array(info["sigma"])
    invs = {c: itype(info["all_category_mu"][c], sigma, info["factor_names"], tau=info["tau"])
            for c in categories}
    weights = {c: np.full(len(sigma), .5) for c in categories}
    seen: list[set[str]] = []
    def signature(cat: str, case: dict[str, Any]) -> str:
        return hashlib.sha256(cat.encode()+case["surface"].tobytes()+case["full"].tobytes()).hexdigest()
    rng = random.Random(seeds[0])
    training: set[str] = set()
    for _ in range(500):
        cat = rng.choice(categories)
        inv = invs[cat]
        case = h.make_case(rng, inv.mu, sigma, info["tau"])
        training.add(signature(cat, case))
        action, selected = h.investigate_fixed_b2(inv, cat, case, weights[cat])
        h.update_k(weights[cat], selected, case["informative"], action == case["correct_action"])
    seen.append(training)
    frozen = {c: k.copy() for c,k in weights.items()}

    def cohort(seed: int) -> list[dict[str, Any]]:
        cohort_rng = random.Random(seed)
        signatures: set[str] = set()
        rows: list[dict[str, Any]] = []
        for i in range(500):
            cat = cohort_rng.choice(categories)
            inv = invs[cat]
            case = h.make_case(cohort_rng, inv.mu, sigma, info["tau"])
            sig = signature(cat, case)
            signatures.add(sig)
            action, selected = h.investigate_fixed_b2(inv, cat, case, frozen[cat])
            v = case["surface"].copy()
            for dim in selected:
                if dim in case["informative"]:
                    v[dim] = case["full"][dim]
            final_action, _, signals = h.confidence(inv, v, cat)
            assert action == final_action
            rows.append({"index": i, "category": cat, "signature": sig,
                         "surface_vector": case["surface"].tolist(), "full_vector": case["full"].tolist(),
                         "final_vector": v.tolist(), "final_d_min": signals["d_min"],
                         "action": action, "verified_action": case["correct_action"],
                         "correct": bool(action == case["correct_action"]),
                         "selected_dimensions": selected,
                         "informative_dimensions": sorted(int(x) for x in case["informative"]),
                         "routing_quality": sum(d in case["informative"] for d in selected)/len(selected),
                         "tier": TIER})
        assert all(not signatures.intersection(prior) for prior in seen)
        seen.append(signatures)
        return rows

    selection = cohort(seeds[1])
    # Lock thresholds BEFORE constructing/inspecting the test set.
    values = np.array([r["final_d_min"] for r in selection])
    thresholds = [None if c == 1. else float(np.quantile(values, c)) for c in COVERAGES]
    evaluation = cohort(seeds[2])
    baseline = float(np.mean([r["correct"] for r in evaluation]))
    curve: list[dict[str, Any]] = []
    for target, threshold in zip(COVERAGES, thresholds):
        accepted = [r for r in evaluation if threshold is None or r["final_d_min"] <= threshold]
        assert accepted
        accuracy = sum(r["correct"] for r in accepted)/len(accepted)
        curve.append({"target_coverage": target, "threshold": threshold,
                      "coverage": len(accepted)/len(evaluation), "action_accuracy": accuracy,
                      "baseline_action_accuracy": baseline, "action_accuracy_lift": accuracy-baseline,
                      "n_accepted": len(accepted), "n_correct": sum(r["correct"] for r in accepted),
                      "n_evaluated": len(evaluation), "tier": TIER})
    assert all(np.array_equal(weights[c],frozen[c]) for c in categories)
    return {"split_seeds": dict(zip(("training","threshold_selection","evaluation"),seeds)),
            "n_training": 500, "n_threshold_selection": 500, "n_evaluation": 500,
            "checks": {"disjoint_splits": True, "evaluation_K_frozen": True, "thresholds_locked_before_test": True},
            "k_after_training": {c:k.tolist() for c,k in frozen.items()},
            "training_signature_sha256": hashlib.sha256("".join(sorted(training)).encode()).hexdigest(),
            "threshold_selection": selection, "evaluation": evaluation, "curve": curve, "tier": TIER}


def main() -> None:
    h = load_module()
    exported = json.loads((ROOT/"real_centroids_v1.json").read_text())
    rng = np.random.default_rng(42)
    result: dict[str, Any] = {
        "experiment": "D3-GAP2-HELDOUT-v1", "tier": TIER, "random_state": 42,
        "protocol": {"signal": "final_d_min", "signal_preregistered": True,
                     "split_sizes": [500,500,500], "replicates": 5, "budget": 2,
                     "thresholds": "per-seed selection-set quantiles; locked before test",
                     "selection_scope": "signal fixed from prior exploratory study; only numeric quantiles estimated",
                     "evaluation": "new independently seeded cohort; actual accepted coverage plotted, not forced rank",
                     "k_rule": "correct informative +.02; other attempted -.005; [.1,3]; frozen for selection/test",
                     "metric": "action_accuracy conditional on acceptance; category supplied, category_accuracy not measured",
                     "routing_quality": "informative reads / attempted reads; separate diagnostic",
                     "baseline": "same B=2 actions, act on all; not budget-zero single-pass",
                     "uncertainty": "paired-seed bootstrap, 10000 resamples; descriptive 95% intervals, five seeds",
                     "limitations": ["exported geometry with synthetic geometry-derived labels and oracle-coupled evidence",
                                     "acceptance occurs after B=2 reads, no investigation-cost saving",
                                     "75% is target on selection data; held-out coverage may differ"]},
        "copilots": [], "source_sha256": {}}
    for cop in COPILOTS:
        runs=[]
        for replicate in range(5):
            seeds = [int(x) for x in rng.integers(0,2**32-1,size=3)]
            runs.append(run_seed(h, exported["copilots"][cop], seeds))
            print(f"{cop}: replicate {replicate+1}/5 complete",flush=True)
        boot=np.random.default_rng(42).integers(0,5,size=(10000,5))
        curve=[]
        for i,target in enumerate(COVERAGES):
            pts=[r["curve"][i] for r in runs]
            accuracies=np.array([p["action_accuracy"] for p in pts])
            lifts=np.array([p["action_accuracy_lift"] for p in pts])
            coverage=np.array([p["coverage"] for p in pts])
            curve.append({"target_coverage":target, "coverage":float(coverage.mean()),
                          "action_accuracy":float(accuracies.mean()),
                          "action_accuracy_sd":float(accuracies.std(ddof=1)),
                          "action_accuracy_95_ci":np.quantile(accuracies[boot].mean(axis=1),[.025,.975]).tolist(),
                          "coverage_95_ci":np.quantile(coverage[boot].mean(axis=1),[.025,.975]).tolist(),
                          "action_accuracy_lift":float(lifts.mean()),
                          "lift_95_ci":np.quantile(lifts[boot].mean(axis=1),[.025,.975]).tolist(),
                          "n_accepted":sum(p["n_accepted"] for p in pts),
                          "n_evaluated":2500,"tier":TIER})
        item={"copilot":cop, "tier":TIER,"seed_runs":runs,"curve":curve,
              "baseline_action_accuracy":curve[0]["action_accuracy"],
              "at_target_75":next(p for p in curve if p["target_coverage"]==.75)}
        result["copilots"].append(item)
        print(json.dumps({"copilot":cop, "at_target_75":item["at_target_75"]}),flush=True)
    for name in ("real_centroids_v1.json", "scripts/gap2_abstention_curve.py",
                 "scripts/routing_variant_bandit.py", "copilot_sdk/scoring/investigation.py",
                 "scripts/gap2_abstention_heldout_v1.py"):
        result["source_sha256"][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(OUT,flush=True)


if __name__ == "__main__":
    main()

