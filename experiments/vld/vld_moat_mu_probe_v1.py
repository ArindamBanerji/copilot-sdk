"""B2 EXP-2 -- PRE-REGISTERED BEFORE EXECUTION; seeds [42,123,7].
Judgment (mu) is firm-specific iff Arm1-Arm2 routing gap under mu+K
exceeds its paired K-only gap by >2pp in >=2/3 seeds.
Compare incumbent-convergence-horizon gaps, with paired K-only seeds.
Also disclose fixed-K-incumbent-horizon comparisons to expose stopping effects.
GATE-B: ../graph-attention-engine-v50/gae/profile_scorer.py:779
ProfileScorer.update, existing pull/push/GT-pull path. Defaults eta=.05,
eta_neg=.05, decay=.001; per-coordinate update clip .005; mu in [0,1].
No learning strategy, min_confidence=0, auto_pause_on_amber=False (defaults).
This is an UNGATED component probe; no production conservation safety claim.
After unchanged B2 K credit, update mu using final ACQUIRED evidence vector
and verified training action, never latent unread evidence or heldout labels.
On error push predicted and pull verified centroid. Publish actual L2 drift.
The label/informative oracle remains FIXED at stream creation; no relabeling.
Existing B2 Learner is subclassed only to add that mu update in credit().
Existing run_arm is compiled IN MEMORY with exactly its immutable-mu assertion
replaced by sigma-immutability / finite bounded mu checks; no loop, convergence,
evaluation, stream, parity or source-file modification. Audit adapter AST.
The evaluation cache already keys on mu, K, sigma, tau and heldout fingerprint.
B2 S_B, seed flow, 600/400/2000 split, .005 convergence, window3, max2000
remain imported unchanged. Both SA tests frozen BEFORE SB generation.
Only mu-learning differs; K-only paired results loaded from EXP-1.
Two full independent rebuilds per seed must produce identical canonical JSON.
Scope: finite simulated verified outcomes; widening is the preregistered
proxy for judgment-specificity, not proof of general proprietary-data value.
"""
from __future__ import annotations
import ast
import hashlib
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Callable, cast
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
GAE_ROOT=ROOT.parent/"graph-attention-engine-v50"
sys.path.insert(0,str(GAE_ROOT))
from gae.profile_scorer import ProfileScorer
from experiments.vld import vld_moat_b2_seeds_v1 as e
from experiments.vld import vld_moat_b2_v1 as b
R=dict[str,Any]
SEEDS=[42,123,7]
RULE="judgment-specific iff routing gap widens by >2pp in >=2/3 seeds"
OUT=ROOT/"experiments/vld/results/moat_mu_learning.json"


class MuLearner(b.Learner):
    def __post_init__(self) -> None:
        super().__post_init__()
        self.initial_mu=np.stack([self.mu[c] for c in self.categories]).copy()
        self.initial_sigma=self.sigma.copy()
        self.updater=ProfileScorer(self.initial_mu,list(self.info["action_names"]),
                                   categories=self.categories)
        self.update_outcomes: dict[str,int]={}

    def credit(self,case: R,run: R,informative: set[int] | None=None) -> None:
        super().credit(case,run,informative)
        vector=(run["step_records"][-1][2] if run["step_records"] else case["surface"]).copy()
        c=self.categories.index(case["category"])
        action=int(run["final_action"]);target=int(case["correct_action"])
        update=self.updater.update(vector,c,action,action==target,gt_action_index=target)
        key=str(update.outcome)
        self.update_outcomes[key]=self.update_outcomes.get(key,0)+1
        self.mu[case["category"]][:]=self.updater.mu[c]
        self.inv[case["category"]].mu[:]=self.updater.mu[c]
        assert np.allclose(self.mu[case["category"]],self.inv[case["category"]].mu)

    def drift(self) -> float:
        return float(np.linalg.norm(np.stack([self.mu[c] for c in self.categories])-self.initial_mu))


