"""D2 latency and publication Fig-1/2/3 from provenance-checked data.

No existing source/data is rewritten. New PNG/SVG, latency CSV and audit only.
Saved KE-1/B1 seeds are preserved; random_state=42 applies to new computation.
"""
from __future__ import annotations
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter
import numpy as np
import seaborn as sns  # type: ignore[import]

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/"experiments/vld"
OUT = DATA/"paper_charts"
RESULTS = DATA/"results"
ORDER = ("soc", "trading", "purchasing", "dataops", "s2p")
NAMES = dict(zip(ORDER,("SOC","Trading","Purchasing","DataOps","S2P")))
COLORS = dict(zip(ORDER,("#2563EB","#DC2626","#059669","#7C3AED","#D97706")))
RATES = {"soc":1200, "s2p":486, "purchasing":231, "dataops":106, "trading":19}
BG, GRAY = "#FAFAFA", "#737373"
HASHES: dict[str,str] = {}
TIER = "REAL_COMPONENT geometry + SIMULATED verification"


def read(relative: str) -> Any:
    p=ROOT/relative
    raw=p.read_bytes()
    HASHES[relative]=hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def save(fig: Any, name: str, description: str) -> None:
    for ext in ("png","svg"):
        metadata = ({"Description":description} if ext == "svg" else {"Description":description})
        fig.savefig(OUT/f"{name}.{ext}", dpi=300, facecolor=BG, metadata=metadata)
    plt.close(fig)


def ke1() -> dict[str,Any]:
    result={}
    summary=read("experiments/vld/k_learning_curve_cross_copilot_summary.json")
    for cop in ORDER:
        name="k_learning_curve_results.json" if cop=="dataops" else f"k_learning_curve_{cop}.json"
        d=read("experiments/vld/"+name)
        end=d["checkpoints"][-1]
        s=next(r for r in summary["copilots"] if r["name"]==cop)
        assert end["learning_arm"]["routing_quality"]==s["final_routing_learning"]
        assert end["control_arm"]["routing_quality"]==s["final_routing_control"]
        result[cop]=d
    return result


