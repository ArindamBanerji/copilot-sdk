"""Three figures for RAW/Z-NORM/MINMAX Q ablation and representative raw scales."""
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
DATA=ROOT/"experiments/vld/q_term_ablation_normalized.json"
CHARTS=ROOT/"experiments/vld/charts"
OUTPUTS=tuple(CHARTS/n for n in (
    "pub_q_ablation_norm_comparison.png","pub_q_ablation_norm_heatmap.png",
    "pub_q_ablation_term_scales.png"))
NORMS=("RAW","Z-NORM","MINMAX")
COPILOTS=("dataops","trading","purchasing","soc","s2p")
NAMES=("DataOps","Trading","Purch.","SOC","S2P")
VARIANTS=("PRECISION-ONLY","DISCRIMINATIVE-ONLY","LEVERAGE-ONLY",
          "PREC+DISC","PREC+LEV","DISC+LEV","ALL-THREE")
SHORT=("P","D","L","P+D","P+L","D+L","ALL")
BLUE="#1769aa"; GOLD="#ce861e"; GREEN="#388563"


def get(data,norm,variant,copilot):
    return next(r for r in data["results"] if
                (r["normalization"],r["variant"],r["copilot"])==(norm,variant,copilot))


def main():
    for p in OUTPUTS:
        if p.exists(): raise FileExistsError(f"Refusing to overwrite {p}")
    data=json.loads(DATA.read_text(encoding="utf-8"))
    assert data["checks"]["aggregate_rows"]==115
    plt.rcParams.update({"figure.facecolor":"#fbfcfe","axes.facecolor":"white",
        "savefig.facecolor":"#fbfcfe","font.size":11,"axes.titlesize":15,
        "text.color":"#293442","axes.labelcolor":"#293442",
        "axes.spines.top":False,"axes.spines.right":False,
        "axes.edgecolor":"#bac4cf","grid.color":"#dce2e9",
        "grid.linewidth":.7,"axes.axisbelow":True,"savefig.dpi":180})
    metadata={"Experiment":"VLD-Q-ABLATION-NORMALIZED",
        "DataSHA256":hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "ScriptSHA256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    fig,axes=plt.subplots(1,3,figsize=(17,7),sharey=True)
    for ax,norm in zip(axes,NORMS):
        summary=next(s for s in data["normalization_summary"] if s["normalization"]==norm)
        rows=[next(r for r in summary["variants"] if r["variant"]==v) for v in VARIANTS]
        y=np.array([r["routing_mean"] for r in rows])
        sd=np.array([r["routing_seed_std"] for r in rows])
        colors=["#a3b4c3","#a3b4c3",GOLD,"#a3b4c3",GREEN,"#a3b4c3",BLUE]
        ax.bar(range(7),y,yerr=sd,color=colors,width=.69,capsize=2.5,
               error_kw={"color":"#354b5e","linewidth":1})
        for i,(value,error) in enumerate(zip(y,sd)):
            ax.text(i,value+error+.02,f"{value:.1%}",ha="center",fontsize=9,
                    weight="bold" if i in (2,4,6) else "normal")
        ax.set_xticks(range(7),SHORT,rotation=35,ha="right")
        ax.set_ylim(0,1.03); ax.set_yticks(np.linspace(0,1,6))
        ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
        ax.set_title(norm,loc="left",pad=15)
        ax.grid(axis="y")
        ax.set_xlabel("Q variant")
    axes[0].set_ylabel("Mean routing quality")
    fig.text(.065,.951,"Q ablation across normalization",fontsize=22)
    fig.text(.065,.895,"Equal weighting across five copilots · B=2 · error bars: SD of paired-seed means",
             fontsize=11,color="#5a6675")
    fig.text(.065,.037,"P: precision · D: discriminative · L: leverage · independently trained K · synthetic evaluation",
             fontsize=11,color="#5a6675")
    fig.subplots_adjust(left=.065,right=.985,bottom=.17,top=.79,wspace=.15)
    CHARTS.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUTPUTS[0],metadata=metadata); plt.close(fig)

    fig,axes=plt.subplots(1,3,figsize=(17.5,8.5),sharey=True)
    for ax,norm in zip(axes,NORMS):
        matrix=np.array([[get(data,norm,v,c)["routing_mean"] for c in COPILOTS] for v in VARIANTS])
        im=ax.imshow(matrix,cmap="RdYlGn",vmin=0,vmax=1,aspect="auto")
        ax.set_xticks(range(5),NAMES,rotation=30,ha="right",fontsize=10)
        ax.set_yticks(range(7),VARIANTS,fontsize=10)
        ax.set_xticks(np.arange(-.5,5,1),minor=True)
        ax.set_yticks(np.arange(-.5,7,1),minor=True)
        ax.grid(which="minor",color="white",linewidth=1.5)
        ax.tick_params(which="minor",bottom=False,left=False)
        for i in range(7):
            for j in range(5):
                value=matrix[i,j]
                ax.text(j,i,f"{value:.1%}",ha="center",va="center",fontsize=9.5,
                         color="white" if value>.8 or value<.18 else "#293442",
                         weight="bold" if i in (4,6) else "normal")
        ax.add_patch(Rectangle((-.49,5.51),4.98,.98,fill=False,edgecolor="#203d57",linewidth=2.2))
        ax.add_patch(Rectangle((-.49,3.51),4.98,.98,fill=False,edgecolor="#503c79",
                              linewidth=2,linestyle="--"))
        ax.set_title(norm,loc="left",pad=14)
    fig.subplots_adjust(left=.15,right=.895,bottom=.145,top=.83,wspace=.095)
    cax=fig.add_axes([.919,.145,.014,.685])
    cb=fig.colorbar(im,cax=cax)
    cb.ax.yaxis.set_major_formatter(PercentFormatter(1,decimals=0))
    cb.set_label("Routing quality")
    fig.text(.15,.955,"Q ablation by normalization and copilot",fontsize=21)
    fig.text(.15,.90,"ALL-THREE: solid outline · PREC+LEV: dashed outline · five paired seeds",
             fontsize=11,color="#5a6675")
    fig.text(.15,.035,"Production geometry · synthetic evidence · normalized precision = 0 · constant-term equivalences verified",
             fontsize=10,color="#5a6675")
    fig.savefig(OUTPUTS[1],metadata=metadata); plt.close(fig)

    example=data["representative_decision"]
    values=[example["raw_terms"][k] for k in ("precision","discriminative","leverage")]
    fig,ax=plt.subplots(figsize=(11.5,7))
    boxes=ax.boxplot(values,positions=[1,2,3],widths=.42,patch_artist=True,
                     showfliers=False,medianprops={"color":"#22374c","linewidth":1.8},
                     whiskerprops={"color":"#72849a"},capprops={"color":"#72849a"})
    for box,color in zip(boxes["boxes"],("#a3b4c3",BLUE,GOLD)):
        box.set_facecolor(color); box.set_alpha(.35)
    for i,vals in enumerate(values,1):
        # Deterministic display offsets, not jitter in the measured values.
        ax.scatter(i+np.linspace(-.075,.075,len(vals)),vals,color="#344e66",
                   s=37,edgecolor="white",linewidth=.6,zorder=3)
    ax.set_xticks([1,2,3],["Precision","Discriminative","Leverage"])
    ax.set_ylabel("Raw component value")
    ax.set_xlim(.45,3.55); ax.set_ylim(bottom=0)
    ax.grid(axis="y")
    fig.text(.10,.95,"Raw Q-term scales: representative decision",fontsize=21)
    fig.text(.10,.895,f"DataOps · seed index 0 ({example['seed']}) · training decision 250 · pre-read",
             fontsize=11,color="#5a6675")
    fig.text(.10,.032,f"Six unattempted dimensions · category: {example['case']['category']} · no K weighting · synthetic case",
             fontsize=10,color="#5a6675")
    fig.subplots_adjust(left=.10,right=.975,bottom=.13,top=.80)
    fig.savefig(OUTPUTS[2],metadata=metadata); plt.close(fig)
    for p in OUTPUTS: print(f"Saved {p}")


if __name__=="__main__":
    main()

