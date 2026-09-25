"""RI-2: RV-1 UCB bonus sweep, matched greedy controls, all five geometries."""
import sys
sys.dont_write_bytecode=True
import ri1_routing_k_interaction as core

CS=(.1,.25,.5,.75,1.0)

def main():
    meta=core.protocol("RI-2",5); hashes=meta["source_hashes"]
    meta["ucb"]="Q + c*sigma/sqrt(training_attempts+1), RV-1 definition (no log-time term)"
    meta["criterion"]="lowest c with mean starvation <=.10 and mean routing delta >=-.02"
    results={}; frontiers={}
    for copilot in core.COPILOTS:
        g=core.geometry(copilot)
        runs={"greedy":[] ,**{f"ucb_{c:g}":[] for c in CS}}
        for seed in core.SEEDS[:5]:
            data=core.prepare(g,seed)
            runs["greedy"].append(core.run_arm(g,data,seed,core.Policy()))
            for c in CS:
                runs[f"ucb_{c:g}"].append(core.run_arm(g,data,seed,core.Policy(exploration="ucb",c=c)))
        rows={k:core.aggregate(v) for k,v in runs.items()}
        for c in CS:
            name=f"ucb_{c:g}"
            rows[name]["c"]=c
            rows[name]["routing_delta_vs_greedy"]=core.paired(rows[name],rows["greedy"])
            rows[name]["accuracy_delta_vs_greedy"]=core.paired(rows[name],rows["greedy"],"accuracy")
            rows[name]["meets_criterion"]=rows[name]["starvation"]<=.10+1e-12 and rows[name]["routing_delta_vs_greedy"]["mean"]>=-.02-1e-12
        eligible=[c for c in CS if rows[f"ucb_{c:g}"]["meets_criterion"]]
        frontier=[]
        for c in CS:
            r=rows[f"ucb_{c:g}"]
            dominated=any(
                rows[f"ucb_{j:g}"]["starvation"] <= r["starvation"] and
                rows[f"ucb_{j:g}"]["final_routing_mean"] >= r["final_routing_mean"] and
                (rows[f"ucb_{j:g}"]["starvation"] < r["starvation"] or rows[f"ucb_{j:g}"]["final_routing_mean"] > r["final_routing_mean"])
                for j in CS if j!=c)
            if not dominated: frontier.append(c)
        frontiers[copilot]={"best_c":min(eligible) if eligible else None,
                            "pareto_c":frontier,"eligible_c":eligible,
                            "selection_basis":"point estimates; inspect paired intervals before deployment"}
        results[copilot]=rows
        print("RI-2",copilot,frontiers[copilot],flush=True)
    core.save("ri2_ucb_sweep.json",{"protocol":meta,"results":results,"pareto_frontier":frontiers},hashes)

if __name__=="__main__": main()

