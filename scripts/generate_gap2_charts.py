"""Render the five GAP2 figures from saved results; no experiment reruns.

Each figure separates the requested surface signal from the exploratory
post-investigation diagnostic. Curves are raw seed means, never smoothed.
"""
from pathlib import Path
import json
import sys

sys.dont_write_bytecode = True
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/vld/charts"
COLORS = {"margin": "#2563a6", "d_min": "#d07823", "entropy": "#27917e"}
LABELS = {"margin": "Margin (higher)", "d_min": "Nearest distance (lower)", "entropy": "Entropy (lower)"}
NAMES = {"dataops": "DataOps", "purchasing": "Purchasing", "soc": "SOC"}
STAGES = (("surface", "Primary: surface confidence"),
          ("final", "Exploratory: confidence after B=2"))


def signals(cop, stage):
    return cop["signals"] if stage == "surface" else cop["post_investigation_diagnostic"]["signals"]


def best(cop, stage):
    obj = cop if stage == "surface" else cop["post_investigation_diagnostic"]
    return next(s for s in obj["signals"] if s["signal"] == obj["best_signal_at_75"])


def style(ax):
    ax.set_facecolor("#f7f9fc")
    ax.grid(axis="y", alpha=.22)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)


def save(fig, name, note):
    fig.text(.5, .022, note, ha="center", fontsize=9, color="#475569")
    fig.subplots_adjust(top=.79, bottom=.20, left=.07, right=.97, wspace=.17)
    path = OUT / name
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)
    print(path.relative_to(ROOT))


def risk_coverage(cop):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), sharey=True)
    fig.suptitle(f"{NAMES[cop['copilot']]} | Does abstention retain better decisions?", fontsize=17, y=.97)
    all_points = [r for stage,_ in STAGES for sig in signals(cop,stage) for r in sig["curve"]]
    lower = max(0, np.floor(min(r["accuracy_bootstrap_95_ci"][0] for r in all_points)*10)/10-.03)
    for ax,(stage,title) in zip(axes,STAGES):
        style(ax)
        for sig in signals(cop,stage):
            rows = sig["curve"]
            x = [r["coverage"] for r in rows]
            y = [r["accuracy_on_acted"] for r in rows]
            ax.plot(x,y,"o-",ms=4,lw=2,color=COLORS[sig["signal"]],label=LABELS[sig["signal"]])
            ax.fill_between(x,[r["accuracy_bootstrap_95_ci"][0] for r in rows],
                            [r["accuracy_bootstrap_95_ci"][1] for r in rows],
                            color=COLORS[sig["signal"]],alpha=.10)
        ax.axhline(cop["baseline_accuracy_all"],ls="--",color="#64748b",lw=1.5,label="All-decision baseline")
        ax.set(title=title,xlabel="Coverage (lower means more abstention)",xlim=(1.02,.08),ylim=(lower,1.035))
        ax.set_xticks([1,.9,.75,.6,.5,.4,.3,.2,.1])
        ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.set_title(title,fontsize=12,pad=12)
    axes[0].set_ylabel("Accuracy on acted decisions")
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="upper center",bbox_to_anchor=(.5,.92),ncol=4,frameon=False,fontsize=10)
    save(fig,f"pub_gap2_risk_coverage_{cop['copilot']}.png",
         "Exported geometry + synthetic oracle | 5 seeds x 500 held-out cases | Bands: descriptive 95% seed bootstrap\n"
         "Raw rankings, no monotonic smoothing. Both panels use identical actions; post-read abstention saves no graph reads.")


def best_summary(copilots):
    fig,axes=plt.subplots(1,2,figsize=(13,5.8),sharey=True)
    fig.suptitle("Accuracy at 75% coverage | Best observed signal",fontsize=17,y=.97)
    x=np.arange(len(copilots)); width=.34
    for ax,(stage,title) in zip(axes,STAGES):
        style(ax)
        base=[c["baseline_accuracy_all"] for c in copilots]
        selected=[best(c,stage) for c in copilots]
        rows=[next(r for r in s["curve"] if r["coverage"]==.75) for s in selected]
        acc=[r["accuracy_on_acted"] for r in rows]
        b=ax.bar(x-width/2,base,width,color="#a8b4c3",label="All decisions")
        v=ax.bar(x+width/2,acc,width,color="#2563a6",label="Retained 75%")
        error=np.array([[r["accuracy_on_acted"]-r["accuracy_bootstrap_95_ci"][0] for r in rows],
                        [r["accuracy_bootstrap_95_ci"][1]-r["accuracy_on_acted"] for r in rows]])
        ax.errorbar(x+width/2,acc,yerr=error,fmt="none",color="#24364b",capsize=3)
        ax.bar_label(b,labels=[f"{a:.1%}" for a in base],padding=4,fontsize=10)
        for i,r in enumerate(rows):
            ax.text(x[i]+width/2,r["accuracy_bootstrap_95_ci"][1]+.015,
                    f"{acc[i]:.1%}\n({100*r['accuracy_lift_vs_baseline']:+.1f} pp)",ha="center",fontsize=9)
        ax.set(xticks=x,xticklabels=[f"{NAMES[c['copilot']]}\n{s['signal']}" for c,s in zip(copilots,selected)],ylim=(0,1.19))
        ax.set_title(title,fontsize=12,pad=12)
        ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.set_yticks(np.arange(0,1.01,.2))
    axes[0].set_ylabel("Accuracy on acted decisions")
    fig.legend(*axes[0].get_legend_handles_labels(),loc="upper center",bbox_to_anchor=(.5,.915),ncol=2,frameon=False)
    save(fig,"pub_gap2_best_signal_summary.png",
         "Best signal selected on these evaluation results: exploratory, not independently validated.\n"
         "Synthetic oracle on exported geometry | Error bars: 95% seed bootstrap | Baseline uses the same B=2 actions.")


def coverage_lift(copilots):
    fig,axes=plt.subplots(1,2,figsize=(13,5.8),sharey=True)
    fig.suptitle("Coverage versus accuracy lift | Tradeoffs remain visible",fontsize=17,y=.97)
    for ax,(stage,title) in zip(axes,STAGES):
        style(ax)
        for cop,color in zip(copilots,["#2563a6","#d07823","#27917e"]):
            sig=best(cop,stage)
            x=[r["coverage"] for r in sig["curve"]]
            y=[100*r["accuracy_lift_vs_baseline"] for r in sig["curve"]]
            ax.plot(x,y,lw=1,alpha=.45,color=color)
            ax.scatter(x,y,s=32,color=color,label=f"{NAMES[cop['copilot']]}: {sig['signal']}")
        ax.axhline(0,ls="--",lw=1.2,color="#64748b")
        ax.set(title=title,xlabel="Coverage (lower means more abstention)",xlim=(1.02,.08))
        ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.set_title(title,fontsize=12,pad=12)
        ax.legend(frameon=False,fontsize=9,loc="best")
    axes[0].set_ylabel("Accuracy lift over all decisions (percentage points)")
    save(fig,"pub_gap2_coverage_vs_lift.png",
         "Each domain's best signal at 75% is held fixed across the curve; selection is exploratory.\n"
         "5 seeds x 500 synthetic cases | No monotonic smoothing | Final-confidence panel uses two reads for every case.")


def main():
    data=json.loads((ROOT/"experiments/vld/gap2_abstention_curve.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11})
    for cop in data["copilots"]:
        risk_coverage(cop)
    best_summary(data["copilots"])
    coverage_lift(data["copilots"])


if __name__ == "__main__":
    main()