def latency(curves: dict[str,Any]) -> list[dict[str,Any]]:
    rows=[]
    for cop in ORDER:
        checkpoints=curves[cop]["checkpoints"]
        # Decimal excludes S2P's exactly +1pp N=50 point from the strict >1pp test.
        point=next(p for p in checkpoints if
                   Decimal(str(p["learning_arm"]["routing_quality"]))-
                   Decimal(str(p["control_arm"]["routing_quality"]))>Decimal(".01"))
        n=point["decision_count"]
        row={"copilot":cop,"decisions_to_divergence":n,
             "assumed_decisions_per_week":RATES[cop],"weeks_to_divergence":n/RATES[cop],
             "weeks_to_plateau":500/RATES[cop],"tier":"ILLUSTRATIVE",
             "assumption_source":"MAP VLD Addendum v20 verified-outcome latency table ($7B manufacturer); "
             "divergence=first KE-1 checkpoint >1pp routing_quality gap; "
             "plateau=assumed N500 planning horizon, not a measured five-domain plateau"}
        rows.append(row)
        print(json.dumps(row))
    with (RESULTS/"verified_outcome_latency.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def fig1(curves: dict[str,Any]) -> dict[str,Any]:
    fig, axes=plt.subplots(1,5,figsize=(10,6),sharey=True)
    fig.subplots_adjust(left=.075,right=.985,bottom=.25,top=.76,wspace=.18)
    report={}
    for ax,cop in zip(axes,ORDER):
        points=curves[cop]["checkpoints"]
        x=[p["decision_count"] for p in points]
        y=[p["learning_arm"]["routing_quality"] for p in points]
        frozen=[p["control_arm"]["routing_quality"] for p in points]
        delta=100*(y[-1]-frozen[-1])
        ax.plot(x,y,color=COLORS[cop],lw=2,marker="o",ms=3,label="K-learn")
        ax.plot(x,frozen,color=GRAY,lw=1.7,ls="--",label="K-frozen")
        ax.set_title(f"{NAMES[cop]}\n+{delta:.0f}pp",fontsize=11,pad=12)
        ax.set_xlim(0,500)
        ax.set_ylim(.35,.90)
        ax.set_xticks([0,250,500])
        ax.tick_params(axis="x",labelrotation=45)
        ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.set_yticks([.4,.5,.6,.7,.8,.9])
        if cop=="s2p":
            ax.scatter([100,250],[.55,.59],facecolors="none",edgecolors=COLORS[cop],s=85,lw=1.3,zorder=5)
        report[cop]={"tier":TIER, "endpoint_routing_delta_pp":delta,
                     "frozen_baseline_moves":len(set(frozen))>1, "seed":curves[cop].get("random_seed"),
                     "negative_gaps":[{"N":n,"gap_pp":100*(a-b)} for n,a,b in zip(x,y,frozen) if a<b],
                     "hurts":[p["learning_arm"]["hurts"] for p in points]}
    axes[0].set_ylabel("routing_quality")
    fig.suptitle("Five-domain K learning curves",fontsize=14,y=.95)
    fig.text(.5,.865,"+3 to +21pp, 0 hurts",ha="center",fontsize=11)
    fig.supxlabel("Verified-decision count",y=.165,fontsize=11)
    fig.legend(handles=[Line2D([0],[0],color="#334155",lw=2,label="K-learn"),
                        Line2D([0],[0],color=GRAY,ls="--",lw=1.7,label="K-frozen")],
               loc="lower center",bbox_to_anchor=(.5,.07),ncol=2,frameon=False)
    fig.text(.5,.038,"REAL_COMPONENT geometry + SIMULATED verification · Single seed/domain · Changing evaluation samples",
             ha="center",fontsize=9)
    fig.text(.5,.012,"N=50–500 observed · S2P negative gaps circled · No smoothing or uncertainty bands",
             ha="center",fontsize=9)
    save(fig,"fig1_five_domain_curves",TIER+"; KE-1 exact checkpoints; single-seed results; no inferred N0 or confidence bands")
    return report


def fig2(b1: dict[str,Any]) -> dict[str,Any]:
    fig,axes=plt.subplots(1,2,figsize=(10,6))
    fig.subplots_adjust(left=.08,right=.98,bottom=.24,top=.76,wspace=.25)
    audit={}
    for ax,cop in zip(axes,("soc","dataops")):
        arms=b1[cop]["D250"]
        incumbent=arms["arm1_incumbent"]["checkpoints"]
        x=np.array([p["decision_count"] for p in incumbent])
        y=np.array([p["routing_quality"] for p in incumbent])
        ax.plot(x,y,color=COLORS[cop],lw=5,alpha=.8,label="Incumbent")
        for key,color,lw,marker,markevery in [
            ("arm3_replay","#059669",3.2,"o",(0,4)),
            ("arm4_migration","#D97706",1.2,"s",(2,4)),
            ("arm2_cold_start",sns.desaturate(COLORS[cop],.5),2,"",(0,4))]:
            pts=[p for p in arms[key]["checkpoints"] if p["decision_count"]>=250]
            xx=np.array([p["decision_count"] for p in pts])
            yy=np.array([p["routing_quality"] for p in pts])
            if key!="arm2_cold_start":
                np.testing.assert_array_equal(yy,y[x>=250])
            ax.plot(xx,yy,color=color,lw=lw,ls="--" if key=="arm2_cold_start" else "-",
                    marker=marker,ms=4,markevery=markevery,
                    markerfacecolor=BG,markeredgewidth=1.2)
        cold=arms["arm2_cold_start"]
        elapsed=int(cold["joint_decisions_to_parity"])
        global_n=250+elapsed
        assert global_n==cold["parity_global_decision"]
        ax.axvline(250,color=GRAY,lw=1,ls=":")
        ax.axvline(global_n,color=GRAY,lw=1.2,ls=":")
        ax.set_title(NAMES[cop],fontsize=14,pad=10)
        ax.set_xlim(0,1000)
        ax.set_xticks([0,250,500,750,1000])
        ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.set_ylim((.62,.84) if cop=="soc" else (.43,.635))
        ax.set_xlabel("Verified-decision count (global)",fontsize=11)
        ax.set_ylabel("routing_quality")
        ax.text(.02,.96,"Entry: D=250\nReplay / migration: 0 new",transform=ax.transAxes,
                fontsize=10,va="top",bbox={"facecolor":BG,"alpha":.85,"edgecolor":"none"})
        parity_y=next(p["routing_quality"] for p in cold["checkpoints"] if p["decision_count"]==global_n)
        ax.annotate(f"{elapsed} since entry"+("\nTransient joint parity" if cop=="dataops" else "\nJoint parity"),
                    xy=(global_n,parity_y),xytext=(global_n-300,parity_y-.065),
                    fontsize=10,arrowprops={"arrowstyle":"->","color":GRAY})
        if cop=="dataops":
            pts=cold["checkpoints"]
            cy=np.array([p["routing_quality"] for p in pts])
            mask=(x>=global_n)&((y-cy)>.01+1e-12)
            ax.fill_between(x,cy,y,where=mask,color=GRAY,alpha=.18,interpolate=True)
            ax.annotate("Final gap: −2.0pp",xy=(1000,cy[-1]),xytext=(520,.451),
                        fontsize=10,arrowprops={"arrowstyle":"->","color":GRAY})
        audit[cop]={"tier":TIER, "joint_parity_since_entry":elapsed,"joint_parity_global_N":global_n,
                    "routing_only_parity_since_entry":cold["routing_decisions_to_parity"],
                    "parity_lost_later":cold["joint_parity_lost_after_first"],
                    "final_incumbent_routing_quality":float(y[-1]),
                    "replay_migration_exact_incumbent_match_after_entry":True}
    fig.suptitle("Delayed-entrant catch-up (D=250)",fontsize=14,y=.95)
    fig.text(.5,.865,"Replay and migration: 0 decisions to parity",ha="center",fontsize=11)
    handles=[Line2D([0],[0],color="#334155",lw=5,label="Incumbent"),
             Line2D([0],[0],color=GRAY,ls="--",lw=2,label="Cold-start"),
             Line2D([0],[0],color="#059669",lw=3,marker="o",mfc=BG,label="Replay"),
             Line2D([0],[0],color="#D97706",lw=1.2,marker="s",mfc=BG,label="Migration")]
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.5,.11),ncol=4,frameon=False)
    fig.text(.5,.07,"Joint parity: routing_quality AND action_accuracy within 1pp · Markers: elapsed counts since entry",
             ha="center",fontsize=9)
    fig.text(.5,.038,"Coincident incumbent / replay / migration curves after entry · Full N=1000 horizon",
             ha="center",fontsize=9)
    fig.text(.5,.01,"REAL_COMPONENT geometry + SIMULATED verification · Single seed · No uncertainty bands",
             ha="center",fontsize=9)
    save(fig,"fig2_delayed_entrant",TIER+"; B1 D250; joint parity markers on global-N axis; exact overlapping replay/migration")
    return audit


