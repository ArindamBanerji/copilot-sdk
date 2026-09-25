"""Group A/D: reproducible charts and report from six measured experiment outputs."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments/vld"
CHARTS=OUT/"charts"
FILES=dict(ri1="ri1_routing_k_interaction.json",ri2="ri2_ucb_sweep.json",ri3="ri3_hybrid.json",ri4="ri4_cross_copilot_transfer.json",ke4="ke4_distribution_sensitivity.json",ke5="ke5_conservation_interaction.json")
COPS=("dataops","trading","purchasing","soc","s2p")
VARS=("static","rnn","gru","lstm")
CS=(.1,.25,.5,.75,1.)
COL=["#2369bd","#d97919","#28936e","#9258ae","#d04a55","#567885"]
CHART_MAP={}
plt.rcParams.update({"figure.facecolor":"#f7f9fc","axes.facecolor":"white","savefig.facecolor":"#f7f9fc","axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"axes.axisbelow":True,"grid.alpha":.18,"font.family":"DejaVu Sans","font.size":11,"axes.titlesize":13,"savefig.dpi":160})
def pct(x):return "n/a" if x is None else f"{100*x:.1f}%"
def pp(x):return f"{100*x:+.1f} pp"
def ci(x):return f"{pp(x['mean'])} [{100*x['ci95'][0]:+.1f}, {100*x['ci95'][1]:+.1f}]"
def save(fig,name):
    path=CHARTS/name
    if path.exists():path=path.with_name(path.stem+"_group_a_d.png")
    if path.exists():raise FileExistsError(path)
    fig.savefig(path,bbox_inches="tight");plt.close(fig)
    CHART_MAP[name]=path.relative_to(OUT).as_posix()
def line(ax,r,label,color,field="routing_mean",ls="-"):
    points=r["checkpoints"];x=[p["decision_count"] for p in points];y=np.array([p[field] for p in points])
    ax.plot(x,y,label=label,color=color,lw=2,marker="o",ms=3,ls=ls)
    if field=="routing_mean":
        e=np.array([p["routing_std"] for p in points]);ax.fill_between(x,np.clip(y-e,0,1),np.clip(y+e,0,1),color=color,alpha=.1)
    ax.set_xlabel("Verified decisions");ax.yaxis.set_major_formatter(PercentFormatter(1))
def render_ucb_pareto(d):
    from matplotlib.lines import Line2D
    fig,(ax,key)=plt.subplots(1,2,figsize=(11,6.3),gridspec_kw={"width_ratios":[4,1]},layout="constrained")
    markers=("o","s","^","D","X")
    for i,cop in enumerate(COPS):
        rows=[d["ri2"]["results"][cop][f"ucb_{c:g}"] for c in CS]
        x=[100*r["starvation"] for r in rows];y=[100*r["routing_delta_vs_greedy"]["mean"] for r in rows]
        ax.plot(x,y,color=COL[i],alpha=.7,lw=1.5)
        for j,(xx,yy) in enumerate(zip(x,y)):
            ax.scatter(xx,yy,color=COL[i],marker=markers[j],s=65,edgecolors="white",linewidths=.5,zorder=3)
    ax.axvline(10,color="#555",ls="--",lw=1);ax.axhline(-2,color="#555",ls="--",lw=1)
    ax.set_xlabel("Unvisited category-factor pairs (%)");ax.set_ylabel("Routing vs greedy (pp)")
    ax.set_title("RI-2 | UCB trade-off");key.axis("off")
    domain=key.legend([Line2D([0],[0],color=COL[i],lw=2) for i in range(5)],
                      ["DataOps","Trading","Purchasing","SOC","S2P"],title="Copilot",loc="upper left",frameon=False)
    key.add_artist(domain)
    key.legend([Line2D([0],[0],color="#556",marker=m,lw=0,ms=8) for m in markers],
               [f"c = {c:g}" for c in CS],title="UCB bonus",loc="lower left",frameon=False)
    save(fig,"pub_ri2_ucb_pareto.png")

def render(d):
    r=d["ri1"]["results"]
    a=np.array([[r[v+"_"+k]["final_routing_mean"] for k in ("fixed","learning")] for v in VARS])
    fig,ax=plt.subplots(figsize=(7.4,5.2),layout="constrained")
    im=ax.imshow(a,cmap="Blues",vmin=.4,vmax=.65,aspect="auto")
    for i in range(4):
        for j in range(2):ax.text(j,i,pct(a[i,j]),ha="center",va="center",color="white" if a[i,j]>.56 else "#123",fontsize=15)
    ax.set_xticks([0,1],["Fixed K","Learned K"]);ax.set_yticks(range(4),[v.upper() for v in VARS]);ax.grid(False)
    ax.set_title("RI-1 | Routing x K");fig.colorbar(im,ax=ax,label="Routing quality",format=PercentFormatter(1))
    save(fig,"pub_ri1_interaction_heatmap.png")
    fig,ax=plt.subplots(figsize=(9,5.2),layout="constrained")
    for i,v in enumerate(VARS):
        ax.bar(np.array([0,1])+(i-1.5)*.18,[r[v+"_"+k]["final_routing_mean"] for k in ("fixed","learning")],width=.17,yerr=[r[v+"_"+k]["final_routing_std"] for k in ("fixed","learning")],color=COL[i],label=v.upper(),capsize=3)
    ax.set_xticks([0,1],["Fixed K","Learned K"]);ax.set_ylim(0,.8);ax.set_ylabel("Routing quality");ax.yaxis.set_major_formatter(PercentFormatter(1));ax.legend(ncol=4);ax.set_title("RI-1 | Ranking comparison")
    save(fig,"pub_ri1_ranking_comparison.png")
    fig,ax=plt.subplots(figsize=(8,4.8),layout="constrained")
    lifts=[d["ri1"]["interaction_effect"][v+"_k_lift_paired"] for v in VARS]
    ax.bar([v.upper() for v in VARS],[100*x["mean"] for x in lifts],color=COL[:4],yerr=[[100*(x["mean"]-x["ci95"][0]) for x in lifts],[100*(x["ci95"][1]-x["mean"]) for x in lifts]],capsize=4)
    ax.set_ylabel("K lift (pp)");ax.set_title("RI-1 | K lift, paired 95% CI");save(fig,"pub_ri1_k_lift.png")
    render_ucb_pareto(d)
    for exp,name in (("ri2","pub_ri2_ucb_sweep_by_copilot.png"),("ri3","pub_ri3_hybrid_comparison.png")):
        fig,axes=plt.subplots(2,3,figsize=(13,7.2),layout="constrained")
        for ax,cop in zip(axes.flat,COPS):
            if exp=="ri2":
                rows=[d[exp]["results"][cop][f"ucb_{c:g}"] for c in CS];xs=list(CS);labels=[str(c) for c in CS]
            else:
                keys=["greedy","epsilon_0.05","epsilon_0.1","epsilon_0.2","epsilon_0.3","greedy_then_explore"]
                rows=[d[exp]["results"][cop][k] for k in keys];xs=list(range(6));labels=["Greedy","e=.05","e=.10","e=.20","e=.30","G/UCB"]
            ax.plot(xs,[100*r["final_routing_mean"] for r in rows],"o-",label="Routing",color=COL[0])
            ax.plot(xs,[100*r["starvation"] for r in rows],"s-",label="Starvation",color=COL[1])
            if exp=="ri2":ax.axhline(100*d[exp]["results"][cop]["greedy"]["final_routing_mean"],color=COL[0],ls="--",label="Greedy routing")
            ax.set_xticks(xs,labels,rotation=35 if exp=="ri3" else 0,ha="right" if exp=="ri3" else "center")
            ax.set_title(cop.title());ax.set_ylabel("%");ax.set_ylim(-3,105)
            if exp=="ri2":ax.set_xlabel("UCB c")
        axes.flat[-1].axis("off");axes.flat[-1].legend(*axes.flat[0].get_legend_handles_labels(),loc="center",frameon=False)
        fig.suptitle("RI-2 | UCB sweep" if exp=="ri2" else "RI-3 | Hybrid comparison");save(fig,name)
    pairs=list(d["ri4"]["results"].values());labels=[r["source"].upper()+" -> "+r["target"].upper() for r in pairs]
    fig,ax=plt.subplots(figsize=(9,5.2),layout="constrained");xx=np.arange(3)
    for j,arm in enumerate(("cold","warm")):
        vals=[np.mean([x[arm+"_decisions"] for x in r["per_seed_speed"] if x[arm+"_decisions"] is not None]) for r in pairs]
        ax.bar(xx+(-.18 if j==0 else .18),vals,.35,label=arm.title(),color=COL[j])
    ax.set_xticks(xx,labels);ax.set_ylabel("Target decisions");ax.legend();ax.set_title("RI-4 | Cold-target 90% crossing")
    save(fig,"pub_ri4_transfer_speedup.png")
    fig,ax=plt.subplots(figsize=(8.5,5.2),layout="constrained")
    for i,r in enumerate(pairs):ax.scatter(100*r["target_overlap_fraction"],100*(r["mean_speedup"] or 0),s=90+45*i,facecolors="none",edgecolors=COL[i],label=labels[i])
    ax.axhline(30,color="#777",ls="--",label="Keep threshold");ax.set_xlim(-5,100);ax.set_ylim(-5,40)
    ax.set_xlabel("Target factor overlap (%)");ax.set_ylabel("Target acceleration (%)");ax.set_title("RI-4 | Exact-name transfer");ax.legend(loc="upper right");ax.annotate("3 coincident null transfers",(0,0),xytext=(15,10),textcoords="offset points")
    save(fig,"pub_ri4_transfer_overlap.png")
    fig,axes=plt.subplots(1,3,figsize=(13,4.8),layout="constrained",sharey=True)
    for i,(ax,dist) in enumerate(zip(axes,("uniform","clustered","adversarial"))):
        line(ax,d["ke4"]["results"][dist]["learning"],"Learned K",COL[i]);line(ax,d["ke4"]["results"][dist]["fixed"],"Fixed K","#697687",ls="--")
        ax.set_title(dist.title());ax.set_ylim(.2,1.05)
    axes[0].set_ylabel("Routing quality");axes[-1].legend(loc="lower right");fig.suptitle("KE-4 | Distribution robustness");save(fig,"pub_ke4_distribution_robustness.png")
    fig,ax=plt.subplots(figsize=(9,5.2),layout="constrained");ds=list(d["ke4"]["summary"]);xx=np.arange(3)
    for i,(field,label) in enumerate((("final_routing_quality","Routing"),("starvation","Starvation"))):ax.bar(xx+(-.18 if i==0 else .18),[100*d["ke4"]["summary"][s][field] for s in ds],.35,label=label,color=COL[i])
    ax.set_xticks(xx,[s.title() for s in ds]);ax.set_ylabel("%");ax.legend();ax.set_title("KE-4 | Final quality and coverage");save(fig,"pub_ke4_final_comparison.png")
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout="constrained")
    for i,(key,label) in enumerate((("without_conservation","Ungated"),("with_conservation","Gated"))):
        line(axes[0],d["ke5"]["results"][key],label,COL[i]);line(axes[1],d["ke5"]["results"][key],label,COL[i],field="longitudinal_routing_mean")
    for ax,title in zip(axes,("Fresh checkpoint cohorts","Fixed diagnostic cohort")):
        ax.set_title(title);ax.set_ylabel("Routing quality");ax.legend()
        for n in (350,450):ax.axvline(n,color="#777",ls=":",lw=1)
    fig.suptitle("KE-5 | Conservation curves");save(fig,"pub_ke5_conservation_curves.png")
    fig,ax=plt.subplots(figsize=(8,5),layout="constrained");points=d["ke5"]["results"]["with_conservation"]["checkpoints"];xx=[p["decision_count"] for p in points]
    ax.plot(xx,[p["blocked_updates_mean"] for p in points],"o-",color=COL[0],label="Factor updates");ax.plot(xx,[p["blocked_decisions_mean"] for p in points],"s--",color=COL[1],label="Decisions")
    ax.set_xlabel("Verified decisions");ax.set_ylabel("Cumulative blocked");ax.set_title("KE-5 | Blocked K updates");ax.legend();save(fig,"pub_ke5_blocked_updates.png")


def report(d):
    r=d["ri1"]["results"];inter=d["ri1"]["interaction_effect"]
    L=["# Group A/D: Routing, K Learning, Transfer and Robustness","",
       "**Date:** September 13, 2026. **Evidence:** exported production centroids with synthetic, oracle-labeled scenarios. No live endpoint, application database, external provider, or customer outcome experiment.","",
       "All six experiments completed. Static+K leads DataOps routing; RNN+K leads task accuracy by point estimate. No transfer pair shares an exact factor name. Distribution and conservation verdicts below follow their pre-registered criteria.","",
       "## 1. RI-1 — Routing × K Interaction","",
       "**Protocol correction:** RV-0's published headline already used K learning. Its learned/fixed evaluations consumed different cases. This experiment explicitly trains all eight cells and evaluates paired cohorts.","",
       "500 decisions per cell/seed, 10 checkpoints, 50 fresh held-out cases/checkpoint, B=2, 10 seeds. K starts at 0.5, updates +0.02/-0.005, and is clipped to [0.1,3.0]. No doubled reward for action flips; that differs from KUtilityStore's optional flip behavior. Fixed K stays at 0.5. GRU/LSTM use the unchanged hand-set RV-0 gates, not trained neural networks.","",
       "| Variant | Fixed K routing | Learned K routing | K lift (paired 95% CI) | Fixed / learned accuracy | Fixed / learned selection starvation |",
       "|---|---:|---:|---:|---:|---:|"]
    for v in VARS:
        f,a=r[v+"_fixed"],r[v+"_learning"]
        L.append(f"| {v.upper()} | {pct(f['final_routing_mean'])} ± {pct(f['final_routing_std'])} | {pct(a['final_routing_mean'])} ± {pct(a['final_routing_std'])} | {ci(inter[v+'_k_lift_paired'])} | {pct(f['final_accuracy_mean'])} / {pct(a['final_accuracy_mean'])} | {pct(f['starvation'])} / {pct(a['starvation'])} |")
    L += ["",f"**Ranking flip: {inter['ranking_changed']}.** Fixed: {' > '.join(inter['ranking_fixed'])}. Learned: {' > '.join(inter['ranking_learning'])}.","",
          f"Static−RNN with K: routing {ci(inter['static_minus_rnn_learning'])}; accuracy {ci(inter['static_minus_rnn_accuracy_learning'])}. Routing difference-in-differences: {ci(inter['static_vs_rnn_difference_in_differences'])}.",
          "","**Paper verdict:** recommend Static+K as the routing-efficiency baseline on this DataOps benchmark. Retain RNN+K as the accuracy comparator; do not call Static universally better. Static computes Q once and uses two policy scorer calls; recurrent variants compute Q twice and use three. These are actual calls in the new harness; RV-0's 3/4 accounting included extra nominal calls.",
          "","Fixed K has 100% update starvation by design; the table reports selection starvation. Final hurts are measured. Sample SD is across seeds, and paired t-intervals are unadjusted exploratory comparisons.",
          "",f"![RI-1 heatmap]({CHART_MAP['pub_ri1_interaction_heatmap.png']})",
          "","## 2. RI-2 — UCB Sweep","",
          "Five seeds per copilot/coefficient with matched greedy controls. UCB is the RV-1 bonus Q + c·σ/√(attempts+1), not conventional log-time UCB. Evaluation retains exploration using frozen training counts. Best c is the lowest tested c with mean starvation ≤10% and mean routing loss ≤2 pp.",
          "","| Copilot | c | Routing | Starvation | Routing vs greedy (95% CI) | Pass |","|---|---:|---:|---:|---:|---|"]
    for cop in COPS:
        for c in CS:
            x=d["ri2"]["results"][cop][f"ucb_{c:g}"]
            L.append(f"| {cop} | {c:g} | {pct(x['final_routing_mean'])} | {pct(x['starvation'])} | {ci(x['routing_delta_vs_greedy'])} | {'YES' if x['meets_criterion'] else 'NO'} |")
    L += ["","| Copilot | Lowest qualifying c | Non-dominated c values |","|---|---:|---|"]
    for cop,f in d["ri2"]["pareto_frontier"].items():
        L.append(f"| {cop} | {f['best_c'] if f['best_c'] is not None else 'None'} | {', '.join(str(x) for x in f['pareto_c'])} |")
    L += ["","These are point-estimate selections from a five-seed sweep, not a held-out hyperparameter certification. Trading has no c meeting both constraints. Paired intervals and accuracy deltas remain available in JSON.",
          "",f"![UCB trade-off]({CHART_MAP['pub_ri2_ucb_pareto.png']})",
          "","## 3. RI-3 — Hybrid Strategies","",
          "Independent ε draws at each read; random choice among valid unattempted factors. Greedy-then-explore uses greedy Q first and UCB c=1 second. Five seeds, 500 decisions, ten 50-case evaluations, with the same paired greedy cohorts as RI-2.",
          "","| Copilot | Strategy | Routing | Accuracy | Starvation | Routing vs greedy | ≤10% / ≤2 pp |","|---|---|---:|---:|---:|---:|---|"]
    for cop in COPS:
        for key,x in d["ri3"]["results"][cop].items():
            L.append(f"| {cop} | {key} | {pct(x['final_routing_mean'])} | {pct(x['final_accuracy_mean'])} | {pct(x['starvation'])} | {pp(x['routing_delta_vs_greedy']['mean'])} | {'YES' if x['meets_ri2_tradeoff'] else 'NO'} |")
    L += ["","Greedy-first guarantees a greedy first choice, not an optimal B=2 allocation. The hybrid clears starvation but Trading loses routing quality beyond the threshold; ε=0.05 preserves more quality but leaves 18% starvation. No tested Trading policy satisfies both constraints.",
          "",f"![Hybrid comparison]({CHART_MAP['pub_ri3_hybrid_comparison.png']})",
          "","## 4. RI-4 — Cross-Copilot Transfer","",
          "Each donor trains for 500 decisions/seed. Cold and warm target arms then train for 500 decisions each; five seeds/pair. Exact factor names only; if shared factors existed, their donor-category mean K would initialize every target category. Unmatched factors default to 0.5.",
          "","The common target is 90% of each cold run's mean routing at N=400/450/500, an observed-tail proxy rather than a proven asymptote. Crossing is measured at N=0 and 50-decision checkpoints; censored/zero-baseline cases are explicit in JSON. Donor training cost is separately reported.",
          "","| Pair | Exact overlap | Mean cold / warm target decisions | Warm/cold | Acceleration | ≥30% keep | L4 evidence |","|---|---:|---:|---:|---:|---|---|"]
    for key,x in d["ri4"]["results"].items():
        cs=[s["cold_decisions"] for s in x["per_seed_speed"] if s["cold_decisions"] is not None];ws=[s["warm_decisions"] for s in x["per_seed_speed"] if s["warm_decisions"] is not None]
        ratio=x["mean_warm_cold_ratio"]
        L.append(f"| {key} | {x['overlap_count']} | {np.mean(cs):.0f} / {np.mean(ws):.0f} | {ratio:.2f} | {pct(x['mean_speedup'])} | {'KEEP' if x['keep'] else 'NO'} | {x['l4_evidence']} |")
    L += ["","No semantic alias, positional mapping, or fabricated shared factor was introduced. Initial K, routes and outcomes match exactly. These null interventions provide no positive or negative efficacy test of non-empty transfer, and no L4/RSI benefit evidence.",
          "",f"![Transfer overlap]({CHART_MAP['pub_ri4_transfer_overlap.png']})",
          "","## 5. KE-4 — Distribution Sensitivity","",
          "Five paired learned/fixed runs per distribution. Uniform uses the current centroid-corruption generator with uniform category/action sampling, not uniform [0,1] vectors. Clustered is 60% first-two-category / 40% all-category mixture (73.3% expected in the first two). Adversarial is an exact midpoint of a closest weighted centroid pair with random endpoint truth; nearest-two distance equality is asserted. Evaluation matches each distribution.",
          "","| Distribution | Learned routing | Fixed routing | K lift (95% CI) | Relative lift | Starvation | Final / all-checkpoint hurts |","|---|---:|---:|---:|---:|---:|---:|"]
    for dist,x in d["ke4"]["results"].items():
        s=d["ke4"]["summary"][dist]
        L.append(f"| {dist} | {pct(x['learning']['final_routing_mean'])} | {pct(x['fixed']['final_routing_mean'])} | {ci(x['routing_delta'])} | {pct(s['relative_routing_delta'])} | {pct(s['starvation'])} | {s['hurts']} / {s['hurts_all_checkpoints']} |")
    L += ["",f"**Pre-registered verdict: {d['ke4']['verdict']}.** Adversarial K lift is non-positive. Both arms already reach 100% routing and accuracy; zero lift is a ceiling effect, not absolute failure on ambiguous cases. The +43% magnitude is not reproduced uniformly.",
          "","The earlier KE-4 script evaluated all distributions on uniform and used a hardcoded historical baseline. This run uses a matched fixed-K control within each distribution.",
          "",f"![Distribution curves]({CHART_MAP['pub_ke4_distribution_robustness.png']})",
          "","## 6. KE-5 — Conservation Interaction","",
          "Five paired DataOps runs. After each verification, canonical calibration receives α=covered categories/total categories, q=cumulative correct/verified, V=verified decisions, penalty_ratio=10. θ_min=23.53/(α·V), signal=α·q·V. GREEN: signal ≥2θ_min; AMBER: signal ≥θ_min; RED otherwise. Only GREEN allows K updates. Verification advances even when K updates are blocked; no bootstrap bypass.",
          "","**Penalty limitation:** the canonical function accepts penalty_ratio but does not use it in threshold/status calculation. This is the canonical gate at the requested DataOps setting, not a validated asymmetric-loss experiment. K learning rates were not silently changed.",
          "","| Arm | Final routing | Accuracy | N350 dip | N450 dip | Blocked decisions / factor updates |","|---|---:|---:|---:|---:|---:|"]
    s=d["ke5"]["summary"]
    for key,x in d["ke5"]["results"].items():
        z=s[key]
        L.append(f"| {key} | {pct(x['final_routing_mean'])} | {pct(x['final_accuracy_mean'])} | {pct(z['dips']['350'])} | {pct(z['dips']['450'])} | {z['blocked_decisions_mean']:.1f} / {z['blocked_updates_mean']:.1f} |")
    L += ["",f"**HELPS: {s['helps']}; COSTS: {s['costs']}.** Primary N350/N450 dip reductions: {pct(s['dip_reductions']['dips']['350'])} / {pct(s['dip_reductions']['dips']['450'])}. Final relative routing loss: {pct(s['final_routing_relative_loss'])} ({pp(s['final_routing_loss'])}). Cost criterion: ≥5% relative; ≥5 pp interpretation also recorded.",
          "",f"Supplemental fixed 50-case longitudinal cohort: dip reductions {pct(s['dip_reductions']['longitudinal_dips']['350'])} / {pct(s['dip_reductions']['longitudinal_dips']['450'])}. This small secondary result does not override the primary verdict. Fresh-cohort fluctuations are not automatically harmful model updates.",
          "","Blocks occur early while support accumulates; with growing V and frozen geometry the gate need not track late curve fluctuations. The earlier KE-5 script compared q directly to θ_min and bypassed 50 decisions. Those results are not interchangeable with this canonical gate run.",
          "",f"![Conservation curves]({CHART_MAP['pub_ke5_conservation_curves.png']})",
          "","## 7. Combined Production Recommendation","",
          "These experiments identify benchmark candidates, not a universal production optimum. RI-1 tests architecture only on DataOps; RI-2/RI-3 test exploration on RNN. Static combined with a selected UCB/ε policy has not been factorially tested and is not claimed as measured.",
          "","**DataOps paper baseline:** Static+K for routing efficiency, retaining RNN+K for task accuracy. For existing RNN deployments, the table selects highest measured routing quality among tested configurations satisfying ≤10% starvation / ≤2 pp loss; ties favor greedy. These are candidates for shadow evaluation.",
          "","| Copilot | Tested RNN candidate | Routing | Starvation | Decision |","|---|---|---:|---:|---|"]
    for cop in COPS:
        combined={"greedy":d["ri3"]["results"][cop]["greedy"]}
        for exp in ("ri2","ri3"):combined.update({k:v for k,v in d[exp]["results"][cop].items() if k!="greedy"})
        g=combined["greedy"]["final_routing_mean"]
        valid=[(k,v) for k,v in combined.items() if v["starvation"]<=.10+1e-12 and v["final_routing_mean"]>=g-.02-1e-12]
        if valid:key,x=max(valid,key=lambda z:(z[1]["final_routing_mean"],z[0]=="greedy"));note="Candidate; validate accuracy and uncertainty"
        else:key,x="greedy",combined["greedy"];note="No candidate meets both constraints; coverage gap remains"
        L.append(f"| {cop} | {key} | {pct(x['final_routing_mean'])} | {pct(x['starvation'])} | {note} |")
    L += ["","Keep K bounded and frozen within episodes, record uncovered factors, and validate policy changes on held-out operational cases. This work does not establish customer time savings, provider availability, unconstrained transfer or guaranteed future improvement.",
          "","## 8. Three-Metric Summary","",
          "**M-VALUE:** final informative-read routing/task accuracy. **M-COST:** actual policy scorer/Q calls and B=2 reads, excluding scenario-generation/oracle work. **M-GOV:** K bounds, frozen episode state, immutable evaluation, explicit coverage and blocked-update accounting. Mechanical checks are not deployment-safety proof.",
          "","Every row passed the state/bounds/accounting checks. JSONs retain per-seed K tensors, selection/update counts, cohort hashes, sample traces and gate histories. In-process latency is recorded, but concurrent execution prevents fine comparative latency claims.",
          "","| Experiment / configuration | M-VALUE: routing / accuracy | M-COST: scorer / Q / reads | M-GOV: starvation / blocked updates | Final hurts |","|---|---:|---:|---:|---:|"]
    rows=[("RI-1 / "+k,v) for k,v in d["ri1"]["results"].items()]
    for exp in ("ri2","ri3"):
        for cop,rr in d[exp]["results"].items():rows.extend((exp.upper()+" / "+cop+" / "+k,v) for k,v in rr.items())
    for pair,x in d["ri4"]["results"].items():rows.extend(("RI-4 / "+pair+" / "+arm,x[arm]) for arm in ("source_training","cold","warm"))
    for dist,x in d["ke4"]["results"].items():rows.extend(("KE-4 / "+dist+" / "+arm,x[arm]) for arm in ("fixed","learning"))
    rows.extend(("KE-5 / "+k,v) for k,v in d["ke5"]["results"].items())
    for key,x in rows:
        cost=x["three_metrics"]["M-COST"];gov=x["three_metrics"]["M-GOV"]
        L.append(f"| {key} | {pct(x['final_routing_mean'])} / {pct(x['final_accuracy_mean'])} | {cost['scorer_evals_per_decision']:.0f} / {cost['q_evals_per_decision']:.0f} / {cost['reads_per_decision']} | {pct(x['starvation'])} / {gov['blocked_updates_mean']:.1f} | {x['hurts']} |")
    L += ["",f"All-checkpoint evaluation hurts across listed arms: **{sum(x['hurts_all_checkpoints'] for _,x in rows)}**. Some controls recur across experiments and are not independent samples.",
          "","**Mechanism-test limits:** oracle labels define useful dimensions; only those reads restore full values, and usefulness labels train K. This favorable evidence model is inherited. A no-op can count as informative when the initial action is already correct. Zero hurts here cannot establish real-world safety or independent predictive validity. Exported centroids and σ are frozen; all exported σ values are 1.0. No centroid training or actual provider traversal occurs.",
          "","**Reproduction:** run the six new experiment scripts using the requested virtual environment with -B -X utf8, then scripts/generate_group_a_d_charts.py. JSON outputs and the report refuse overwrite. Chart names use _group_a_d when a requested name already exists.",
          "","**Post-check source fingerprints:**"]
    for filename in ("copilot_sdk/scoring/investigation.py","copilot_sdk/backend/investigation_router.py","copilot_sdk/scoring/scorer.py"):
        L.append(f"- {filename}: {hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()}")
    L += ["","**Results and checksums:**"]
    for name in FILES.values():L.append(f"- [{name}]({name}) — SHA-256 {hashlib.sha256((OUT/name).read_bytes()).hexdigest()}")
    L += ["","**All chart artifacts:**"]
    for requested,path in CHART_MAP.items():
        note=" (prior requested-name artifact preserved)" if Path(path).name!=requested else ""
        L.append(f"- [{Path(path).name}]({path}){note}")
    with (OUT/"group_a_d_report.md").open("x",encoding="utf-8") as f:f.write("\n".join(L)+"\n")
    print("WROTE group_a_d_report.md")
def main():
    data={k:json.loads((OUT/f).read_text(encoding="utf-8")) for k,f in FILES.items()}
    for payload in data.values():
        for name,expected in payload["protocol"]["source_hashes"].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
    assert not (OUT/"group_a_d_report.md").exists()
    CHARTS.mkdir(exist_ok=True)
    render(data);report(data)
    print("CHARTS",json.dumps(CHART_MAP,indent=2))
if __name__=="__main__":main()