def mu_evaluate(learner: Any,cohort: Any,cache: R) -> R:
    result=cast(R,b.evaluate(learner,cohort,cache))
    result["mu_drift_l2"]=learner.drift()
    result["mu_sha256"]=b.digest({c:m.tolist() for c,m in learner.mu.items()})
    result["geometry_tier"]="REAL_COMPONENT initialization + SIMULATED adaptation"
    return result


def adapted_runner() -> tuple[Callable[...,Any],R]:
    source=inspect.getsource(b.run_arm)
    tree=ast.parse(source)
    function=tree.body[0]
    assert isinstance(function,ast.FunctionDef)
    expected=ast.parse('assert digest({"mu":learner.state()["mu"],"sigma":learner.state()["sigma"]})==initial_geometry').body[0]
    matched=[i for i,node in enumerate(function.body)
             if ast.dump(node,include_attributes=False)==ast.dump(expected,include_attributes=False)]
    assert len(matched)==1,"B2 runner changed: review immutable-mu adapter before running"
    replacement=ast.parse('assert np.array_equal(learner.sigma,learner.initial_sigma) and all(np.all(np.isfinite(m)) and np.all((m>=0)&(m<=1)) for m in learner.mu.values())').body[0]
    function.body[matched[0]]=replacement
    ast.fix_missing_locations(tree)
    namespace=dict(vars(b));namespace["evaluate"]=mu_evaluate
    exec(compile(tree,"<B2 mu-flag adapter: immutable-geometry guard only>","exec"),namespace)
    audit={"tier":e.TIER,"source_function_sha256":hashlib.sha256(source.encode()).hexdigest(),
           "replaced_assertions":1,"changed_loop_or_convergence":False,
           "adapter":"immutable-mu assert -> immutable-sigma, finite bounded mu; evaluate adds drift metadata"}
    return cast(Callable[...,Any],namespace["run_arm"]),audit


def horizon_gap(row: R,n: int) -> R:
    points=[p for p in row["arm1"]["checkpoints_on_SA_heldout"] if p["decision_count"]<=n]
    reference=b.mean_level(points)
    entrant=e.at_horizon(row["arm2"],n)
    return {"routing":reference["routing_quality"]-entrant["routing_quality"],
            "action":reference["action_accuracy"]-entrant["action_accuracy"],
            "requested_N":n,"incumbent_effective_N":points[-1]["decision_count"],
            "competitor_effective_N":entrant["effective_training_decisions"],"tier":e.TIER}


