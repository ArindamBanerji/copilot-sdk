"""KE-4: matched learned/fixed K controls for each training/evaluation distribution."""
import sys
sys.dont_write_bytecode=True
import ri1_routing_k_interaction as core
DISTRIBUTIONS=("uniform","clustered","adversarial")

def main():
    meta=core.protocol("KE-4",5); hashes=meta["source_hashes"]
    meta["distributions"]={
        "uniform":"existing centroid-corruption generator, uniform category/action choices",
        "clustered":"60% chooses first two categories, 40% chooses all six uniformly; expected 73.33% in first two",
        "adversarial":"exact midpoint of closest weighted centroid pair, random endpoint truth; top-two distance gap asserted <1e-10"}
    meta["evaluation_distribution"]="same distribution as training, matched learned/fixed cohorts"
    meta["criterion"]="ROBUST if all mean deltas >0 and zero learning-arm hurts across all checkpoints; FRAGILE if adversarial delta <=0; else DISTRIBUTION_DEPENDENT"
    results={};summary={}
    g=core.geometry("dataops")
    for dist in DISTRIBUTIONS:
        learned=[];fixed=[]
        for seed in core.SEEDS[:5]:
            data=core.prepare(g,seed,dist)
            learned.append(core.run_arm(g,data,seed,core.Policy()))
            fixed.append(core.run_arm(g,data,seed,core.Policy(learning=False)))
        la,fa=core.aggregate(learned),core.aggregate(fixed)
        delta=core.paired(la,fa)
        results[dist]={"learning":la,"fixed":fa,"routing_delta":delta}
        summary[dist]={"routing_delta":delta["mean"],"routing_delta_ci95":delta["ci95"],
                       "relative_routing_delta":delta["mean"]/fa["final_routing_mean"] if fa["final_routing_mean"] else None,
                       "final_routing_quality":la["final_routing_mean"],"final_accuracy":la["final_accuracy_mean"],
                       "starvation":la["starvation"],"hurts":la["hurts"],"hurts_all_checkpoints":la["hurts_all_checkpoints"]}
        print("KE-4",dist,summary[dist],flush=True)
    robust=all(x["routing_delta"]>0 and x["hurts_all_checkpoints"]==0 for x in summary.values())
    verdict="ROBUST" if robust else "FRAGILE" if summary["adversarial"]["routing_delta"]<=0 else "DISTRIBUTION_DEPENDENT"
    core.save("ke4_distribution_sensitivity.json",{"protocol":meta,"results":results,"summary":summary,"verdict":verdict},hashes)
if __name__=="__main__": main()

