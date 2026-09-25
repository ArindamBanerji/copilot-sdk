"""KE-5: canonical calibration status gates K updates; frozen geometry in both arms."""
import os
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import numpy as np
import ri1_routing_k_interaction as core

GAE=Path(os.environ.get("CLAUDE_GAE",str(core.ROOT.parent/"graph-attention-engine-v50")))
calibration=core.module_from_file("group_ad_calibration",GAE/"gae/calibration.py")

def gate(n,correct,categories_seen,total_categories):
    result=calibration.conservation_status(
        verified_count=n,correct_count=correct,total_decisions=n,penalty_ratio=10,
        categories_with_data=categories_seen,total_categories=total_categories)
    alpha=categories_seen/total_categories
    theta=calibration.compute_theta_min(alpha,n)
    return {"alpha":alpha,"q":correct/n,"V":n,"theta_min":theta,
            "signal":alpha*(correct/n)*n,"status":result.status,"penalty_ratio":10}

def dips(run,longitudinal=False):
    rows=run["checkpoints"]
    field=lambda x:x["longitudinal"]["routing_quality"] if longitudinal else x["routing_quality"]
    return {str(n):max(0.,field(rows[n//50-2])-field(rows[n//50-1])) for n in (350,450)}

def main():
    meta=core.protocol("KE-5",5); hashes=meta["source_hashes"]
    meta["conservation"]={
        "implementation":str(GAE/"gae/calibration.py"),"sha256":core.digest(GAE/"gae/calibration.py"),
        "theta_min":"23.53/(alpha*V)","signal":"alpha*q*V",
        "alpha":"categories with >=1 verified outcome / total categories",
        "q":"cumulative correct/verified","V":"all verified training decisions, including blocked K updates",
        "GREEN":"signal >= 2*theta_min","AMBER":"theta_min <= signal < 2*theta_min","RED":"signal < theta_min",
        "penalty_ratio":10,"penalty_effect":"canonical conservation_status accepts but does not use penalty_ratio in threshold/status",
        "bootstrap":"no bypass: evaluate canonical status after every verification as requested",
        "gate_scope":"K update only; no scenario withholding, scoring changes, or action execution"}
    meta["longitudinal_control"]="supplemental same N=0 cohort of 50 cases at every checkpoint; primary eval remains fresh 50"
    meta["helps_criterion"]="positive mean reduction of downward steps at N350/N450; absence in both arms is not prevention"
    meta["costs_criterion"]="relative final-routing loss >=5%; absolute percentage-point loss also reported"
    g=core.geometry("dataops"); arms={"without_conservation":[],"with_conservation":[]}
    for seed in core.SEEDS[:5]:
        data=core.prepare(g,seed)
        arms["without_conservation"].append(core.run_arm(g,data,seed,core.Policy(),longitudinal=True))
        arms["with_conservation"].append(core.run_arm(g,data,seed,core.Policy(conservation=True),gate=gate,longitudinal=True))
        print("KE-5 seed",seed,"blocked decisions",arms["with_conservation"][-1]["blocked_decisions"],flush=True)
    results={k:core.aggregate(v) for k,v in arms.items()}
    summary={}
    for name,runs in arms.items():
        summary[name]={"dips":{str(n):float(np.mean([dips(r)[str(n)] for r in runs])) for n in (350,450)},
                       "longitudinal_dips":{str(n):float(np.mean([dips(r,True)[str(n)] for r in runs])) for n in (350,450)},
                       "blocked_decisions_mean":float(np.mean([r["blocked_decisions"] for r in runs])),
                       "blocked_updates_mean":float(np.mean([r["blocked_updates"] for r in runs]))}
    control,treated=results["without_conservation"],results["with_conservation"]
    loss=control["final_routing_mean"]-treated["final_routing_mean"]
    relative=loss/control["final_routing_mean"]
    reductions={k:{str(n):summary["without_conservation"][k][str(n)]-summary["with_conservation"][k][str(n)]
                   for n in (350,450)} for k in ("dips","longitudinal_dips")}
    summary.update({"routing_delta":core.paired(treated,control),"final_routing_loss":loss,
                    "final_routing_relative_loss":relative,"dip_reductions":reductions,
                    "helps":np.mean(list(reductions["dips"].values())).item()>1e-12,
                    "longitudinal_helps":np.mean(list(reductions["longitudinal_dips"].values())).item()>1e-12,
                    "costs":relative>=.05-1e-12,"costs_5pp":loss>=.05-1e-12})
    assert core.digest(GAE/"gae/calibration.py")==meta["conservation"]["sha256"]
    core.save("ke5_conservation_interaction.json",{"protocol":meta,"results":results,"summary":summary},hashes)
if __name__=="__main__": main()

