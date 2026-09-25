"""Render the pooled confidence frontier from CONS-PD-2."""
import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).parent
DATA = ROOT / "experiments" / "vld" / "results" / "conservation_decision_features.json"
OUT = ROOT / "experiments" / "vld" / "charts" / "pub_confidence_frontier.png"


def main() -> None:
    payload = json.loads(DATA.read_text())
    pooled = payload["frontier_improvement"]["pooled"]
    points = [(float(t), row["coverage"] * 100, (1 - row["accuracy"]) * 100) for t, row in pooled.items() if row["accuracy"] is not None]
    points.sort()
    thresholds, coverage, error = zip(*points)

    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.titlesize": 12})
    fig, ax = plt.subplots(figsize=(7.2, 4.5), constrained_layout=True)
    ax.plot(coverage, error, color="#2166ac", lw=2.4, marker="o", ms=5, label="Pooled confidence frontier")
    labels = {0.50: "0.5", 0.70: "0.7", 0.80: "0.8", 0.90: "0.9"}
    for t, cov, err in zip(thresholds, coverage, error):
        if t in labels:
            ax.annotate(f"t={labels[t]}", (cov, err), xytext=(5, 7), textcoords="offset points", fontsize=9)
    operating = 0.70
    op = pooled[f"{operating:.2f}"]
    op_x, op_y = op["coverage"] * 100, (1 - op["accuracy"]) * 100
    ax.scatter([op_x], [op_y], s=80, color="#d95f02", edgecolor="white", linewidth=1.2, zorder=4, label="Operating point (t=0.7)")
    ax.set_title("Confidence Frontier: Automation Rate vs Error Rate")
    ax.set_xlabel("Automation rate (%)")
    ax.set_ylabel("Error rate (%)")
    ax.set_xlim(0, 100)
    ax.set_ylim(bottom=0)
    ax.grid(axis="both", which="major", color="#d9d9d9", lw=0.8)
    ax.legend(loc="upper right", frameon=True, framealpha=0.95)
    ax.spines[["top", "right"]].set_visible(False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