def fig3(data: dict[str,Any]) -> dict[str,Any]:
    fig,ax=plt.subplots(figsize=(10,6))
    fig.subplots_adjust(left=.105,right=.975,bottom=.22,top=.87)
    audit={}
    for item in data["copilots"]:
        cop=item["copilot"]
        pts=item["curve"]
        x=np.array([p["coverage"] for p in pts])
        y=np.array([p["action_accuracy"] for p in pts])
        ci=np.array([p["action_accuracy_95_ci"] for p in pts])
        ax.plot(x,y,color=COLORS[cop],lw=2.2,marker="o",ms=3,label=NAMES[cop])
        ax.fill_between(x,ci[:,0],ci[:,1],color=COLORS[cop],alpha=.12)
        ax.axhline(item["baseline_action_accuracy"],color=GRAY,ls="--",lw=1,alpha=.75)
        p=item["at_target_75"]
        ax.scatter([p["coverage"]],[p["action_accuracy"]],color=COLORS[cop],s=65,zorder=4)
        audit[cop]=p
    ax.axvline(.75,color=GRAY,ls=":",lw=1)
    ax.set_xlim(1.015,.08)
    ax.set_ylim(.70,1.025)
    ax.set_xticks([1,.9,.8,.75,.6,.5,.4,.3,.2,.1])
    ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.set_xlabel("Held-out coverage (accepted fraction)",fontsize=11)
    ax.set_ylabel("action_accuracy on accepted subset",fontsize=11)
    ax.set_title("Risk–coverage on untouched evaluation data",fontsize=14,pad=15)
    ax.legend(loc="lower right",frameon=True,fontsize=11)
    # Direct point callouts; lifts refer to the fixed selection-set 75% threshold.
    positions={"soc":(.66,.973),"dataops":(.67,.830),"purchasing":(.61,.900)}
    for cop,p in audit.items():
        label=f"{NAMES[cop]} +{100*p['action_accuracy_lift']:.1f}pp\n{100*p['coverage']:.1f}% held-out"
        ax.annotate(label,xy=(p["coverage"],p["action_accuracy"]),xytext=positions[cop],
                    color=COLORS[cop],fontsize=10,
                    arrowprops={"arrowstyle":"->","color":COLORS[cop]},
                    bbox={"facecolor":BG,"alpha":.9,"edgecolor":"none","pad":2})
    fig.text(.5,.12,"final_d_min · 75% target on selection set · Dashed gray: act-on-all B=2 baselines",
             ha="center",fontsize=10)
    fig.text(.5,.075,"REAL_COMPONENT geometry + SIMULATED verification · 500 train / 500 selection / 500 test × 5 seeds",
             ha="center",fontsize=9)
    fig.text(.5,.035,"Bands: descriptive paired-seed bootstrap 95% · All accepted and abstained cases already use two reads",
             ha="center",fontsize=9)
    save(fig,"fig3_risk_coverage",TIER+"; independent train/threshold-selection/test; fixed final_d_min; actual held-out coverage")
    return audit


