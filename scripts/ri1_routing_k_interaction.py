"""RI-1 factorial and shared, artifact-only experiment harness.

Uses the exported geometry and the exact RV-0 GRU/LSTM heuristics.
Run with the requested virtual environment and -B. No application databases.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
import time

sys.dont_write_bytecode = True
import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/vld"
COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")
VARIANTS = ("static", "rnn", "gru", "lstm")
SEEDS = tuple(20260913 + i for i in range(10))
N = 500
EVAL = 50
INTERVAL = 50
BUDGET = 2
INPUTS = (
    "real_centroids_v1.json", "copilot_sdk/scoring/investigation.py",
    "copilot_sdk/backend/investigation_router.py", "copilot_sdk/scoring/scorer.py",
    "scripts/k_learning_curve_experiment.py", "scripts/k_learning_curve_cross_copilot.py",
    "scripts/routing_variant_gru_ablation.py", "scripts/routing_variant_bandit.py",
    "experiments/vld/rv0_gru_ablation_results.json",
    "experiments/vld/rv1_bandit_results.json",
    "experiments/vld/k_learning_curve_cross_copilot_summary.json",
    "experiments/vld/rv01_routing_variants_report.md",
    "experiments/vld/k_learning_curve_cross_copilot_report.md",
)


def module_from_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


rv0 = module_from_file("group_ad_rv0", ROOT / "scripts/routing_variant_gru_ablation.py")
production = module_from_file("group_ad_investigation", ROOT / "copilot_sdk/scoring/investigation.py")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def input_hashes():
    return {f: digest(ROOT / f) for f in INPUTS}


@dataclass(frozen=True)
class Policy:
    variant: str = "rnn"
    learning: bool = True
    exploration: str = "greedy"
    c: float = 0.0
    epsilon: float = 0.0
    conservation: bool = False


def geometry(name):
    info = json.loads((ROOT / "real_centroids_v1.json").read_text(encoding="utf-8"))["copilots"][name]
    cats = list(info["category_names"])
    factors = list(info["factor_names"])
    sigma = np.asarray(info["sigma"], dtype=float)
    mu = {c: np.asarray(info["all_category_mu"][c], dtype=float) for c in cats}
    assert sigma.shape == (len(factors),) and np.all(sigma > 0)
    for value in mu.values():
        assert value.shape == (len(info["action_names"]), len(factors))
    return {"name": name, "categories": cats, "factors": factors,
            "actions": info["action_names"], "mu": mu, "sigma": sigma,
            "tau": float(info["tau"]), "info": info}


def informative_set(mu, sigma, tau, surface, full):
    truth, _, _ = rv0.score(mu, sigma, tau, full)
    action0, p0, _ = rv0.score(mu, sigma, tau, surface)
    useful = set()
    for dim in range(len(surface)):
        v = surface.copy()
        v[dim] = full[dim]
        action, probs, _ = rv0.score(mu, sigma, tau, v)
        gain = float(probs[truth] - p0[truth])
        gap = abs(float(mu[truth, dim] - mu[action0, dim]))
        if action == truth or (gain >= 0.02 and gap >= 0.08):
            useful.add(dim)
    if not useful:
        useful.update(int(i) for i in np.argsort(np.abs(full - surface))[::-1][:2])
    return truth, action0, useful


def make_case(rng, g, distribution="uniform"):
    cats = g["categories"]
    if distribution == "clustered" and rng.random() < 0.60:
        cat = rng.choice(cats[:2])
    else:
        cat = rng.choice(cats)
    mu, sigma, tau = g["mu"][cat], g["sigma"], g["tau"]
    if distribution != "adversarial":
        case = rv0.make_case(rng, mu, sigma, tau)
    else:
        # A closest pair has a midpoint on the nearest-prototype boundary.
        # Choosing any tied closest pair and either endpoint avoids biased truth labels.
        precision = 1 / np.maximum(sigma**2, 0.001)
        pairs = [(float(np.sum(precision * (mu[a]-mu[b])**2)), a, b)
                 for a in range(len(mu)) for b in range(a+1, len(mu))]
        closest = min(x[0] for x in pairs)
        candidates = [x for x in pairs if np.isclose(x[0], closest, rtol=1e-10, atol=1e-12)]
        _, a, b = rng.choice(candidates)
        truth_endpoint = rng.choice((a, b))
        surface = (mu[a] + mu[b]) / 2
        full = np.clip(mu[truth_endpoint] + np.array([rng.gauss(0, 0.035) for _ in sigma]), 0.02, 0.98)
        truth, action0, useful = informative_set(mu, sigma, tau, surface, full)
        distances = np.sum(precision * (mu-surface)**2, axis=1)
        ordered = np.sort(distances)
        gap = float(abs(distances[a]-distances[b]))
        assert gap < 1e-10 and abs(ordered[1]-ordered[0]) < 1e-10
        case = {"surface": surface, "full": full, "correct_action": truth,
                "informative": useful, "ambiguity_pair": [a, b], "distance_gap": gap}
    case["category"] = cat
    case["surface_action"] = rv0.score(mu, sigma, tau, case["surface"])[0]
    case["informative"] = set(int(i) for i in case["informative"])
    return case


def cases_hash(cases):
    data = [{"category": x["category"], "surface": x["surface"].tolist(),
             "full": x["full"].tolist(), "correct_action": x["correct_action"],
             "informative": sorted(x["informative"])} for x in cases]
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def prepare(g, seed, distribution="uniform"):
    code = sum(ord(c) for c in g["name"]) * 100
    rng = random.Random(seed + code)
    train = [make_case(rng, g, distribution) for _ in range(N)]
    ev = {}
    for checkpoint in range(0, N+1, INTERVAL):
        erng = random.Random(seed + code + 100000 + checkpoint)
        ev[checkpoint] = [make_case(erng, g, distribution) for _ in range(EVAL)]
    return {"train": train, "eval": ev,
            "hashes": {"train": cases_hash(train),
                       "eval": {str(n): cases_hash(v) for n, v in ev.items()}}}


def episode(case, g, k, attempts, policy, rng):
    start = time.perf_counter()
    mu, sigma, tau = g["mu"][case["category"]], g["sigma"], g["tau"]
    v = case["surface"].copy()
    full = case["full"]
    selected = []
    q_trace = []
    enriched = set()
    hidden = np.zeros(len(v))
    cell = np.zeros(len(v))
    scorer_calls = q_calls = 0
    if policy.variant == "static":
        _, probs, _ = rv0.score(mu, sigma, tau, v)
        scorer_calls += 1
        q = rv0.q_rnn(mu, sigma, v, probs, set(), k)
        q_calls += 1
        planned = [int(i) for i in np.argsort(q)[::-1] if q[int(i)] > 0][:BUDGET]
        q_trace.append(q.tolist())
        for dim in planned:
            selected.append(dim)
            if dim in case["informative"]:
                v[dim] = full[dim]
    else:
        for hop in range(min(BUDGET, len(v))):
            _, probs, _ = rv0.score(mu, sigma, tau, v)
            scorer_calls += 1
            if policy.variant == "rnn":
                q = rv0.q_rnn(mu, sigma, v, probs, enriched, k)
            elif policy.variant == "gru":
                q, hidden = rv0.q_gru(mu, sigma, tau, v, probs, enriched, k, hidden)
            elif policy.variant == "lstm":
                q, hidden, cell = rv0.q_lstm(mu, sigma, tau, v, probs, enriched, k, hidden, cell)
            else:
                raise ValueError(policy.variant)
            q_calls += 1
            valid = np.where(q > 0)[0]
            if not len(valid):
                break
            selection_scores = q.copy()
            if policy.exploration == "ucb" or (policy.exploration == "hybrid" and hop == 1):
                bonus_c = 1.0 if policy.exploration == "hybrid" else policy.c
                selection_scores[valid] += bonus_c * sigma[valid] / np.sqrt(attempts[valid]+1)
            if policy.exploration == "epsilon" and rng.random() < policy.epsilon:
                dim = int(rng.choice(list(valid)))
            else:
                selection_scores[q <= 0] = -np.inf
                dim = int(np.argmax(selection_scores))
            q_trace.append({"q": q.tolist(), "selection_scores":
                            [None if not np.isfinite(x) else float(x) for x in selection_scores]})
            enriched.add(dim)
            selected.append(dim)
            if dim in case["informative"]:
                v[dim] = full[dim]
    final = rv0.score(mu, sigma, tau, v)[0]
    scorer_calls += 1
    truth, initial = case["correct_action"], case["surface_action"]
    return {"selected": selected, "informative_reads": sum(i in case["informative"] for i in selected),
            "reads": len(selected), "correct": final == truth,
            "saved": initial != truth and final == truth,
            "hurt": initial == truth and final != truth, "surface_correct": initial == truth,
            "final_action": int(final), "scorer_calls": scorer_calls, "q_calls": q_calls,
            "elapsed_ms": 1000*(time.perf_counter()-start), "q_trace": q_trace}


def state_snapshot(weights):
    return {k: v.tolist() for k, v in weights.items()}


def evaluate(g, cases, weights, attempts, policy, seed):
    frozen = state_snapshot(weights)
    frozen_counts = state_snapshot(attempts)
    rng = random.Random(seed)
    runs = [episode(case, g, weights[case["category"]], attempts[case["category"]], policy, rng)
            for case in cases]
    assert frozen == state_snapshot(weights) and frozen_counts == state_snapshot(attempts)
    total_reads = sum(x["reads"] for x in runs)
    result = {"routing_quality": sum(x["informative_reads"] for x in runs)/max(total_reads, 1),
              "accuracy": sum(x["correct"] for x in runs)/len(runs),
              "saves": sum(x["saved"] for x in runs), "hurts": sum(x["hurt"] for x in runs),
              "surface_correct": sum(x["surface_correct"] for x in runs),
              "reads": total_reads, "scorer_calls_per_decision": np.mean([x["scorer_calls"] for x in runs]).item(),
              "q_calls_per_decision": np.mean([x["q_calls"] for x in runs]).item(),
              "latency_ms_mean": np.mean([x["elapsed_ms"] for x in runs]).item(),
              "latency_ms_p95": np.percentile([x["elapsed_ms"] for x in runs],95).item(),
              "evaluation_cases": len(runs)}
    return result


def run_arm(g, data, seed, policy, initial=None, gate=None, longitudinal=False):
    cats, dims = g["categories"], len(g["factors"])
    weights = {c: np.full(dims, 0.5) if initial is None else initial[c].copy() for c in cats}
    initial_weights = state_snapshot(weights)
    attempts = {c: np.zeros(dims, dtype=int) for c in cats}
    updates = {c: np.zeros(dims, dtype=int) for c in cats}
    support = Counter()
    rng = random.Random(seed+900000)
    base = evaluate(g, data["eval"][0], weights, attempts, policy, seed+800000)
    checkpoints = []
    history = []
    blocked_steps = blocked_decisions = train_correct = train_hurts = 0
    examples = []
    for n, case in enumerate(data["train"], 1):
        cat = case["category"]
        before = weights[cat].copy()
        run = episode(case, g, before, attempts[cat], policy, rng)
        support[cat] += 1
        train_correct += int(run["correct"])
        train_hurts += int(run["hurt"])
        for dim in run["selected"]:
            attempts[cat][dim] += 1
        allowed = True
        if gate is not None:
            record = gate(n, train_correct, len(support), len(cats))
            allowed = record["status"] == "GREEN"
            history.append({"decision_count": n, **record})
        if policy.learning and allowed:
            # Prompt's exact +/- rates, RV-0/RV-1 convention: no flip bonus.
            rv0.update_k(weights[cat], run["selected"], case["informative"], run["correct"])
            for dim in run["selected"]:
                updates[cat][dim] += 1
        elif policy.learning and not allowed:
            blocked_decisions += 1
            blocked_steps += len(run["selected"])
        assert np.all(weights[cat] >= 0.1) and np.all(weights[cat] <= 3)
        if not policy.learning:
            assert np.all(weights[cat] == 0.5)
        if n <= 3:
            examples.append({"decision": n, "category": cat, "k_before": before.tolist(),
                             "surface": case["surface"].tolist(), "truth": case["correct_action"],
                             **{k: v for k,v in run.items() if k != "elapsed_ms"}})
        if n % INTERVAL == 0:
            point = evaluate(g, data["eval"][n], weights, attempts, policy, seed+800000+n)
            point.update({"decision_count": n,
                          "selection_starvation": float(np.mean(np.concatenate(list(attempts.values())) == 0)),
                          "update_starvation": float(np.mean(np.concatenate(list(updates.values())) == 0)),
                          "blocked_decisions": blocked_decisions, "blocked_updates": blocked_steps,
                          "k_by_category": state_snapshot(weights)})
            if longitudinal:
                # Supplemental same 50 cases at every checkpoint: separates drift from fresh-cohort noise.
                point["longitudinal"] = evaluate(g, data["eval"][0], weights, attempts, policy, seed+800000)
            checkpoints.append(point)
    return {"seed": seed, "baseline": base, "checkpoints": checkpoints,
            "initial_k": initial_weights, "final_k": state_snapshot(weights),
            "attempt_counts": state_snapshot(attempts), "update_counts": state_snapshot(updates),
            "category_counts": dict(support), "blocked_decisions": blocked_decisions,
            "blocked_updates": blocked_steps, "training_hurts": train_hurts,
            "training_correct": train_correct, "conservation_history": history,
            "case_hashes": data["hashes"], "example_traces": examples}


def mean_sd(values):
    a = np.asarray(values, dtype=float)
    return float(np.mean(a)), float(np.std(a, ddof=1)) if len(a)>1 else 0.0


def paired(a, b, metric="routing_quality"):
    vals = [x["checkpoints"][-1][metric] - y["checkpoints"][-1][metric]
            for x,y in zip(a["seed_runs"],b["seed_runs"])]
    avg, sd = mean_sd(vals)
    error = float(student_t.ppf(0.975,len(vals)-1)*sd/np.sqrt(len(vals))) if len(vals)>1 else 0
    return {"mean": avg, "std": sd, "ci95": [avg-error, avg+error], "seed_deltas": vals}


def time_to_target(run, target):
    rows = [{"decision_count": 0, **run["baseline"]}] + run["checkpoints"]
    return next((r["decision_count"] for r in rows if r["routing_quality"] >= target), None)


def aggregate(runs):
    points = []
    for i in range(len(runs[0]["checkpoints"])):
        rows = [r["checkpoints"][i] for r in runs]
        item = {"decision_count": rows[0]["decision_count"]}
        for source,dest in [("routing_quality","routing"),("accuracy","accuracy"),
                            ("selection_starvation","starvation"),("update_starvation","update_starvation"),
                            ("blocked_decisions","blocked_decisions"),("blocked_updates","blocked_updates"),
                            ("scorer_calls_per_decision","scorer_evals"),("q_calls_per_decision","q_evals"),
                            ("latency_ms_mean","latency_ms")]:
            avg,sd=mean_sd([r[source] for r in rows])
            item[dest+"_mean"],item[dest+"_std"]=avg,sd
        item["hurts"] = sum(r["hurts"] for r in rows)
        item["saves"] = sum(r["saves"] for r in rows)
        item["surface_correct"] = sum(r["surface_correct"] for r in rows)
        if "longitudinal" in rows[0]:
            item["longitudinal_routing_mean"] = mean_sd([r["longitudinal"]["routing_quality"] for r in rows])[0]
        points.append(item)
    final = points[-1]
    # Observed-tail proxy, not a proven asymptote.
    target = .9 * float(np.mean([x["routing_mean"] for x in points[-3:]]))
    avgcurve = {"baseline": {"routing_quality": mean_sd([r["baseline"]["routing_quality"] for r in runs])[0]},
                "checkpoints": [{"decision_count": x["decision_count"], "routing_quality": x["routing_mean"]} for x in points]}
    result = {"final_routing_mean": final["routing_mean"], "final_routing_std": final["routing_std"],
              "final_accuracy_mean": final["accuracy_mean"], "final_accuracy_std": final["accuracy_std"],
              "starvation": final["starvation_mean"], "update_starvation": final["update_starvation_mean"],
              "hurts": final["hurts"], "hurts_all_checkpoints": sum(x["hurts"] for x in points),
              "training_hurts": sum(r["training_hurts"] for r in runs),
              "decisions_to_90pct": time_to_target(avgcurve,target), "target90": target,
              "checkpoints": points, "seed_runs": runs}
    result["three_metrics"] = {
        "M-VALUE": {"routing_quality": result["final_routing_mean"], "accuracy": result["final_accuracy_mean"],
                    "saves": final["saves"], "hurts": final["hurts"]},
        "M-COST": {"reads_per_decision": BUDGET, "scorer_evals_per_decision": final["scorer_evals_mean"],
                   "q_evals_per_decision": final["q_evals_mean"], "latency_ms_mean": final["latency_ms_mean"],
                   "accuracy_per_scorer_eval": result["final_accuracy_mean"]/final["scorer_evals_mean"],
                   "latency_scope": "in-process synthetic evidence; no database/network/UI latency"},
        "M-GOV": {"bounded_k": True, "frozen_k_within_episode": True, "evaluation_state_immutable": True,
                  "selection_starvation": result["starvation"], "update_starvation": result["update_starvation"],
                  "blocked_updates_mean": final["blocked_updates_mean"],
                  "deployment_safety": "NOT ESTABLISHED; synthetic trace/accounting checks only"}}
    return result


def protocol(experiment, seed_count):
    return {"experiment": experiment, "generated_utc": datetime.now(timezone.utc).isoformat(),
            "python": sys.version, "python_executable": sys.executable, "numpy": np.__version__,
            "seeds": list(SEEDS[:seed_count]), "total_decisions": N, "checkpoints": N//INTERVAL,
            "checkpoint_interval": INTERVAL, "evaluation_scenarios_per_checkpoint": EVAL,
            "budget": BUDGET, "k_initial": .5, "k_bounds": [.1,3], "k_update": {"positive": .02,"negative": .005,"flip_bonus": False},
            "k_reward": "selected dimension is oracle-informative AND final decision is correct",
            "scenario": "RV-0: uniform categories/actions; centroid-near truth + one/two corrupted dimensions, not uniform [0,1] vectors",
            "evidence": "oracle-informative dimensions restore full value; other reads leave vector unchanged",
            "pairing": "identical pre-generated train/eval cohorts per seed across arms; separate policy RNG",
            "evaluation": "fresh 50 cases each checkpoint; frozen K and counts, exploration retained at evaluation",
            "baseline": "additional independent 50-case N=0 diagnostic",
            "starvation": "fraction category-dimension pairs with zero TRAIN selections; update starvation separately recorded",
            "hurts": "surface-correct to final-wrong; final totals, all-checkpoint totals, training totals separate",
            "uncertainty": "sample SD; paired seed t-intervals (95%), unadjusted exploratory comparisons",
            "decisions_to_90pct": "first crossing of 90% mean routing at N=400/450/500, includes N=0; proxy not established asymptote",
            "grulstm": "untrained, hand-set RV-0 gates; not trained neural-network baselines",
            "source_hashes": input_hashes()}


def save(name, payload, hashes):
    assert input_hashes() == hashes, "An experiment input changed while running"
    out = OUT / name
    if out.exists():
        raise FileExistsError(f"Refusing to replace existing result: {out}")
    payload["protocol"]["inputs_unchanged"] = True
    payload["protocol"]["experiment_script_hashes"] = {
        path.name: digest(path) for path in sorted((ROOT/"scripts").glob("*group_a_d*"))}
    for path in sorted((ROOT/"scripts").glob("ri[1234]_*.py")):
        payload["protocol"]["experiment_script_hashes"][path.name]=digest(path)
    for path in [(ROOT/"scripts/ke4_distribution_sensitivity.py"),(ROOT/"scripts/ke5_conservation_interaction.py")]:
        if path.exists(): payload["protocol"]["experiment_script_hashes"][path.name]=digest(path)
    OUT.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as f:
        json.dump(payload,f,indent=2,allow_nan=False)
        f.write("\n")
    print("WROTE",out.name,flush=True)


def self_check():
    checks = 0
    for name in COPILOTS:
        g = geometry(name)
        rng=random.Random(171)
        for _ in range(12):
            case=make_case(rng,g)
            cat=case["category"]; mu=g["mu"][cat]
            engine=production.VLDInvestigator(mu,g["sigma"],g["factors"],tau=g["tau"])
            k=np.linspace(.1,3,len(g["factors"]))
            _,probs,_=rv0.score(mu,g["sigma"],g["tau"],case["surface"])
            assert np.allclose(engine.compute_Q(case["surface"],probs,{0},k),
                               rv0.q_rnn(mu,g["sigma"],case["surface"],probs,{0},k),rtol=0,atol=1e-14)
            for variant in VARIANTS:
                old=rv0.select_dims(variant,mu,g["sigma"],g["tau"],case,k,BUDGET)
                new=episode(case,g,k,np.zeros(len(k)),Policy(variant=variant),random.Random(1))
                assert old["selected"]==new["selected"] and old["correct"]==new["correct"]
                assert len(set(new["selected"]))==BUDGET
                checks+=1
    g=geometry("dataops")
    for _ in range(30): make_case(random.Random(_),g,"adversarial")
    w=np.array([.1,3.]); rv0.update_k(w,[0,1],{1},True)
    assert np.array_equal(w,[.1,3.])
    print("SELF-CHECK PASSED",checks,"variant parity cases; Q parity; midpoint boundaries; K bounds",flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-check",action="store_true")
    args=parser.parse_args()
    self_check()
    if args.self_check: return
    meta=protocol("RI-1",10); hashes=meta["source_hashes"]
    g=geometry("dataops")
    runs={f"{v}_{k}":[] for v in VARIANTS for k in ("fixed","learning")}
    for seed in SEEDS:
        data=prepare(g,seed)
        for variant in VARIANTS:
            for k in ("fixed","learning"):
                runs[f"{variant}_{k}"].append(run_arm(g,data,seed,Policy(variant=variant,learning=k=="learning")))
        print("RI-1 seed",seed,"complete",flush=True)
    results={name:aggregate(values) for name,values in runs.items()}
    interaction={}
    for v in VARIANTS:
        lift=paired(results[v+"_learning"],results[v+"_fixed"])
        interaction[v+"_k_lift"]=lift["mean"]
        interaction[v+"_k_lift_paired"]=lift
    for condition in ("fixed","learning"):
        interaction["ranking_"+condition]=sorted(VARIANTS,key=lambda v:results[v+"_"+condition]["final_routing_mean"],reverse=True)
    interaction["ranking_changed"]=interaction["ranking_fixed"]!=interaction["ranking_learning"]
    interaction["static_minus_rnn_learning"]=paired(results["static_learning"],results["rnn_learning"])
    interaction["static_minus_rnn_accuracy_learning"]=paired(results["static_learning"],results["rnn_learning"],"accuracy")
    d=np.array(interaction["static_k_lift_paired"]["seed_deltas"])-np.array(interaction["rnn_k_lift_paired"]["seed_deltas"])
    avg,sd=mean_sd(d); err=float(student_t.ppf(.975,len(d)-1)*sd/np.sqrt(len(d)))
    interaction["static_vs_rnn_difference_in_differences"]={"mean":avg,"ci95":[avg-err,avg+err],"seed_deltas":d.tolist()}
    meta["prior_result_correction"]="RV-0 headline results were K-learning, not K-fixed. Its control used different evaluation cases."
    save("ri1_routing_k_interaction.json",{"design":"4x2 factorial","protocol":meta,"results":results,"interaction_effect":interaction},hashes)


if __name__=="__main__":
    main()

