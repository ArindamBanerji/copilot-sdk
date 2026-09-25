"""GAP1: production C4 halting versus the paired, fixed two-read frontier.

New artifacts only. A common 500-decision B2 training history isolates the halt
policy at evaluation. No production source or runtime global is modified.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import statistics
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import numpy as np
import budget_accuracy_frontier as baseline
from copilot_sdk.scoring.investigation import VLDInvestigator

OUT = ROOT / "experiments/vld/gap1_adaptive_halting.json"
CSV = OUT.with_suffix(".csv")
FRONTIER = ROOT / "experiments/vld/budget_accuracy_frontier.json"
DELTAS = (.001, .005, .01, .02, .05, .1)
COPILOTS = ("dataops", "purchasing", "trading", "soc", "s2p")
REASONS = {"budget_exhausted": "budget", "residual_below_threshold": "residual",
           "oscillation_detected": "oscillation"}
FIELDS = ("copilot", "delta", "policy", "acc_mean", "acc_std", "acc_delta_vs_B2",
          "reads_mean", "reads_saved_per_decision", "pct_reads_saved",
          "halt_budget_pct", "halt_residual_pct", "halt_oscillation_pct")
INPUTS = baseline.CORE + ("scripts/k_learning_curve_experiment.py",
          "scripts/budget_accuracy_frontier.py", "real_centroids_v1.json",
          "experiments/vld/budget_accuracy_frontier.json",
          "experiments/vld/k_learning_curve_cross_copilot_summary.json",
          "docs/quality/vld_tier5_implementation_summary_2026-09-12.md",
          "scripts/gap1_adaptive_halting.py")
# Chart code is not a numerical input; chart provenance is embedded in PNG metadata.


def hashes():
    return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS}


def adaptive_episode(case, inv, k, delta):
    before_k = k.copy()
    before_mu, before_sigma = inv.mu.copy(), inv.sigma.copy()
    provider = baseline.FullVectorEvidence(case)
    trace = inv.investigate(case["id"], case["category"], case["surface"], provider,
                            budget=4, K_weights=k, delta=delta, max_flips=2)
    np.testing.assert_array_equal(k, before_k)
    np.testing.assert_array_equal(inv.mu, before_mu)
    np.testing.assert_array_equal(inv.sigma, before_sigma)
    selected = [s.dimension for s in trace.steps]
    assert selected == provider.requested
    assert 2 <= len(selected) <= 4 and len(set(selected)) == len(selected)
    assert all(s.status == "acquired" for s in trace.steps)
    assert trace.halt_reason in REASONS
    residuals = []
    for s in trace.steps:
        v, previous = np.asarray(s.v_after), np.asarray(s.v_before)
        residuals.append(float(np.linalg.norm(v-previous) / np.sqrt(np.sum(v*v)+1e-10)))
    return {"case_id": case["id"], "category": case["category"],
            "selected": selected, "reads": len(selected),
            "actions": [trace.surface_action] + [s.action_after for s in trace.steps],
            "residuals": residuals, "halt_reason": trace.halt_reason,
            "final_action": trace.final_action, "oracle_action": case["correct_action"],
            "correct": bool(trace.final_action == case["correct_action"])}


def metrics(rows):
    counts = Counter(r["halt_reason"] for r in rows)
    return {"accuracy": statistics.mean(int(r["correct"]) for r in rows),
            "reads": statistics.mean(r["reads"] for r in rows),
            "min_reads": min(r["reads"] for r in rows),
            "max_reads": max(r["reads"] for r in rows),
            "read_count_distribution": {str(i): sum(r["reads"] == i for r in rows)
                                        for i in range(2, 5)},
            "halt_counts": {r: counts[r] for r in REASONS}}


def ci95(values):
    m = statistics.mean(values)
    h = 2.776445105 * statistics.stdev(values) / np.sqrt(len(values))
    return [float(m-h), float(m+h)]


def aggregate(copilot, delta, runs, control_runs):
    acc = [r["metrics"]["accuracy"] for r in runs]
    reads = [r["metrics"]["reads"] for r in runs]
    differences = [100*(a-c["metrics"]["accuracy"]) for a,c in zip(acc,control_runs)]
    savings = [c["metrics"]["reads"]-r for r,c in zip(reads,control_runs)]
    control_reads = statistics.mean(c["metrics"]["reads"] for c in control_runs)
    row = {"copilot": copilot, "delta": delta,
           "policy": "fixed_b2" if delta is None else "adaptive_halt",
           "acc_mean": statistics.mean(acc), "acc_std": statistics.stdev(acc),
           "acc_delta_vs_B2": statistics.mean(differences),
           "reads_mean": statistics.mean(reads), "reads_std": statistics.stdev(reads),
           "reads_saved_per_decision": statistics.mean(savings),
           "pct_reads_saved": 100*statistics.mean(savings)/control_reads,
           "acc_delta_paired_t95_ci_pp": ci95(differences),
           "reads_saved_paired_t95_ci": ci95(savings),
           "seed_runs": runs}
    for reason, short in REASONS.items():
        row["halt_"+short+"_pct"] = 100*sum(r["metrics"]["halt_counts"][reason]
                                            for r in runs)/(200*len(runs))
    row["accuracy_qualified"] = row["acc_delta_vs_B2"] >= -1.0-1e-12
    row["qualifies"] = bool(delta is not None and row["accuracy_qualified"]
                           and row["reads_saved_per_decision"] > 0)
    return row


def compact(row):
    return {k:v for k,v in row.items() if k != "seed_runs"}


def selections(adaptive):
    qualifies = [r for r in adaptive if r["qualifies"]]
    key = lambda r: (r["reads_mean"], -r["acc_mean"], r["delta"])
    best = compact(min(qualifies, key=key)) if qualifies else None
    diagnostic_pool = [r for r in adaptive if r["accuracy_qualified"]] or adaptive
    diagnostic = compact(min(diagnostic_pool, key=key))
    return best, diagnostic


def pareto(rows):
    return [compact(r) for r in rows if not any(
        s["reads_mean"] <= r["reads_mean"]+1e-12
        and s["acc_mean"] >= r["acc_mean"]-1e-12
        and (s["reads_mean"] < r["reads_mean"]-1e-12
             or s["acc_mean"] > r["acc_mean"]+1e-12)
        for s in rows)]


def verify_episode(row, case, info, k, delta):
    """Independent numerical replay of Q, oracle, residual and halt precedence."""
    mu = np.asarray(info["all_category_mu"][case["category"]])
    sigma = np.asarray(info["sigma"])
    v, full = np.asarray(case["surface"]).copy(), np.asarray(case["full"])
    def predict(vector):
        dist = np.sum((vector-mu)**2 / np.maximum(sigma**2,.001),axis=1)
        z = -dist/info["tau"]; p = np.exp(z-z.max()); p /= p.sum()
        return int(np.argmax(p)), p
    oracle, _ = predict(full)
    assert row["oracle_action"] == oracle
    actions = [predict(v)[0]]
    attempted = []
    flips = 0
    for i,dim in enumerate(row["selected"]):
        _, p = predict(v)
        a1,a2 = np.argsort(p)[::-1][:2]
        q = np.asarray(k)*(1/(100*np.maximum(sigma**2,.001))
                          +np.abs(mu[a1]-mu[a2])
                          +np.abs((v-mu[a1])**2-(v-mu[a2])**2))
        q[attempted] = -1
        assert dim == int(np.argmax(q))
        previous = v.copy()
        v[dim] = full[dim]
        attempted.append(dim)
        action, _ = predict(v)
        flips += action != actions[-1]
        actions.append(action)
        if delta is not None:
            residual = float(np.linalg.norm(v-previous)/np.sqrt(np.sum(v*v)+1e-10))
            assert np.isclose(residual, row["residuals"][i], atol=1e-14)
            oscillation = len(actions) >= 3 and actions[-1] == actions[-3] and actions[-1] != actions[-2]
            expected = ("residual_below_threshold" if i+1 >= 2 and residual < delta
                        else "oscillation_detected" if oscillation or flips >= 2
                        else "budget_exhausted" if i == 3 else None)
            if i < len(row["selected"])-1:
                assert expected is None, "Missed production early halt"
            else:
                assert expected == row["halt_reason"]
    assert row["final_action"] == predict(v)[0]
    assert row["correct"] == (row["final_action"] == oracle)
    if delta is not None:
        assert row["actions"] == actions


def validate(data, export, frontier):
    assert len(data["copilots"]) == 5 and len(data["rows"]) == 35
    checked = 0
    for cop in data["copilots"]:
        name = cop["copilot"]
        control = cop["fixed_b2"]
        assert len(cop["adaptive_results"]) == 6
        assert [r["delta"] for r in cop["adaptive_results"]] == list(DELTAS)
        assert control["acc_mean"] == frontier["copilots"][name]["results"]["2"]["vld"]["accuracy_mean"]
        assert control["reads_mean"] == 2
        for row in [control]+cop["adaptive_results"]:
            assert len(row["seed_runs"]) == 5
            for run,cohort in zip(row["seed_runs"],cop["training_and_evaluation"]):
                assert run["seed"] == cohort["seed"] and run["evaluation_frozen"]
                rows = run["evaluation_rows"]
                assert len(rows) == 200 and metrics(rows) == run["metrics"]
                for episode,case in zip(rows,cohort["evaluation_cases"]):
                    assert episode["case_id"] == case["id"]
                    assert 2 <= episode["reads"] <= (2 if row["delta"] is None else 4)
                    verify_episode(episode, case, export[name],
                                   cohort["k_by_category"][case["category"]], row["delta"])
                    checked += 1
            expected = aggregate(name,row["delta"],row["seed_runs"],control["seed_runs"])
            assert compact(row) == compact(expected)
            assert abs(sum(row["halt_"+s+"_pct"] for s in REASONS.values())-100) < 1e-9
        best,diagnostic = selections(cop["adaptive_results"])
        assert cop["best_qualifying"] == best
        assert cop["diagnostic_result"] == diagnostic
        assert cop["pareto_frontier"] == pareto([control]+cop["adaptive_results"])
        # Under these source semantics no positive read saving is possible.
        assert best is None
        assert all(r["reads_saved_per_decision"] <= 0 for r in cop["adaptive_results"])
    expected_csv = [{k:r[k] for k in FIELDS} for c in data["copilots"]
                    for r in [c["fixed_b2"]]+c["adaptive_results"]]
    assert data["rows"] == expected_csv
    return {"aggregate_rows":35, "seed_arms":175, "evaluation_episodes_replayed":checked,
            "unique_evaluation_cases":5000, "training_decisions":12500,
            "baseline_reproduced":"PASS", "frozen_shared_K":"PASS",
            "Q_and_halt_replay":"PASS", "halt_percentages":"PASS",
            "qualification_requires_positive_savings":"PASS", "minimum_two_reads":"PASS"}


def headlines(data):
    for cop in data["copilots"]:
        best = cop["best_qualifying"]
        if best is None:
            print(f"{cop['copilot']}: NO delta meets <=1pp accuracy loss with reads saved > 0")
            row = cop["diagnostic_result"]
            print(f"  Diagnostic delta={row['delta']}: reads={row['reads_mean']:.3f}, "
                  f"saved={row['reads_saved_per_decision']:+.3f}, "
                  f"accuracy delta={row['acc_delta_vs_B2']:+.2f}pp")
        else:
            print(f"{cop['copilot']}: delta={best['delta']}, "
                  f"reads_saved={best['reads_saved_per_decision']:.3f}/decision "
                  f"({best['pct_reads_saved']:.1f}%), acc_delta={best['acc_delta_vs_B2']:+.1f}pp")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only",action="store_true")
    args = parser.parse_args()
    export = json.loads((ROOT/"real_centroids_v1.json").read_text())["copilots"]
    frontier = json.loads(FRONTIER.read_text())
    if args.validate_only:
        data = json.loads(OUT.read_text())
        print(json.dumps(validate(data,export,frontier),indent=2))
        assert data["source_hashes_before"] == data["source_hashes_after"] == hashes()
        with CSV.open(newline="") as f:
            reader=csv.DictReader(f); rows=list(reader)
            assert reader.fieldnames == list(FIELDS) and len(rows)==35
        for actual,expected in zip(rows,data["rows"]):
            for key,value in expected.items():
                assert actual[key] == ("" if value is None else str(value))
        headlines(data)
        return
    for path in (OUT,CSV):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
    before = hashes()
    data = {"experiment":"VLD-GAP1", "protocol":{
        "date":"2026-09-13", "training_decisions_per_seed":500,
        "evaluation_decisions_per_seed":200, "seeds":list(baseline.SEEDS),
        "deltas":list(DELTAS), "fixed_budget":2, "adaptive_budget":4,
        "training":"Rerun the frontier's 500-decision B2 training per copilot/seed; share its frozen K across all delta evaluations to isolate halting",
        "training_reuse":"Six identical training histories computed once per seed, not six policy-dependent training arms",
        "K":"Category indexed; initial .5, bounds [.1,3], +.02/-.005; production correct-informative flip bonus doubles positive update",
        "KE1_relationship":"Same scenario generator and K update rule; full-coordinate evidence and paired frontier seeds preserve B2 comparability rather than reproducing the old KE1 aggregate",
        "evidence":"Every read reveals full[dimension], independent of oracle usefulness labels",
        "evidence_tier":"REAL_COMPONENT exported geometry + SYNTHETIC decisions and verification",
        "oracle":"Full-vector nearest-centroid action; legacy investigator scorer as in the frontier",
        "halting":"Unmodified VLDInvestigator.investigate(), delta swept, max_flips=2, budget=4",
        "production_correction":"Production already enables C4 at B=2; fixed B2 has identical read count here because no halt can occur before two reads",
        "residual":"norm(v_after-v_before)/sqrt(sum(v_after**2)+1e-10); checked after >=2 acquired reads",
        "oscillation":"A->B->A OR cumulative flip_count>=2 (including A->B->C)",
        "precedence":"Residual, then oscillation/flip cap, then budget; a residual reason at read 4 does not save reads against B4",
        "eligibility":"Mean accuracy delta >= -1pp AND strictly positive reads_saved_per_decision versus B2",
        "units":{"acc_mean":"fraction", "acc_std":"sample SD across seeds",
                 "acc_delta_vs_B2":"percentage points", "halt_percentages":"0-100",
                 "pct_reads_saved":"100*(2-mean_reads)/2; negative means extra reads"},
        "uncertainty":"Descriptive paired t95 CI across five matched seeds; no confirmatory holdout for delta selection",
        "diagnostic_selection":"If no qualifying delta, report minimum-read accuracy-qualified adaptive delta (then highest accuracy, then lowest delta); never relabel it qualifying",
        "structural_limit":"All evidence available, positive Q, >=6 dimensions: residual needs two acquired reads, oscillation needs two transitions; adaptive reads >=2, so B2 savings cannot be positive"},
        "source_hashes_before":before, "copilots":[], "rows":[]}
    for name in COPILOTS:
        info = export[name]
        prior = frontier["copilots"][name]
        cop = {"copilot":name, "ndim":len(info["factor_names"]),
               "training_and_evaluation":[]}
        fixed_runs = []
        adaptive_runs = {delta:[] for delta in DELTAS}
        for seed,old_cohort,old_run in zip(baseline.SEEDS, prior["cohorts"],
                                         prior["results"]["2"]["vld"]["seed_runs"]):
            assert seed == old_cohort["seed"] == old_run["seed"]
            invs = baseline.investigators(info)
            train = baseline.cases_for(info,invs,old_cohort["generator_seed"],500,1000000)
            evaluation = baseline.cases_for(info,invs,old_cohort["generator_seed"],200,9000000)
            assert baseline.digest([baseline.serialize_case(c) for c in train]) == old_cohort["training_sha256"]
            assert baseline.digest([baseline.serialize_case(c) for c in evaluation]) == old_cohort["evaluation_sha256"]
            replay = baseline.run_arm(info,invs,train,evaluation,"vld",2,seed)
            assert replay == old_run, "Fixed B2 training/evaluation must reproduce the authoritative frontier exactly"
            frozen = replay["k_by_category"]
            cop["training_and_evaluation"].append({
                "seed":seed, "generator_seed":old_cohort["generator_seed"],
                "training_count":500, "training_sha256":old_cohort["training_sha256"],
                "evaluation_sha256":old_cohort["evaluation_sha256"],
                "k_by_category":frozen, "k_update_counts":replay["k_update_counts"],
                "training_checkpoints":replay["training_checkpoints"],
                "evaluation_cases":[baseline.serialize_case(c) for c in evaluation],
                "baseline_reproduced":True})
            fixed_rows = [{**r,"halt_reason":"budget_exhausted"} for r in replay["evaluation_rows"]]
            fixed_runs.append({"seed":seed, "metrics":metrics(fixed_rows),
                               "evaluation_rows":fixed_rows, "evaluation_frozen":True})
            prod_invs = {c:VLDInvestigator(info["all_category_mu"][c],info["sigma"],
                        info["factor_names"],tau=info["tau"],action_names=info["action_names"])
                         for c in info["category_names"]}
            frozen_hash = baseline.digest(frozen)
            for delta in DELTAS:
                rows = [adaptive_episode(c,prod_invs[c["category"]],
                          np.asarray(frozen[c["category"]]),delta) for c in evaluation]
                assert baseline.digest(frozen) == frozen_hash
                adaptive_runs[delta].append({"seed":seed,"metrics":metrics(rows),
                    "evaluation_rows":rows,"evaluation_frozen":True})
            print(f"{name}: seed {seed}, B2 reproduced and six thresholds evaluated",flush=True)
        cop["fixed_b2"] = aggregate(name,None,fixed_runs,fixed_runs)
        cop["adaptive_results"] = [aggregate(name,d,adaptive_runs[d],fixed_runs) for d in DELTAS]
        cop["best_qualifying"],cop["diagnostic_result"] = selections(cop["adaptive_results"])
        cop["pareto_frontier"] = pareto([cop["fixed_b2"]]+cop["adaptive_results"])
        cop["verdict"] = "NO_QUALIFYING_DELTA"
        data["copilots"].append(cop)
        data["rows"].extend({k:r[k] for k in FIELDS}
                           for r in [cop["fixed_b2"]]+cop["adaptive_results"])
    data["checks"] = validate(data,export,frontier)
    data["headline"] = "No tested delta saves reads versus fixed B2; the production two-read floor prevents the proposed headline"
    data["source_hashes_after"] = hashes()
    assert before == data["source_hashes_after"]
    content = json.dumps(data,indent=2,allow_nan=False)+"\n"
    buffer = io.StringIO(newline="")
    writer=csv.DictWriter(buffer,fieldnames=FIELDS)
    writer.writeheader(); writer.writerows(data["rows"])
    with OUT.open("x",encoding="utf-8",newline="\n") as f:
        f.write(content)
    with CSV.open("x",encoding="utf-8",newline="") as f:
        f.write(buffer.getvalue())
    headlines(data)
    print(f"Saved {OUT}\nSaved {CSV}")


if __name__ == "__main__":
    main()

