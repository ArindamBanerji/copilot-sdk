"""RI-5 and shared, artifact-only recurrence experiment machinery.

Run with the project interpreter and -B. Other new experiment entrypoints
import this module so all controls share exactly the same measurement code.
No production modules, datasets, databases, or existing scripts are written.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys
import time

import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/vld"
from routing_variant_bandit import make_case, score, q_rnn

COPILOTS = ["dataops", "trading", "purchasing", "soc", "s2p"]
PENALTIES = dict(soc=20, dataops=10, s2p=5, purchasing=3, trading=2)
SITUATION_BUDGETS = dict(S1=0, S2=1, S3=2, S4=3, S5=2, S6=1)
CORE = ["copilot_sdk/scoring/investigation.py", "copilot_sdk/backend/investigation_router.py", "copilot_sdk/scoring/scorer.py"]
EXPECTED = ["3441dcbd", "08f4df7a", "24ac9e49"]


def hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in CORE}


def load_classifier():
    # Direct load avoids package initialization and any application side effects.
    spec = importlib.util.spec_from_file_location("vld_experiment_c4", ROOT / "copilot_sdk/scoring/situation_classifier.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.SituationClassifier()


def components(mu, sigma, v, probs):
    a, b = np.argsort(probs)[::-1][:2]
    return np.column_stack((1 / np.maximum(sigma**2, .001) / 100,
                            np.abs(mu[a] - mu[b]),
                            np.abs((v - mu[a])**2 - (v - mu[b])**2)))


class State:
    def __init__(self, categories, dims, pooled=False):
        keys = ["pooled"] if pooled else categories
        self.pooled = pooled
        self.k = {c: np.full(dims, .5) for c in keys}
        self.n = {c: np.zeros(dims, dtype=int) for c in keys}
        self.last = {c: np.zeros(dims, dtype=int) for c in keys}
        self.update_mean = {c: np.zeros(dims) for c in keys}
        self.m2 = {c: np.zeros(dims) for c in keys}
        self.co = {c: np.zeros((dims, dims), dtype=int) for c in keys}
        self.category_n = {c: np.zeros(dims, dtype=int) for c in categories}
        self.mode = {c: .5 for c in categories}  # initially all K at baseline
        self.w = np.ones(3)

    def key(self, category):
        return "pooled" if self.pooled else category

    def effective(self, category, decision, decay):
        key = self.key(category)
        elapsed = decision - self.last[key]
        age = (elapsed - elapsed.min()) / max(1, int(elapsed.max() - elapsed.min()))
        return self.k[key] * np.exp(-decay * age)

    def rich_std(self, key):
        # One prior pseudo-observation with variance .25; persist both variance
        # and sigma. Normal takes a standard deviation, not a variance.
        variance = (.25 + self.m2[key]) / (self.n[key] + 1)
        return np.sqrt(variance)

    def update_modes(self):
        for c in self.mode:
            starvation = float(np.mean(np.isclose(self.k[self.key(c)], .5, atol=1e-12, rtol=0)))
            self.mode[c] = .5 if starvation > .3 else (.25 if starvation >= .1 else 0.)

    def snapshot(self, decision, decay):
        return {
            "k": {c: v.tolist() for c, v in self.k.items()},
            "k_effective": {c: self.effective(c, decision, decay).tolist() for c in self.k},
            "n": {c: v.tolist() for c, v in self.n.items()},
            "last_selected": {c: v.tolist() for c, v in self.last.items()},
            "sigma_k": {c: self.rich_std(c).tolist() for c in self.k},
            "update_variance": {c: (self.m2[c] / np.maximum(1, self.n[c] - 1)).tolist() for c in self.k},
            "category_modes": dict(self.mode), "q_weights": self.w.tolist(),
            "cooccurrence": {c: v.tolist() for c, v in self.co.items()},
        }


def case_for(rng, mu, sigma, tau, regime):
    case = make_case(rng, mu, sigma, tau)
    if regime is not None:
        dims = {0, 2} if regime == 0 else {1, 3}
        target = case["correct_action"]
        distractor = max((a for a in range(len(mu)) if a != target),
                         key=lambda a: float(np.linalg.norm(mu[a] - mu[target])))
        case["surface"] = case["full"].copy()
        for d in sorted(dims):
            case["surface"][d] = np.clip(mu[distractor, d] + rng.gauss(0, .03), .02, .98)
        case["informative"] = dims
    return case


def category_for(rng, categories, shifted, phase):
    if not shifted:
        return rng.choice(categories)
    split = len(categories) // 2
    first = .8 if phase == 0 else .2
    weights = [first / split if i < split else (1-first)/(len(categories)-split) for i in range(len(categories))]
    return rng.choices(categories, weights=weights)[0]


def lookahead(v, mu, sigma, tau, remaining, depth, scorer):
    """Exact small centroid-branch rollout; never consumes hidden case evidence.

    The current action posterior supplies branch probabilities. Each branch
    substitutes that action's centroid coordinate; subsequent branches use
    the updated posterior. Utility is expected terminal probability margin.
    """
    _, probs, current_margin = scorer(v)
    utilities = []
    for d in remaining:
        expected = 0.
        for a in range(len(mu)):
            candidate = v.copy()
            candidate[d] = mu[a, d]
            _, _, margin = scorer(candidate)
            if depth > 1 and len(remaining) > 1:
                _, future = lookahead(candidate, mu, sigma, tau, [j for j in remaining if j != d], depth-1, scorer)
                margin += future
            expected += float(probs[a]) * margin
        utilities.append(expected - current_margin)
    winner = int(np.argmax(utilities))
    return remaining[winner], utilities[winner]


def episode(case, category, mu, sigma, tau, state, cfg, rng, decision, train, classifier=None):
    key = state.key(category)
    k = state.effective(category, decision, cfg.get("decay", 0))
    v = case["surface"].copy()
    selected, xs = [], []
    evals = 0

    def scorer(vector):
        nonlocal evals
        evals += 1
        return score(mu, sigma, tau, vector)

    surface_action, probs, _ = scorer(v)
    budget = cfg.get("budget", 2)
    situation = None
    if classifier is not None:
        q = q_rnn(mu, sigma, v, probs, set(), k)
        situation = classifier.classify(v, mu, sigma, probs, q).situation
        if cfg.get("hierarchical"):
            budget = SITUATION_BUDGETS[situation]
    for step in range(min(budget, len(v))):
        # Match prior harness accounting: surface + B intermediate + final.
        _, probs, _ = scorer(v)
        x = components(mu, sigma, v, probs)
        q = (x @ (state.w if cfg.get("learned") else np.ones(3))) * k
        q *= cfg.get("risk_scale", 1)
        if selected:
            q[selected] = -np.inf
        valid = [d for d in range(len(v)) if d not in selected]
        if cfg.get("lookahead", 0):
            dim, _ = lookahead(v, mu, sigma, tau, valid, min(cfg["lookahead"], budget-step), scorer)
        else:
            scores = q.copy()
            mode = cfg.get("mode", "greedy")
            if mode in ("thompson", "rich"):
                std = state.rich_std(key) if mode == "rich" else sigma
                std = std * cfg.get("risk_sigma", 1) / np.sqrt(state.n[key]+1)
                for d in valid:
                    scores[d] = rng.gauss(float(q[d]), float(std[d]))
            if mode in ("ucb", "adaptive"):
                c = state.mode[category] if mode == "adaptive" else cfg.get("c", .5)
                scores += c * sigma / np.sqrt(state.n[key]+1)
            if selected and cfg.get("beta", 0):
                row = state.co[key][selected[-1]]
                scores += cfg["beta"] * row / (row.sum()+1)
            dim = int(np.argmax(scores))
        selected.append(dim)
        xs.append(x[dim].copy())
        if dim in case["informative"]:
            v[dim] = case["full"][dim]
    final_action, _, _ = scorer(v)
    correct = final_action == case["correct_action"]
    learning_evals = 0
    if train:
        for d in selected:
            old = state.k[key][d]
            state.k[key][d] = np.clip(old + (.02 if correct and d in case["informative"] else -.005), .1, 3.)
            update = state.k[key][d] - old
            state.n[key][d] += 1
            state.category_n[category][d] += 1
            state.last[key][d] = decision
            delta = update - state.update_mean[key][d]
            state.update_mean[key][d] += delta / state.n[key][d]
            state.m2[key][d] += delta * (update - state.update_mean[key][d])
        if correct:
            for i, j in zip(selected, selected[1:]):
                state.co[key][i, j] += 1
        if cfg.get("learned"):
            # Verified full-vector counterfactuals are an explicitly privileged
            # upper-bound training signal; they are unavailable at selection.
            _, p0, _ = score(mu, sigma, tau, case["surface"])
            gains = []
            for d in range(len(v)):
                candidate = case["surface"].copy()
                if d in case["informative"]:
                    candidate[d] = case["full"][d]
                _, p, _ = score(mu, sigma, tau, candidate)
                gains.append(float(p[case["correct_action"]] - p0[case["correct_action"]]))
            target = np.zeros(len(v))
            target[int(np.argmax(gains))] = 1.
            design = components(mu, sigma, case["surface"], p0)
            gradient = design.T @ (design @ state.w - target) / len(v)
            state.w = np.clip(state.w - .05 * gradient, .01, 10.)
            learning_evals = len(v)+1
    return dict(reads=len(selected), informative_reads=sum(d in case["informative"] for d in selected),
                correct=int(correct), saved=int(surface_action != case["correct_action"] and correct),
                hurt=int(surface_action == case["correct_action"] and not correct),
                scorer_evals=evals, learning_scorer_evals=learning_evals, situation=situation,
                selected=selected, final_action=int(final_action))


def metrics(rows):
    reads = sum(r["reads"] for r in rows)
    evals = sum(r["scorer_evals"] for r in rows)
    n = len(rows)
    return dict(routing_quality=sum(r["informative_reads"] for r in rows)/max(1, reads),
                accuracy=sum(r["correct"] for r in rows)/n,
                avg_reads=reads/n, scorer_evals=evals/n,
                accuracy_per_scorer_eval=sum(r["correct"] for r in rows)/max(1, evals),
                learning_scorer_evals=sum(r["learning_scorer_evals"] for r in rows)/n,
                saves=sum(r["saved"] for r in rows), hurts=sum(r["hurt"] for r in rows))


def run_seed(info, cfg, seed, experiment):
    cats = info["category_names"]
    sigma, tau = np.array(info["sigma"]), float(info["tau"])
    mus = {c: np.array(info["all_category_mu"][c]) for c in cats}
    state = State(cats, len(sigma), cfg.get("pooled", False))
    train_rng, policy_rng = random.Random(seed), random.Random(seed+8000000)
    classifier = load_classifier() if experiment == "rv5" else None
    temporal, shifted = experiment == "ri6", experiment == "ri9"
    training, checkpoints = [], []
    stream_hash, route_hash = hashlib.sha256(), hashlib.sha256()
    immediate = None

    def evaluate(t, phase):
        erng, prng = random.Random(seed+100000+t), random.Random(seed+9000000+t)
        rows = []
        before = json.dumps(state.snapshot(t, cfg.get("decay", 0)), sort_keys=True)
        for _ in range(50):
            c = category_for(erng, cats, shifted, phase)
            case = case_for(erng, mus[c], sigma, tau, phase if temporal else None)
            rows.append(episode(case, c, mus[c], sigma, tau, state, cfg, prng, t, False, classifier))
        assert before == json.dumps(state.snapshot(t, cfg.get("decay", 0)), sort_keys=True), "evaluation mutated learner"
        return {**metrics(rows), "situation_counts": {s: sum(r["situation"] == s for r in rows) for s in SITUATION_BUDGETS},
                "eval_rows": rows}

    started = time.perf_counter()
    for t in range(1, 501):
        phase = int(t > 250)
        c = category_for(train_rng, cats, shifted, phase)
        case = case_for(train_rng, mus[c], sigma, tau, phase if temporal else None)
        stream_hash.update(c.encode()+case["surface"].tobytes()+case["full"].tobytes()+bytes(sorted(case["informative"])))
        row = episode(case, c, mus[c], sigma, tau, state, cfg, policy_rng, t, True, classifier)
        training.append(row)
        route_hash.update(json.dumps([c, row["selected"], row["final_action"]]).encode())
        if t % 50 == 0:
            state.update_modes()
            result = evaluate(t, phase)
            result.update(decision_count=t, starvation=float(np.mean([n == 0 for n in state.category_n.values()])),
                          weight_starvation=float(np.mean([np.isclose(k, .5, atol=1e-12, rtol=0) for k in state.k.values()])),
                          state=state.snapshot(t, cfg.get("decay", 0)))
            checkpoints.append(result)
        if t == 250 and (temporal or shifted):
            immediate = evaluate(t, 1)
    out = dict(seed=seed, checkpoints=checkpoints, training_metrics=metrics(training),
               training_rows=training, training_stream_sha256=stream_hash.hexdigest(),
               training_routes_sha256=route_hash.hexdigest(), elapsed_seconds=time.perf_counter()-started,
               category_attempts={c: n.tolist() for c, n in state.category_n.items()})
    if temporal or shifted:
        pre = float(np.mean([p["routing_quality"] for p in checkpoints if p["decision_count"] in (200, 250)]))
        target = .9 * pre
        candidates = [(0, immediate["routing_quality"])] + [(p["decision_count"]-250, p["routing_quality"]) for p in checkpoints if p["decision_count"] > 250]
        recovery = next((t for t, q in candidates if q >= target), None)
        out["recovery"] = dict(pre_shift_quality=pre, pre_shift_training_201_250=metrics(training[200:250]),
                               target=target, immediate_post_shift=immediate,
                               decisions_to_90pct=recovery, censored=recovery is None,
                               restricted_recovery=min(250, recovery) if recovery is not None else 250,
                               final_quality=checkpoints[-1]["routing_quality"])
    return out


def aggregate(runs):
    cps = []
    for i in range(10):
        row = {"decision_count": (i+1)*50}
        for metric in ("routing_quality", "accuracy", "avg_reads", "scorer_evals", "accuracy_per_scorer_eval", "starvation", "weight_starvation"):
            values = [r["checkpoints"][i][metric] for r in runs]
            row[metric+"_mean"], row[metric+"_std"] = float(np.mean(values)), float(np.std(values, ddof=1))
        cps.append(row)
    final = cps[-1]
    out = dict(checkpoints=cps, final_routing_mean=final["routing_quality_mean"],
               final_accuracy_mean=final["accuracy_mean"], starvation=final["starvation_mean"],
               avg_reads=final["avg_reads_mean"], scorer_evals=final["scorer_evals_mean"],
               accuracy_per_scorer_eval=final["accuracy_per_scorer_eval_mean"],
               training_avg_reads=float(np.mean([r["training_metrics"]["avg_reads"] for r in runs])),
               learning_scorer_evals=float(np.mean([r["training_metrics"]["learning_scorer_evals"] for r in runs])), seed_runs=runs)
    if "recovery" in runs[0]:
        out["recovery"] = dict(pre_shift_quality=float(np.mean([r["recovery"]["pre_shift_quality"] for r in runs])),
                               restricted_mean_decisions=float(np.mean([r["recovery"]["restricted_recovery"] for r in runs])),
                               censored_seeds=sum(r["recovery"]["censored"] for r in runs),
                               recovered_at_zero=sum(r["recovery"]["decisions_to_90pct"] == 0 for r in runs))
    return out


def paired(a, b, metric="routing_quality"):
    values = np.array([x["checkpoints"][-1][metric]-y["checkpoints"][-1][metric] for x, y in zip(a["seed_runs"], b["seed_runs"])])
    rng = np.random.default_rng(20260913)
    means = rng.choice(values, size=(10000, len(values)), replace=True).mean(axis=1)
    return dict(mean=float(values.mean()), seed_deltas=values.tolist(),
                bootstrap_95_interval=np.quantile(means, [.025, .975]).tolist())


def run_experiment(experiment, filename, configs, copilots, verdict_fn, seeds=5, notes=None):
    before = hashes()
    assert all(before[p].startswith(e) for p, e in zip(CORE, EXPECTED)), "unexpected source baseline"
    export = json.loads((ROOT/"real_centroids_v1.json").read_text(encoding="utf-8"))["copilots"]
    results, resolved_configs = {}, {}
    for copilot in copilots:
        cs = configs(copilot) if callable(configs) else configs
        resolved_configs[copilot] = cs
        results[copilot] = {}
        for name, cfg in cs.items():
            runs = [run_seed(export[copilot], cfg, 20260913+sum(map(ord, copilot))*100+s, experiment) for s in range(seeds)]
            results[copilot][name] = aggregate(runs)
            r = results[copilot][name]
            print(f"{experiment} {copilot} {name}: routing={r['final_routing_mean']:.3f}, accuracy={r['final_accuracy_mean']:.3f}, starvation={r['starvation']:.3f}", flush=True)
        baseline = next(iter(results[copilot].values()))
        for r in results[copilot].values():
            assert [s["training_stream_sha256"] for s in r["seed_runs"]] == [s["training_stream_sha256"] for s in baseline["seed_runs"]]
            r["paired_routing_vs_control"] = paired(r, baseline)
            r["paired_accuracy_vs_control"] = paired(r, baseline, "accuracy")
    assert hashes() == before
    payload = dict(experiment=experiment, protocol=dict(total_decisions=500, checkpoints=10, evaluation_scenarios_per_checkpoint=50,
                   seeds=seeds, seed_base=20260913, k_learning=True, k_initial=.5, k_bounds=[.1, 3.], lr_positive=.02, lr_negative=.005,
                   scenario_source="routing_variant_bandit.make_case; synthetic cases on exported real geometry",
                   routing_metric="informative reads / actual reads", starvation_metric="category-dimension cells never selected / all cells",
                   category_mode_metric="fraction of category K weights equal to initial .5 at each checkpoint",
                   evaluation="50 held-out cases per checkpoint, frozen state; independent case/policy RNG streams; paired variants",
                   uncertainty="sample SD and paired-seed percentile bootstrap 95% interval; descriptive, no multiplicity correction",
                   recovery="first held-out checkpoint >=90% mean quality at 200 and 250; immediate post-shift probe; 50-decision resolution; unrecovered censored at 250",
                   production_differences="prior bandit harness update +.02/-.005, no flip bonus or early halt; centroid scorer fallback, no live evidence"),
                   notes=notes or [], configs=resolved_configs, results=results, verdict=verdict_fn(results),
                   source_hashes_before=before, source_hashes_after=hashes(),
                   requested_hash_prefixes=dict(zip(CORE, ["3441dcdb", "08f4df7a", "24ac9e49"])),
                   preexisting_hash_discrepancy="investigation.py observed 3441dcbd before any writes; prompt expects 3441dcdb (last two characters transposed). Source preserved.",
                   centroid_sha256=hashlib.sha256((ROOT/"real_centroids_v1.json").read_bytes()).hexdigest(),
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   entrypoint_sha256=hashlib.sha256(Path(sys.argv[0]).read_bytes()).hexdigest())
    (OUT/filename).write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    print(f"{filename}: {payload['verdict']}", flush=True)
    return payload


def rich_verdict(results):
    trading = results["trading"]
    g, r = trading["GREEDY-SCALAR-K"], trading["THOMPSON-RICH-K"]
    reduction = g["starvation"] - r["starvation"]
    gaps = {c: v["THOMPSON-RICH-K"]["final_routing_mean"]-v["GREEDY-SCALAR-K"]["final_routing_mean"] for c, v in results.items()}
    return dict(keep=reduction >= .2 and min(gaps.values()) >= -.03,
                trading_starvation_reduction_pp=100*reduction, routing_deltas_pp={c: 100*v for c, v in gaps.items()},
                criterion="Trading starvation reduction >=20pp and routing loss <=3pp on every copilot")


if __name__ == "__main__":
    run_experiment("ri5", "ri5_rich_k_state.json", {"GREEDY-SCALAR-K": {}, "THOMPSON-SCALAR-K": {"mode": "thompson"}, "THOMPSON-RICH-K": {"mode": "rich"}}, COPILOTS, rich_verdict,
                   notes=["sigma_K is the SD of K update increments; raw sample variance is also retained. Prior variance .25 with one pseudo-observation prevents zero initial uncertainty. Normal scale = sigma_K/sqrt(N+1).", "N counts selected reads that return a result, including unchanged evidence; every synthetic provider read returns a result."])
