"""Publication figures for Q term ablation, including signed sequential changes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"experiments/vld/q_term_ablation.json"
CHARTS=ROOT/"experiments/vld/charts"
OUTPUTS=tuple(CHARTS/n for n in ("pub_q_ablation_routing_heatmap.png",
    "pub_q_ablation_bar_dataops.png","pub_q_ablation_term_contribution.png"))
COPILOTS=("dataops","trading","purchasing","soc","s2p")
NAMES=("DataOps","Trading","Purchasing","SOC","S2P")
SHORT=("Precision","Disc.","Leverage","P + D","P + L","D + L","ALL-THREE","Random","No K")
BLUE="#1769aa"; GREEN="#328364"; GOLD="#d59423"


def main():
    for p in OUTPUTS:
        if p.exists():
            raise FileExistsError(f"Refusing to overwrite {p}")
    data=json.loads(DATA.read_text(encoding="utf-8"))
    assert len(data["variants"])==9
    plt.rcParams.update({"figure.facecolor":"#fbfcfe","axes.facecolor":"white",
        "savefig.facecolor":"#fbfcfe","font.size":11,"axes.titlesize":14,
        "text.color":"#293442","axes.labelcolor":"#293442",
        "axes.spines.top":False,"axes.spines.right":False,
        "axes.edgecolor":"#bac4cf","grid.color":"#dce2e9",
        "grid.linewidth":.7,"axes.axisbelow":True,"savefig.dpi":180})
    metadata={"Experiment":"VLD-Q-ABLATION",
        "DataSHA256":hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "ScriptSHA256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    matrix=np.array([[next(r for r in v["copilots"] if r["copilot"]==c)["routing_mean"]
                      for c in COPILOTS] for v in data["variants"]])
    all_index=next(i for i,v in enumerate(data["variants"]) if v["variant"]=="ALL-THREE")
    fig,ax=plt.subplots(figsize=(11.5,8.5))
    heat=ax.imshow(matrix,cmap="RdYlGn",vmin=0,vmax=1,aspect="auto")
    ax.set_xticks(range(5),NAMES)
    ax.set_yticks(range(9),[v["variant"] for v in data["variants"]])
    ax.set_xticks(np.arange(-.5,5,1),minor=True)
    ax.set_yticks(np.arange(-.5,9,1),minor=True)
    ax.grid(which="minor",color="white",linewidth=2); ax.tick_params(which="minor",bottom=False,left=False)
    for i in range(9):
        for j in range(5):
            value=matrix[i,j]
            ax.text(j,i,f"{value:.2%}",ha="center",va="center",
                    color="white" if value>.78 or value<.18 else "#253442",
                    weight="bold" if i==all_index else "normal",fontsize=12)
    ax.add_patch(Rectangle((-.49,all_index-.49),4.98,.98,fill=False,
                           edgecolor="#152f48",linewidth=2.5,clip_on=False))
    ax.get_yticklabels()[all_index].set_weight("bold")
    cbar=fig.colorbar(heat,ax=ax,fraction=.04,pad=.035)
    cbar.ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    cbar.set_label("Routing quality")
    fig.text(.235,.953,"Q term ablation",fontsize=22)
    fig.text(.235,.903,"500 training · 200 evaluation · 5 paired seeds · B=2",fontsize=11,color="#5a6675")
    fig.text(.235,.03,"Production geometry · synthetic evidence · ALL-THREE control outlined",fontsize=10,color="#5a6675")
    fig.subplots_adjust(left=.235,right=.90,bottom=.11,top=.86)
    CHARTS.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUTPUTS[0],metadata=metadata); plt.close(fig)

    rows=[next(c for c in v["copilots"] if c["copilot"]=="dataops") for v in data["variants"]]
    y=np.array([r["routing_mean"] for r in rows]); sd=np.array([r["routing_std"] for r in rows])
    colors=[BLUE if i==all_index else "#91a9bc" for i in range(9)]
    fig,ax=plt.subplots(figsize=(12,7))
    bars=ax.bar(range(9),y,yerr=sd,width=.68,color=colors,capsize=3,
                error_kw={"color":"#32465a","linewidth":1.1})
    for i,(bar,value,error) in enumerate(zip(bars,y,sd)):
        ax.text(i,value+error+.017,f"{value:.2%}",ha="center",fontsize=10,
                weight="bold" if i==all_index else "normal")
    ax.axhline(y[all_index],color=BLUE,linestyle="--",linewidth=1,alpha=.6)
    ax.set_xticks(range(9),SHORT,rotation=25,ha="right")
    ax.set_ylim(0,1.08); ax.set_yticks(np.linspace(0,1,6))
    ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    ax.set_ylabel("Routing quality"); ax.grid(axis="y")
    fig.text(.09,.95,"DataOps: Q term ablation",fontsize=22)
    fig.text(.09,.896,"ALL-THREE highlighted · error bars: seed SD · B=2",fontsize=11,color="#5a6675")
    fig.text(.09,.032,"Production geometry · synthetic evidence · separately learned K per variant",fontsize=10,color="#5a6675")
    fig.subplots_adjust(left=.09,right=.985,bottom=.18,top=.81)
    fig.savefig(OUTPUTS[1],metadata=metadata); plt.close(fig)

    contributions=[next(r for r in data["term_contribution"] if r["copilot"]==c) for c in COPILOTS]
    x=np.arange(5); pos=np.zeros(5); neg=np.zeros(5)
    fig,ax=plt.subplots(figsize=(11.5,7.5))
    for field,label,color in (
        ("precision_baseline_pp","Precision-only",BLUE),
        ("add_disc_pp","+ Discriminative",GREEN),
        ("add_leverage_after_disc_pp","+ Leverage",GOLD)):
        values=np.array([r[field] for r in contributions])
        bottom=np.where(values>=0,pos,neg)
        ax.bar(x,values,bottom=bottom,width=.62,color=color,label=label)
        for i,(value,b) in enumerate(zip(values,bottom)):
            if abs(value)>=3:
                ax.text(i,b+value/2,f"{value:+.1f}" if field!="precision_baseline_pp" else f"{value:.1f}",
                        ha="center",va="center",fontsize=11,color="white",weight="bold")
        pos+=np.maximum(values,0); neg+=np.minimum(values,0)
    totals=matrix[all_index]*100
    ax.scatter(x,totals,marker="D",s=40,color="#223448",label="ALL-THREE total",zorder=5)
    for i,total in enumerate(totals):
        ax.text(i,max(pos[i],total)+3,f"{total:.2f}%",ha="center",fontsize=12,weight="bold")
    ax.axhline(0,color="#748598",linewidth=1)
    ax.set_xticks(x,NAMES); ax.set_ylabel("Routing / sequential change (pp)")
    ax.set_ylim(min(-5,float(neg.min())-6),max(100,float(pos.max())+12))
    ax.grid(axis="y")
    fig.text(.10,.95,"Sequential Q-term contribution",fontsize=21)
    fig.text(.10,.90,"Precision-only → + discriminative → + leverage · retrained K · signed increments",
             fontsize=11,color="#5a6675")
    fig.legend(*ax.get_legend_handles_labels(),loc="lower left",
               bbox_to_anchor=(.09,.79),ncol=4,frameon=False,fontsize=10)
    fig.text(.10,.03,"Path-dependent effects · negative increments below zero · production geometry · synthetic evidence",
             fontsize=10,color="#5a6675")
    fig.subplots_adjust(left=.10,right=.975,bottom=.12,top=.77)
    fig.savefig(OUTPUTS[2],metadata=metadata); plt.close(fig)
    for p in OUTPUTS:
        print(f"Saved {p}")


if __name__=="__main__":
    main()
