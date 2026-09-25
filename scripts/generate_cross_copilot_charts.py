"""Generate cross-copilot K learning curve publication charts."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "vld"
CHARTS = EXP / "charts"
COPILOTS = ["dataops", "trading", "purchasing", "soc", "s2p"]


def load(name: str) -> dict:
    path = EXP / ("k_learning_curve_results.json" if name == "dataops" else f"k_learning_curve_{name}.json")
    return json.loads(path.read_text(encoding="utf-8"))


def tensor_cells(payload: dict) -> int:
    if "tensor_cells" in payload:
        return int(payload["tensor_cells"])
    return len(payload["category_names"]) * len(payload["action_names"]) * len(payload["factor_names"])


def starvation(payload: dict) -> tuple[float, int, int]:
    if "starvation" in payload:
        s = payload["starvation"]
        return float(s["starvation_rate"]), int(s["starved_category_dims"]), int(s["total_category_dims"])
    final = payload["checkpoints"][-1]["learning_arm"]["k_weights_by_category"]
    total = 0
    starved = 0
    for weights in final.values():
        for w in weights:
            total += 1
            if abs(float(w) - 0.5) <= 1e-9:
                starved += 1
    return (starved / total if total else 0.0), starved, total


def style():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
    })


def save(fig, name: str):
    CHARTS.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(CHARTS / name, dpi=180)
    plt.close(fig)


def main():
    style()
    data = {name: load(name) for name in COPILOTS}

    fig, ax = plt.subplots(figsize=(9, 5))
    control_sum = None
    for name, payload in data.items():
        xs = [c["decision_count"] for c in payload["checkpoints"]]
        ys = [c["learning_arm"]["routing_quality"] for c in payload["checkpoints"]]
        cs = [c["control_arm"]["routing_quality"] for c in payload["checkpoints"]]
        control_sum = cs if control_sum is None else [a + b for a, b in zip(control_sum, cs)]
        ax.plot(xs, ys, marker="o", linewidth=2, label=f"{name} ({tensor_cells(payload)})")
    avg_control = [v / len(data) for v in control_sum]
    ax.plot(xs, avg_control, linestyle="--", color="gray", linewidth=2, label="avg control")
    ax.set_title("K Learning Routing Quality Across Copilots")
    ax.set_xlabel("Decisions")
    ax.set_ylabel("Routing quality")
    ax.set_ylim(0, 1)
    ax.legend(ncol=2, frameon=False)
    save(fig, "pub_cross_copilot_routing.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    names = list(data)
    rates = [starvation(data[n])[0] for n in names]
    bars = ax.bar(names, rates, color="#4C78A8")
    ax.set_title("Dimension Starvation by Copilot and Tensor Size")
    ax.set_ylabel("Starvation rate")
    ax.set_ylim(0, max(0.1, max(rates) * 1.25))
    for bar, name in zip(bars, names):
        rate, starved, total = starvation(data[name])
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{tensor_cells(data[name])}\n{starved}/{total}", ha="center", va="bottom", fontsize=9)
    save(fig, "pub_cross_copilot_starvation.png")

    fig, ax = plt.subplots(figsize=(9, 5))
    for name, payload in data.items():
        xs = [c["decision_count"] for c in payload["checkpoints"]]
        ys = [c["learning_arm"]["accuracy"] for c in payload["checkpoints"]]
        ax.plot(xs, ys, marker="o", linewidth=2, label=f"{name} ({tensor_cells(payload)})")
    ax.set_title("K Learning Accuracy Across Copilots")
    ax.set_xlabel("Decisions")
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0, 1)
    ax.legend(ncol=2, frameon=False)
    save(fig, "pub_cross_copilot_accuracy.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    for name, payload in data.items():
        ax.scatter([tensor_cells(payload)], [starvation(payload)[0]], s=80)
        ax.annotate(name, (tensor_cells(payload), starvation(payload)[0]), xytext=(5, 5), textcoords="offset points")
    ax.set_title("Tensor Size vs Dimension Starvation Rate")
    ax.set_xlabel("Tensor cells")
    ax.set_ylabel("Starvation rate")
    ax.set_ylim(0, max(0.1, max(starvation(p)[0] for p in data.values()) * 1.25))
    save(fig, "pub_tensor_vs_starvation.png")

    for path in sorted(CHARTS.glob("pub_*.png")):
        print(path)


if __name__ == "__main__":
    main()
