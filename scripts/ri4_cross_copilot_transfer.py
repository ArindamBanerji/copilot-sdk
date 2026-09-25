"""RI-4: exact-name K transfer. Empty overlap remains an explicit null intervention."""
import sys
sys.dont_write_bytecode=True
import numpy as np
import ri1_routing_k_interaction as core

PAIRS=(("soc","s2p"),("s2p","soc"),("dataops","trading"))

def transfer_weights(source_g,target_g,source_run):
    overlaps=sorted(set(source_g["factors"]) & set(target_g["factors"]))
    pooled=np.mean([source_run["final_k"][c] for c in source_g["categories"]],axis=0)
    target={c:np.full(len(target_g["factors"]),.5) for c in target_g["categories"]}
    for factor in overlaps:
        for c in target:
            target[c][target_g["factors"].index(factor)]=pooled[source_g["factors"].index(factor)]
    return overlaps,target

def main():
    meta=core.protocol("RI-4",5); hashes=meta["source_hashes"]
    meta["transfer"]="exact factor-name equality only; source-category mean for shared factors broadcast to target categories; unmatched .5"
    meta["criterion"]="warm/cold decisions <=.70 at common target=90% cold N400/450/500 mean"
    meta["source_training_cost"]="500 donor decisions per seed, reported separately, not hidden in target speedup"
    results={}
    for source,target in PAIRS:
        sg,tg=core.geometry(source),core.geometry(target)
        donor_runs=[]; cold=[]; warm=[]; speed=[]
        for seed in core.SEEDS[:5]:
            donor=core.run_arm(sg,core.prepare(sg,seed),seed,core.Policy())
            donor_runs.append(donor)
            overlap,initial=transfer_weights(sg,tg,donor)
            data=core.prepare(tg,seed)
            cr=core.run_arm(tg,data,seed,core.Policy())
            wr=core.run_arm(tg,data,seed,core.Policy(),initial=initial)
            cold.append(cr);warm.append(wr)
            threshold=.9*float(np.mean([p["routing_quality"] for p in cr["checkpoints"][-3:]]))
            ct=core.time_to_target(cr,threshold);wt=core.time_to_target(wr,threshold)
            ratio=wt/ct if ct is not None and ct>0 and wt is not None else None
            speed.append({"seed":seed,"target":threshold,"cold_decisions":ct,"warm_decisions":wt,
                          "warm_cold_ratio":ratio,"acceleration":None if ratio is None else 1-ratio,
                          "keep":bool(overlap and ratio is not None and ratio<=.70),
                          "censored":ct is None or wt is None,
                          "baseline_already_above_target":ct==0})
            if not overlap:
                assert cr["final_k"]==wr["final_k"] and cr["attempt_counts"]==wr["attempt_counts"]
                assert all(a["routing_quality"]==b["routing_quality"] and a["accuracy"]==b["accuracy"]
                           for a,b in zip(cr["checkpoints"],wr["checkpoints"]))
        ca,wa=core.aggregate(cold),core.aggregate(warm)
        ratios=[x["warm_cold_ratio"] for x in speed if x["warm_cold_ratio"] is not None]
        ratio=float(np.mean(ratios)) if ratios else None
        results[f"{source}_to_{target}"]={
            "source":source,"target":target,"overlap_factors":overlap,"overlap_count":len(overlap),
            "target_overlap_fraction":len(overlap)/len(tg["factors"]),
            "source_factor_names":sg["factors"],"target_factor_names":tg["factors"],
            "source_training":core.aggregate(donor_runs),"cold":ca,"warm":wa,"per_seed_speed":speed,
            "mean_warm_cold_ratio":ratio,"mean_speedup":None if ratio is None else 1-ratio,
            "routing_delta":core.paired(wa,ca),
            "keep":bool(overlap and ratio is not None and ratio<=.70),
            "l4_evidence":"NOT TESTABLE: zero exact overlap; identical initialization" if not overlap else "KEEP" if ratio is not None and ratio<=.70 else "NOT SUPPORTED"}
        print("RI-4",source,"->",target,"overlap",overlap,"ratio",ratio,flush=True)
    core.save("ri4_cross_copilot_transfer.json",{"protocol":meta,"results":results},hashes)
if __name__=="__main__": main()

