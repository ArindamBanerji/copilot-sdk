"""RAW, per-read Z-NORM and MINMAX Q ablations; fixed B2 and paired cohorts."""
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
import q_term_ablation as prior_code

base=prior_code.base
OUT=ROOT/"experiments/vld/q_term_ablation_normalized.json"
CSV=OUT.with_suffix(".csv")
PRIOR=ROOT/"experiments/vld/q_term_ablation.json"
NORMS=("RAW","Z-NORM","MINMAX")
VARIANTS=prior_code.VARIANTS[:7]
COPILOTS=prior_code.COPILOTS
CONFIGS=tuple((n,v) for n in NORMS for v in VARIANTS)+(("SHARED","RANDOM"),("SHARED","NO-K"))
FIELDS=("copilot","normalization","variant","routing_mean","routing_std",
        "accuracy_mean","accuracy_std","starvation","delta_vs_raw_all_three_routing")
INPUTS=base.CORE+("real_centroids_v1.json","scripts/k_learning_curve_experiment.py",
    "scripts/budget_accuracy_frontier.py","scripts/q_term_ablation.py",
    "experiments/vld/q_term_ablation.json","scripts/q_term_ablation_normalized.py")


def hashes():
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS}


def components(mu,sigma,v,p):
    a1,a2=np.argsort(p)[::-1][:2]
    raw=np.empty((3,mu.shape[1]))
    for d in range(mu.shape[1]):
        raw[0,d]=(1.0/max(float(sigma[d]**2),.001))/100.
        raw[1,d]=abs(float(mu[a1,d]-mu[a2,d]))
        raw[2,d]=abs(float((v[d]-mu[a1,d])**2-(v[d]-mu[a2,d])**2))
    return raw


def normalize(raw,available,normalization):
    """Compute moments over UNATTEMPTED dimensions only; population SD."""
    if normalization=="RAW":
        return raw.copy()
    output=np.zeros_like(raw)
    for j in range(3):
        values=raw[j,available]
        # Exact constants are mathematically zero under both transforms.
        # Prevent floating mean cancellation from creating artificial K ranking.
        if np.ptp(values)==0:
            continue
        if normalization=="Z-NORM":
            output[j,available]=(values-values.mean())/(values.std(ddof=0)+1e-10)
        elif normalization=="MINMAX":
            output[j,available]=(values-values.min())/(values.max()-values.min()+1e-10)
        else:
            raise ValueError(normalization)
    return output


def signed_q(mu,sigma,v,p,k,variant,normalization,available):
    raw=components(mu,sigma,v,p)
    transformed=normalize(raw,available,normalization)
    mask=prior_code.MASKS[prior_code.VARIANTS.index(variant)]
    # Left-to-right summation preserves raw production rounding.
    values=(transformed[0]*mask[0]+transformed[1]*mask[1]+transformed[2]*mask[2])*k
    return values,raw,transformed


class NormalizedInvestigator(prior_code.AblationInvestigator):
    def __init__(self,info,category,variant,routing_seed,normalization):
        super().__init__(info,category,variant,routing_seed)
        self.normalization=normalization

    def compute_Q(self,v,P,enriched_set=None,K_weights=None):
        if self.normalization in ("RAW","SHARED"):
            return super().compute_Q(v,P,enriched_set,K_weights)
        attempted=self.prior_attempts | set(enriched_set or ())
        available=np.array([d for d in range(len(self.factor_names)) if d not in attempted],dtype=int)
        assert len(available)>0
        k=np.ones(len(self.factor_names)) if K_weights is None else np.asarray(K_weights)
        weighted,_,_=signed_q(self.mu,self.sigma,np.asarray(v),np.asarray(P),k,
                              self.variant,self.normalization,available)
        assert np.all(np.isfinite(weighted[available]))
        chosen=int(available[np.argmax(weighted[available])])
        # The production loop treats max Q<=0 as a halt and uses -1 masking.
        # A selection-only proxy carries the exact signed-score argmax into the
        # unchanged loop. No score shift before K, clipping, or absolute value.
        proxy=np.full(len(self.factor_names),-1.)
        proxy[available]=0.
        proxy[chosen]=1.
        return proxy


