"""B2 v1 -- PRE-REGISTERED BEFORE EXECUTION. random_state=42.

DECISION RULE (scope: ROUTING-LEVEL SPECIFICITY ONLY):
"The moat is data-specific (strong claim) IFF Arm 2 fails to reach sustained
parity on the incumbent's held-out decisions. If Arm 2 reaches parity, the
moat is time-only and the paper weakens the claim -- with this evidence."
This rule is conditional on the incumbent meeting the declared convergence
criterion. An unconverged incumbent yields INCONCLUSIVE, not a strong claim.
Mu-specificity is UNTESTED, dependent on TIER-6/7; no centroid learning.

METRICS: routing_quality=informative_reads/attempted_reads;
action_accuracy=final_action==verified_action / cases. Both required for parity.
Category is supplied; category_accuracy is not measured.
PARITY: each metric >= mean of incumbent's final three held-out checkpoints
minus .01; outperformance qualifies. Three consecutive checkpoints required.
Report onset AND confirmation (onset+100 decisions at 50-decision resolution).
Primary decisions_to_sustained_parity is onset after confirmation. Later losses
are reported, not hidden. No finite window proves perpetual parity.

CONVERGENCE: max-min <= .005 in BOTH development-set metrics across THREE
consecutive checkpoints; minimum 500 processed decisions, maximum 2000,
checkpoint interval 50 including zero. No hard stop at 1000.
Stopping is on a disjoint development set from the arm's allowed distribution,
NOT the S_A held-out test. Test evaluations are recorded only; they never
control learning, stopping, perturbations, or thresholds. For inputs-only,
verified metrics cannot be used for stopping: require identical predicted
actions/read plans on unlabeled development inputs across three checkpoints.
Report that exception and the final held-out flatness diagnostic explicitly.
Not-reached is censored at the actual stopping N (not automatically at 2000).

S_A: unchanged KE-1 make_case, exported production mu/sigma/tau, uniform
categories. Generate 3000 cases per copilot, seeded 42+copilot index*10000.
Split by independent seeded permutation: 600 test (20%), 400 development,
2000 training. Freeze/hash BOTH S_A test sets BEFORE generating any S_B.
All arms use the exact same primary S_A test, including migration and probe.

S_B (SIMULATED second customer): categories in export order have probabilities
SOC [.05,.40,.10,.20,.15,.10], DataOps [.05,.10,.10,.10,.45,.20].
Let center_d and s_d be mean and max(population SD,.035) across ALL exported
category/action centroid rows. s is EMPIRICAL GEOMETRY SD, not unit metric sigma.
Let z=(mu-center)/s. For each category/action row:
  mu_B=clip(center+s*((1-.30)*scale*z+.30*roll(z,1)+shift), .02,.98)
  scale=[1.35,.65,1.20,.80,1.10,.90]
  shift=[+.75,-.50,+1.00,-.75,+.50,-1.00] empirical SD.
Cyclic mixing changes cross-factor structure; scales change factor-mix weights.
Generate cases with unchanged make_case on mu_B. Accept cases by verified-action
weights (relative acceptance, NOT asserted realized priors):
SOC [1,.8,.35,.15], DataOps [.2,1,.8,.6,.4], in export action order.
Entity IDs are disjoint Firm-A / Firm-B namespaces. All SAME-DOMAIN learners
start with ORIGINAL exported geometry and uniform K=.5; only K can adapt.
S_B is not a reordered S_A stream. Realized mean/SD deltas, correlations,
category priors and both KL directions are logged from equal-size train pools.

ACCESS: 3a receives category, entity ID and SURFACE only. Full=surface and
pseudo-label=own surface prediction; the unchanged credit machinery reinforces
its acquired pseudo-evidence. No full vector, verified label or informative tag
from S_A crosses the inputs-only boundary. This tests ONE self-label baseline,
not impossibility of unsupervised transfer.
3b gets exact 10%/50% labeled S_A in each randomized block of 10, rest S_B.
3c observes S_A evidence with labels delayed 50 decisions; exactly 2/5 labels
per shuffled block of 20 corrupted (10%/25%) to a different action. Pending
labels are not flushed after stopping. Credit uses only the received label and
actual acquired before/after evidence, not the clean informative tag.
KE-1's oracle-coupled synthetic evidence model remains a stated limitation.

ARM 4 DRIFT -- LOCKED PARAMETER, NEVER TUNED AFTER RESULTS:
same transform as above but rho=.10, scale=[1.10,.90,1.10,.90,1.05,.95],
shift=[+.25,-.25,+.25,-.25,+.25,-.25] empirical geometry SD;
category/action sampling stays S_A-uniform. Same random draws/split indices,
paired identifiers with drift suffix; no test examples enter training.
Copy converged incumbent K rows/update counters and deep-copy mu/sigma.
Continue one incumbent clone on drifted training to development convergence:
this is the current reference. Independently adapt a stale migrated clone.
Log primary original S_A held-out metrics for EVERY migration checkpoint AND
additional paired drifted-current S_A metrics; current reference and migrant
use the identical drifted evaluation slice. Report stale pre/post-drift dip,
stale-vs-current gap, re-parity onset/confirmation, received labels/read costs.
Zero/negative dip or zero recovery onset are legitimate outcomes. Integration
engineering is qualitative, not invented dollars or measured elapsed time.

TRANSFER-ACROSS-INCOMPATIBLE-DOMAINS PROBE, NOT ROBUSTNESS REPLICATION:
train SOC on DataOps geometry/stream and vice versa using the same learner.
At evaluation ONLY, project K by export category-index and factor-index
(6 categories x 6 factors each) into the target's native geometry. Mu/action
indices are NOT transferred (4 vs 5 actions). Export every source->target name
mapping. This arbitrary positional bridge tests no semantic equivalence and
carries NO replication weight. Expected no transfer is a hypothesis, not target.

TIERS: incumbent geometry REAL_COMPONENT with synthetic verification; S_B,
partial-access modifications and drift SIMULATED; cross-domain geometry
REAL_COMPONENT with SIMULATED positional bridge. Wall-clock conversions
ILLUSTRATIVE: SOC 1200 and DataOps 106 verified/week (MAP v20).
CONSERVATION: unchanged KE-1 K credit, no shared scorer learning gate invocation.
No production safety, live-outcome or universal proprietary-data claim.

DETERMINISM: two independent FULL computations, each rebuilding streams,
learners and caches. Canonical sorted-key JSON compared byte-for-byte.
No timestamps/runtime/temp paths. Final SHA256 excludes only its own field.
Expected qualitative hypotheses (not tuning targets): independent and unlabeled
arms fail joint parity; migration incurs some staleness/recovery cost.
B1's verdict is superseded/retracted as a moat inference; its artifacts untouched.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, cast

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from scripts import k_learning_curve_cross_copilot as h

R = dict[str, Any]
MAX_N, MIN_N, EVERY, WINDOW, TOL, PARITY = 2000, 500, 50, 3, .005, .01
OUT = ROOT / "experiments/vld/results"
METRICS = ("routing_quality", "action_accuracy")
RATES = {"soc":1200,"dataops":106}
B_PRIORS = {"soc":[.05,.40,.10,.20,.15,.10],"dataops":[.05,.10,.10,.10,.45,.20]}
B_ACCEPT = {"soc":[1.,.8,.35,.15],"dataops":[.2,1.,.8,.6,.4]}
B_SCALE = [1.35,.65,1.2,.8,1.1,.9]
B_SHIFT = [.75,-.5,1.,-.75,.5,-1.]
D_SCALE = [1.1,.9,1.1,.9,1.05,.95]
D_SHIFT = [.25,-.25,.25,-.25,.25,-.25]


def canonical(value: Any) -> bytes:
    return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def serial(case: R) -> R:
    return {"category":case["category"],"entity_id":case["entity_id"],
            "surface":case["surface"].tolist(),"full":case["full"].tolist(),
            "correct_action":int(case["correct_action"]),
            "informative":sorted(int(x) for x in case["informative"])}


@dataclass
class Cohort:
    cases: list[R]
    fingerprint: str = field(init=False)
    def __post_init__(self) -> None:
        for c in self.cases:
            c["surface"].setflags(write=False)
            c["full"].setflags(write=False)
        self.fingerprint=digest([serial(c) for c in self.cases])


@dataclass
class Learner:
    copilot: str
    info: R
    store: Any = field(init=False)
    inv: dict[str,Any] = field(init=False)
    mu: dict[str,Any] = field(init=False)
    sigma: Any = field(init=False)
    categories: list[str] = field(init=False)
    factors: list[str] = field(init=False)
    def __post_init__(self) -> None:
        self.categories=list(self.info["category_names"])
        self.factors=list(self.info["factor_names"])
        self.mu={c:np.array(self.info["all_category_mu"][c],dtype=float).copy() for c in self.categories}
        self.sigma=np.array(self.info["sigma"],dtype=float).copy()
        self.store=h.KUtilityStore(h.SQLiteDecisionStore(),len(self.factors))
        self.inv={c:h.VLDInvestigator(self.mu[c],self.sigma,self.factors,tau=self.info["tau"])
                  for c in self.categories}

    def weights(self) -> R:
        return {c:self.store.get_weights(c).tolist() for c in self.categories}

    def state(self) -> R:
        records=[list(r) for r in self.store.conn.execute(
            "SELECT category,dimension,weight,n_updates FROM k_utility ORDER BY category,dimension").fetchall()]
        return {"K":self.weights(),"K_records":records,"mu":{c:m.tolist() for c,m in self.mu.items()},
                "sigma":self.sigma.tolist(),"tau":self.info["tau"]}

    def acquire(self,case: R) -> R:
        c=case["category"]
        return cast(R,h.run_investigation(case,self.inv[c],self.store.get_weights(c),budget=2))

    def credit(self,case: R,run: R,informative: set[int] | None = None) -> None:
        c=case["category"]
        h.reward_learning_store(self.store,c,self.factors,h.DIMENSION_SOURCES[self.copilot],
                                self.inv[c],run,set(case["informative"]) if informative is None else informative)

    def close(self) -> None:
        self.store.conn.close()


def migrate(source: Learner,target: Learner) -> None:
    source.store.conn.backup(target.store.conn)
    target.mu={c:m.copy() for c,m in source.mu.items()}
    target.sigma=source.sigma.copy()
    target.inv={c:h.VLDInvestigator(target.mu[c],target.sigma,target.factors,tau=target.info["tau"])
                for c in target.categories}
    assert target.store.conn is not source.store.conn
    assert not any(np.shares_memory(target.mu[c],source.mu[c]) for c in source.categories)
    assert target.state()==source.state()


def shifted(info: R,drift: bool=False) -> tuple[R,R]:
    original=np.array([info["all_category_mu"][c] for c in info["category_names"]])
    center=original.mean(axis=(0,1))
    sd=np.maximum(original.std(axis=(0,1)),.035)
    scale=np.array(D_SCALE if drift else B_SCALE)
    shift=np.array(D_SHIFT if drift else B_SHIFT)
    rho=.1 if drift else .3
    z=(original-center)/sd
    transformed=np.clip(center+sd*((1-rho)*scale*z+rho*np.roll(z,1,axis=-1)+shift),.02,.98)
    modified=dict(info)
    modified["all_category_mu"]={c:transformed[i].tolist() for i,c in enumerate(info["category_names"])}
    return modified,{"tier":"SIMULATED","rho":rho,"scale":scale.tolist(),"shift_in_empirical_SD":shift.tolist(),
                     "empirical_geometry_SD":sd.tolist(),"center":center.tolist(),
                     "transformed_mu":modified["all_category_mu"],"clip":[.02,.98]}


def generate(cop: str,info: R,n: int,seed: int,namespace: str,
             priors: list[float] | None=None,accept: list[float] | None=None) -> list[R]:
    rng=random.Random(seed)
    factory=Learner(cop,info)
    cases: list[R]=[]
    while len(cases)<n:
        c=(rng.choice(factory.categories) if priors is None
           else rng.choices(factory.categories,weights=priors,k=1)[0])
        case=cast(R,h.make_case(rng,c,factory.mu[c],factory.inv[c]))
        if accept is not None and rng.random()>accept[int(case["correct_action"])]:
            continue
        case["entity_id"]=f"{namespace}/{len(cases):05d}"
        cases.append(case)
    factory.close()
    return cases


def split_pool(pool: list[R],seed: int) -> R:
    indices=list(range(len(pool)))
    random.Random(seed).shuffle(indices)
    test=indices[:600];dev=indices[600:1000];train=indices[1000:3000]
    parts: R={"test":Cohort([pool[i] for i in test]),"dev":Cohort([pool[i] for i in dev]),
           "train":Cohort([pool[i] for i in train]),"split_indices":{"test":test,"dev":dev,"train":train}}
    assert not set(test)&set(dev) and not set(test)&set(train) and not set(dev)&set(train)
    signatures=lambda rows:{hashlib.sha256(c["category"].encode()+c["surface"].tobytes()).hexdigest()
                            for c in rows}
    assert not signatures(parts["test"].cases)&signatures(parts["train"].cases+parts["dev"].cases)
    return parts


def evaluate(learner: Learner,cohort: Cohort,cache: R) -> R:
    key=digest({"K":learner.weights(),"mu":{c:m.tolist() for c,m in learner.mu.items()},
                "sigma":learner.sigma.tolist(),"tau":learner.info["tau"],"test":cohort.fingerprint})
    if key in cache:
        return dict(cache[key])
    weights={c:learner.store.get_weights(c).copy() for c in learner.categories}
    reads=informative=correct=0
    predictions=[]
    for case in cohort.cases:
        c=case["category"]
        run=h.run_investigation(case,learner.inv[c],weights[c],budget=2)
        reads+=int(run["total_reads"]);informative+=int(run["informative_reads"]);correct+=int(run["correct"])
        predictions.append([int(run["final_action"]),[int(x) for x in run["selected"]]])
    assert all(np.array_equal(weights[c],learner.store.get_weights(c)) for c in learner.categories)
    result={"routing_quality":informative/reads,"action_accuracy":correct/len(cohort.cases),
            "informative_reads":informative,"total_reads":reads,"correct_actions":correct,
            "n_evaluated":len(cohort.cases),"prediction_and_read_hash":digest(predictions),
            "evaluation_set_sha256":cohort.fingerprint}
    cache[key]=result
    return dict(result)


def inputs_only(case: R,learner: Learner) -> R:
    # Allowed view: category, entity ID, and surface only. No label/full/tag access.
    c=case["category"];surface=case["surface"].copy()
    label=int(learner.inv[c].score(surface)[0])
    return {"category":c,"entity_id":case["entity_id"],"surface":surface,"full":surface.copy(),
            "surface_action":label,"correct_action":label,"informative":set(range(len(surface)))}


def view_inputs(cohort: Cohort,learner: Learner) -> Cohort:
    return Cohort([inputs_only({"category":c["category"],"entity_id":c["entity_id"],
                               "surface":c["surface"]},learner) for c in cohort.cases])


def flat(points: list[R]) -> bool:
    return len(points)>=WINDOW and all(max(p[m] for p in points[-WINDOW:])-
                                      min(p[m] for p in points[-WINDOW:])<=TOL+1e-12 for m in METRICS)


def mean_level(points: list[R]) -> R:
    return {m:float(np.mean([p[m] for p in points[-WINDOW:]])) for m in METRICS}


def parity_summary(points: list[R],reference: R,converged: bool) -> R:
    if not converged:
        return {"decisions_to_sustained_parity":"reference_not_converged",
                "confirmation_decision":None,"parity_lost_after_confirmation":None,
                "residual_gap_routing":reference["routing_quality"]-points[-1]["routing_quality"],
                "residual_gap_action":reference["action_accuracy"]-points[-1]["action_accuracy"]}
    good=[all(p[m]>=reference[m]-PARITY-1e-12 for m in METRICS) for p in points]
    ending=next((i for i in range(WINDOW-1,len(good)) if all(good[i-WINDOW+1:i+1])),None)
    return {"decisions_to_sustained_parity":"not_reached" if ending is None else points[ending-WINDOW+1]["decision_count"],
            "confirmation_decision":None if ending is None else points[ending]["decision_count"],
            "parity_lost_after_confirmation":False if ending is None else not all(good[ending+1:]),
            "residual_gap_routing":reference["routing_quality"]-points[-1]["routing_quality"],
            "residual_gap_action":reference["action_accuracy"]-points[-1]["action_accuracy"],
            "reference_level":dict(reference),"parity_threshold_pp":1.0,"stability_window":WINDOW,
            "censoring_decisions":points[-1]["decision_count"]}


def shuffled_mask(n: int,block: int,take: int,seed: int) -> list[bool]:
    rng=random.Random(seed)
    mask: list[bool]=[]
    for start in range(0,n,block):
        indices=list(range(block));rng.shuffle(indices)
        chosen=set(indices[:take])
        mask.extend(i in chosen for i in range(min(block,n-start)))
    return mask


def observed_credit(learner: Learner,case: R,run: R,target: int) -> tuple[R,set[int]]:
    inv=learner.inv[case["category"]]
    allowed=set()
    for dim,before,after in run["step_records"]:
        surface_action,p_before,_=h.score(inv,before)
        action,p_after,_=h.score(inv,after)
        gain=float(p_after[target]-p_before[target])
        gap=abs(float(inv.mu[target,dim]-inv.mu[surface_action,dim]))
        if action==target or (gain>=.02 and gap>=.08):
            allowed.add(int(dim))
    credited=dict(run)
    credited["correct"]=int(run["final_action"])==target
    return credited,allowed


def noisy_dev(cohort: Cohort,learner: Learner,epsilon: float,seed: int) -> Cohort:
    mask=shuffled_mask(len(cohort.cases),20,round(20*epsilon),seed)
    rng=random.Random(seed+1)
    cases=[]
    for c,bad in zip(cohort.cases,mask):
        new=dict(c);inv=learner.inv[c["category"]]
        target=int(c["correct_action"])
        if bad:
            target=(target+rng.randrange(1,len(learner.info["action_names"])))%len(learner.info["action_names"])
        new["correct_action"]=target
        surface_action,ps,_=h.score(inv,c["surface"])
        informative=set()
        for dim in range(len(learner.factors)):
            v=c["surface"].copy();v[dim]=c["full"][dim]
            action,p,_=h.score(inv,v)
            if action==target or (float(p[target]-ps[target])>=.02 and
                                  abs(float(inv.mu[target,dim]-inv.mu[surface_action,dim]))>=.08):
                informative.add(dim)
        if not informative:
            informative={int(d) for d in np.flatnonzero(c["full"]!=c["surface"])}
        new["informative"]=informative
        cases.append(new)
    return Cohort(cases)


def project_k(source: Learner,target: Learner) -> None:
    rows=[]
    for index,source_cat in enumerate(source.categories):
        target_cat=target.categories[index]
        for dim,value in enumerate(source.store.get_weights(source_cat)):
            rows.append((target_cat,dim,float(value),0))
    target.store.conn.execute("DELETE FROM k_utility")
    target.store.conn.executemany("INSERT INTO k_utility VALUES (?,?,?,?)",rows)
    target.store.conn.commit()


def run_arm(name: str,learner: Learner,train: Cohort,development: Cohort,test: Cohort,
            cache: R,tier: str,mode: str="normal",epsilon: float=0.,seed: int=42,
            extra_test: Cohort | None=None,projection: Learner | None=None) -> R:
    development=development if mode!="inputs" else view_inputs(development,learner)
    if mode=="noisy":
        development=noisy_dev(development,learner,epsilon,seed+3000)
    corruption=shuffled_mask(MAX_N,20,round(20*epsilon),seed)
    label_rng=random.Random(seed+1)
    pending: list[tuple[int,R,R,int,bool]]=[]
    points: list[R]=[];dev_points: list[R]=[];extra_points: list[R]=[]
    delivered=corrupted_delivered=sa_labels=sb_labels=paid_reads=0
    generated_corrupt=0
    convergence: int | None=None
    initial_geometry=digest({"mu":learner.state()["mu"],"sigma":learner.state()["sigma"]})

    def checkpoint(n: int) -> bool:
        evaluation_learner=learner
        if projection is not None:
            project_k(learner,projection)
            evaluation_learner=projection
        p=evaluate(evaluation_learner,test,cache)
        p.update({"decision_count":n,"tier":tier,"evaluation_geometry_tier":"REAL_COMPONENT",
                  "verification_tier":"SIMULATED","K_weights_by_category":learner.weights(),
                  "labels_received":delivered,"SA_verified_labels_received":sa_labels,
                  "SB_verified_labels_received":sb_labels,"corrupt_labels_received":corrupted_delivered,
                  "training_evidence_reads":paid_reads})
        points.append(p)
        dp=evaluate(learner,development,cache)
        dp.update({"decision_count":n,"tier":tier,"role":"stopping-development-only",
                   "label_source":"self" if mode=="inputs" else "received_noisy" if mode=="noisy" else "synthetic_verified"})
        dev_points.append(dp)
        if extra_test is not None:
            ep=evaluate(evaluation_learner,extra_test,cache)
            ep.update({"decision_count":n,"tier":"SIMULATED","role":"paired-current-SA-under-declared-drift"})
            extra_points.append(ep)
        stable=(len(dev_points)>=WINDOW and
                len({p["prediction_and_read_hash"] for p in dev_points[-WINDOW:]})==1
                if mode=="inputs" else flat(dev_points))
        if n%250==0:
            print(f"{learner.copilot}/{name} N={n}: routing={p['routing_quality']:.4f} "
                  f"action={p['action_accuracy']:.4f} dev_stable={stable}",flush=True)
        return bool(n>=MIN_N and stable)

    checkpoint(0)
    for n,original in enumerate(train.cases[:MAX_N],1):
        case=inputs_only(original,learner) if mode=="inputs" else original
        run=learner.acquire(case)
        paid_reads+=int(run["total_reads"])
        if mode=="noisy":
            target=int(case["correct_action"]);bad=corruption[n-1]
            if bad:
                target=(target+label_rng.randrange(1,len(learner.info["action_names"])))%len(learner.info["action_names"])
                generated_corrupt+=1
            pending.append((n+50,case,run,target,bad))
            while pending and pending[0][0]<=n:
                _,old_case,old_run,label,is_bad=pending.pop(0)
                credited,allowed=observed_credit(learner,old_case,old_run,label)
                learner.credit(old_case,credited,allowed)
                delivered+=1;sa_labels+=1;corrupted_delivered+=int(is_bad)
        else:
            learner.credit(case,run)
            if mode!="inputs":
                delivered+=1
                sa_labels+=int(case["entity_id"].startswith("Firm-A"))
                sb_labels+=int(case["entity_id"].startswith("Firm-B"))
        if n%EVERY==0 and checkpoint(n):
            convergence=n
            break
    final_n=points[-1]["decision_count"]
    assert digest({"mu":learner.state()["mu"],"sigma":learner.state()["sigma"]})==initial_geometry
    result={"stream":name,"tier":tier,"geometry_tier":"REAL_COMPONENT","verification_tier":"SIMULATED",
            "convergence_point":convergence,"converged":convergence is not None,
            "stop_reason":"development_convergence" if convergence is not None else "max_budget",
            "convergence_metric_source":"unlabeled_prediction_read_plan" if mode=="inputs" else "own_distribution_development",
            "processed_decisions":final_n,"max_budget":MAX_N,"checkpoints_on_SA_heldout":points,
            "development_checkpoints":dev_points,"final_routing":points[-1]["routing_quality"],
            "final_action":points[-1]["action_accuracy"],"final_heldout_flat":flat(points),
            "final_state":learner.state(),"labels_received":delivered,
            "SA_verified_labels_received":sa_labels,"SB_verified_labels_received":sb_labels,
            "pending_verifications":len(pending),"corrupted_labels_generated":generated_corrupt,
            "corrupted_labels_received":corrupted_delivered,"training_evidence_reads":paid_reads,
            "primary_evaluation_sha256":test.fingerprint}
    if extra_test is not None:
        result["checkpoints_on_current_SA_drifted_heldout"]=extra_points
    return result


def distribution_distance(a: Cohort,b: Cohort,info: R) -> R:
    cats=info["category_names"]
    pa=np.array([sum(c["category"]==cat for c in a.cases)/len(a.cases) for cat in cats])
    pb=np.array([sum(c["category"]==cat for c in b.cases)/len(b.cases) for cat in cats])
    assert np.all(pa>0) and np.all(pb>0)
    metrics={}
    for field_name in ("surface","full"):
        aa=np.array([c[field_name] for c in a.cases])
        bb=np.array([c[field_name] for c in b.cases])
        rows=[]
        for d,name in enumerate(info["factor_names"]):
            am=float(aa[:,d].mean());bm=float(bb[:,d].mean())
            ast=float(aa[:,d].std());bst=float(bb[:,d].std())
            rows.append({"factor":name,"SA_mean":am,"SB_mean":bm,"mean_delta_B_minus_A":bm-am,
                         "SA_SD":ast,"SB_SD":bst,"SD_delta_B_minus_A":bst-ast,
                         "mean_delta_in_SA_SD":(bm-am)/max(ast,1e-12),"tier":"SIMULATED"})
        ac=np.corrcoef(aa,rowvar=False);bc=np.corrcoef(bb,rowvar=False)
        metrics[field_name]={"factor_statistics":rows,"SA_correlation":ac.tolist(),
                             "SB_correlation":bc.tolist(),"correlation_delta_frobenius":float(np.linalg.norm(bc-ac)),
                             "tier":"SIMULATED"}
    return {"tier":"SIMULATED","sample_sizes":{"SA":len(a.cases),"SB":len(b.cases)},
            "category_priors_SA":dict(zip(cats,pa.tolist())),"category_priors_SB":dict(zip(cats,pb.tolist())),
            "KL_SA_to_SB_nats":float(np.sum(pa*np.log(pa/pb))),
            "KL_SB_to_SA_nats":float(np.sum(pb*np.log(pb/pa))),"factors":metrics,
            "action_frequencies_SA":{str(i):sum(c["correct_action"]==i for c in a.cases)/len(a.cases)
                                     for i in range(len(info["action_names"]))},
            "action_frequencies_SB":{str(i):sum(c["correct_action"]==i for c in b.cases)/len(b.cases)
                                     for i in range(len(info["action_names"]))}}


def attach_parity(arm: R,reference: R,converged: bool,cop: str) -> None:
    arm.update(parity_summary(arm["checkpoints_on_SA_heldout"],reference,converged))
    n=arm["decisions_to_sustained_parity"]
    arm["wall_clock_to_parity"]={"weeks":n/RATES[cop] if isinstance(n,int) else None,
                                "tier":"ILLUSTRATIVE","assumed_verified_per_week":RATES[cop],
                                "assumption_source":"MAP VLD Addendum v20 ($7B manufacturer)"}
    arm["scope"]="routing-level specificity, K-only; mu-specificity untested"


def compute_all() -> R:
    export=cast(R,h.load_export())
    sa: R={};seeds={}
    # This entire loop finishes before any S_B generation.
    for index,cop in enumerate(("soc","dataops")):
        seed=42+index*10000;seeds[cop]=seed
        sa[cop]=split_pool(generate(cop,export[cop],3000,seed,f"Firm-A/{cop}"),seed+500000)
    frozen_test_hashes={cop:sa[cop]["test"].fingerprint for cop in sa}
    cache: R={}
    result: R={"metadata":{"random_state":42,"held_out_fraction":.2,"convergence_tolerance":TOL,
             "stability_window":WINDOW,"parity_threshold_pp":100*PARITY,"checkpoint_interval":EVERY,
             "min_convergence_decisions":MIN_N,"max_decisions":MAX_N,
             "heldout_frozen_before_SB_generation":True,"heldout_test_hashes":frozen_test_hashes,
             "S_B_perturbation_spec":{},"migration_drift_spec":{},
             "metric_definitions":{"routing_quality":"informative reads / attempted reads",
                                   "action_accuracy":"final action == verified action / cases",
                                   "category_accuracy":"not measured; category is supplied"},
             "scope":"routing-level specificity (K-only); mu-specificity untested, requires TIER-6/7",
             "comparison_reference":"incumbent final three held-out checkpoints at development-defined convergence",
             "parity_time":"onset of qualifying three-checkpoint window, with confirmation and later-loss flag",
             "evidence_tiers":{"geometry":"REAL_COMPONENT","verification":"SIMULATED","firm_B":"SIMULATED",
                               "migration_drift":"SIMULATED","wall_clock":"ILLUSTRATIVE"},
             "B1_status":"superseded/retracted as a moat inference; original artifacts unmodified",
             "hypotheses_not_targets":["Arm2 fails parity","inputs-only fails parity","migration incurs nonzero recovery"],
             "limitations":["single root seed and finite development convergence window",
                            "KE-1 geometry-derived labels and oracle-coupled evidence; no live outcomes",
                            "fixed mu: limited learner capacity can contribute to transfer failure",
                            "one second-firm profile is not a proof against every competitor",
                            "no-label baseline is one self-label strategy, not an impossibility result",
                            "no labels are proven unobtainable by this experiment",
                            "positional cross-domain mapping has no semantic or replication validity",
                            "no conservation gate invoked by unchanged KE-1 K updates"]}}
    for cop in ("soc","dataops"):
        seed=seeds[cop];info=export[cop];pool=sa[cop]
        info_b,spec=shifted(info)
        spec.update({"category_probabilities":dict(zip(info["category_names"],B_PRIORS[cop])),
                     "action_acceptance_weights":dict(zip(info["action_names"],B_ACCEPT[cop])),
                     "same_domain_learner_geometry":"original export, NOT mu_B"})
        result["metadata"]["S_B_perturbation_spec"][cop]=spec
        sb=generate(cop,info_b,2400,seed+100000,f"Firm-B/{cop}",B_PRIORS[cop],B_ACCEPT[cop])
        sb_train=Cohort(sb[:2000]);sb_dev=Cohort(sb[2000:])
        test=pool["test"]
        assert digest([serial(c) for c in test.cases])==frozen_test_hashes[cop]
        assert not {c["entity_id"] for c in test.cases}&{c["entity_id"] for c in sb}
        domain: R={
            "stream_audit":{"tier":"SIMULATED","SA_pool_size":3000,"heldout_size":600,"development_size":400,
                           "training_size":2000,"heldout_fraction":.2,"split_seed":seed+500000,
                           "split_indices":pool["split_indices"],"heldout_sha256":test.fingerprint,
                           "SA_training_sha256":pool["train"].fingerprint,"SB_training_sha256":sb_train.fingerprint,
                           "SB_development_sha256":sb_dev.fingerprint,"no_train_test_overlap":True,
                           "frozen_before_SB_generation":True,"test_never_used_for_stopping":True,
                           "realized_distribution_distance":distribution_distance(pool["train"],sb_train,info)}
        }
        incumbent=Learner(cop,info)
        a1=run_arm("S_A",incumbent,pool["train"],pool["dev"],test,cache,"REAL_COMPONENT",seed=seed)
        a1["checkpoints"]=a1["checkpoints_on_SA_heldout"]
        reference=mean_level(a1["checkpoints"])
        a1["converged_reference_level"]=reference
        domain["arm1_incumbent"]=a1
        independent=Learner(cop,info)
        a2=run_arm("S_B",independent,sb_train,sb_dev,test,cache,"SIMULATED",seed=seed)
        attach_parity(a2,reference,a1["converged"],cop)
        assert a2["SA_verified_labels_received"]==0
        if not a1["converged"]:
            a2["preregistered_verdict"]="INCONCLUSIVE: incumbent not converged within budget"
        elif isinstance(a2["decisions_to_sustained_parity"],int):
            a2["preregistered_verdict"]="TIME-ONLY under the pre-registered routing-level rule"
        else:
            a2["preregistered_verdict"]="DATA-SPECIFIC under the pre-registered routing-level rule, within the observed horizon"
        domain["arm2_independent"]=a2
        independent.close()
        unlabeled=Learner(cop,info)
        # Sanitization physically removes label/full/informative fields before the runner.
        sanitized=Cohort([inputs_only({"category":c["category"],"entity_id":c["entity_id"],
                                      "surface":c["surface"]},unlabeled) for c in pool["train"].cases])
        a3a=run_arm("S_A_inputs_only",unlabeled,sanitized,pool["dev"],test,cache,
                   "SIMULATED",mode="inputs",seed=seed+300)
        attach_parity(a3a,reference,a1["converged"],cop)
        assert a3a["labels_received"]==a3a["SA_verified_labels_received"]==0
        a3a["allowed_access"]=["category","entity_id","surface_vector"]
        a3a["labels_unobtainable_inference"]="not established; one self-label strategy tested"
        domain["arm3a_inputs_no_labels"]=a3a
        unlabeled.close()
        for fraction in (.1,.5):
            mixed=Learner(cop,info)
            mask=shuffled_mask(2000,10,round(10*fraction),seed+500)
            dev_mask=shuffled_mask(400,10,round(10*fraction),seed+501)
            train=Cohort([a if selected else b for a,b,selected in zip(pool["train"].cases,sb_train.cases,mask)])
            dev=Cohort([a if selected else b for a,b,selected in zip(pool["dev"].cases,sb_dev.cases,dev_mask)])
            arm=run_arm(f"SA_fraction_{fraction}",mixed,train,dev,test,cache,"SIMULATED",seed=seed+500)
            attach_parity(arm,reference,a1["converged"],cop)
            arm["SA_fraction"]=fraction
            arm["realized_SA_fraction"]=arm["SA_verified_labels_received"]/arm["processed_decisions"]
            assert abs(arm["realized_SA_fraction"]-fraction)<1e-12
            domain[f"arm3b_{round(fraction*100)}pct"]=arm
            mixed.close()
        for epsilon in (.1,.25):
            noisy=Learner(cop,info)
            arm=run_arm(f"SA_delayed50_eps{epsilon}",noisy,pool["train"],pool["dev"],test,cache,"SIMULATED",
                        mode="noisy",epsilon=epsilon,seed=seed+700)
            attach_parity(arm,reference,a1["converged"],cop)
            arm.update({"label_lag_decisions":50,"label_corruption_rate":epsilon,
                        "credit_source":"received potentially corrupt label + acquired before/after evidence",
                        "realized_corruption_fraction_received":arm["corrupted_labels_received"]/arm["labels_received"]})
            domain[f"arm3c_eps{round(epsilon*100)}"]=arm
            noisy.close()

        drift_info,drift_spec=shifted(info,drift=True)
        result["metadata"]["migration_drift_spec"][cop]=drift_spec
        drift_pool=split_pool(generate(cop,drift_info,3000,seed,f"Firm-A-drift/{cop}"),seed+500000)
        assert drift_pool["split_indices"]==pool["split_indices"]
        current=Learner(cop,info);migrate(incumbent,current)
        current_arm=run_arm("current_incumbent_drift",current,drift_pool["train"],drift_pool["dev"],test,cache,
                            "SIMULATED",seed=seed,extra_test=drift_pool["test"])
        current_ref=mean_level(current_arm["checkpoints_on_current_SA_drifted_heldout"])
        migrant=Learner(cop,info);migrate(incumbent,migrant)
        copied_state=migrant.state()
        old_metrics=evaluate(migrant,test,cache)
        stale_metrics=evaluate(migrant,drift_pool["test"],cache)
        a4=run_arm("migration_stale_snapshot_then_drift",migrant,drift_pool["train"],drift_pool["dev"],test,cache,
                   "SIMULATED",seed=seed,extra_test=drift_pool["test"])
        attach_parity(a4,reference,a1["converged"],cop)
        recovery=parity_summary(a4["checkpoints_on_current_SA_drifted_heldout"],current_ref,
                                bool(a1["converged"] and current_arm["converged"]))
        onset=recovery["decisions_to_sustained_parity"]
        a4.update({"staleness_dip_routing":old_metrics["routing_quality"]-stale_metrics["routing_quality"],
                   "staleness_dip_action":old_metrics["action_accuracy"]-stale_metrics["action_accuracy"],
                   "stale_gap_to_current_routing":current_ref["routing_quality"]-stale_metrics["routing_quality"],
                   "stale_gap_to_current_action":current_ref["action_accuracy"]-stale_metrics["action_accuracy"],
                   "decisions_to_re_parity":onset,"re_parity_confirmation":recovery["confirmation_decision"],
                   "recovery_parity":recovery,"current_incumbent":current_arm,
                   "current_converged_reference":current_ref,
                   "migrated_snapshot":{"source_decision_count":a1["processed_decisions"],
                                        "state":copied_state,"mu_delta_on_copy":0.0,
                                        "serialized_state_bytes":len(canonical(copied_state)),
                                        "independent_memory_and_sqlite":True,"tier":"REAL_COMPONENT"},
                   "staleness_pre_drift":old_metrics,"staleness_post_drift":stale_metrics,
                   "drift_heldout_sha256":drift_pool["test"].fingerprint,
                   "switching_cost_summary":
                       "Measured re-parity onset="+str(onset)+", confirmation="+str(recovery["confirmation_decision"])+
                       " processed/verified drift decisions. Engineering burden not monetized: schema/factor mapping, "
                       "state export/import, provenance validation, scorer parity checks and current-outcome re-verification.",
                   "switching_cost_wall_clock":{"weeks_to_reparity":onset/RATES[cop] if isinstance(onset,int) else None,
                                               "tier":"ILLUSTRATIVE","verified_per_week":RATES[cop]},
                   "drift_realized_distance":distribution_distance(pool["train"],drift_pool["train"],info)})
        domain["arm4_migration"]=a4
        current.close();migrant.close()

        foreign="dataops" if cop=="soc" else "soc"
        foreign_learner=Learner(foreign,export[foreign]);projected=Learner(cop,info)
        probe=run_arm("incompatible_domain_probe",foreign_learner,sa[foreign]["train"],sa[foreign]["dev"],
                      test,cache,"REAL_COMPONENT",seed=seeds[foreign],projection=projected)
        probe["foreign_verified_labels_received"]=probe["SA_verified_labels_received"]
        probe["SA_verified_labels_received"]=0
        for point in probe["checkpoints_on_SA_heldout"]:
            point["foreign_verified_labels_received"]=point["SA_verified_labels_received"]
            point["SA_verified_labels_received"]=0
        attach_parity(probe,reference,a1["converged"],cop)
        probe.update({"experiment_label":"transfer-across-incompatible-domains probe",
                      "trained_on":foreign,"evaluated_on":cop+"_SA_heldout","replication_weight":"NONE",
                      "geometry_tier":"REAL_COMPONENT","mapping_tier":"SIMULATED",
                      "factor_mapping":[{"source":a,"target":b,"dimension":i}
                                        for i,(a,b) in enumerate(zip(export[foreign]["factor_names"],info["factor_names"]))],
                      "category_mapping":[{"source":a,"target":b,"index":i}
                                          for i,(a,b) in enumerate(zip(export[foreign]["category_names"],info["category_names"]))],
                      "action_mapping":"none; use target native geometry/action space for evaluation",
                      "exact_factor_name_overlap":sorted(set(export[foreign]["factor_names"])&set(info["factor_names"])),
                      "parity":"reached" if isinstance(probe["decisions_to_sustained_parity"],int) else "not_reached"})
        domain["robustness_cross_copilot"]=probe
        foreign_learner.close();projected.close();incumbent.close()
        domain["fig2_data"]={
            "tier":"SIMULATED",
            "metric_names":list(METRICS),
            "incumbent":[{k:p[k] for k in ("decision_count",*METRICS,"tier")} for p in a1["checkpoints"]],
            "independent":[{k:p[k] for k in ("decision_count",*METRICS,"tier")}
                           for p in a2["checkpoints_on_SA_heldout"]],
            "access":[{"condition":name,**{k:arm[k] for k in ("decisions_to_sustained_parity","confirmation_decision",
                      "residual_gap_routing","residual_gap_action","SA_verified_labels_received","tier")}}
                      for name,arm in domain.items() if name.startswith("arm3")]}
        assert all(arm["primary_evaluation_sha256"]==test.fingerprint for name,arm in domain.items()
                   if name.startswith("arm") or name=="robustness_cross_copilot")
        result[cop]=domain
        print(cop,"COMPLETE",a2["preregistered_verdict"],flush=True)
    assert all(digest([serial(c) for c in sa[cop]["test"].cases])==frozen_test_hashes[cop] for cop in sa)
    result["metadata"]["checks"]={"every_arm_same_primary_SA_test":True,"test_frozen_before_SB":True,
                                   "no_test_training_leakage":True,"mu_sigma_unchanged_by_learning":True,
                                   "no_input_only_verified_labels":True,"no_Arm2_SA_training_labels":True,
                                   "independent_migration_storage":True}
    return result


def write_summary(result: R) -> str:
    lines=["# B2 — Routing-level moat experiment","",
           "Date: September 14, 2026. random_state=42. K-only; no source modifications.",
           "B2 supersedes B1's moat inference. B1's scripts, results and figures are retained unchanged. "
           "No B1 endpoint or conclusion was used as a target.",
           "",
           "## 1. Pre-registered streams and realized distances","",
           "S_A uses unchanged KE-1 make_case with uniform categories and original exported geometry. "
           "The second-firm latent profile shifts means by [+0.75,−0.50,+1.00,−0.75,+0.50,−1.00] empirical "
           "geometry SD, scales factors by [1.35,.65,1.20,.80,1.10,.90], and mixes 30% of the preceding cyclic "
           "standardized factor. Values clip to [.02,.98]. SD is measured across centroid rows, not unit metric sigma. "
           "All same-domain LEARNERS retain the original μ/σ; only K learns. Changing latent profile changes data "
           "and verification distribution, not the learning algorithm.",
           "Tier: second-firm perturbations/distances SIMULATED; original geometry REAL_COMPONENT with synthetic verification."]
    for cop in ("soc","dataops"):
        domain=result[cop];distance=domain["stream_audit"]["realized_distribution_distance"]
        spec=result["metadata"]["S_B_perturbation_spec"][cop]
        lines.extend(["",f"### {cop.upper()}","",
                      "Specified S_B category probabilities: "+json.dumps(spec["category_probabilities"])+".",
                      "Relative action acceptance weights: "+json.dumps(spec["action_acceptance_weights"])+". "
                      "These are acceptance weights; realized action frequencies are recorded separately in JSON.",
                      f"Realized category KL(S_A||S_B)={distance['KL_SA_to_SB_nats']:.6f} nats; "
                      f"KL(S_B||S_A)={distance['KL_SB_to_SA_nats']:.6f} nats (2,000 training cases each).",
                      "Realized S_A priors: "+json.dumps(distance["category_priors_SA"])+".",
                      "Realized S_B priors: "+json.dumps(distance["category_priors_SB"])+".","",
                      "| Factor (surface inputs) | A mean | B mean | B−A mean | A SD | B SD | B−A SD | Mean shift / A SD | Tier |",
                      "|---|---:|---:|---:|---:|---:|---:|---:|---|"])
        for row in distance["factors"]["surface"]["factor_statistics"]:
            lines.append(f"| {row['factor']} | {row['SA_mean']:.5f} | {row['SB_mean']:.5f} | "
                         f"{row['mean_delta_B_minus_A']:+.5f} | {row['SA_SD']:.5f} | {row['SB_SD']:.5f} | "
                         f"{row['SD_delta_B_minus_A']:+.5f} | {row['mean_delta_in_SA_SD']:+.3f} | SIMULATED |")
        lines.append("Full latent-vector mean/SD tables and both correlation matrices are in "
                     "stream_audit.realized_distribution_distance.factors.full and .surface.")
    lines.extend(["","## 2. Frozen held-out slice and leakage checks","",
        "For each copilot, generate 3,000 S_A cases and independently shuffle split indices: 600 fixed test (20%), "
        "400 development, 2,000 training. Both test sets are frozen/hash-checked BEFORE generating any S_B. "
        "Category+surface fingerprints and indices have no test/train/development overlap. No arm receives test "
        "cases for learning, threshold selection or stopping. Every arm—including migration and the incompatible-domain "
        "probe—records both metrics on exactly this same primary S_A test. Arm 2's S_B development evaluation is "
        "only a stopping monitor, never the reported moat test.",
        "Arm 4 additionally evaluates a paired drifted-current S_A slice, shared by migrant and current incumbent. "
        "This supplemental test does not replace the common original S_A test. Split indices and evaluation hashes "
        "are persisted in the JSON. Synthetic verification is the geometry-derived full-vector oracle; "
        "the informative-read evidence model is inherited from KE-1 and is not live customer evidence.",
        "Convergence is development max−min ≤0.5pp in both metrics over three consecutive checkpoints, "
        "minimum N500, maximum N2000, checkpoints every 50. It is a finite operational criterion, not mathematical "
        "asymptotic convergence. The inputs-only arm uses unlabeled action/read-plan stability because verified "
        "development labels would violate that condition. Held-out final-window flatness is a diagnostic, not a "
        "checkpoint-selection criterion.",
        "Parity uses both metrics against the mean of Arm 1's final three held-out checkpoints at its development-defined "
        "convergence. Reported time is the onset of three qualifying checkpoints; confirmation is separately shown. "
        "Later losses are disclosed. Not-reached is censored at the actual stopping count.",
        "","## 3. Arm 1 convergence","",
        "| Copilot | Convergence N | Stop N | Converged routing_quality | Converged action_accuracy | Held-out last 3 flat | Tier |",
        "|---|---:|---:|---:|---:|---|---|"])
    for cop in ("soc","dataops"):
        a=result[cop]["arm1_incumbent"];r=a["converged_reference_level"]
        lines.append(f"| {cop} | {a['convergence_point']} | {a['processed_decisions']} | "
                     f"{r['routing_quality']:.4%} | {r['action_accuracy']:.4%} | {a['final_heldout_flat']} | REAL_COMPONENT |")
    lines.extend(["","## 4. Arm 2 — pre-registered decision rule","",
        '> "The moat is data-specific (strong claim) IFF Arm 2 fails to reach sustained parity on the incumbent’s '
        'held-out decisions. If Arm 2 reaches parity, the moat is time-only and the paper weakens the claim—with this evidence."',
        "", "Every claim below means **routing-level specificity of K under this learner/profile/horizon**. "
        "μ-specificity is untested and dependent on TIER-6/7. Joint parity additionally requires action_accuracy.",
        "",
        "| Copilot | Parity onset | Confirmation | Stop N | Routing deficit (pp) | Action deficit (pp) | Later loss | Tier |",
        "|---|---|---|---:|---:|---:|---|---|"])
    for cop in ("soc","dataops"):
        a=result[cop]["arm2_independent"]
        lines.append(f"| {cop} | {a['decisions_to_sustained_parity']} | {a['confirmation_decision']} | "
                     f"{a['processed_decisions']} | {100*a['residual_gap_routing']:+.3f} | "
                     f"{100*a['residual_gap_action']:+.3f} | {a['parity_lost_after_confirmation']} | SIMULATED |")
    for cop in ("soc","dataops"):
        a=result[cop]["arm2_independent"]
        lines.extend(["",f"**{cop}: {a['preregistered_verdict']}.** "
                      f"Final routing_quality={a['final_routing']:.3%}; action_accuracy={a['final_action']:.3%}. "
                      "No S_A training inputs or verified labels were supplied to this learner. "
                      "Failure to reach parity at a finite stopping horizon does not prove failure for every "
                      "competitor, algorithm or future stream."])
    lines.extend(["","## 5. Arm 3 — access versus catch-up","",
        "Deficit is incumbent converged level minus final entrant; a negative deficit means outperformance. "
        "Labels received are counted; a fraction is not treated as free access. Original training evidence remains "
        "the KE-1 synthetic oracle-coupled provider. Inputs-only gets neither latent full vectors nor clean informative tags. "
        "Noisy arms queue captured investigations for 50 decisions and credit only the received label plus acquired evidence.",
        "",
        "| Copilot | Access | Parity onset | Confirmation | Stop N | A labels received | Routing deficit pp | Action deficit pp | Tier |",
        "|---|---|---|---|---:|---:|---:|---:|---|"])
    for cop in ("soc","dataops"):
        for name,a in result[cop].items():
            if name.startswith("arm3"):
                lines.append(f"| {cop} | {name} | {a['decisions_to_sustained_parity']} | "
                             f"{a['confirmation_decision']} | {a['processed_decisions']} | {a['SA_verified_labels_received']} | "
                             f"{100*a['residual_gap_routing']:+.3f} | {100*a['residual_gap_action']:+.3f} | SIMULATED |")
    lines.extend(["",
        "A failure of 3a supports the value of verified labels relative to this particular self-label baseline; "
        "it does **not** show that labels are unobtainable or that all unlabeled methods must fail. "
        "See JSON for actual corruption fractions, pending verifications, later parity losses and paid evidence reads.",
        "","## 6. Arm 4 — measured switching-cost decomposition","",
        "Predeclared drift: ±.25 empirical geometry SD, factor scales [1.10,.90,1.10,.90,1.05,.95], rho=.10 "
        "cyclic mixing, clipped [.02,.98], category/action sampling unchanged. Drift is not tuned after execution. "
        "Staleness dip compares the SAME migrated state before versus after the paired drift; it may be zero or "
        "negative. Re-parity compares to a continuing incumbent independently adapted on the drifted training stream. "
        "No μ updates occur; copied μ retains its values. Cost is measured adaptation/re-verification volume, "
        "plus a qualitative integration burden; no invented dollar or engineering-hour estimate.",
        "",
        "| Copilot | Routing staleness dip pp | Action staleness dip pp | Gap to current routing pp | Gap to current action pp | Re-parity onset | Confirmation | Current reference convergence N | Tier |",
        "|---|---:|---:|---:|---:|---|---|---|---|"])
    for cop in ("soc","dataops"):
        a=result[cop]["arm4_migration"]
        lines.append(f"| {cop} | {100*a['staleness_dip_routing']:+.3f} | {100*a['staleness_dip_action']:+.3f} | "
                     f"{100*a['stale_gap_to_current_routing']:+.3f} | {100*a['stale_gap_to_current_action']:+.3f} | "
                     f"{a['decisions_to_re_parity']} | {a['re_parity_confirmation']} | "
                     f"{a['current_incumbent']['convergence_point']} | SIMULATED |")
    for cop in ("soc","dataops"):
        a=result[cop]["arm4_migration"]
        lines.extend(["",f"{cop}: {a['switching_cost_summary']} "
                      f"Final pending verifications={a['pending_verifications']}; "
                      f"total adaptation decisions actually run={a['processed_decisions']}. "
                      f"Illustrative weeks to re-parity={a['switching_cost_wall_clock']['weeks_to_reparity']} "
                      f"at {RATES[cop]} verified/week."])
    lines.extend(["",
        "The stability confirmation window is an observation requirement, not a claim that all those labels are "
        "technically necessary for recovery. Copying K/μ is explicitly customer-authorized full-state access; "
        "this arm does not independently test the competitor-without-data moat.",
        "","## 7. Transfer-across-incompatible-domains probe","",
        "**Not a robustness replication. No replication weight.** The source domain learns on its own exported "
        "geometry and S_A training data. At evaluation only, K is mapped by category/factor position into target "
        "native geometry. This positional bridge is SIMULATED; source and target geometries are REAL_COMPONENT. "
        "No action indices or μ are transferred. Different factor meanings make transfer failure ambiguous; "
        "even agreement with Arm 2 is not independent replication evidence.",
        "",
        "| Target | Trained on | Parity onset | Final routing_quality | Final action_accuracy | Same reach/fail as Arm 2 | Tier |",
        "|---|---|---|---:|---:|---|---|"])
    for cop in ("soc","dataops"):
        p=result[cop]["robustness_cross_copilot"];a2=result[cop]["arm2_independent"]
        agrees=isinstance(p["decisions_to_sustained_parity"],int)==isinstance(a2["decisions_to_sustained_parity"],int)
        lines.append(f"| {cop} | {p['trained_on']} | {p['decisions_to_sustained_parity']} | "
                     f"{p['final_routing']:.3%} | {p['final_action']:.3%} | {agrees} | REAL_COMPONENT geometry / SIMULATED mapping |")
    for cop in ("soc","dataops"):
        p=result[cop]["robustness_cross_copilot"]
        lines.extend(["",f"{p['trained_on']} → {cop} factor mapping:", "",
                      "| Index | Source factor | Target factor |",
                      "|---:|---|---|"])
        for row in p["factor_mapping"]:
            lines.append(f"| {row['dimension']} | {row['source']} | {row['target']} |")
        lines.append("Category mapping by corresponding export index: "+json.dumps(p["category_mapping"])+".")
    conclusions=[]
    for cop in ("soc","dataops"):
        a=result[cop]["arm2_independent"]
        conclusions.append(f"{cop}: {a['preregistered_verdict']} "
                           f"(joint parity={a['decisions_to_sustained_parity']}, observed N={a['processed_decisions']})")
    lines.extend(["","## 8. Paper conclusion","",
        "Under the pre-registered rule, "+"; ".join(conclusions)+". "
        "These are finite, single-seed tests of routing-level specificity in learned K, using exported geometry "
        "and synthetic verified outcomes. They neither establish μ-specificity nor prove labels unobtainable. "
        "Partial-access and migration outcomes quantify this learner's information/re-verification tradeoffs; "
        "the incompatible-domain probe has no replication weight. The stronger interpretation is conditional "
        "on the stated convergence criterion and cannot be generalized beyond the tested profiles.",
        "","## 9. Revised Fig-2 data and reproducibility","",
        "Use each copilot's fig2_data.incumbent and fig2_data.independent for both routing_quality and "
        "action_accuracy curves; use fig2_data.access for the partial-access panel. Raw checkpoints retain "
        "K, labels received, stopping metrics, exact counts and evaluation-set hashes. These replace B1's "
        "moat figure DATA; no existing figure file is overwritten.",
        "Wall-clock assumptions: SOC=1,200 and DataOps=106 verified outcomes/week from MAP v20 "
        "($7B manufacturer); tier ILLUSTRATIVE. The JSON stores weeks per arm.",
        "Run mypy on experiments/vld/vld_moat_b2_v1.py before python -B experiments/vld/vld_moat_b2_v1.py. "
        "The script performs two independent full computations and compares canonical JSON bytes. "
        "The recorded determinism hash excludes only metadata.determinism_hash.",
        "Mypy passed before execution. Full determinism self-test passed; source/geometry hashes are retained. "
        "Only this new script, result JSON and summary were authored; no git commands or source modifications."])
    return "\n".join(lines)+"\n"


def main() -> None:
    paths=[ROOT/"real_centroids_v1.json",ROOT/"scripts/k_learning_curve_cross_copilot.py",
           ROOT/"copilot_sdk/scoring/scorer.py",ROOT/"copilot_sdk/scoring/investigation.py",
           ROOT/"copilot_sdk/backend/investigation_router.py",Path(__file__).resolve(),
           ROOT/"docs/design/map_vld_addendum_v20 (1).md"]
    source_hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    print("INDEPENDENT FULL COMPUTATION 1/2",flush=True)
    first=compute_all()
    print("INDEPENDENT FULL COMPUTATION 2/2",flush=True)
    second=compute_all()
    assert canonical(first)==canonical(second),"Full-computation determinism mismatch"
    first["metadata"]["source_sha256"]=source_hashes
    first["metadata"]["authorities"]=[
        "G:/My Drive/public-files/gen-ai-roi/claude_projects/design/blogs/ci_core/vld_B2_moat_redesign_memo.md",
        "G:/My Drive/public-files/gen-ai-roi/claude_projects/design/blogs/ci_core/vld_paper_experiments_request_v2.md",
        "User B2 four clarifications: K-only; incompatible-domain probe; measured distances; frozen test before SB"]
    first["metadata"]["determinism_self_test"]={"independent_full_computations":2,"passed":True}
    first["metadata"]["determinism_hash"]=digest(first)
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==source_hashes[p.relative_to(ROOT).as_posix()] for p in paths)
    OUT.mkdir(parents=True,exist_ok=True)
    output=OUT/"vld_moat_b2_v1.json"
    output.write_bytes(canonical(first))
    (OUT/"moat_b2_summary.md").write_text(write_summary(first),encoding="utf-8")
    print("DETERMINISM PASS",first["metadata"]["determinism_hash"],flush=True)
    for cop in ("soc","dataops"):
        a=first[cop]["arm2_independent"]
        print(cop, json.dumps({k:a[k] for k in ("preregistered_verdict","decisions_to_sustained_parity",
                                               "residual_gap_routing","residual_gap_action")}),flush=True)


if __name__=="__main__":
    main()
