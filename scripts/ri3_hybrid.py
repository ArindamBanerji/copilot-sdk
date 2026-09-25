"""RI-3: epsilon and greedy-first/UCB-second exploration under B=2."""
import sys
sys.dont_write_bytecode=True
import ri1_routing_k_interaction as core
EPSILONS=(.05,.1,.2,.3)

def main():
    meta=core.protocol("RI-3",5); hashes=meta["source_hashes"]
    meta["epsilon_scope"]="independent draw at each read, including evaluation; random valid unattempted factor"
    meta["hybrid"]="first read greedy Q; second read RV-1 UCB c=1"
    results={}
    for copilot in core.COPILOTS:
        g=core.geometry(copilot)
        policies={"greedy":core.Policy(),
                  **{f"epsilon_{e:g}":core.Policy(exploration="epsilon",epsilon=e) for e in EPSILONS},
                  "greedy_then_explore":core.Policy(exploration="hybrid")}
        runs={k:[] for k in policies}
        for seed in core.SEEDS[:5]:
            data=core.prepare(g,seed)
            for key,policy in policies.items():
                runs[key].append(core.run_arm(g,data,seed,policy))
        rows={k:core.aggregate(v) for k,v in runs.items()}
        for key,value in rows.items():
            value["routing_delta_vs_greedy"]=core.paired(value,rows["greedy"])
            value["accuracy_delta_vs_greedy"]=core.paired(value,rows["greedy"],"accuracy")
            value["meets_ri2_tradeoff"]=value["starvation"]<=.10+1e-12 and value["routing_delta_vs_greedy"]["mean"]>=-.02-1e-12
        results[copilot]=rows
        print("RI-3",copilot,[(k,round(v["final_routing_mean"],3),round(v["starvation"],3)) for k,v in rows.items()],flush=True)
    core.save("ri3_hybrid.json",{"protocol":meta,"results":results},hashes)
if __name__=="__main__": main()