def investigators(info,variant,seed,norm):
    return {c:NormalizedInvestigator(info,c,variant,seed+900000007+1009*i,norm)
            for i,c in enumerate(info["category_names"])}


def aggregate(name,norm,variant,runs,raw_control):
    common=prior_code.aggregate(name,variant,runs,raw_control)
    common["normalization"]=norm
    common["delta_vs_raw_all_three_routing"]=common.pop("delta_vs_all_three_routing")
    common["delta_vs_raw_all_three_accuracy"]=common.pop("delta_vs_all_three_accuracy")
    return common


def find(data,norm,variant,name):
    return next(r for r in data["results"] if
                (r["normalization"],r["variant"],r["copilot"])==(norm,variant,name))


def analysis_tables(data):
    summaries=[]
    for norm in NORMS:
        rows=[]
        for variant in VARIANTS:
            by_cop=[find(data,norm,variant,c) for c in COPILOTS]
            # Equal copilot weighting, then paired seed uncertainty.
            seed_means=[statistics.mean(r["seed_runs"][i]["metrics"]["routing_quality"]
                                         for r in by_cop) for i in range(5)]
            rows.append({"variant":variant,"routing_mean":statistics.mean(seed_means),
                         "routing_seed_std":statistics.stdev(seed_means),
                         "routing_paired_t95_ci":prior_code.ci(seed_means),
                         "per_seed_macro_routing":seed_means})
        ranked=sorted(rows,key=lambda r:(-r["routing_mean"],VARIANTS.index(r["variant"])))
        singles=sorted(rows[:3],key=lambda r:-r["routing_mean"])
        contrast={}
        for lhs,rhs in (("LEVERAGE-ONLY","DISCRIMINATIVE-ONLY"),("PREC+LEV","ALL-THREE")):
            per_cop=[]
            for name in COPILOTS:
                a,b=find(data,norm,lhs,name),find(data,norm,rhs,name)
                deltas=[100*(x["metrics"]["routing_quality"]-y["metrics"]["routing_quality"])
                        for x,y in zip(a["seed_runs"],b["seed_runs"])]
                per_cop.append({"copilot":name,"routing_delta_pp":statistics.mean(deltas),
                                "paired_t95_ci_pp":prior_code.ci(deltas),"per_seed_delta_pp":deltas})
            macro=[statistics.mean(r["per_seed_delta_pp"][i] for r in per_cop) for i in range(5)]
            contrast[lhs+" vs "+rhs]={"per_copilot":per_cop,
                "macro_routing_delta_pp":statistics.mean(macro),
                "macro_paired_t95_ci_pp":prior_code.ci(macro),
                "strict_wins":sum(r["routing_delta_pp"]>1e-12 for r in per_cop),
                "ties":sum(abs(r["routing_delta_pp"])<=1e-12 for r in per_cop)}
        summaries.append({"normalization":norm,"variants":rows,"ranking":ranked,
            "single_term_ranking":singles,"leverage_leads_single_terms":
                singles[0]["variant"]=="LEVERAGE-ONLY","contrasts":contrast})
    return summaries


