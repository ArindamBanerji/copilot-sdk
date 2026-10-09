"""Render the two RL outreach figures from the supplied publication brief.

No experiments are run. Fitted-linear's -35.6% is recovery of fitted-Q's
gain, not a percentage-point change against closed-form routing. The final
recurrence step uses the requested illustrative 52%, explicitly labelled.

Layout uses a 100-pixel-per-inch presentation grid with 14/11/10 pt text.
Matplotlib renders at 300 dpi before antialiased reduction to the exact
requested pixel dimensions; the final PNGs retain 300 dpi print metadata.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import shutil
from typing import Literal

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "experiments/jm_extracted/charts"
COPY_OUTPUT = ROOT / "experiments/vld/charts"
DPI = 300
BACKGROUND = "#FAFAFA"
NAVY = "#17324D"
GREEN = "#16A34A"
RED = "#DC2626"
AMBER = "#D99A14"
GRAY = "#64748B"
GRID = "#E2E8F0"


def style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 11,
        "text.color": NAVY,
        "axes.labelcolor": NAVY,
        "xtick.color": GRAY,
        "ytick.color": NAVY,
        "figure.facecolor": BACKGROUND,
        "axes.facecolor": BACKGROUND,
        "axes.edgecolor": GRID,
        "savefig.facecolor": BACKGROUND,
        "figure.dpi": DPI,
    })


def clean_axes(ax: Axes, grid_axis: Literal["x", "y"] = "x") -> None:
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(length=0, pad=7)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def save(fig: Figure, filename: str, size: tuple[int, int]) -> Path:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    COPY_OUTPUT.mkdir(parents=True, exist_ok=True)
    buffer = BytesIO()
    # No tight bounding-box crop: preserve the exact canvas aspect ratio.
    fig.savefig(buffer, format="png", dpi=DPI)
    plt.close(fig)
    buffer.seek(0)
    target = OUTPUT / filename
    with Image.open(buffer) as rendered:
        final = rendered.convert("RGB").resize(size, Image.Resampling.LANCZOS)
        final.save(target, dpi=(DPI, DPI))
    shutil.copy2(target, COPY_OUTPUT / filename)
    with Image.open(target) as check:
        assert check.size == size, (target, check.size)
        assert all(abs(value - DPI) < 0.1 for value in check.info["dpi"])
        check.verify()
    assert target.stat().st_size > 10 * 1024, target
    assert target.read_bytes() == (COPY_OUTPUT / filename).read_bytes()
    return target


def render_offline_routing() -> Path:
    fig = plt.figure(figsize=(9.8, 5), constrained_layout=True)
    layout = fig.add_gridspec(3, 1, height_ratios=[2.2, 1.15, 0.8])
    routing = fig.add_subplot(layout[0])
    linear = fig.add_subplot(layout[1])
    footer = fig.add_subplot(layout[2])
    fig.suptitle("Why not just use RL for routing?", fontsize=14,
                 fontweight="bold", x=0.5)

    clean_axes(routing)
    routing.axvline(0, color=NAVY, linewidth=1.2)
    routing.barh(1, 15.5, height=0.36, color=GREEN, alpha=0.9)
    routing.errorbar(15.5, 1, xerr=5.5, fmt="none", ecolor=NAVY,
                     capsize=6, elinewidth=1.6)
    routing.barh(0, -32.75, height=0.36, color=RED, alpha=0.9)
    routing.text(15.5, 1.29, "+10 to +21 pp", ha="center", fontsize=11,
                 fontweight="bold", color=GREEN)
    routing.text(-32.75, 0.29, "−32.75 pp", ha="left", fontsize=11,
                 fontweight="bold", color=RED)
    routing.set_yticks([1, 0], ["Fitted-Q\nin-distribution", "Fitted-Q\nout-of-distribution"])
    routing.set_xlim(-40, 26)
    routing.set_ylim(-0.5, 1.7)
    routing.set_xticks([-40, -20, 0, 20], ["−40", "−20", "0", "+20"])
    routing.set_xlabel("Routing change (pp) · 0 = closed-form baseline", fontsize=10)

    # Separate scale prevents percentage recovery being read as a pp loss.
    clean_axes(linear)
    linear.axvline(0, color=NAVY, linewidth=1.2)
    linear.barh(0, -35.6, height=0.42, color=RED, alpha=0.9)
    linear.text(-35.6, 0.31, "−35.6%", color=RED, fontweight="bold", fontsize=11)
    linear.set_yticks([0], ["Fitted-linear"])
    linear.set_xlim(-40, 26)
    linear.set_ylim(-0.4, 0.75)
    linear.set_xticks([-40, -20, 0, 20], ["−40%", "−20%", "0%", "+20%"])
    linear.set_xlabel("Fitted-Q gain recovered (%) · separate metric", fontsize=10)

    footer.set_axis_off()
    footer.text(0.5, 0.55,
                "Learned routing = per-deployment upgrade.\nClosed-form = portable default.",
                ha="center", va="center", fontsize=10, fontweight="bold",
                transform=footer.transAxes)
    return save(fig, "rl_offline_routing.png", (980, 500))


def render_recurrence_ladder() -> Path:
    fig = plt.figure(figsize=(9.8, 4), constrained_layout=True)
    layout = fig.add_gridspec(2, 1, height_ratios=[4.2, 1])
    ax = fig.add_subplot(layout[0])
    footer = fig.add_subplot(layout[1])
    fig.suptitle("Where does more RL machinery help?", fontsize=14, fontweight="bold")
    clean_axes(ax, "y")
    ax.set_xlim(0, 3)
    ax.set_ylim(48, 66)
    ax.set_yticks([48, 52, 56, 60, 64], ["48%", "52%", "56%", "60%", "64%"])
    ax.set_ylabel("Routing quality (%)")
    ax.set_xticks([0.5, 1.5, 2.5], [
        "Static closed-form router\n(acquisition level)",
        "Carried recurrent state",
        "Gated variants",
    ])
    ax.hlines(60.8, 0, 1, color=GREEN, linewidth=3.5)
    ax.vlines(1, 56.6, 60.8, color=AMBER, linewidth=2)
    ax.hlines(56.6, 1, 2, color=AMBER, linewidth=3.5)
    ax.vlines(2, 52, 56.6, color=GRAY, linewidth=2, linestyles="dashed")
    ax.hlines(52, 2, 3, color=GRAY, linewidth=3.5, linestyles="dashed")
    for center, value, color in [(0.5, 60.8, GREEN), (1.5, 56.6, AMBER), (2.5, 52.0, GRAY)]:
        ax.scatter(center, value, s=55, color=color, zorder=3)
    ax.text(0.5, 62.0, "60.8%", ha="center", color=GREEN, fontweight="bold", fontsize=12)
    ax.text(1.5, 57.8, "56.6%", ha="center", color="#9A6B08", fontweight="bold", fontsize=12)
    ax.text(2.5, 53.2, "<56.6% · below both\n~52% representative", ha="center",
            color=GRAY, fontsize=10)
    footer.set_axis_off()
    footer.text(0.5, 0.75, "Value appears at acquisition. More machinery does not help.",
                ha="center", va="center", fontsize=10, fontweight="bold",
                transform=footer.transAxes)
    footer.text(0.5, 0.2, "Dashed step: illustrative placement; exact gated score not supplied.",
                ha="center", va="center", fontsize=9, color=GRAY, transform=footer.transAxes)
    return save(fig, "rl_recurrence_ladder.png", (980, 400))


def main() -> None:
    style()
    for path in (render_offline_routing(), render_recurrence_ladder()):
        print(f"{path.relative_to(ROOT)}: {path.stat().st_size:,} bytes")
        copy = COPY_OUTPUT / path.name
        print(f"{copy.relative_to(ROOT)}: {copy.stat().st_size:,} bytes (identical copy)")


if __name__ == "__main__":
    main()
