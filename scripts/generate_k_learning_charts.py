"""Generate publication charts for the K learning curve experiment."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "experiments" / "vld" / "k_learning_curve_results.json"
CHART_DIR = ROOT / "experiments" / "vld" / "charts"


def load_results() -> dict:
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))


def setup_style() -> None:
    plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#333333",
            "axes.labelcolor": "#222222",
            "xtick.color": "#222222",
            "ytick.color": "#222222",
            "grid.color": "#dddddd",
            "font.size": 10,
        }
    )


def with_origin(xs: list[int], values: list[float], origin: float) -> tuple[list[int], list[float]]:
    return [0, *xs], [origin, *values]


def save_line_chart(
    xs: list[int],
    learning: list[float],
    control: list[float],
    ylabel: str,
    title: str,
    filename: str,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x_learning, y_learning = with_origin(xs, learning, control[0] if control else 0.0)
    x_control, y_control = with_origin(xs, control, control[0] if control else 0.0)
    ax.plot(x_learning, y_learning, color="#2563eb", linewidth=2.4, marker="o", label="Learning")
    ax.plot(x_control, y_control, color="#737373", linewidth=2.0, linestyle="--", marker="s", label="Fixed K")
    ax.set_title(title, pad=12)
    ax.set_xlabel("Decision count")
    ax.set_ylabel(ylabel)
    ax.set_ylim(0.0, 1.02)
    ax.grid(True, axis="y", linewidth=0.8)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(CHART_DIR / filename, dpi=180)
    plt.close(fig)


def save_heatmap(data: dict) -> None:
    checkpoints = data["checkpoints"]
    categories = data["category_names"]
    factors = data["factor_names"]
    snapshots = [0, 100, 250, 500]
    by_count = {item["decision_count"]: item for item in checkpoints}
    initial = {category: [0.5] * len(factors) for category in categories}

    fig, axes = plt.subplots(1, 4, figsize=(14, 5), constrained_layout=True)
    image = None
    for ax, count in zip(axes, snapshots):
        weights = initial if count == 0 else by_count[count]["learning_arm"]["k_weights_by_category"]
        matrix = np.asarray([weights[category] for category in categories], dtype=float)
        image = ax.imshow(matrix, vmin=0.1, vmax=3.0, cmap="viridis", aspect="auto")
        ax.set_title(f"N={count}")
        ax.set_xticks(range(len(factors)))
        ax.set_xticklabels([f"D{i}" for i in range(len(factors))])
        ax.set_yticks(range(len(categories)))
        ax.set_yticklabels(categories if ax is axes[0] else [])
    fig.suptitle("K Weight Evolution by Category and Dimension", y=1.04)
    if image is not None:
        fig.colorbar(image, ax=axes, shrink=0.8, label="K weight")
    fig.savefig(CHART_DIR / "pub_k_heatmap_evolution.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_convergence(data: dict) -> None:
    checkpoints = data["checkpoints"]
    categories = data["category_names"]
    factors = data["factor_names"]
    category = categories[0]
    xs = [0, *[item["decision_count"] for item in checkpoints]]
    final_weights = np.asarray(
        checkpoints[-1]["learning_arm"]["k_weights_by_category"][category],
        dtype=float,
    )
    top = list(np.argsort(final_weights)[-3:][::-1])
    bottom = list(np.argsort(final_weights)[:3])
    dims = top + [dim for dim in bottom if dim not in top]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    colors = ["#2563eb", "#16a34a", "#9333ea", "#737373", "#a3a3a3", "#d4d4d4"]
    for idx, dim in enumerate(dims):
        values = [0.5]
        values.extend(
            item["learning_arm"]["k_weights_by_category"][category][dim]
            for item in checkpoints
        )
        ax.plot(
            xs,
            values,
            linewidth=2.0,
            marker="o",
            color=colors[idx % len(colors)],
            label=f"D{dim}: {factors[dim]}",
        )
    ax.set_title("Per-Dimension K Weight Convergence", pad=12)
    ax.set_xlabel("Decision count")
    ax.set_ylabel("K weight")
    ax.set_ylim(0.05, 3.05)
    ax.grid(True, axis="y", linewidth=0.8)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "pub_k_convergence.png", dpi=180)
    plt.close(fig)


def main() -> None:
    data = load_results()
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    setup_style()
    checkpoints = data["checkpoints"]
    xs = [item["decision_count"] for item in checkpoints]
    save_line_chart(
        xs,
        [item["learning_arm"]["routing_quality"] for item in checkpoints],
        [item["control_arm"]["routing_quality"] for item in checkpoints],
        "Routing quality",
        "K Utility Learning: Routing Quality vs Decision Count",
        "pub_k_learning_routing.png",
    )
    save_line_chart(
        xs,
        [item["learning_arm"]["accuracy"] for item in checkpoints],
        [item["control_arm"]["accuracy"] for item in checkpoints],
        "Accuracy",
        "K Utility Learning: Decision Accuracy vs Decision Count",
        "pub_k_learning_accuracy.png",
    )
    save_heatmap(data)
    save_convergence(data)
    for path in sorted(CHART_DIR.glob("*.png")):
        print(path)


if __name__ == "__main__":
    main()
