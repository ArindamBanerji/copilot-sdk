"""Nine Q term ablations on paired production-geometry synthetic decisions."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import random
import statistics
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/"scripts"))
import numpy as np
import budget_accuracy_frontier as base

OUT=ROOT/"experiments/vld/q_term_ablation.json"
CSV=OUT.with_suffix(".csv")
FRONTIER=ROOT/"experiments/vld/budget_accuracy_frontier.json"
VARIANTS=("PRECISION-ONLY","DISCRIMINATIVE-ONLY","LEVERAGE-ONLY",
          "PREC+DISC","PREC+LEV","DISC+LEV","ALL-THREE","RANDOM","NO-K")
MASKS=((1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),(1,1,1),(1,1,1),(1,1,1))
COPILOTS=("dataops","trading","purchasing","soc","s2p")
FIELDS=("copilot","variant","routing_mean","routing_std","accuracy_mean",
        "accuracy_std","starvation","delta_vs_all_three_routing","delta_vs_all_three_accuracy")
INPUTS=base.CORE+("real_centroids_v1.json","scripts/k_learning_curve_experiment.py",
        "scripts/budget_accuracy_frontier.py","experiments/vld/budget_accuracy_frontier.json",
        "scripts/q_term_ablation.py")


def hashes():
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS}


def component_q(mu,sigma,v,p,k,variant):
    a1,a2=np.argsort(p)[::-1][:2]
    mask=MASKS[VARIANTS.index(variant)]
    q=np.zeros(mu.shape[1])
    for d in range(len(q)):
        # Match production operation order exactly; excluded components are zero.
        precision=(1.0/max(float(sigma[d]**2),.001))/100.
        discriminative=abs(float(mu[a1,d]-mu[a2,d]))
        leverage=abs(float((v[d]-mu[a1,d])**2-(v[d]-mu[a2,d])**2))
        q[d]=precision*mask[0]+discriminative*mask[1]+leverage*mask[2]
        if variant!="NO-K":
            q[d]*=float(k[d])
    return q


class AblationInvestigator(base.FrontierInvestigator):
    def __init__(self,info,category,variant,routing_seed):
        super().__init__(info["all_category_mu"][category],info["sigma"],
                         info["factor_names"],tau=info["tau"],action_names=info["action_names"])
        self.variant=variant
        self.routing_rng=random.Random(routing_seed)

    def compute_Q(self,v,P,enriched_set=None,K_weights=None):
        k=np.ones(len(self.factor_names)) if K_weights is None else np.asarray(K_weights)
        q=component_q(self.mu,self.sigma,np.asarray(v),np.asarray(P),k,self.variant)
        if self.variant=="RANDOM":
            q=np.asarray([self.routing_rng.random() for _ in self.factor_names])
        for d in self.prior_attempts | set(enriched_set or ()):
            q[d]=-1.
        # No Q floors, ranking tweaks, or fallback policies.
        assert q.max()>0, "All remaining Q values zero: fixed-B2 protocol needs explicit review"
        return q


def invs_for(info,variant,generator_seed):
    return {c:AblationInvestigator(info,c,variant,generator_seed+900000007+1009*i)
            for i,c in enumerate(info["category_names"])}


def starvation(run,info):
    updates={(r["category"],r["dimension"]):r["updates"] for r in run["k_update_counts"]}
    slots=[(c,d) for c in info["category_names"] for d in range(len(info["factor_names"]))]
    missing=[{"category":c,"dimension":d,"factor_name":info["factor_names"][d]}
             for c,d in slots if updates.get((c,d),0)==0]
    unmoved=sum(abs(run["k_by_category"][c][d]-.5)<=1e-9 for c,d in slots)/len(slots)
    assert sum(updates.values())==1000
    return {"selection_starvation":len(missing)/len(slots),
            "unselected_pairs":missing,"total_category_dimension_pairs":len(slots),
            "legacy_unmoved_k_fraction":unmoved}


def ci(values):
    mean=statistics.mean(values)
    half=2.776445105*statistics.stdev(values)/np.sqrt(len(values))
    return [float(mean-half),float(mean+half)]


def aggregate(name,variant,runs,control):
    routing=[r["metrics"]["routing_quality"] for r in runs]
    accuracy=[r["metrics"]["accuracy"] for r in runs]
    rd=[100*(v-c["metrics"]["routing_quality"]) for v,c in zip(routing,control)]
    ad=[100*(v-c["metrics"]["accuracy"]) for v,c in zip(accuracy,control)]
    return {"copilot":name,"variant":variant,
        "routing_mean":statistics.mean(routing),"routing_std":statistics.stdev(routing),
        "accuracy_mean":statistics.mean(accuracy),"accuracy_std":statistics.stdev(accuracy),
        "starvation":statistics.mean(r["starvation"]["selection_starvation"] for r in runs),
        "starvation_std":statistics.stdev(r["starvation"]["selection_starvation"] for r in runs),
        "legacy_unmoved_k_fraction":statistics.mean(r["starvation"]["legacy_unmoved_k_fraction"] for r in runs),
        "delta_vs_all_three_routing":statistics.mean(rd),
        "delta_vs_all_three_accuracy":statistics.mean(ad),
        "routing_delta_paired_t95_ci_pp":ci(rd),"accuracy_delta_paired_t95_ci_pp":ci(ad),
        "reads_mean":statistics.mean(r["metrics"]["reads"] for r in runs),
        "seed_runs":runs}


def lookup(data,variant,name):
    return next(c for v in data["variants"] if v["variant"]==variant
                for c in v["copilots"] if c["copilot"]==name)


def comparisons(data):
    output=[]
    for variant in VARIANTS:
        if variant=="ALL-THREE":
            continue
        strict,ties,losses=[],[],[]
        for name in COPILOTS:
            a=lookup(data,"ALL-THREE",name)["routing_mean"]
            b=lookup(data,variant,name)["routing_mean"]
            (strict if a>b+1e-12 else losses if a<b-1e-12 else ties).append(name)
        output.append({"subset_or_comparator":variant,"strict_wins":strict,"ties":ties,
                       "losses":losses,"noninferior_count":len(strict)+len(ties),
                       "requested_4_of_5_gate":len(strict)+len(ties)>=4})
    return output


def contribution(data):
    rows=[]
    for name in COPILOTS:
        p=lookup(data,"PRECISION-ONLY",name)
        pd=lookup(data,"PREC+DISC",name)
        pl=lookup(data,"PREC+LEV",name)
        all3=lookup(data,"ALL-THREE",name)
        per_seed=[]
        for a,b,c,d in zip(p["seed_runs"],pd["seed_runs"],pl["seed_runs"],all3["seed_runs"]):
            x,y,z,w=[r["metrics"]["routing_quality"] for r in (a,b,c,d)]
            per_seed.append({"precision_baseline_pp":100*x,"add_disc_pp":100*(y-x),
                             "add_leverage_after_disc_pp":100*(w-y),
                             "disc_leverage_interaction_given_precision_pp":100*(w-y-z+x)})
        rows.append({"copilot":name,
            **{k:statistics.mean(s[k] for s in per_seed) for k in per_seed[0]},
            "interaction_paired_t95_ci_pp":ci([s["disc_leverage_interaction_given_precision_pp"] for s in per_seed]),
            "per_seed":per_seed})
    return rows


def verify_run(run,cohort,info,variant):
    """Replay held-out ordering, actions and metrics with frozen K."""
    categories=info["category_names"]
    rngs={c:random.Random(cohort["generator_seed"]+900000007+1009*i)
          for i,c in enumerate(categories)}
    if variant=="RANDOM":
        for c in cohort["training_categories"]:
            for _ in range(2*len(info["factor_names"])):
                rngs[c].random()
    for row,case in zip(run["evaluation_rows"],cohort["evaluation_cases"]):
        assert row["case_id"]==case["id"] and row["category"]==case["category"]
        assert row["reads"]==2 and len(set(row["selected"]))==2
        mu=np.asarray(info["all_category_mu"][case["category"]])
        sigma=np.asarray(info["sigma"])
        v=np.asarray(case["surface"]).copy()
        k=np.asarray(run["k_by_category"][case["category"]])
        attempted=[]
        for dim in row["selected"]:
            dist=np.sum((v-mu)**2/np.maximum(sigma**2,.001),axis=1)
            logits=-dist/info["tau"]; p=np.exp(logits-logits.max()); p/=p.sum()
            a1,a2=np.argsort(p)[::-1][:2]
            terms=np.array([1/(100*np.maximum(sigma**2,.001)),
                            np.abs(mu[a1]-mu[a2]),
                            np.abs((v-mu[a1])**2-(v-mu[a2])**2)])
            mask=np.asarray(MASKS[VARIANTS.index(variant)])
            q=np.sum(terms*mask[:,None],axis=0)
            if variant!="NO-K":
                q*=k
            if variant=="RANDOM":
                q=np.array([rngs[case["category"]].random() for _ in sigma])
            q[attempted]=-1
            assert dim==int(np.argmax(q)),(variant,dim,q)
            v[dim]=case["full"][dim]; attempted.append(dim)
        predicted=int(np.argmin(np.sum((v-mu)**2/np.maximum(sigma**2,.001),axis=1)))
        oracle=int(np.argmin(np.sum((np.asarray(case["full"])-mu)**2/np.maximum(sigma**2,.001),axis=1)))
        assert predicted==row["final_action"]
        assert row["correct"]==(predicted==oracle)
        assert row["oracle_action"]==oracle
        assert row["informative_reads"]==sum(d in case["informative"] for d in attempted)
    assert run["metrics"]==base.metrics(run["evaluation_rows"])
    assert run["starvation"]==starvation(run,info)
    assert run["evaluation_frozen"]
    assert all(.1<=v<=3 for values in run["k_by_category"].values() for v in values)


def validate(data,export,frontier):
    assert [v["variant"] for v in data["variants"]]==list(VARIANTS)
    assert len(data["rows"])==45
    count=0
    for v in data["variants"]:
        assert len(v["copilots"])==5
        for row in v["copilots"]:
            name,variant=row["copilot"],v["variant"]
            assert len(row["seed_runs"])==5
            for run,cohort in zip(row["seed_runs"],data["cohorts"][name]):
                assert len(run["evaluation_rows"])==200
                assert run["seed"]==cohort["seed"]
                verify_run(run,cohort,export[name],variant)
                count+=200
            control=lookup(data,"ALL-THREE",name)["seed_runs"]
            assert row==aggregate(name,variant,row["seed_runs"],control)
    for name in COPILOTS:
        a=lookup(data,"ALL-THREE",name)
        b=frontier["copilots"][name]["results"]["2"]["vld"]
        assert a["routing_mean"]==b["routing_quality_mean"]
        assert a["accuracy_mean"]==b["accuracy_mean"]
    assert data["comparisons"]==comparisons(data)
    assert data["term_contribution"]==contribution(data)
    assert data["rows"]==[{k:r[k] for k in FIELDS} for v in data["variants"] for r in v["copilots"]]
    return {"variants":9,"copilots":5,"aggregate_rows":45,"seed_arms":225,
            "training_episodes":112500,"evaluation_episodes_replayed":count,
            "unique_training_cases":12500,"unique_evaluation_cases":5000,
            "all_three_frontier_parity":"PASS","fixed_B2":"PASS","paired_cases":"PASS",
            "frozen_evaluation_K":"PASS","Q_oracle_and_metric_replay":"PASS",
            "selection_starvation":"PASS"}


def summary(data):
    print("Variant                 DataOps  Trading    Purch      SOC      S2P")
    for variant in VARIANTS:
        values=[lookup(data,variant,c)["routing_mean"] for c in COPILOTS]
        print(f"{variant:<23} "+" ".join(f"{v:>7.1%}" for v in values))
    for r in data["comparisons"]:
        print(f"ALL-THREE vs {r['subset_or_comparator']}: >= {r['noninferior_count']}/5; "
              f"strict {len(r['strict_wins'])}, ties {len(r['ties'])}, losses {len(r['losses'])}")
    print("POST-2:",data["post2_verdict"])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only",action="store_true")
    args=parser.parse_args()
    export=json.loads((ROOT/"real_centroids_v1.json").read_text())["copilots"]
    frontier=json.loads(FRONTIER.read_text())
    if args.validate_only:
        data=json.loads(OUT.read_text())
        print(json.dumps(validate(data,export,frontier),indent=2))
        assert data["source_hashes_before"]==data["source_hashes_after"]==hashes()
        with CSV.open(newline="") as f:
            reader=csv.DictReader(f); actual=list(reader)
            assert reader.fieldnames==list(FIELDS) and len(actual)==45
        assert actual==[{k:str(v) for k,v in row.items()} for row in data["rows"]]
        summary(data)
        return
    for p in (OUT,CSV):
        if p.exists():
            raise FileExistsError(f"Refusing to overwrite {p}")
    before=hashes()
    data={"experiment":"VLD-Q-ABLATION","protocol":{
        "date":"2026-09-13","training_decisions":500,"evaluation_decisions":200,
        "seeds":list(base.SEEDS),"budget":2,"paired":True,
        "training":"Separate category-indexed K store per variant/copilot/seed; identical 500 pre-generated decisions",
        "K":"Initial .5; +.02/-.005 with production x2 correct informative flip bonus; bounds [.1,3]",
        "NO-K":"Effective Q uses K=1; shadow K still receives identical feedback for diagnostics and never affects selection",
        "RANDOM":"Fresh iid Uniform[0,1) per dimension per read; separate category RNG independent of scenario generation; K ignored",
        "evidence":"Full-coordinate synthetic reads, unchanged from budget frontier; labels affect feedback/measurement only",
        "routing_quality":"Informative reads / 400 held-out reads per seed; inherited labels can count unchanged coordinates informative",
        "starvation":"Mean fraction of category-dimension pairs with zero TRAIN selections; every selected pair receives an update",
        "legacy_unmoved_k_fraction":"Separate diagnostic: final learned/shadow K within 1e-9 of .5; not selection starvation",
        "scoring":"Unmodified production investigator scoring fallback as in budget frontier",
        "selection":"Compute three terms, zero excluded terms, sum in production order; Q recomputed after each read",
        "zero_Q":"No floors or fallback; assert positive selectable Q and exactly two reads in every episode",
        "precision_limit":"All exported sigma=1: precision=.01 constant across dimensions; cannot identify heterogeneous uncertainty effects",
        "uncertainty":"Sample SD over five seeds; descriptive paired t95 CI, no multiplicity correction",
        "delta_units":"CSV deltas in percentage points; routing, accuracy, starvation in fractions",
        "evidence_tier":"REAL_COMPONENT exported production geometry + SYNTHETIC decisions/verification",
        "contribution":"Ordered path PRECISION-ONLY -> PREC+DISC -> ALL-THREE; retrained K, order-dependent effects, not an independent causal decomposition",
        "interaction":"ALL-THREE - PREC+DISC - PREC+LEV + PRECISION-ONLY; descriptive conditional interaction",
        "post2":"Empirical hypothesis, not an integrity assertion; user >= comparison includes ties"},
        "source_hashes_before":before,"variants":[{"variant":v,"copilots":[]} for v in VARIANTS],
        "cohorts":{},"rows":[]}
    for name in COPILOTS:
        info=export[name]; prior=frontier["copilots"][name]
        data["cohorts"][name]=[]
        runs={v:[] for v in VARIANTS}
        for seed,cohort,old in zip(base.SEEDS,prior["cohorts"],prior["results"]["2"]["vld"]["seed_runs"]):
            plain=base.investigators(info)
            train=base.cases_for(info,plain,cohort["generator_seed"],500,1000000)
            evaluation=base.cases_for(info,plain,cohort["generator_seed"],200,9000000)
            assert base.digest([base.serialize_case(c) for c in train])==cohort["training_sha256"]
            assert base.digest([base.serialize_case(c) for c in evaluation])==cohort["evaluation_sha256"]
            data["cohorts"][name].append({**cohort,"training_categories":[c["category"] for c in train]})
            for variant in VARIANTS:
                invs=invs_for(info,variant,cohort["generator_seed"])
                run=base.run_arm(info,invs,train,evaluation,"vld",2,seed)
                if variant=="ALL-THREE":
                    assert run==old, "Production-form control must exactly reproduce the frontier"
                run["starvation"]=starvation(run,info)
                runs[variant].append(run)
            print(f"{name}: seed {seed}, all nine variants complete",flush=True)
        for variant in VARIANTS:
            row=aggregate(name,variant,runs[variant],runs["ALL-THREE"])
            next(v for v in data["variants"] if v["variant"]==variant)["copilots"].append(row)
    data["rows"]=[{k:r[k] for k in FIELDS} for v in data["variants"] for r in v["copilots"]]
    data["comparisons"]=comparisons(data)
    singles=data["comparisons"][:3]
    data["post2_verdict"]="PASS" if all(r["requested_4_of_5_gate"] for r in singles) else "NOT_MET"
    data["term_contribution"]=contribution(data)
    data["checks"]=validate(data,export,frontier)
    data["source_hashes_after"]=hashes()
    assert before==data["source_hashes_after"]
    text=json.dumps(data,indent=2,allow_nan=False)+"\n"
    buf=io.StringIO(newline=""); writer=csv.DictWriter(buf,fieldnames=FIELDS)
    writer.writeheader(); writer.writerows(data["rows"])
    with OUT.open("x",encoding="utf-8",newline="\n") as f: f.write(text)
    with CSV.open("x",encoding="utf-8",newline="") as f: f.write(buf.getvalue())
    summary(data)
    print(f"Saved {OUT}\nSaved {CSV}")


if __name__=="__main__":
    main()