def main() -> None:
    kpath=ROOT/"experiments/vld/results/moat_b2_seeds.json"
    runner,audit=adapted_runner()
    paths=[Path(__file__).resolve(),GAE_ROOT/"gae/profile_scorer.py",GAE_ROOT/"gae/kernels.py"]
    hashes={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else "../graph-attention-engine-v50/"+p.relative_to(GAE_ROOT).as_posix():
            hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    base_hashes=e.source_hashes()
    result: R={"status":"measured","mu_update_path":"../graph-attention-engine-v50/gae/profile_scorer.py:779 ProfileScorer.update",
              "soc":{"per_seed":{}},"dataops":{"per_seed":{}}}
    checks: R={}
    measurements: R={}
    for seed in SEEDS:
        print(f"MU SEED {seed}: independent computation 1/2",flush=True)
        first=e.run_seed(seed,MuLearner,runner)
        print(f"MU SEED {seed}: independent computation 2/2",flush=True)
        second=e.run_seed(seed,MuLearner,runner)
        assert b.canonical(first)==b.canonical(second),f"mu seed {seed} determinism mismatch"
        checks[str(seed)]={"passed":True,"independent_full_computations":2,"sha256":b.digest(first)}
        measurements[str(seed)]=first
    k=json.loads(kpath.read_text(encoding="utf-8"))
    hashes[kpath.relative_to(ROOT).as_posix()]=hashlib.sha256(kpath.read_bytes()).hexdigest()
    for seed in SEEDS:
        first=measurements[str(seed)]
        for cop in ("soc","dataops"):
            row=first[cop];control=k[cop]["per_seed"][str(seed)]
            assert row["stream_audit"]==control["stream_audit"]
            assert row["S_B_perturbation_spec"]==control["S_B_perturbation_spec"]
            aligned=horizon_gap(row,control["arm1"]["processed_decisions"])
            mr=row["arm2_residual_routing_at_arm1_horizon"]
            ma=row["arm2_residual_action_at_arm1_horizon"]
            kr=control["arm2_residual_routing_at_arm1_horizon"]
            ka=control["arm2_residual_action_at_arm1_horizon"]
            eligible=row["arm1_converged"] and control["arm1_converged"]
            row.update({"mu_k_routing_gap":mr,"mu_k_action_gap":ma,
                "k_only_routing_gap":kr,"k_only_action_gap":ka,
                "gap_widening_routing":mr-kr,"gap_widening_action":ma-ka,
                "incumbent_mu_drift_l2":row["arm1"]["checkpoints_on_SA_heldout"][-1]["mu_drift_l2"],
                "competitor_mu_drift_l2":row["arm2"]["checkpoints_on_SA_heldout"][-1]["mu_drift_l2"],
                "mu_k_at_K_only_incumbent_horizon":aligned,
                "aligned_routing_gap_widening":aligned["routing"]-kr,
                "eligible_converged_reference":eligible,"widens_by_more_than_2pp":eligible and mr-kr>.02})
            row["arm2"]["scope"]="mu+K component probe; no operational safety claim"
            result[cop]["per_seed"][str(seed)]=row
    for cop in ("soc","dataops"):
        rows=list(result[cop]["per_seed"].values())
        widened=sum(r["widens_by_more_than_2pp"] for r in rows)
        summary: R={"tier":e.TIER,"units":"percentage_points","seeds_widened":widened,
            "verdict":"judgment-specific" if widened>=2 else "routing-only",
            "interpretation":"preregistered widening criterion; failure does not prove mu has no firm specificity",
            "mu_k_gap_mean":100*float(np.mean([r["mu_k_routing_gap"] for r in rows])),
            "k_only_gap_mean":100*float(np.mean([r["k_only_routing_gap"] for r in rows])),
            "gap_widened_by":100*float(np.mean([r["gap_widening_routing"] for r in rows])),
            "action_gap_widened_by":100*float(np.mean([r["gap_widening_action"] for r in rows])),
            "aligned_gap_widened_by":100*float(np.mean([r["aligned_routing_gap_widening"] for r in rows])),
            "routing_gap_widening_stats":e.stats([r["gap_widening_routing"] for r in rows],4.302652729696142)}
        result[cop]["aggregate"]=summary
    assert e.source_hashes()==base_hashes
    result["metadata"]={"seeds":SEEDS,"pre_registered_rule":RULE,"tier":e.TIER,
        "scope":"mu+K learning; tests widening beyond routing-level K specificity",
        "determinism_per_seed":checks,"source_sha256":hashes,"B2_source_sha256":base_hashes,"runner_adapter":audit,
        "mu_parameters":{"eta":.05,"eta_neg":.05,"count_decay":.001,"per_coordinate_delta_clip":.005,
                         "mu_bounds":[0,1],"min_confidence":0,"auto_pause_on_amber":False},
        "comparison":"own-incumbent convergence horizons, paired seeds; additional common K-incumbent horizon",
        "mu_training_input":"acquired B2 final vector + verified label; no unread latent evidence",
        "limitations":["ungated component experiment, not SDK production learning lifecycle",
                       "fixed oracle labels and informative dimensions from original stream generation",
                       "three seeds, one simulated alternative-firm profile; no universal asset claim",
                       "different convergence horizons disclosed with common-horizon sensitivity"],
        "gate_outcome":"GATE-B"}
    result["metadata"]["determinism_hash"]=b.digest(result)
    OUT.write_bytes(b.canonical(result))
    for cop in ("soc","dataops"):print(cop,json.dumps(result[cop]["aggregate"]),flush=True)


if __name__=="__main__":
    main()
