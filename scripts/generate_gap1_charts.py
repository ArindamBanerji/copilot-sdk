"""Three GAP1 figures, with explicit missing qualifiers and diagnostic labels."""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter, MaxNLocator
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/"experiments/vld/gap1_adaptive_halting.json"
CHARTS = ROOT/"experiments/vld/charts"
OUTPUTS = tuple(CHARTS/name for name in (
    "pub_gap1_reads_vs_accuracy.png", "pub_gap1_halt_distribution.png",
    "pub_gap1_reads_saved_summary.png"))
NAMES = {"dataops":"DataOps", "purchasing":"Purchasing", "trading":"Trading",
         "soc":"SOC", "s2p":"S2P"}
BLUE, ORANGE, GREEN = "#1769aa", "#d47715", "#29845b"


def main():
    for path in OUTPUTS:
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
    data=json.loads(DATA.read_text(encoding="utf-8"))
    assert data["checks"]["aggregate_rows"] == 35
    plt.rcParams.update({"figure.facecolor":"#fbfcfe", "axes.facecolor":"white",
        "savefig.facecolor":"#fbfcfe", "font.size":11, "axes.titlesize":14,
        "text.color":"#293442", "axes.labelcolor":"#293442",
        "axes.spines.top":False, "axes.spines.right":False,
        "axes.edgecolor":"#bac4cf", "grid.color":"#dce2e9",
        "grid.linewidth":.7, "axes.axisbelow":True, "savefig.dpi":180})
    metadata={"Experiment":"VLD-GAP1",
        "DataSHA256":hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "ScriptSHA256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    fig,axes=plt.subplots(2,3,figsize=(15,9))
    for ax,cop in zip(axes.flat,data["copilots"]):
        b=cop["fixed_b2"]
        adaptive=cop["adaptive_results"]
        lower=max(0,min(r["acc_mean"] for r in [b]+adaptive)-.055)
        upper=min(1.0,max(r["acc_mean"] for r in [b]+adaptive)+.06)
        ax.set_xlim(1.85,4.1); ax.set_ylim(lower,upper)
        ax.add_patch(Rectangle((1.85,b["acc_mean"]-.01),.15,
                               upper-(b["acc_mean"]-.01),color=GREEN,alpha=.1))
        ax.axvline(2,color="#8693a2",linestyle=":",linewidth=1)
        ax.axhline(b["acc_mean"]-.01,color="#8693a2",linestyle="--",linewidth=1)
        frontier=sorted(set((r["reads_mean"],r["acc_mean"]) for r in cop["pareto_frontier"]))
        ax.plot([p[0] for p in frontier],[p[1] for p in frontier],
                color=GREEN,linewidth=1.6,zorder=2)
        groups=defaultdict(list)
        for i,row in enumerate(adaptive,1):
            ax.scatter(row["reads_mean"],row["acc_mean"],s=48,color=ORANGE,
                       edgecolor="white",linewidth=.6,zorder=3)
            groups[(row["reads_mean"],row["acc_mean"])].append(i)
        for i,((x,y),indices) in enumerate(sorted(groups.items())):
            label=("δ"+str(indices[0]) if len(indices)==1
                   else "δ"+",".join(str(n) for n in indices))
            offset=(7,10+13*(i%2)) if i%2==0 else (7,-18)
            ax.annotate(label,(x,y),xytext=offset,textcoords="offset points",
                        fontsize=9,ha="left")
        ax.scatter([2],[b["acc_mean"]],marker="D",s=62,color=BLUE,zorder=4)
        ax.scatter([p[0] for p in frontier],[p[1] for p in frontier],
                   s=125,facecolors="none",edgecolors=GREEN,linewidth=1.4,zorder=5)
        ax.annotate("B2",(2,b["acc_mean"]),xytext=(7,-17),
                    textcoords="offset points",fontsize=10,color=BLUE)
        ax.set_title(NAMES[cop["copilot"]],loc="left",pad=12)
        ax.set_xlabel("Mean reads / decision")
        ax.set_ylabel("Action accuracy")
        ax.set_xticks([2,2.5,3,3.5,4])
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6,steps=[1,2,5,10]))
        ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.grid(axis="y")
    notes=axes.flat[-1]; notes.axis("off")
    notes.legend(handles=[
        Line2D([],[],marker="D",color=BLUE,linestyle="",label="Fixed B2"),
        Line2D([],[],marker="o",color=ORANGE,linestyle="",label="Adaptive B≤4"),
        Line2D([],[],color=GREEN,label="Pareto frontier"),
        Line2D([],[],color="#8693a2",linestyle="--",label="B2 accuracy −1pp")],
        loc="upper left",frameon=False,fontsize=12)
    notes.text(.03,.50,"δ1 .001    δ2 .005    δ3 .01\nδ4 .02      δ5 .05      δ6 .1\n\n"
               "Shared K · 500 training\n200 evaluation · 5 seeds\n"
               "Green region: matched accuracy + reads <2\n"
               "Coincident points: grouped δ labels",
               transform=notes.transAxes,va="top",fontsize=10.5,linespacing=1.65)
    fig.text(.065,.955,"Adaptive halting: reads vs accuracy",fontsize=21,ha="left")
    fig.text(.065,.912,"Production geometry · synthetic evidence · no qualifying threshold",fontsize=11,color="#5a6675")
    fig.subplots_adjust(left=.065,right=.985,bottom=.09,top=.855,hspace=.42,wspace=.29)
    CHARTS.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUTPUTS[0],metadata=metadata); plt.close(fig)

    selected=[c["best_qualifying"] or c["diagnostic_result"] for c in data["copilots"]]
    x=np.arange(len(selected))
    fig,ax=plt.subplots(figsize=(11,6.8))
    bottom=np.zeros(len(selected))
    for field,label,color in (("halt_budget_pct","Budget","#8999aa"),
                               ("halt_residual_pct","Residual",BLUE),
                               ("halt_oscillation_pct","Oscillation / flip cap",ORANGE)):
        values=np.array([r[field] for r in selected])/100
        ax.bar(x,values,bottom=bottom,width=.6,color=color,label=label)
        for i,(v,base) in enumerate(zip(values,bottom)):
            if v>=.025:
                ax.text(i,base+v/2,f"{v:.1%}",ha="center",va="center",
                        fontsize=11,color="white",weight="bold")
        bottom+=values
    ax.set_ylim(0,1.025); ax.set_yticks(np.linspace(0,1,6))
    ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.set_ylabel("Decisions")
    ax.set_xticks(x,[NAMES[c["copilot"]]+"\nδ="+str(r["delta"])
                    for c,r in zip(data["copilots"],selected)])
    ax.grid(axis="y")
    fig.text(.10,.95,"Terminal halt reasons",fontsize=21)
    fig.text(.10,.895,"Diagnostic thresholds · minimum reads within the 1pp accuracy limit · no qualifying delta",
             fontsize=10.5,color="#5a6675")
    fig.legend(*ax.get_legend_handles_labels(),loc="lower left",
               bbox_to_anchor=(.09,.79),ncol=3,frameon=False,fontsize=11)
    fig.text(.10,.035,"Residual / oscillation at read 4: no early-read saving · 5 seeds",fontsize=10,color="#5a6675")
    fig.subplots_adjust(left=.10,right=.975,bottom=.15,top=.77)
    fig.savefig(OUTPUTS[1],metadata=metadata); plt.close(fig)

    fig,ax=plt.subplots(figsize=(10.5,6.4))
    qualified=[c["best_qualifying"] for c in data["copilots"]]
    for i,best in enumerate(qualified):
        if best is None:
            ax.text(i,.06,"N/Q",ha="center",va="bottom",fontsize=17,color="#69788a",weight="bold")
        else:
            value=best["reads_saved_per_decision"]
            ax.bar(i,value,width=.6,color=BLUE)
            ax.text(i,value+.04,f"{value:.3f}",ha="center")
    ax.axhline(0,color="#aab5c2",linewidth=1)
    ax.set_xticks(x,[NAMES[c["copilot"]] for c in data["copilots"]])
    ax.set_xlim(-.6,4.6)
    ax.set_ylim(-.02,max([1]+[r["reads_saved_per_decision"]+.2 for r in qualified if r]))
    ax.set_ylabel("Reads saved / decision")
    ax.grid(axis="y")
    fig.text(.10,.95,"Reads saved at matched accuracy",fontsize=21)
    fig.text(.10,.892,"Fixed B2 comparator · ≤1pp accuracy loss · strictly positive savings",fontsize=11,color="#5a6675")
    if all(r is None for r in qualified):
        ax.text(.5,.62,"No qualifying threshold in any copilot",transform=ax.transAxes,
                ha="center",fontsize=15,color="#536476")
        ax.text(.5,.48,"Production C4 minimum: 2 reads",transform=ax.transAxes,
                ha="center",fontsize=12,color="#536476")
    fig.text(.10,.035,"N/Q: no qualifying delta; no measured zero-valued bar · production geometry · synthetic evidence",
             fontsize=10,color="#5a6675")
    fig.subplots_adjust(left=.10,right=.98,bottom=.13,top=.81)
    fig.savefig(OUTPUTS[2],metadata=metadata); plt.close(fig)
    for path in OUTPUTS:
        print(f"Saved {path}")


if __name__ == "__main__":
    main()
