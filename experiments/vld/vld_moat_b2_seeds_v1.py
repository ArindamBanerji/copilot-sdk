"""B2 follow-up EXP-1 -- PRE-REGISTERED BEFORE EXECUTION.
Moat claim holds iff Arm 2 fails sustained parity in >= 4/5 seeds.
Seeds [42,123,7,2024,99]; only Arm1/Arm2, SOC/DataOps.
Import B2 generation, split, learner, run_arm, convergence and parity unchanged.
Authoritative IMPLEMENTED settings: 3000 SA, test600/dev400/train2000;
TOL=.005, window3, min500/max2000, checkpoint50, parity .01 on BOTH metrics.
The prompt's 20/10/70 split and 1pp convergence descriptions differ from B2;
preserve the code, not those descriptions. Freeze BOTH tests before ANY SB.
Seed flows: SA=root+domain_index*10000; split=SA+500000; SB=SA+100000.
K initialization is deterministic uniform .5, not randomized. Scenario order
is the original seeded generation/split order. No global RNG or retuning.
Primary headline: incumbent converged final-three mean minus Arm2 state at
incumbent convergence N. If Arm2 already stopped, hold its converged state;
do not continue learning or invent intermediate states. Log effective N.
B2-compatible endpoint fields retained separately for seed42 exact comparison.
Parity remains over the full original Arm2 trajectory, not just matched horizon.
Every aggregate gap is in percentage points; per-seed gaps are fractions.
Sample SD (ddof=1), two-sided Student-t 95% CI (df=4) over five seeds.
Two independent full rebuilds per seed, compare canonical JSON bytes.
Finite-horizon seed robustness on ONE simulated alternative firm profile.
No inference that verified labels are unobtainable; no operational safety claim.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable
import numpy as np
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from experiments.vld import vld_moat_b2_v1 as b

R=dict[str,Any]
SEEDS=[42,123,7,2024,99]
TIER="REAL_COMPONENT geometry + SIMULATED streams and verification"
RULE="moat holds iff Arm 2 fails sustained parity in >= 4/5 seeds"
OUT=ROOT/"experiments/vld/results/moat_b2_seeds.json"


def build_streams(root_seed: int) -> R:
    export=b.h.load_export()
    sa: R={}
    for i,cop in enumerate(("soc","dataops")):
        seed=root_seed+i*10000
        sa[cop]=b.split_pool(b.generate(cop,export[cop],3000,seed,f"Firm-A/{cop}"),seed+500000)
    hashes={c:sa[c]["test"].fingerprint for c in sa}
    result: R={}
    for i,cop in enumerate(("soc","dataops")):
        seed=root_seed+i*10000
        info=export[cop]
        shifted,spec=b.shifted(info)
        spec.update({"category_probabilities":dict(zip(info["category_names"],b.B_PRIORS[cop])),
                     "action_acceptance_weights":dict(zip(info["action_names"],b.B_ACCEPT[cop])),
                     "same_domain_learner_geometry":"original export, NOT mu_B"})
        sb=b.generate(cop,shifted,2400,seed+100000,f"Firm-B/{cop}",b.B_PRIORS[cop],b.B_ACCEPT[cop])
        train=b.Cohort(sb[:2000]);dev=b.Cohort(sb[2000:])
        assert b.digest([b.serial(c) for c in sa[cop]["test"].cases])==hashes[cop]
        result[cop]={"info":info,"seed":seed,"sa":sa[cop],"sb_train":train,"sb_dev":dev,
                     "spec":spec,"audit":{"tier":TIER,"frozen_before_SB_generation":True,
                         "heldout_sha256":hashes[cop],"split_indices":sa[cop]["split_indices"],
                         "SA_training_sha256":sa[cop]["train"].fingerprint,
                         "SB_training_sha256":train.fingerprint,
                         "realized_distribution_distance":b.distribution_distance(sa[cop]["train"],train,info)}}
    return result


def at_horizon(arm: R,n: int) -> R:
    points=arm["checkpoints_on_SA_heldout"]
    selected=[p for p in points if p["decision_count"]<=n][-1]
    assert selected["decision_count"]==n or arm["processed_decisions"]<n
    return {"requested_decisions":n,"effective_training_decisions":selected["decision_count"],
            "state_held_after_convergence":selected["decision_count"]<n,
            "routing_quality":selected["routing_quality"],"action_accuracy":selected["action_accuracy"],
            "tier":TIER}


def run_seed(seed: int, learner_factory: Callable[...,Any]=b.Learner,
             runner: Callable[...,Any]=b.run_arm) -> R:
    streams=build_streams(seed)
    result: R={}
    cache: R={}
    for cop in ("soc","dataops"):
        s=streams[cop];pool=s["sa"]
        learners=[learner_factory(cop,s["info"]),learner_factory(cop,s["info"])]
        try:
            a1=runner("S_A",learners[0],pool["train"],pool["dev"],pool["test"],cache,
                      "REAL_COMPONENT",seed=s["seed"])
            a2=runner("S_B",learners[1],s["sb_train"],s["sb_dev"],pool["test"],cache,
                      "SIMULATED",seed=s["seed"])
            ref=b.mean_level(a1["checkpoints_on_SA_heldout"])
            b.attach_parity(a2,ref,a1["converged"],cop)
            horizon=at_horizon(a2,a1["processed_decisions"])
            assert a2["SA_verified_labels_received"]==0
            assert a1["primary_evaluation_sha256"]==a2["primary_evaluation_sha256"]==pool["test"].fingerprint
            result[cop]={"tier":TIER,"seed":seed,"arm1_final_routing":a1["final_routing"],
                "arm1_final_action":a1["final_action"],"arm1_converged_reference":ref,
                "arm1_convergence":a1["convergence_point"],"arm1_converged":a1["converged"],
                "arm2_residual_routing":a2["residual_gap_routing"],
                "arm2_residual_action":a2["residual_gap_action"],
                "arm2_residual_routing_at_arm1_horizon":ref["routing_quality"]-horizon["routing_quality"],
                "arm2_residual_action_at_arm1_horizon":ref["action_accuracy"]-horizon["action_accuracy"],
                "arm2_at_arm1_horizon":horizon,
                "arm2_sustained_parity":isinstance(a2["decisions_to_sustained_parity"],int),
                "arm2_parity_status":a2["decisions_to_sustained_parity"],
                "arm1":a1,"arm2":a2,"stream_audit":s["audit"],"S_B_perturbation_spec":s["spec"]}
        finally:
            for learner in learners: learner.close()
    return result


def stats(values: list[float], t_critical: float=2.7764451051977987) -> R:
    a=np.asarray(values,dtype=float)*100
    mean=float(a.mean());sd=float(a.std(ddof=1))
    half=t_critical*sd/float(np.sqrt(len(a)))
    return {"mean":mean,"std":sd,"min":float(a.min()),"max":float(a.max()),
            "ci95":[mean-half,mean+half],"n":len(a),"units":"percentage_points","tier":TIER}


def aggregate(rows: R) -> R:
    result: R={"tier":TIER,"units":"percentage_points","comparison":"incumbent convergence horizon"}
    for metric in ("routing","action"):
        summary=stats([r[f"arm2_residual_{metric}_at_arm1_horizon"] for r in rows.values()])
        for key in ("mean","std","min","max","ci95"):
            result[f"{metric}_gap_{key}"]=summary[key]
        result[f"endpoint_{metric}_gap"]=stats([r[f"arm2_residual_{metric}"] for r in rows.values()])
    reached=sum(r["arm2_sustained_parity"] for r in rows.values())
    failed=sum(r["arm1_converged"] and not r["arm2_sustained_parity"] for r in rows.values())
    result.update({"seeds_reaching_parity":reached,"seeds_failing_parity":failed,
                   "verdict":f"moat holds: {failed}/5 seeds fail parity" if failed>=4 else
                   f"moat rule not met: {failed}/5 seeds fail parity",
                   "ci_method":"two-sided Student-t, df=4; sample SD; five root seeds",
                   "scope":"routing-level specificity; one S_B profile; finite development-convergence horizons"})
    return result


def source_hashes() -> R:
    paths=[ROOT/"experiments/vld/vld_moat_b2_v1.py",
           ROOT/"scripts/k_learning_curve_cross_copilot.py",ROOT/"real_centroids_v1.json",
           ROOT/"copilot_sdk/scoring/scorer.py",ROOT/"copilot_sdk/scoring/investigation.py",
           ROOT/"copilot_sdk/backend/investigation_router.py",Path(__file__).resolve()]
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main() -> None:
    assert (b.TOL,b.WINDOW,b.PARITY,b.MAX_N)==(.005,3,.01,2000)
    hashes=source_hashes()
    result: R={"soc":{"per_seed":{}},"dataops":{"per_seed":{}}}
    checks: R={}
    baseline=json.loads((ROOT/"experiments/vld/results/vld_moat_b2_v1.json").read_text(encoding="utf-8"))
    for seed in SEEDS:
        print(f"SEED {seed}: independent computation 1/2",flush=True)
        first=run_seed(seed)
        print(f"SEED {seed}: independent computation 2/2",flush=True)
        second=run_seed(seed)
        assert b.canonical(first)==b.canonical(second),f"seed {seed} determinism mismatch"
        checks[str(seed)]={"passed":True,"independent_full_computations":2,"sha256":b.digest(first)}
        for cop in ("soc","dataops"):
            row=first[cop]
            if seed==42:
                for key,old in (("arm2_residual_routing","residual_gap_routing"),
                                ("arm2_residual_action","residual_gap_action")):
                    assert abs(row[key]-baseline[cop]["arm2_independent"][old])<1e-12
                row["seed42_matches_B2_exactly"]=True
            result[cop]["per_seed"][str(seed)]=row
    for cop in ("soc","dataops"):
        result[cop]["aggregate"]=aggregate(result[cop]["per_seed"])
    result["metadata"]={"seeds":SEEDS,"pre_registered_rule":RULE,"tier":TIER,
        "b2_reference_seed":42,"source_sha256":hashes,"determinism_per_seed":checks,
        "S_B_perturbation_spec":{c:result[c]["per_seed"]["42"]["S_B_perturbation_spec"] for c in ("soc","dataops")},
        "scope":"K-learning only; mu fixed; routing-level specificity",
        "actual_split":{"test":600,"development":400,"train":2000,"heldout_fraction":.2},
        "convergence_tolerance":b.TOL,"stability_window":b.WINDOW,"parity_threshold":b.PARITY,
        "seed_flow":{"SA":"root+domain_index*10000","split":"SA+500000","SB":"SA+100000",
                     "K_initialization":"uniform .5; no randomness","ordering":"B2 seeded generation/split order"},
        "headline_fields":"*_at_arm1_horizon; endpoint fields retained for exact B2 reproduction",
        "horizon_policy":"freeze entrant state after its own development convergence if earlier than incumbent",
        "limitations":["five seeds, one alternative-firm profile","simulated oracle-coupled evidence and verification",
                       "no claim that labels are unobtainable","convergence is finite operational stability"]}
    assert source_hashes()==hashes
    result["metadata"]["determinism_hash"]=b.digest(result)
    OUT.write_bytes(b.canonical(result))
    for cop in ("soc","dataops"): print(cop,json.dumps(result[cop]["aggregate"]),flush=True)


if __name__=="__main__":
    main()

