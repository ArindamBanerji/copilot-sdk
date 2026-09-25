"""Render B2 checkpoint data; never fit or invent learning trajectories.

Run mypy on this file before execution. Headline gaps use the incumbent's
final-three reference minus the competitor at that seed's incumbent horizon.
Curve averages instead use actual checkpoint levels, holding stopped states
constant only through the last observed checkpoint in that domain. Dashed
segments disclose this hold; endpoint gaps are reported separately.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/vld/results/moat_b2_seeds.json"
OUTPUT = ROOT / "experiments/jm_extracted/charts/pub_moat_catchup_v2.png"
INK = "#172B42"
MUTED = "#52667B"
BLUE = "#176A91"
ORANGE = "#BE612F"
GAP = "#DCE9EC"
Record = dict[str, Any]


def gap_label(aggregate: Record, endpoint: bool = False) -> str:
    if endpoint:
        summary = aggregate["endpoint_routing_gap"]
        return f"{summary['mean']:.1f} ± {summary['std']:.1f}pp"
    return f"{aggregate['routing_gap_mean']:.1f} ± {aggregate['routing_gap_std']:.1f}pp"


def validate(domain: Record) -> None:
    rows = list(domain["per_seed"].values())
    aggregate = domain["aggregate"]
    horizon_gaps: list[float] = []
    endpoint_gaps: list[float] = []
    for row in rows:
        incumbent = row["arm1"]["checkpoints_on_SA_heldout"]
        entrant = row["arm2"]["checkpoints_on_SA_heldout"]
        for points in (incumbent, entrant):
            assert all(p["decision_count"] == p["labels_received"] for p in points)
            assert all(0 <= p["routing_quality"] <= 1 for p in points)
            assert all(p["evaluation_set_sha256"] == incumbent[0]["evaluation_set_sha256"] for p in points)
        reference = float(np.mean([p["routing_quality"] for p in incumbent[-3:]]))
        assert np.isclose(reference, row["arm1_converged_reference"]["routing_quality"])
        at_horizon = [p for p in entrant if p["decision_count"] <= incumbent[-1]["decision_count"]][-1]
        assert np.isclose(at_horizon["routing_quality"], row["arm2_at_arm1_horizon"]["routing_quality"])
        horizon_gaps.append(100 * (reference - at_horizon["routing_quality"]))
        endpoint_gaps.append(100 * (reference - entrant[-1]["routing_quality"]))
    assert np.isclose(np.mean(horizon_gaps), aggregate["routing_gap_mean"])
    assert np.isclose(np.std(horizon_gaps, ddof=1), aggregate["routing_gap_std"])
    assert np.isclose(np.mean(endpoint_gaps), aggregate["endpoint_routing_gap"]["mean"])
    assert np.isclose(np.std(endpoint_gaps, ddof=1), aggregate["endpoint_routing_gap"]["std"])
    assert sum(r["arm2_sustained_parity"] for r in rows) == aggregate["seeds_reaching_parity"]


def panel(ax: Axes, domain: Record, name: str) -> None:
    rows = list(domain["per_seed"].values())
    aggregate = domain["aggregate"]
    all_points = [r[a]["checkpoints_on_SA_heldout"] for r in rows for a in ("arm1", "arm2")]
    last_n = max(points[-1]["decision_count"] for points in all_points)
    grid = np.arange(0, last_n + 1, 50)
    means = []
    for arm, color in (("arm1", BLUE), ("arm2", ORANGE)):
        curves = []
        stops = []
        for row in rows:
            points = row[arm]["checkpoints_on_SA_heldout"]
            lookup = {p["decision_count"]: p["routing_quality"] * 100 for p in points}
            stop = points[-1]["decision_count"]
            stops.append(stop)
            # Every pre-stop point is directly measured. No interpolation.
            curves.append([lookup[min(int(n), stop)] for n in grid])
        mean = np.mean(curves, axis=0)
        means.append(mean)
        all_observed = grid <= min(stops)
        includes_hold = grid >= min(stops)
        ax.plot(grid[all_observed], mean[all_observed], color=color, lw=2.8,
                marker="o", markersize=3.8, zorder=4)
        ax.plot(grid[includes_hold], mean[includes_hold], color=color, lw=2.8,
                linestyle=(0, (4, 2)), zorder=4)
        ax.scatter([grid[-1]], [mean[-1]], color=color, s=26, zorder=5)
    ax.fill_between(grid, means[0], means[1], color=GAP, alpha=0.85)
    ax.set(xlim=(0, 1000), xlabel="Verified decisions", ylabel="Routing quality (%)")
    ax.set_xticks([0, 250, 500, 750, 1000])
    ax.set_ylim((48, 87) if name == "SOC" else (42, 63))
    ax.set_title(f"{name}  |  incumbent's held-out decisions", loc="left", fontsize=13,
                 fontweight="bold", pad=17)
    ax.grid(axis="y", color="#DEE5E9", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color("#BECBD4")
    ax.tick_params(colors=MUTED, length=0, pad=8)
    y = 70.0 if name == "SOC" else 46.0
    x = 660 if name == "SOC" else 480
    ax.text(x, y, f"{gap_label(aggregate)} ({name})", ha="center", color=INK,
            fontsize=18 if name == "SOC" else 15, weight="bold")
    ax.text(x, y - (2.1 if name == "SOC" else 1.2), "At incumbent convergence horizon",
            ha="center", fontsize=10, color=MUTED)
    n = len(rows)
    ax.text(0.04, 0.94, f"{aggregate['seeds_reaching_parity']} of {n} seeds reach parity",
            transform=ax.transAxes, fontsize=11, color=INK,
            bbox={"boxstyle": "round,pad=0.5", "fc": "#F1F5F7", "ec": "none"})
    print(f"{name}: horizon {aggregate['routing_gap_mean']:.10f} ± "
          f"{aggregate['routing_gap_std']:.10f}pp; endpoint {gap_label(aggregate, True)}; "
          f"direct checkpoints through N={last_n}, frozen states disclosed")


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    data: Record = json.loads(source_bytes)
    for name in ("soc", "dataops"):
        validate(data[name])
    soc = data["soc"]["aggregate"]
    dataops = data["dataops"]["aggregate"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "text.color": INK, "axes.labelcolor": INK,
                         "axes.titlecolor": INK, "axes.facecolor": "#FFFFFF",
                         "figure.facecolor": "#FAFCFD", "axes.labelpad": 12})
    fig = plt.figure(figsize=(15.5, 9.5), layout="constrained")
    fig.set_constrained_layout_pads(w_pad=0.3, h_pad=0.2, hspace=0.05, wspace=0.06)
    layout = fig.add_gridspec(3, 2, height_ratios=[1.25, 4.5, 1.65], width_ratios=[1.55, 1])
    header = fig.add_subplot(layout[0, :])
    header.axis("off")
    header.text(0, 0.96, "First-Mover Moat: Non-Transferable Judgment", fontsize=23,
                weight="bold", va="top")
    header.text(0, 0.59, "Competitor on a different firm's stream never reaches parity",
                fontsize=16, va="top")
    header.text(0, 0.29, f"{gap_label(soc)} gap (SOC), {soc['seeds_reaching_parity']}/5 seeds"
                "  •  within the measured B2 horizons", fontsize=14, color=BLUE, va="top")
    panel(fig.add_subplot(layout[1, 0]), data["soc"], "SOC")
    panel(fig.add_subplot(layout[1, 1]), data["dataops"], "DataOps")
    footer = fig.add_subplot(layout[2, :])
    footer.axis("off")
    footer.legend(handles=[Line2D([], [], color=BLUE, lw=3, label="Incumbent · own firm's stream"),
                           Line2D([], [], color=ORANGE, lw=3, label="Competitor · different-firm stream")],
                  loc="upper left", bbox_to_anchor=(-0.008, 1.08), frameon=False, ncol=2,
                  fontsize=12, handlelength=2.5, columnspacing=3)
    notes = [
        "Direct 50-decision checkpoints; curves are five-seed means. Dashed segments include states frozen after each arm stops.",
        "Headline gaps: incumbent's final-three mean minus competitor at each incumbent horizon; ± denotes sample SD across seeds.",
        f"Separate endpoint gaps: SOC {gap_label(soc, True)}; DataOps {gap_label(dataops, True)}. No extrapolation beyond observed horizons.",
        "measured (JM apparatus) · Real-component geometry; simulated streams and verification · One alternative-firm profile; K learning only.",
        "Non-transferable, not un-copyable — the gap rests on verified-outcome labels being firm-specific",
        "Source: experiments/vld/results/moat_b2_seeds.json",
    ]
    for i, note in enumerate(notes):
        footer.text(0, 0.74 - i * 0.14, note, va="top", fontsize=10.2,
                    color=INK if i == 4 else MUTED, weight="medium" if i == 4 else "normal")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=300, metadata={
        "Title": "First-Mover Moat: Non-Transferable Judgment",
        "Description": "B2 measured checkpoint means; dashed frozen states; headline horizon gaps distinct from endpoint gaps.",
        "Source": SOURCE.relative_to(ROOT).as_posix(),
        "SourceSHA256": hashlib.sha256(source_bytes).hexdigest(),
    })
    plt.close(fig)
    print(f"{OUTPUT}: {OUTPUT.stat().st_size:,} bytes; 300 dpi")


if __name__ == "__main__":
    main()