def independent_replay(run,cohort,info,variant,norm):
    if norm in ("RAW","SHARED"):
        prior_code.verify_run(run,cohort,info,variant)
        return
    for row,case in zip(run["evaluation_rows"],cohort["evaluation_cases"]):
        assert row["case_id"]==case["id"] and row["category"]==case["category"]
        assert len(row["selected"])==row["reads"]==2 and len(set(row["selected"]))==2
        mu=np.asarray(info["all_category_mu"][case["category"]])
        sigma=np.asarray(info["sigma"])
        v=np.asarray(case["surface"]).copy()
        full=np.asarray(case["full"])
        k=np.asarray(run["k_by_category"][case["category"]])
        attempted=[]
        for chosen in row["selected"]:
            dist=np.sum((v-mu)**2/np.maximum(sigma**2,.001),axis=1)
            logits=-dist/info["tau"]; probabilities=np.exp(logits-logits.max())
            a1,a2=np.argsort(probabilities)[::-1][:2]
            raw=[1/(100*np.maximum(sigma**2,.001)),
                 np.abs(mu[a1]-mu[a2]),np.abs((v-mu[a1])**2-(v-mu[a2])**2)]
            available=[d for d in range(len(sigma)) if d not in attempted]
            normalized=[]
            for component in raw:
                values=[float(component[d]) for d in available]
                if max(values)==min(values):
                    normalized.append([0.]*len(values))
                elif norm=="Z-NORM":
                    m=statistics.mean(values)
                    sd=statistics.pstdev(values)
                    normalized.append([(x-m)/(sd+1e-10) for x in values])
                else:
                    lo,hi=min(values),max(values)
                    normalized.append([(x-lo)/(hi-lo+1e-10) for x in values])
            mask=prior_code.MASKS[prior_code.VARIANTS.index(variant)]
            weighted=[sum(normalized[j][i]*mask[j] for j in range(3))*k[d]
                      for i,d in enumerate(available)]
            predicted=available[max(range(len(available)),key=lambda i:weighted[i])]
            assert chosen==predicted,(norm,variant,chosen,predicted,weighted)
            v[chosen]=full[chosen]; attempted.append(chosen)
        action=int(np.argmin(np.sum((v-mu)**2/np.maximum(sigma**2,.001),axis=1)))
        oracle=int(np.argmin(np.sum((full-mu)**2/np.maximum(sigma**2,.001),axis=1)))
        assert row["final_action"]==action and row["oracle_action"]==oracle
        assert row["correct"]==(action==oracle)
        assert row["informative_reads"]==sum(d in case["informative"] for d in attempted)
    assert run["metrics"]==base.metrics(run["evaluation_rows"])
    assert run["starvation"]==prior_code.starvation(run,info)
    assert run["evaluation_frozen"]


def validate(data,export,prior):
    assert len(data["results"])==115
    actual={(r["normalization"],r["variant"],r["copilot"]) for r in data["results"]}
    assert actual=={(n,v,c) for n,v in CONFIGS for c in COPILOTS}
    count=0
    for row in data["results"]:
        n,v,c=row["normalization"],row["variant"],row["copilot"]
        assert len(row["seed_runs"])==5
        for i,(run,cohort) in enumerate(zip(row["seed_runs"],data["cohorts"][c])):
            assert len(run["evaluation_rows"])==200 and run["seed"]==cohort["seed"]
            independent_replay(run,cohort,export[c],v,n)
            if n in ("RAW","SHARED"):
                assert run==prior_code.lookup(prior,v,c)["seed_runs"][i]
            count+=200
        expected=aggregate(c,n,v,row["seed_runs"],find(data,"RAW","ALL-THREE",c)["seed_runs"])
        assert row==expected
    for norm in ("Z-NORM","MINMAX"):
        for c in COPILOTS:
            for a,b in (("DISCRIMINATIVE-ONLY","PREC+DISC"),
                        ("LEVERAGE-ONLY","PREC+LEV"),("DISC+LEV","ALL-THREE")):
                assert find(data,norm,a,c)["seed_runs"]==find(data,norm,b,c)["seed_runs"]
            p=find(data,norm,"PRECISION-ONLY",c)
            for run in p["seed_runs"]:
                assert all(r["selected"]==[0,1] for r in run["evaluation_rows"])
            assert abs(p["starvation"]-(1-2/len(export[c]["factor_names"])))<1e-12
    assert data["normalization_summary"]==analysis_tables(data)
    assert data["rows"]==[{k:r[k] for k in FIELDS} for r in data["results"]]
    return {"configurations":23,"copilots":5,"seed_cells":575,"aggregate_rows":115,
            "training_episodes":287500,"evaluation_episodes_replayed":count,
            "unique_training_cases":12500,"unique_evaluation_cases":5000,
            "all_RAW_and_shared_controls_exact_prior_match":"PASS",
            "fixed_B2_and_frozen_K":"PASS","unattempted_only_normalization":"PASS",
            "independent_score_and_selection_replay":"PASS",
            "constant_precision_zero_and_equivalent_variants":"PASS",
            "paired_cohort_hashes":"PASS"}