def main() -> None:
    np.random.seed(42)
    sns.set_theme(style="whitegrid",font="sans-serif",rc={
        "figure.facecolor":BG,"axes.facecolor":BG,"font.size":11,"axes.labelsize":11,
        "axes.titlesize":14,"xtick.labelsize":10,"ytick.labelsize":10,"svg.fonttype":"none",
        "grid.alpha":.35,"axes.spines.top":False,"axes.spines.right":False})
    OUT.mkdir(parents=True,exist_ok=True)
    RESULTS.mkdir(parents=True,exist_ok=True)
    curves=ke1()
    b1=read("experiments/vld/results/delayed_entrant_catchup.json")
    held=read("experiments/vld/results/gap2_abstention_heldout_v1.json")
    old=read("experiments/vld/gap2_abstention_curve.json")
    extended=read("experiments/vld/k_learning_curve_dataops_extended.json")
    rows=latency(curves)
    a1=fig1(curves)
    a2=fig2(b1)
    a3=fig3(held)
    original={}
    for c in old["copilots"]:
        signal=next(s for s in c["post_investigation_diagnostic"]["signals"] if s["signal"]=="d_min")
        original[c["copilot"]]=next(p for p in signal["curve"] if p["coverage"]==.75)
    audit={"random_state":42,"latency_tier":"ILLUSTRATIVE","figure_tier":TIER,
           "source_sha256":HASHES,"latency":rows,"fig1":a1,"fig2":a2,"fig3":a3,
           "original_exploratory_gap2_at_75":original,
           "extended_dataops":[{"N":p["decision_count"],"routing_quality":p["learning_arm"]["routing_quality"]}
                              for p in extended["checkpoints"] if p["decision_count"] in (500,1000,2000)],
           "plateau_note":"N500 is the MAP planning assumption, not a measured plateau for every domain"}
    (RESULTS/"d1_d2_figures_audit_v1.json").write_text(json.dumps(audit,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    lines=["# D1 / D2 / Fig-1–3 production notes","",
           "Date: September 14, 2026. New computation random_state=42; original KE-1/B1 seeds preserved.",
           "",
           "## Input gate",
           "",
           "KE-1 summary contains endpoints only. Exact checkpoint files supply ten points per domain at N=50–500; "
           "DataOps uses k_learning_curve_results.json. Each domain has one training seed, not multi-seed uncertainty. "
           "No N=0 point is fabricated.",
           "B1 JSON is indexed by copilot / D250 / arm1_incumbent, arm2_cold_start, arm3_replay, arm4_migration. "
           "Checkpoints carry global decision_count and entrant live_decisions.",
           "Original GAP-2 script scripts/gap2_abstention_curve.py selects the best signal at 75% on evaluation data "
           "and ranks the evaluation cohort to derive its thresholds. final_d_min is its post-investigation d_min. "
           "A fresh three-way rerun was required and completed; only its untouched test curve appears in Fig-3.",
           "S2P trace sources: prepaper v10 S2P-SC2 and sibling s2p-copilot/backend/app/vld_preseed.py and evidence_provider.py. "
           "The actual clause is bulk-volume pass-through, not commodity-index entitlement. No absent clause is invented.",
           "",
           "## D1","",
           "See recursion_trace_example.md. The executed K-only trace uses explicit planted K5=.62, "
           "a B=3 acquisition and simulated verification, then a changed B=2 next decision against a frozen-K counterfactual. "
           "ΔK=[.02,.02,0,0,0,.04,0,0], Δμ=0. The .200/.100 discrepancy is base versus K-weighted Q. "
           "Tier: REAL_COMPONENT geometry + SIMULATED verification, PLANTED FIXTURE evidence/start. "
           "The production callback's flip bonus, external verification and lack of conservation enforcement in this "
           "local demonstration are disclosed.",
           "",
           "## D2","",
           "All wall-clock estimates are ILLUSTRATIVE. MAP v20 ($7B manufacturer) assumes "
           "SOC 1200, S2P 486, Purchasing 231, DataOps 106, Trading 19 verified outcomes/week. "
           "Weeks=N/rate. Divergence is the first observed strictly >1pp learn-minus-frozen routing_quality gap, "
           "not a statistically significant or sustained divergence. Checkpoint spacing limits temporal resolution.",
           "S2P's N=50 gap is exactly +1pp and does not qualify; N=100 is negative; first >1pp is N=150.",
           "weeks_to_plateau uses MAP's assumed N=500 planning horizon, explicitly not a measured five-domain plateau. "
           "Extended DataOps routing is .630 at 500, .640 at 1000, .630 at 2000; "
           "that separate single-seed run supports near-plateau language only for DataOps.",
           "",
           "| Copilot | N divergence | Verified/week assumption | Weeks divergence | Weeks to assumed N500 |",
           "|---|---:|---:|---:|---:|"]
    for r in sorted(rows,key=lambda r:r["weeks_to_divergence"]):
        lines.append(f"| {NAMES[r['copilot']]} | {r['decisions_to_divergence']} | "
                     f"{r['assumed_decisions_per_week']} | {r['weeks_to_divergence']:.6f} | {r['weeks_to_plateau']:.6f} |")
    lines.extend(["",
        "B1 versus KE-1: SOC B1 final=.786 at N1000, KE-1=.810 at N500; DataOps=.5875 versus .630. "
        "Different seeds, horizon and evaluation cohorts (B1 fixed 1000 cases, KE-1 changing 50-case samples) "
        "prevent an exact endpoint replication claim. Divergence points use KE-1 exclusively.",
        "", "## Fig-1","",
        "Exact final lifts: SOC +12pp, Trading +12pp, Purchasing +21pp, DataOps +19pp, S2P +3pp. "
        "All saved learning-arm checkpoint hurts are zero. This metric is synthetic action degradation versus "
        "surface on that evaluation cohort, not a no-degradation guarantee. "
        "S2P's −2pp at N100 and −3pp at N250 are circled. All five frozen baselines move because evaluation "
        "samples change despite fixed K. No smoothing, extrapolation or invented bands. "
        "The chart shows the 500-decision observation horizon, not an established five-domain plateau.",
        "", "## Fig-2","",
        "Global-N axis runs 0–1000; entrant curves start at D250. Replay and migration exactly match incumbent "
        "from entry onward, so three curves overlap. Different widths and open markers expose the coincident lines "
        "without numerical offsets. 0 decisions to parity means no NEW verifications after entry; "
        "it excludes replay computation and migration engineering.",
        "The requested SOC 525 and DataOps 575 numbers are JOINT parity (routing_quality AND action_accuracy within "
        "1pp), elapsed since entry. Markers are therefore at global N775/N825. Routing-only first parity is "
        "475 for SOC and 200 for DataOps; these metrics are not interchanged. "
        "DataOps joint parity is transient and not sustained through the horizon; at N1000 its cold arm is "
        ".5675 versus incumbent .5875 (−2.0pp routing_quality). The full tail is plotted and subsequent >1pp gaps shaded.",
        "", "## Fig-3","",
        "New protocol: 500 train / 500 threshold-selection / 500 evaluation, five seeds per domain; "
        "signal fixed in advance to final_d_min. Numeric thresholds are selection-set quantiles, "
        "locked before generation of the test cohort. Split fingerprints are disjoint; K is frozen for selection/test. "
        "Original decision generator, B=2 recurrence and K rule are reused; all labels and evidence remain simulated.",
        "X plots actual test coverage, not enforced test-set quantiles. Callouts refer to the selection-set 75% target. "
        "Y is action_accuracy on accepted decisions, distinct from routing_quality; category is supplied. "
        "Baseline is the same B=2 policy acting on every case, not budget-zero single-pass. "
        "Bands are descriptive paired-seed bootstrap intervals; five seeds and geometry-derived truth limit inference.",
        "",
        "| Copilot | Original lift at 75% | Held-out coverage at 75% target | New action_accuracy lift | Lift 95% interval |",
        "|---|---:|---:|---:|---:|"])
    for cop,p in a3.items():
        prior=100*original[cop]["accuracy_lift_vs_baseline"]
        lo,hi=[100*v for v in p["lift_95_ci"]]
        lines.append(f"| {NAMES[cop]} | +{prior:.2f}pp | {100*p['coverage']:.2f}% | "
                     f"+{100*p['action_accuracy_lift']:.2f}pp | [{lo:.2f}, {hi:.2f}]pp |")
    lines.extend(["",
        "The +9.5–15.2pp exploratory range is not exactly replicated: fresh held-out lifts span +8.92–13.36pp. "
        "All remain positive. SOC accepted cases have zero observed errors at this threshold, hence its "
        "five-seed bootstrap accuracy interval degenerates to [1,1]; this is not proof of zero population risk. "
        "Threshold uncertainty and five-seed bootstrap are descriptive, not deployment guarantees.",
        "", "## Reproduction","",
        "Run mypy on each new script with pyproject.toml before executing. "
        "Run python -B scripts/d1_recursion_trace_v1.py; "
        "python -B scripts/gap2_abstention_heldout_v1.py; "
        "python -B scripts/generate_d1_d2_paper_figures_v1.py. "
        "Source hashes and machine-readable plotting values are in d1_d2_figures_audit_v1.json. "
        "Charts: whitegrid, #FAFAFA, sans-serif, 11pt axis labels, 14pt main titles, 10×6 inches, "
        "300dpi PNG and editable-text SVG.",
        "Only new scripts and outputs were authored. No git commands or edits to pre-existing sources."])
    (RESULTS/"d1_d2_figures_notes_v1.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"latency_order":[r["copilot"] for r in sorted(rows,key=lambda r:r["weeks_to_divergence"])],
                      "fig3":a3}))


if __name__=="__main__":
    main()
