"""C2 -- PREREGISTERED before execution, 2026-09-14.
Metric: routing_quality gap widening (mu+K minus paired K-only), in pp.
Judgment-specific iff widening >2pp in >=3/5 seeds, with converged references.
If >=3/5 domains fail, narrow judgment specificity to the measured subset;
do not infer an evidence-rich causal explanation from domain names alone.
Seeds: 42,123,7,2024,99. SAME B2 learner/generator/convergence/parity.
Actual B2 split: 2000 train / 400 dev / 600 test, NOT 70/10/20.
Convergence .005 range in BOTH dev metrics, 3 checkpoints, min500/max2000,
checkpoint50. Joint routing_quality/action_accuracy parity .01, window3.
Primary gaps at each learner condition's incumbent convergence horizon;
also report mu+K at K-only incumbent horizon. Category supplied, not measured.
Use EXP1 K-only SOC/DataOps controls. Reproduce all six EXP2 cells BEFORE
running new seeds/domains. Compare per-seed values and THREE-SEED means.
Never compare a three-seed mean with seed42 alone.
All gap fields in this new output are PERCENTAGE POINTS; checkpoint metrics
and nested original harness records remain fractions.

S_B dimensional extension LOCKED BEFORE RUN (no retuning):
SOC/DataOps exactly original. Trading/Purchasing/S2P use unchanged shifted()
code in a private namespace, np.resize of six-factor scale/shift vectors.
rho=.30; clipping [.02,.98]; same empirical SD floor .035.
Category weights: truncate/resize DataOps [.05,.10,.10,.10,.45,.20],
normalize to sum1 (five categories: [.0625,.125,.125,.125,.5625]).
Action acceptance: truncate/resize DataOps [.2,1,.8,.6,.4] in export order.
This is ONE fixed index-based alternative-firm profile per new domain,
not a fitted or semantically validated customer model.
Domain seed offsets SOC0/DataOps10000/Trading20000/Purchasing30000/S2P40000.
Within each independent batch all target SA tests freeze before ANY SB.
Two independent stream/learner/cache rebuilds per seed and domain.

Reuse MuLearner and the audited in-memory run_arm guard adapter from EXP2.
ProfileScorer.update defaults eta/eta_neg .05, decay .001, per-coordinate
cap .005, bounds [0,1]. Ungated component experiment, not production safety.
Geometry REAL_COMPONENT; streams, verification and mu adaptation SIMULATED.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import types
from typing import Any, Callable, cast
import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.vld import vld_moat_mu_probe_v1 as m
from experiments.vld import vld_moat_b2_seeds_v1 as e
from experiments.vld import vld_moat_b2_v1 as b

R = dict[str, Any]
SEEDS = [42, 123, 7, 2024, 99]
COPS = ("soc", "dataops", "trading", "purchasing", "s2p")
NEW = COPS[2:]
TIER = "REAL_COMPONENT geometry + SIMULATED streams and verification"
RULE = "judgment-specific iff routing_quality gap widens by >2pp in >=3/5 seeds"
OUT = ROOT / "experiments/vld/results/c2_mu_learning_all_five.json"


def extended_streams(root_seed: int) -> R:
    export = b.h.load_export()
    sa: R = {}
    for cop in NEW:
        seed = root_seed + COPS.index(cop)*10000
        sa[cop] = b.split_pool(b.generate(cop, export[cop], 3000, seed,
                                        f"Firm-A/{cop}"), seed+500000)
    frozen = {cop: sa[cop]["test"].fingerprint for cop in NEW}
    result: R = {}
    for cop in NEW:
        info = export[cop]
        dim = len(info["factor_names"])
        namespace = dict(vars(b))
        namespace["B_SCALE"] = np.resize(b.B_SCALE, dim).tolist()
        namespace["B_SHIFT"] = np.resize(b.B_SHIFT, dim).tolist()
        transform = types.FunctionType(b.shifted.__code__, namespace,
                                       argdefs=b.shifted.__defaults__)
        shifted, spec = transform(info)
        priors = np.resize(b.B_PRIORS["dataops"], len(info["category_names"]))
        priors = (priors / priors.sum()).tolist()
        accept = np.resize(b.B_ACCEPT["dataops"], len(info["action_names"])).tolist()
        seed = root_seed + COPS.index(cop)*10000
        cases = b.generate(cop, shifted, 2400, seed+100000,
                           f"Firm-B/{cop}", priors, accept)
        train, dev = b.Cohort(cases[:2000]), b.Cohort(cases[2000:])
        spec.update({"category_probabilities": dict(zip(info["category_names"], priors)),
                     "action_acceptance_weights": dict(zip(info["action_names"], accept)),
                     "same_domain_learner_geometry": "original export, NOT mu_B",
                     "dimensional_extension": "cyclic factor vectors; resized DataOps priors/acceptance"})
        assert b.digest([b.serial(c) for c in sa[cop]["test"].cases]) == frozen[cop]
        result[cop] = {"info": info, "seed": seed, "sa": sa[cop],
                      "sb_train": train, "sb_dev": dev, "spec": spec,
                      "audit": {"tier": TIER, "frozen_before_SB_generation": True,
                                "heldout_sha256": frozen[cop],
                                "split_indices": sa[cop]["split_indices"],
                                "SA_training_sha256": sa[cop]["train"].fingerprint,
                                "SB_training_sha256": train.fingerprint,
                                "realized_distribution_distance":
                                    b.distribution_distance(sa[cop]["train"], train, info)}}
    return result


def pair(cop: str, s: R, seed: int, factory: Callable[..., Any],
         runner: Callable[..., Any]) -> R:
    pool = s["sa"]
    learners = [factory(cop, s["info"]), factory(cop, s["info"])]
    cache: R = {}
    try:
        a1 = runner("S_A", learners[0], pool["train"], pool["dev"],
                    pool["test"], cache, TIER, seed=s["seed"])
        a2 = runner("S_B", learners[1], s["sb_train"], s["sb_dev"],
                    pool["test"], cache, TIER, seed=s["seed"])
        ref = b.mean_level(a1["checkpoints_on_SA_heldout"])
        a2.update(b.parity_summary(a2["checkpoints_on_SA_heldout"], ref, a1["converged"]))
        horizon = e.at_horizon(a2, a1["processed_decisions"])
        assert a2["SA_verified_labels_received"] == 0
        assert a1["primary_evaluation_sha256"] == a2["primary_evaluation_sha256"] == pool["test"].fingerprint
        return {"tier": TIER, "seed": seed, "arm1": a1, "arm2": a2,
                "arm1_converged": a1["converged"], "arm1_convergence": a1["convergence_point"],
                "arm2_residual_routing_at_arm1_horizon": ref["routing_quality"]-horizon["routing_quality"],
                "arm2_residual_action_at_arm1_horizon": ref["action_accuracy"]-horizon["action_accuracy"],
                "arm2_sustained_parity": isinstance(a2["decisions_to_sustained_parity"], int),
                "stream_audit": s["audit"], "S_B_perturbation_spec": s["spec"]}
    finally:
        for learner in learners:
            learner.close()


def combine(mu: R, k: R, source: str) -> R:
    assert mu["stream_audit"] == k["stream_audit"]
    assert mu["S_B_perturbation_spec"] == k["S_B_perturbation_spec"]
    mr, ma = (float(mu[f"arm2_residual_{x}_at_arm1_horizon"]) for x in ("routing", "action"))
    kr, ka = (float(k[f"arm2_residual_{x}_at_arm1_horizon"]) for x in ("routing", "action"))
    aligned = m.horizon_gap(mu, k["arm1"]["processed_decisions"])
    eligible = bool(mu["arm1_converged"] and k["arm1_converged"])
    return {"tier": TIER, "gap_units": "percentage_points",
            "mu_k_routing_gap": 100*mr, "mu_k_action_gap": 100*ma,
            "k_only_routing_gap": 100*kr, "k_only_action_gap": 100*ka,
            "k_only_source": source, "gap_widening_routing": 100*(mr-kr),
            "gap_widening_action": 100*(ma-ka),
            "incumbent_mu_drift_l2": mu["arm1"]["checkpoints_on_SA_heldout"][-1]["mu_drift_l2"],
            "competitor_mu_drift_l2": mu["arm2"]["checkpoints_on_SA_heldout"][-1]["mu_drift_l2"],
            "eligible_converged_reference": eligible,
            "widens_gt_2pp": eligible and mr-kr > .02,
            "common_K_incumbent_horizon": aligned,
            "common_horizon_widening_routing_pp": 100*(aligned["routing"]-kr),
            "mu_k": mu, "k_only": k}


def pp_stats(values: list[float]) -> R:
    return cast(R, e.stats([v/100 for v in values]))


def summarize(result: R) -> None:
    for cop in COPS:
        rows = list(result[cop]["per_seed"].values())
        widened = sum(r["widens_gt_2pp"] for r in rows)
        agg: R = {"tier": TIER, "gap_units": "percentage_points",
                  "seeds_widened_gt_2pp": widened,
                  "verdict": "judgment-specific" if widened >= 3 else "routing-only",
                  "unconverged_references": sum(not r["eligible_converged_reference"] for r in rows)}
        for field, prefix in (("gap_widening_routing", "widening"),
                              ("k_only_routing_gap", "k_only_gap"),
                              ("mu_k_routing_gap", "mu_k_gap"),
                              ("gap_widening_action", "action_widening"),
                              ("common_horizon_widening_routing_pp", "common_horizon_widening")):
            stats = pp_stats([r[field] for r in rows])
            for key in ("mean", "std", "min", "max", "ci95"):
                agg[f"{prefix}_{key}"] = stats[key]
        result[cop]["aggregate"] = agg


def write_summary(result: R) -> None:
    lines = ["# C2: mu-learning moat across five domains", "",
             f"Evidence tier: {TIER}. Gap units: percentage points. Means ± sample SD over five seeds.",
             "Primary comparison: routing_quality gap at each condition's incumbent convergence horizon. "
             "action_accuracy gaps and every checkpoint are retained in the JSON.", "",
             "| Copilot | K-only routing gap | Mu+K routing gap | Widening | Seeds >2pp | Verdict |",
             "|---|---:|---:|---:|---:|---|"]
    for cop in COPS:
        a = result[cop]["aggregate"]
        lines.append(f"| {cop} | {a['k_only_gap_mean']:.2f} ± {a['k_only_gap_std']:.2f} | "
                     f"{a['mu_k_gap_mean']:.2f} ± {a['mu_k_gap_std']:.2f} | "
                     f"{a['widening_mean']:+.2f} ± {a['widening_std']:.2f} | "
                     f"{a['seeds_widened_gt_2pp']}/5 | {a['verdict']} |")
    yes = [c for c in COPS if result[c]["aggregate"]["verdict"] == "judgment-specific"]
    no = [c for c in COPS if c not in yes]
    lines += ["", f"Judgment-specific under the preregistered criterion: {', '.join(yes) or 'none'}.",
              f"Routing-only classification: {', '.join(no) or 'none'} ({len(no)}/5 domains).",
              "This classification tests incremental mu gap widening; failing it is not proof of no mu specificity, "
              "and it does not independently establish a positive K-only moat.",
              "", "## Sanity and reproducibility",
              "All SOC/DataOps seeds 42, 123, 7 reproduce EXP-2 per-seed routing/action gaps, mu drift and full "
              "held-out checkpoints. Their three-seed mean widening reproduces +15.935185pp / −2.509259pp. "
              "The prompt's seed42-versus-three-seed-mean check is invalid; seed42 is +11.666667pp / −3.333333pp.",
              "Every newly computed seed/domain has two independent stream/learner/cache rebuilds with "
              "byte-identical canonical JSON. Existing EXP1 SOC/DataOps K-only controls are reused.",
              "", "## Protocol and interpretation",
              "SOC/DataOps S_B is unchanged. For the three new domains the preregistered extension repeats "
              "the six-factor perturbation vectors cyclically and truncates/normalizes DataOps category weights "
              "to [0.0625, 0.125, 0.125, 0.125, 0.5625]; action acceptance uses the first A DataOps entries. "
              "The exact per-factor vectors, category/action names and realized distribution distances are in each row.",
              "All target tests freeze before S_B generation in each batch. The actual inherited split is "
              "2000 training / 400 development / 600 held-out; development convergence uses a 0.5pp range "
              "over three checkpoints, minimum 500 and maximum 2000. Joint parity requires routing_quality "
              "and action_accuracy within 1pp for three consecutive checkpoints. No held-out stopping.",
              "Centroid updates reuse the existing ungated ProfileScorer component. Fixed synthetic oracle labels "
              "and informative dimensions remain a limitation. This is not operational evidence or an oracle-separated study.",
              "No multi-step evidence richness variable was measured. Domain differences alone do not establish "
              "that mechanism; the results characterize these geometries and this one alternative-firm profile.",
              "", "## Common-horizon sensitivity",
              "| Copilot | Routing widening at K-only incumbent horizon (pp) |", "|---|---:|"]
    for cop in COPS:
        a = result[cop]["aggregate"]
        lines.append(f"| {cop} | {a['common_horizon_widening_mean']:+.2f} ± {a['common_horizon_widening_std']:.2f} |")
    lines += ["", "## Null stakes",
              (f"{len(no)}/5 domains are routing-only: the broad judgment-specificity claim must narrow to the "
               "measured subset. An 'evidence-rich domains' explanation remains untested."
               if len(no) >= 3 else
               f"{len(no)}/5 domains are routing-only; the preregistered three-domain narrowing trigger is not met. "
               "Do not generalize beyond the measured domains and profile."),
              "Stopping-horizon sensitivity is disclosed rather than used to change the preregistered verdict.",
              ""]
    (OUT.parent/"c2_mu_learning_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    assert not OUT.exists(), "Do not overwrite an existing campaign output"
    assert (b.TOL, b.WINDOW, b.PARITY, b.MAX_N) == (.005, 3, .01, 2000)
    before = e.source_hashes()
    k = json.loads((OUT.parent/"moat_b2_seeds.json").read_text(encoding="utf-8"))
    old = json.loads((OUT.parent/"moat_mu_learning.json").read_text(encoding="utf-8"))
    runner, audit = m.adapted_runner()
    result: R = {c: {"per_seed": {}} for c in COPS}
    checks: R = {}
    sanity: R = {}
    for seed in SEEDS:
        print(f"C2 existing domains seed={seed} rebuild 1/2", flush=True)
        first = e.run_seed(seed, m.MuLearner, runner)
        print(f"C2 existing domains seed={seed} rebuild 2/2", flush=True)
        second = e.run_seed(seed, m.MuLearner, runner)
        assert b.canonical(first) == b.canonical(second)
        checks[f"existing/{seed}"] = {"passed": True, "rebuilds": 2, "sha256": b.digest(first)}
        for cop in COPS[:2]:
            row = combine(first[cop], k[cop]["per_seed"][str(seed)], "exp1")
            if seed in m.SEEDS:
                ref = old[cop]["per_seed"][str(seed)]
                for field in ("mu_k_routing_gap", "mu_k_action_gap", "k_only_routing_gap",
                              "k_only_action_gap", "gap_widening_routing", "gap_widening_action"):
                    assert abs(row[field]-100*ref[field]) < 1e-10, (cop, seed, field)
                for field in ("incumbent_mu_drift_l2", "competitor_mu_drift_l2"):
                    assert abs(row[field]-ref[field]) < 1e-12
                for arm in ("arm1", "arm2"):
                    assert b.canonical(first[cop][arm]["checkpoints_on_SA_heldout"]) == b.canonical(ref[arm]["checkpoints_on_SA_heldout"])
            result[cop]["per_seed"][str(seed)] = row
        if seed == 7:
            for cop in COPS[:2]:
                measured = float(np.mean([result[cop]["per_seed"][str(s)]["gap_widening_routing"] for s in m.SEEDS]))
                assert abs(measured-old[cop]["aggregate"]["gap_widened_by"]) < 1e-10
                sanity[f"{cop}_matched"] = True
                sanity[f"{cop}_three_seed_widening_pp"] = measured
            print("C2 EXP2 SANITY PASS: six cells and matched three-seed means", flush=True)
    for seed in SEEDS:
        builds: list[R] = []
        for rebuild in (1, 2):
            print(f"C2 new domains seed={seed} rebuild {rebuild}/2", flush=True)
            streams = extended_streams(seed)
            batch: R = {}
            for cop in NEW:
                control = pair(cop, streams[cop], seed, b.Learner, b.run_arm)
                mu = pair(cop, streams[cop], seed, m.MuLearner, runner)
                batch[cop] = combine(mu, control, "paired_run")
            builds.append(batch)
        assert b.canonical(builds[0]) == b.canonical(builds[1])
        checks[f"new/{seed}"] = {"passed": True, "rebuilds": 2, "sha256": b.digest(builds[0])}
        for cop in NEW:
            result[cop]["per_seed"][str(seed)] = builds[0][cop]
    summarize(result)
    assert e.source_hashes() == before
    result["metadata"] = {"seeds": SEEDS, "tier": TIER, "pre_registered_rule": RULE,
        "mu_update_path": "gae/profile_scorer.py:779 ProfileScorer.update",
        "exp2_sanity_check": sanity, "determinism_per_seed": checks, "runner_adapter": audit,
        "checkpoint_metric_units": "fractions", "gap_units": "percentage_points",
        "category_accuracy": "not measured; category supplied",
        "profile_extension": __doc__, "source_sha256": before,
        "new_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "mu_probe_source_sha256": hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()}
    result["metadata"]["determinism_hash"] = b.digest(result)
    OUT.write_bytes(b.canonical(result))
    write_summary(result)
    for cop in COPS:
        print(cop, json.dumps(result[cop]["aggregate"]), flush=True)


if __name__ == "__main__":
    main()