def representative(info,case,cohort):
    inv=base.VLDInvestigator(info["all_category_mu"][case["category"]],info["sigma"],
                             info["factor_names"],tau=info["tau"])
    raw=components(inv.mu,inv.sigma,case["surface"],inv.score(case["surface"])[1])
    return {"copilot":"dataops","seed_index":0,"seed":cohort["seed"],
        "generator_seed":cohort["generator_seed"],"training_decision_number":250,
        "within_decision_read_index":0,"case":base.serialize_case(case),
        "factor_names":info["factor_names"],"unattempted_dimensions":list(range(len(info["factor_names"]))),
        "raw_terms":dict(zip(("precision","discriminative","leverage"),raw.tolist())),
        "term_statistics":{name:{"min":float(a.min()),"max":float(a.max()),
                          "mean":float(a.mean()),"population_std":float(a.std())}
                          for name,a in zip(("precision","discriminative","leverage"),raw)},
        "scope":"One pre-read decision; descriptive example, not a scale estimate over all decisions"}


def print_summary(data):
    for n in data["normalization_summary"]:
        print("\n=== "+n["normalization"]+" ===")
        for r in n["ranking"]:
            print(f"  {r['variant']:<22} {r['routing_mean']:.2%}")
        print("Singles: "+" > ".join(f"{r['variant']} ({r['routing_mean']:.2%})"
                                      for r in n["single_term_ranking"]))
        for label,c in n["contrasts"].items():
            print(f"  {label}: macro delta {c['macro_routing_delta_pp']:+.2f}pp; "
                  f"strict wins {c['strict_wins']}/5")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only",action="store_true")
    args=parser.parse_args()
    export=json.loads((ROOT/"real_centroids_v1.json").read_text())["copilots"]
    prior=json.loads(PRIOR.read_text())
    if args.validate_only:
        data=json.loads(OUT.read_text())
        print(json.dumps(validate(data,export,prior),indent=2))
        assert data["source_hashes_before"]==data["source_hashes_after"]==hashes()
        with CSV.open(newline="") as f:
            reader=csv.DictReader(f); rows=list(reader)
            assert reader.fieldnames==list(FIELDS)
        assert rows==[{k:str(v) for k,v in r.items()} for r in data["rows"]]
        print_summary(data)
        return
    for p in (OUT,CSV):
        if p.exists(): raise FileExistsError(f"Refusing to overwrite {p}")
    before=hashes()
    data={"experiment":"VLD-Q-ABLATION-NORMALIZED","protocol":{
        "date":"2026-09-13","configurations":23,"training_decisions":500,
        "evaluation_decisions":200,"seeds":list(base.SEEDS),"budget":2,
        "normalizations":list(NORMS),"normalization_scope":"At every read, separately per term, over all and only unattempted dimensions; recomputed after updating v and a1/a2",
        "z":"(x-mean)/(population_std+1e-10), ddof=0",
        "minmax":"(x-min)/(max-min+1e-10)",
        "constant_terms":"Exactly constant arrays map exactly to zero, avoiding floating-point cancellation artifacts",
        "K":"Same per-variant training as raw ablation: .5 initial, [.1,3], +.02/-.005 and production x2 correct informative flip bonus",
        "operation_order":"Normalize each component, zero excluded components, sum, then multiply by learned K",
        "negative_Q":"Select argmax of signed weighted Q over unattempted dimensions; no clipping, abs, or shifting before K",
        "production_adapter":"Normalized arms pass a one-hot argmax selection proxy to unchanged investigator to bypass its nonpositive-Q halt and -1 mask; preserves ranking and fixed B2",
        "tie_breaking":"First unattempted dimension in factor order, including all-zero precision-only scores",
        "shared_controls":"SHARED RANDOM and NO-K retain the raw definitions and are each run once per copilot/seed; not duplicated in every normalization",
        "RANDOM":"Fresh independent uniform priorities per read; independent category RNG; shadow K ignored",
        "NO-K":"Raw three-term Q with effective K=1; shadow K updates ignored by selection",
        "pairing":"Same 500 training and 200 fresh evaluation cases as prior ablation across all 23 configs; separate learned K stores",
        "evidence":"Same full-coordinate synthetic provider, informative labels and production scorer fallback as prior ablation",
        "starvation":"Fraction of category-dimension pairs never selected during training; legacy unchanged-K fraction stored separately",
        "uncertainty":"Sample seed SD and descriptive paired t95 CI; macro summaries equally weight copilots",
        "units":"Routing, accuracy, starvation are fractions; CSV routing delta is percentage points versus RAW ALL-THREE",
        "precision_limit":"All sigma=1, so normalized precision is identically zero and its K-only ranking information is removed",
        "interpretation_limit":"Normalization changes both within-read rankings and the K feedback trajectory; z-score centering also changes signed K interactions. Ranking robustness does not by itself prove intrinsic information content or pure scale causation",
        "evidence_tier":"REAL_COMPONENT exported production geometry + SYNTHETIC decisions/verification"},
        "source_hashes_before":before,"results":[],"cohorts":prior["cohorts"],"rows":[]}
    for name in COPILOTS:
        info=export[name]; runs={config:[] for config in CONFIGS}
        for i,cohort in enumerate(prior["cohorts"][name]):
            plain=base.investigators(info)
            train=base.cases_for(info,plain,cohort["generator_seed"],500,1000000)
            evaluation=base.cases_for(info,plain,cohort["generator_seed"],200,9000000)
            assert base.digest([base.serialize_case(c) for c in train])==cohort["training_sha256"]
            assert base.digest([base.serialize_case(c) for c in evaluation])==cohort["evaluation_sha256"]
            if name=="dataops" and i==0:
                data["representative_decision"]=representative(info,train[249],cohort)
            for norm,variant in CONFIGS:
                invs=investigators(info,variant,cohort["generator_seed"],norm)
                run=base.run_arm(info,invs,train,evaluation,"vld",2,cohort["seed"])
                run["starvation"]=prior_code.starvation(run,info)
                if norm in ("RAW","SHARED"):
                    assert run==prior_code.lookup(prior,variant,name)["seed_runs"][i]
                runs[(norm,variant)].append(run)
            print(f"{name}: seed {cohort['seed']}, 23 configs complete",flush=True)
        for norm,variant in CONFIGS:
            data["results"].append(aggregate(name,norm,variant,runs[(norm,variant)],
                                             runs[("RAW","ALL-THREE")]))
    data["rows"]=[{k:r[k] for k in FIELDS} for r in data["results"]]
    data["normalization_summary"]=analysis_tables(data)
    data["checks"]=validate(data,export,prior)
    data["source_hashes_after"]=hashes()
    assert data["source_hashes_after"]==before
    text=json.dumps(data,indent=2,allow_nan=False)+"\n"
    buf=io.StringIO(newline=""); writer=csv.DictWriter(buf,fieldnames=FIELDS)
    writer.writeheader(); writer.writerows(data["rows"])
    with OUT.open("x",encoding="utf-8",newline="\n") as f: f.write(text)
    with CSV.open("x",encoding="utf-8",newline="") as f: f.write(buf.getvalue())
    print_summary(data)
    print(f"Saved {OUT}\nSaved {CSV}")


if __name__=="__main__":
    main()

