"""C1 + C6 -- PRE-REGISTERED BEFORE EXECUTION, root seeds [42,123,7].
C1 rule: oracle-separated values moving >3pp from prior values indicate
label dependence; collapse requires paper re-tiering. HARD GATE FAILED:
GroundTruthOracle exists but no five-domain VLD adapters / harness label hook.
DO NOT build wiring. All runs are existing-tier REAL_COMPONENT + SIMULATED.
Oracle comparisons are null, NOT zero: label dependence is NOT TESTED.
Prior labels are geometry-derived synthetic, not LLM labels. Changes between
new seeds and historical cohorts are diagnostics, never oracle evidence.
K-curve: unchanged KE1 generator, B2, K credit, 500 training, 10 checkpoints,
50 paired evaluation cases/checkpoint. SEED=root (same domain-char offset);
evaluation root+100000+checkpoint; no scorer construction side-effect check.
Budget: existing FrontierInvestigator / episode / reward / run_arm; VLD,
B in [1,2,3,5], 500 train/200 evaluation, per-budget K, all coordinates readable.
Domain RNG offset and split namespaces unchanged from budget harness.
Prior B5 absent is reported missing, never substituted with exhaustive.
Risk: import heldout run_seed unchanged; 500 train/500 selection/500 test,
B2 final_d_min. Per-domain root+10000*index -> numpy draws three split seeds.
Thresholds fixed before evaluation generation. Full coverage grid unchanged.
C6 rule: risk-coverage is domain-specific if Trading/S2P show non-monotonic
curves or final_d_min ranking failure. Non-monotonic=ANY action_accuracy drop
>1e-12 as target coverage decreases (all original grid points, no smoothing).
Report also requested90/75/50 subset monotonicity and positive75 lift per seed.
No claim of calibrated probabilities or deployment guarantee.
Two independent full rebuilds compare canonical JSON bytes per domain/seed.
No source/global mutation, no git, only new script/result files.
category_accuracy not measured (category supplied); routing_quality and
action_accuracy retained with names; inherited legacy fields explicitly mapped.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import random
import sys
import types
from typing import Any, cast
import numpy as np

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from scripts import k_learning_curve_cross_copilot as k
from scripts import budget_accuracy_frontier as f
from scripts import gap2_abstention_heldout_v1 as r

R=dict[str,Any]
COPS=("dataops","purchasing","soc","trading","s2p")
SEEDS=[42,123,7]
BUDGETS=[1,2,3,5]
TIER="REAL_COMPONENT geometry + SIMULATED decisions/evidence/verification"
OUT=ROOT/"experiments/vld/results"
TARGETS=(.9,.75,.5)
SOURCES=("scripts/k_learning_curve_cross_copilot.py","scripts/k_learning_curve_experiment.py",
         "scripts/budget_accuracy_frontier.py","scripts/gap2_abstention_heldout_v1.py",
         "scripts/gap2_abstention_curve.py","scripts/routing_variant_bandit.py",
         "copilot_sdk/scoring/scorer.py","copilot_sdk/scoring/investigation.py",
         "copilot_sdk/backend/investigation_router.py","examples/jm_reference/oracle.py",
         "examples/build_your_own/oracle.py","real_centroids_v1.json",
         "experiments/vld/k_learning_curve_cross_copilot_summary.json",
         "experiments/vld/budget_accuracy_frontier.json",
         "experiments/vld/results/gap2_abstention_heldout_v1.json")


def canonical(x: Any) -> bytes:
    return (json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode()


def digest(x: Any) -> str:
    return hashlib.sha256(canonical(x)).hexdigest()


def hashes() -> R:
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
            for p in (*SOURCES,"experiments/vld/c1_c6_campaign_v1.py")}


def k_curve(cop: str,info: R,seed: int) -> R:
    cats=list(info["category_names"]);factors=list(info["factor_names"])
    sigma=np.array(info["sigma"])
    mu={c:np.array(info["all_category_mu"][c]) for c in cats}
    invs={c:k.VLDInvestigator(mu[c],sigma,factors,tau=info["tau"]) for c in cats}
    lm=k.KUtilityStore(k.SQLiteDecisionStore(),len(factors))
    fixed=k.KUtilityStore(k.SQLiteDecisionStore(),len(factors))
    # Reuse EXACT evaluator code, with a private globals dictionary for seed.
    namespace=dict(k.evaluate.__globals__);namespace["SEED"]=seed
    evaluate=types.FunctionType(k.evaluate.__code__,namespace)
    rng=random.Random(seed+sum(ord(ch) for ch in cop))
    checkpoints=[]
    try:
        for n in range(1,501):
            c=rng.choice(cats);inv=invs[c]
            case=k.make_case(rng,c,mu[c],inv)
            run=k.run_investigation(case,inv,lm.get_weights(c))
            k.reward_learning_store(lm,c,factors,k.DIMENSION_SOURCES[cop],inv,run,set(case["informative"]))
            if n%50==0:
                p=evaluate(n,cats,mu,sigma,factors,info["tau"],lm,fixed)
                for arm in ("learning_arm","control_arm"):
                    p[arm]["action_accuracy"]=p[arm].pop("accuracy")
                    p[arm]["tier"]=TIER
                p["routing_quality_delta"]=p["learning_arm"]["routing_quality"]-p["control_arm"]["routing_quality"]
                p["action_accuracy_delta"]=p["learning_arm"]["action_accuracy"]-p["control_arm"]["action_accuracy"]
                p["tier"]=TIER;checkpoints.append(p)
        return {"seed":seed,"tier":TIER,"training_decisions":500,"checkpoints":checkpoints,
                "evaluation_cases_per_checkpoint":50,"category_accuracy":None}
    finally:
        lm.conn.close();fixed.conn.close()


def budget(cop: str,info: R,seed: int) -> R:
    invs=f.investigators(info)
    domain_seed=seed+100000*(f.COPILOTS.index(cop)+1)
    train=f.cases_for(info,invs,domain_seed,500,1000000)
    test=f.cases_for(info,invs,domain_seed,200,9000000)
    train_sigs={digest(f.serialize_case(c)) for c in train}
    test_sigs={digest(f.serialize_case(c)) for c in test}
    assert not train_sigs&test_sigs
    runs={}
    for B in BUDGETS:
        run=f.run_arm(info,invs,train,test,"vld",B,seed)
        run["metrics"]["action_accuracy"]=run["metrics"].pop("accuracy")
        run["training_metrics"]["action_accuracy"]=run["training_metrics"].pop("accuracy")
        run.update({"tier":TIER,"budget":B,"policy":"vld","category_accuracy":None})
        for row in run["evaluation_rows"]: row["tier"]=TIER
        for p in run["training_checkpoints"]:p["tier"]=TIER
        runs[str(B)]=run
    return {"seed":seed,"tier":TIER,"runs":runs,"training_sha256":digest(sorted(train_sigs)),
            "evaluation_sha256":digest(sorted(test_sigs))}


def monotonic(curve: list[R]) -> bool:
    return all(b["action_accuracy"]>=a["action_accuracy"]-1e-12 for a,b in zip(curve,curve[1:]))


def risk(cop: str,info: R,seed: int) -> R:
    split=[int(x) for x in np.random.default_rng(seed+10000*COPS.index(cop)).integers(0,2**32-1,size=3)]
    run=r.run_seed(r.load_module(),info,split)
    curve=[]
    for p in run["curve"]:
        curve.append({**p,"actual_coverage":p["coverage"],"baseline":p["baseline_action_accuracy"],
                      "lift":p["action_accuracy_lift"],
                      "metric":"action_accuracy conditional on accepted subset"})
    return {"copilot":cop,"seed":seed,"tier":TIER,"coverage_curve":curve,
            "monotonic":monotonic(curve),
            "monotonic_requested_90_75_50":monotonic([p for p in curve if p["target_coverage"] in TARGETS]),
            "positive_lift_at_75":next(p["lift"] for p in curve if p["target_coverage"]==.75)>0,
            "raw_run":run}


def run_cell(cop: str,info: R,seed: int) -> R:
    return {"k_curve":k_curve(cop,info,seed),"budget_frontier":budget(cop,info,seed),
            "risk_coverage":risk(cop,info,seed)}


def mean_sd(vals: list[float]) -> R:
    a=np.array(vals,dtype=float)
    return {"mean":float(a.mean()),"sd":float(a.std(ddof=1)),"tier":TIER}


def risk_aggregate(runs: list[R]) -> R:
    curve=[]
    for i,target in enumerate(r.COVERAGES):
        rows=[run["coverage_curve"][i] for run in runs]
        point: R={"target_coverage":target,"tier":TIER}
        for key in ("action_accuracy","actual_coverage","baseline","lift"):
            summary=mean_sd([p[key] for p in rows])
            point[key]=summary["mean"];point[key+"_sd"]=summary["sd"]
        point["n_accepted"]=sum(p["n_accepted"] for p in rows)
        point["n_evaluated"]=sum(p["n_evaluated"] for p in rows)
        curve.append(point)
    return {"tier":TIER,"coverage_curve":curve,"monotonic":monotonic(curve),
            "monotonic_seeds":sum(run["monotonic"] for run in runs),
            "monotonic_requested_seeds":sum(run["monotonic_requested_90_75_50"] for run in runs),
            "at_target_75":next(p for p in curve if p["target_coverage"]==.75)}


def comparison(cop: str,exp: str,metric: str,vals: list[float],prior: float | None,
               detail: str="") -> R:
    summary=mean_sd(vals);delta=None if prior is None else 100*(summary["mean"]-prior)
    return {"copilot":cop,"experiment":exp,"metric":metric,"condition":detail,
        "oracle_sep_value":None,"llm_labeled_value":None,"delta_pp":None,"material":None,
        "oracle_comparison_status":"not_measured: oracle-sep pending -- harness wiring needed",
        "existing_tier_value":summary["mean"],"existing_tier_sd":summary["sd"],
        "prior_synthetic_value":prior,"existing_tier_delta_pp":delta,
        "existing_tier_movement_gt_3pp":None if delta is None else abs(delta)>3,
        "seeds_used":SEEDS,"tier":TIER,
        "interpretation":"seed/cohort diagnostic only; not a test of label dependence"}


def fmt(x: Any,scale: float=100) -> str:
    return "not measured" if x is None else f"{scale*float(x):.2f}"


def summaries(c1: R,c6: R) -> None:
    lines=["# C1 oracle-separation gate and existing-tier reruns","",
        "Date: September 14, 2026. Seeds: 42, 123, 7.",
        "",
        "**Oracle-separation upgrade pending: harness wiring needed.** Zero of five target domains are wired "
        "to GroundTruthOracle in the three requested harnesses. All five were rerun at existing tier; no oracle wiring was built.",
        "",
        "GroundTruthOracle exists at examples/jm_reference/oracle.py:30 (label_correct at line100). "
        "The domain-agnostic adapter examples/build_your_own/oracle.py:12 is used by email/reading examples; "
        "trading_clone re-exports the generic class. These are not exported-five-domain VLD adapters. "
        "Substantiation Trader/Chef/DataOps oracles inject treatment effects, not per-case action truth.",
        "",
        "K-curve make_case, budget scenario/cases_for, and risk make_case derive labels from the same "
        "geometry used by the scorer. They have no existing independent-oracle callback. The budget harness "
        "also asserts exhaustive predictions equal its geometry-derived label. Prior labels are synthetic, "
        "**not LLM labels**. Creating independent labels and reconciling informative-dimension/evidence semantics "
        "would require the prohibited wiring work.",
        "",
        "Oracle-separated values, oracle-minus-prior deltas and materiality are null, not zero. "
        "**Verdict: label dependence versus independence remains untested.** No claim is upgraded to ORACLE-SEP.",
        "",
        "The table below is an existing-tier seed/cohort rerun comparison. A >3pp difference here is NOT "
        "evidence of label dependence. Missing B5 historical results are not replaced with exhaustive values.",
        "",
        "| Copilot | Experiment | Metric / condition | Prior synthetic % | New existing-tier % | Difference pp | >3pp rerun movement |",
        "|---|---|---|---:|---:|---:|---|"]
    for p in c1["results"]:
        lines.append(f"| {p['copilot']} | {p['experiment']} | {p['metric']} {p['condition']} | "
                     f"{fmt(p['prior_synthetic_value'])} | {fmt(p['existing_tier_value'])} | "
                     f"{fmt(p['existing_tier_delta_pp'],1)} | {p['existing_tier_movement_gt_3pp']} |")
    lines+=["","Every row: "+TIER+".","",
        "K-curve keeps 500 decisions, 10 changing 50-case evaluation cohorts, paired learned/frozen K; "
        "budget reuses production investigation segments and fixed read quotas at B1/2/3/5, "
        "500 training/200 frozen-K evaluation; risk reuses the unchanged 500/500/500 held-out function. "
        "K-curve/risk evidence remains informative-label-filtered; budget reveals every selected coordinate. "
        "These evidence semantics are intentionally preserved, not pooled.",
        "",
        "Both routing_quality and action_accuracy are retained; category_accuracy is not measured because "
        "category is supplied. Risk baseline is B2 acting on all cases, not budget0. Target coverage is set "
        "on selection data; actual held-out coverage is measured. Three-seed SD is descriptive.",
        "",
        "Two independent full rebuilds per domain/seed matched byte-for-byte. Source/geometry hashes and "
        "raw checkpoint/decision data are in the JSON. No production source changed."]
    (OUT/"c1_oracle_sep_summary.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    lines=["# C6 held-out risk-coverage: five-domain table","",
        "Date: September 14, 2026. Metric: action_accuracy on accepted decisions; all rows "+TIER+".",
        "Trading/S2P use roots42/123/7. DataOps/Purchasing/SOC below retain the prior five-replicate "
        "three-way held-out results, as requested; new same-three-seed runs for those domains are in C1.",
        "",
        "| Copilot | Replicates | Target coverage | Actual coverage % | Accepted action_accuracy % | Baseline action_accuracy % | Lift pp | Source |",
        "|---|---:|---:|---:|---:|---:|---:|---|"]
    for p in c6["five_domain_table"]:
        lines.append(f"| {p['copilot']} | {p['replicates']} | {p['target_coverage']:.0%} | "
                     f"{fmt(p['actual_coverage'])} | {fmt(p['action_accuracy'])} | {fmt(p['baseline'])} | "
                     f"{fmt(p['lift'])} | {p['source']} |")
    lines+=["","| New copilot | Full-grid monotonic seeds | Requested90/75/50 monotonic seeds | Aggregate full-grid monotonic |",
            "|---|---:|---:|---|"]
    for cop in ("trading","s2p"):
        a=c6["copilots"][cop]["aggregate"]
        lines.append(f"| {cop} | {a['monotonic_seeds']}/3 | {a['monotonic_requested_seeds']}/3 | {a['monotonic']} |")
    lines+=["",c6["verdict"],"",
        "Monotonicity means no decrease in accepted-subset action_accuracy as target coverage decreases over "
        "the original complete grid, with numerical tolerance1e-12. No curve smoothing or evaluation-set "
        "threshold selection. Any small tail decrease is flagged descriptively, not asserted statistically significant.",
        "",
        "final_d_min is a ranking signal, not a calibrated probability. Positive75% lift does not establish "
        "universal monotonicity or zero population risk. Abstention happens after B2 reads, so this is not "
        "an evidence-read saving. Raw selection/evaluation records, split-disjointness and frozen-K checks "
        "are retained. The two rebuilds matched. Five-domain table complete at existing tier."]
    (OUT/"c6_risk_coverage_summary.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main() -> None:
    paths=[OUT/n for n in ("c1_oracle_sep_results.json","c1_oracle_sep_summary.md",
                           "c6_risk_coverage_trading_s2p.json","c6_risk_coverage_summary.md")]
    assert not any(p.exists() for p in paths),"Existing campaign output: review before overwriting"
    before=hashes();export=k.load_export()
    prior_k={x["name"]:x for x in json.loads((ROOT/SOURCES[12]).read_text())["copilots"]}
    prior_b=json.loads((ROOT/SOURCES[13]).read_text())["copilots"]
    prior_r={x["copilot"]:x for x in json.loads((ROOT/SOURCES[14]).read_text())["copilots"]}
    cells: R={};checks: R={}
    for cop in COPS:
        cells[cop]={};checks[cop]={}
        for seed in SEEDS:
            print(f"{cop} seed{seed}: rebuild1",flush=True)
            first=run_cell(cop,export[cop],seed)
            print(f"{cop} seed{seed}: rebuild2",flush=True)
            second=run_cell(cop,export[cop],seed)
            assert canonical(first)==canonical(second)
            cells[cop][str(seed)]=first
            checks[cop][str(seed)]={"passed":True,"rebuilds":2,"sha256":digest(first)}
    rows=[]
    for cop in COPS:
        runs=list(cells[cop].values())
        for metric,old in (("routing_quality","final_routing_learning"),("action_accuracy","accuracy_learning")):
            rows.append(comparison(cop,"K_curve",metric,[x["k_curve"]["checkpoints"][-1]["learning_arm"][metric] for x in runs],prior_k[cop][old],"learned N500"))
        rows.append(comparison(cop,"K_curve","routing_quality_delta",[x["k_curve"]["checkpoints"][-1]["routing_quality_delta"] for x in runs],prior_k[cop]["routing_delta"],"learned minus frozen N500"))
        for B in BUDGETS:
            budget_prior=prior_b[cop]["results"].get(str(B),{}).get("vld",{}).get("accuracy_mean")
            rows.append(comparison(cop,"budget_frontier","action_accuracy",[x["budget_frontier"]["runs"][str(B)]["metrics"]["action_accuracy"] for x in runs],budget_prior,f"B={B}"))
        for target in TARGETS:
            new=[next(p for p in x["risk_coverage"]["coverage_curve"] if p["target_coverage"]==target) for x in runs]
            risk_prior: R=next((p for p in prior_r.get(cop,{}).get("curve",[]) if p["target_coverage"]==target),{})
            for metric,oldkey in (("action_accuracy","action_accuracy"),("lift","action_accuracy_lift")):
                rows.append(comparison(cop,"risk_coverage","action_accuracy_lift" if metric=="lift" else metric,[p[metric] for p in new],risk_prior.get(oldkey),f"target={target:.0%}"))
    metadata={"seeds":SEEDS,"tier":TIER,"oracle_gate":"pending -- harness wiring needed",
              "oracle_wired_domains":[],"existing_tier_domains":list(COPS),"label_dependence_verdict":"not_tested",
              "source_sha256":before,"determinism":checks,"prior_label_source":"synthetic same-geometry nearest-centroid, not LLM",
              "metric_definitions":{"routing_quality":"informative reads / attempted reads",
                                    "action_accuracy":"predicted final action == verified action",
                                    "category_accuracy":"not measured: category supplied"},
              "risk_seed_flow":"numpy.default_rng(root+10000*domain_index) generates train/selection/test seeds",
              "domain_order":list(COPS),"pre_registered_materiality_pp":3}
    c1: R={"metadata":metadata,"results":rows,"raw_runs":cells}
    c6: R={"metadata":metadata,"copilots":{},"five_domain_table":[]}
    for cop in ("trading","s2p"):
        runs=[cells[cop][str(seed)]["risk_coverage"] for seed in SEEDS]
        c6["copilots"][cop]={"tier":TIER,"per_seed":{str(x["seed"]):x for x in runs},
                            "aggregate":risk_aggregate(runs)}
    for cop in COPS:
        for target in TARGETS:
            if cop in prior_r:
                p=next(x for x in prior_r[cop]["curve"] if x["target_coverage"]==target)
                row={"actual_coverage":p["coverage"],"action_accuracy":p["action_accuracy"],
                     "baseline":prior_r[cop]["baseline_action_accuracy"],"lift":p["action_accuracy_lift"],
                     "replicates":5,"source":"prior heldout v1"}
            else:
                p=next(x for x in c6["copilots"][cop]["aggregate"]["coverage_curve"] if x["target_coverage"]==target)
                row={key:p[key] for key in ("actual_coverage","action_accuracy","baseline","lift")}
                row.update({"replicates":3,"source":"C6 new run"})
            c6["five_domain_table"].append({"copilot":cop,"target_coverage":target,"tier":TIER,**row})
    fails=any(not run["monotonic"] or not run["positive_lift_at_75"]
              for cop in ("trading","s2p") for run in c6["copilots"][cop]["per_seed"].values())
    c6["verdict"]=("Domain-specific: at least one Trading/S2P seed has a non-monotonic full curve or no positive75% lift; "
                   "do not claim universal calibration." if fails else
                   "Trading/S2P passed the measured monotonicity and positive75% lift checks; finite synthetic evidence, not universal calibration.")
    assert hashes()==before
    # Separate metadata objects so each self-hash excludes only its own field.
    c1["metadata"]=dict(metadata);c6["metadata"]=dict(metadata)
    c1["metadata"]["determinism_hash"]=digest(c1)
    c6["metadata"]["determinism_hash"]=digest(c6)
    paths[0].write_bytes(canonical(c1));paths[2].write_bytes(canonical(c6))
    summaries(c1,c6)
    for cop in ("trading","s2p"):print(cop,json.dumps(c6["copilots"][cop]["aggregate"]),flush=True)


if __name__=="__main__":
    main()
