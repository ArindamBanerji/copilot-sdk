"""Render the publication moat catch-up chart from the frozen B2 seed JSON."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).parent
DATA = ROOT / "experiments" / "vld" / "results" / "moat_b2_seeds.json"
OUT = ROOT / "experiments" / "vld" / "charts" / "pub_moat_catchup.png"


def series(data: dict, arm: str, grid: np.ndarray) -> np.ndarray:
    xs, ys = [], []
    for row in data.values():
        points = row[arm]["checkpoints_on_SA_heldout"]
        xs.append(np.asarray([p["decision_count"] for p in points], dtype=float))
        ys.append(np.asarray([p["routing_quality"] for p in points], dtype=float))
    values = np.vstack([np.interp(grid, x, y) for x, y in zip(xs, ys)])
    return values


def main() -> None:
    payload = json.loads(DATA.read_text())
    seeds = payload["dataops"]["per_seed"]
    max_decisions = max(
        max(p["decision_count"] for row in seeds.values() for p in row["arm1"]["checkpoints_on_SA_heldout"]),
        max(p["decision_count"] for row in seeds.values() for p in row["arm2"]["checkpoints_on_SA_heldout"]),
    )
    x = np.arange(0, int(max_decisions) + 1, 25)
    incumbent = series(seeds, "arm1", x)
    entrant = series(seeds, "arm2", x)
    incumbent_mean, incumbent_sd = incumbent.mean(0) * 100, incumbent.std(0, ddof=1) * 100
    entrant_mean, entrant_sd = entrant.mean(0) * 100, entrant.std(0, ddof=1) * 100

    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.titlesize": 12})
    fig, ax = plt.subplots(figsize=(7.2, 4.5), constrained_layout=True)
    blue, orange = "#2166ac", "#e08214"
    ax.plot(x, incumbent_mean, color=blue, lw=2.3, label="Incumbent (N verified decisions)")
    ax.fill_between(x, incumbent_mean - incumbent_sd, incumbent_mean + incumbent_sd, color=blue, alpha=0.16)
    ax.plot(x, entrant_mean, color=orange, lw=2.3, label="Entrant (cold start)")
    ax.fill_between(x, entrant_mean - entrant_sd, entrant_mean + entrant_sd, color=orange, alpha=0.16)

    endpoint_gap = float(incumbent_mean[-1] - entrant_mean[-1])
    ax.annotate(
        f"{endpoint_gap:.2f} pp gap at {int(x[-1]):,} decisions",
        xy=(x[-1], entrant_mean[-1]), xytext=(-155, 25), textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": "#444"}, fontsize=9,
        bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#bbbbbb"},
    )
    ax.set_title("Routing-Accuracy Moat: Incumbent vs Entrant")
    ax.set_xlabel("Verified decisions")
    ax.set_ylabel("Routing accuracy (%)")
    ax.set_xlim(left=0)
    ax.set_ylim(40, 65)
    ax.grid(axis="both", which="major", color="#d9d9d9", lw=0.8)
    ax.legend(loc="upper left", frameon=True, framealpha=0.95)
    ax.spines[["top", "right"]].set_visible(False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
