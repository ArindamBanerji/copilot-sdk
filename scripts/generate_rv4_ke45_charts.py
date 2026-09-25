"""Generate RV-4 / KE-4 / KE-5 charts and combined report."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
VLD = ROOT / "experiments" / "vld"
CHARTS = VLD / "charts"
REPORT = VLD / "rv4_ke45_report.md"


def load(name: str) -> dict:
    return json.loads((VLD / name).read_text(encoding="utf-8"))


def style() -> None:
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


def mean_curve(runs: list[dict], key: str = "routing_quality") -> list[float]:
    n = len(runs[0]["checkpoints"])
    return [
        float(sum(run["checkpoints"][i][key] for run in runs) / len(runs))
        for i in range(n)
    ]


def save_rv4_charts(rv4: dict) -> None:
    summary = rv4["summary"]["by_copilot"]
    copilots = list(summary)
    uniform = [summary[c]["uniform_fixed_budget"]["routing_quality"] for c in copilots]
    adaptive = [summary[c]["adaptive_budget"]["routing_quality"] for c in copilots]
    penalties = [summary[c]["penalty_ratio"] for c in copilots]
    gains = [summary[c]["adaptive_routing_gain"] for c in copilots]

    x = np.arange(len(copilots))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(x - width / 2, uniform, width, label="Uniform B=2", color="#737373")
    ax.bar(x + width / 2, adaptive, width, label="Adaptive B", color="#2563eb")
    ax.set_title("RV-4 Adaptive Budget")
    ax.set_ylabel("Routing quality")
    ax.set_xticks(x)
    ax.set_xticklabels(copilots)
    ax.set_ylim(0, 1)
    ax.grid(True, axis="y")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(CHARTS / "pub_rv4_adaptive_budget.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.scatter(penalties, gains, s=80, color="#2563eb")
    for copilot, penalty, gain in zip(copilots, penalties, gains):
        ax.annotate(copilot, (penalty, gain), xytext=(5, 5), textcoords="offset points")
    ax.axhline(0, color="#737373", linestyle="--", linewidth=1)
    ax.set_title("RV-4 Penalty vs Routing Gain")
    ax.set_xlabel("Penalty ratio")
    ax.set_ylabel("Adaptive gain")
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(CHARTS / "pub_rv4_penalty_vs_gain.png", dpi=180)
    plt.close(fig)


def save_ke4_charts(ke4: dict) -> None:
    results = ke4["results"]
    xs = [50 * (i + 1) for i in range(10)]
    colors = {"uniform": "#2563eb", "clustered": "#16a34a", "adversarial": "#dc2626"}

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for dist, runs in results.items():
        ax.plot(xs, mean_curve(runs), marker="o", linewidth=2, color=colors[dist], label=dist)
    ax.set_title("KE-4 Distribution Robustness")
    ax.set_xlabel("Decision count")
    ax.set_ylabel("Routing quality")
    ax.set_ylim(0, 1)
    ax.grid(True, axis="y")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(CHARTS / "pub_ke4_distribution_robustness.png", dpi=180)
    plt.close(fig)

    summary = ke4["summary"]
    dists = list(summary)
    quality = [summary[d]["final_routing_quality"] for d in dists]
    starvation = [summary[d]["starvation_rate"] for d in dists]
    x = np.arange(len(dists))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    ax.bar(x - width / 2, quality, width, label="Routing", color="#2563eb")
    ax.bar(x + width / 2, starvation, width, label="Starvation", color="#f97316")
    ax.set_title("KE-4 Final Comparison")
    ax.set_ylabel("Rate")
    ax.set_xticks(x)
    ax.set_xticklabels(dists)
    ax.set_ylim(0, 1)
    ax.grid(True, axis="y")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(CHARTS / "pub_ke4_final_comparison.png", dpi=180)
    plt.close(fig)


def conservation_curve(ke5: dict, arm: str, key: str) -> list[float]:
    runs = ke5["runs"]
    n = len(runs[0]["checkpoints"][arm])
    return [
        float(sum(run["checkpoints"][arm][i][key] for run in runs) / len(runs))
        for i in range(n)
    ]


def save_ke5_charts(ke5: dict) -> None:
    xs = [50 * (i + 1) for i in range(10)]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(xs, conservation_curve(ke5, "without_conservation", "routing_quality"), marker="o", linewidth=2, label="No conservation", color="#737373")
    ax.plot(xs, conservation_curve(ke5, "with_conservation", "routing_quality"), marker="o", linewidth=2, label="With conservation", color="#2563eb")
    ax.set_title("KE-5 Conservation Curves")
    ax.set_xlabel("Decision count")
    ax.set_ylabel("Routing quality")
    ax.set_ylim(0, 1)
    ax.grid(True, axis="y")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(CHARTS / "pub_ke5_conservation_curves.png", dpi=180)
    plt.close(fig)

    runs = ke5["runs"]
    blocked = [
        float(sum(run["blocked_by_checkpoint"][i]["blocked_updates"] for run in runs) / len(runs))
        for i in range(10)
    ]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(xs, blocked, marker="o", linewidth=2, color="#dc2626")
    ax.set_title("KE-5 Blocked K Updates")
    ax.set_xlabel("Decision count")
    ax.set_ylabel("Blocked updates")
    ax.grid(True, axis="y")
    fig.tight_layout()
    fig.savefig(CHARTS / "pub_ke5_blocked_updates.png", dpi=180)
    plt.close(fig)


def fmt(value: float) -> str:
    return f"{value:.3f}"


def write_report(rv4: dict, ke4: dict, ke5: dict) -> None:
    rv4_summary = rv4["summary"]
    ke4_summary = ke4["summary"]
    ke5_summary = ke5["summary"]
    lines: list[str] = []
    lines.append("# RV-4 / KE-4 / KE-5 Combined Report")
    lines.append("")
    lines.append("## 1. RV-4 Risk-Sensitive Q")
    lines.append("")
    lines.append("Fixed budget confirmed the expected scale-invariance: multiplying Q by a domain penalty ratio does not materially change dimension order at B=2. The risk-fixed arm is near the uniform-fixed arm for each copilot; differences are seed and learning-path noise, not a routing mechanism change.")
    lines.append("")
    lines.append("| Copilot | Penalty | Uniform B=2 | Risk B=2 | Adaptive B | Adaptive gain | Thompson+risk | S1 abstain |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for copilot, item in rv4_summary["by_copilot"].items():
        lines.append(
            f"| {copilot} | {item['penalty_ratio']:.0f} | "
            f"{fmt(item['uniform_fixed_budget']['routing_quality'])} | "
            f"{fmt(item['risk_fixed_budget']['routing_quality'])} | "
            f"{fmt(item['adaptive_budget']['routing_quality'])} | "
            f"{fmt(item['adaptive_routing_gain'])} | "
            f"{fmt(item['thompson_risk']['routing_quality'])} | "
            f"{fmt(item['adaptive_budget']['s1_abstain_calibration'])} |"
        )
    verdict = rv4_summary["kill_keep"]
    lines.append("")
    lines.append(f"Kill/keep verdict: **{verdict['verdict']}**. High-penalty mean adaptive gain was {fmt(verdict['high_penalty_mean_gain'])}, low-penalty no-degradation was `{verdict['low_penalty_no_degradation']}`, and abstain calibration was not degraded: `{verdict['abstain_calibration_not_degraded']}`.")
    lines.append("")
    lines.append("The adaptive-budget policy increased reads in high-penalty domains but reduced routing-quality-per-read because later reads are less often informative. Accuracy can still improve in some domains because extra reads recover more cases, but RV-4 as a Q multiplier is not supported as a clean RGI strengthening result.")
    lines.append("")
    lines.append("## 2. KE-4 Distribution Sensitivity")
    lines.append("")
    lines.append("| Distribution | Final routing | Final accuracy | Hurts | Starvation |")
    lines.append("|---|---:|---:|---:|---:|")
    for dist, item in ke4_summary.items():
        lines.append(f"| {dist} | {fmt(item['final_routing_quality'])} | {fmt(item['final_accuracy'])} | {item['hurts']} | {fmt(item['starvation_rate'])} |")
    lines.append("")
    lines.append(f"Pre-registered verdict: **{ke4['verdict']}**. All three distributions produced positive routing quality over the fixed-control reference region with zero final-checkpoint hurts. The adversarial case was lower than uniform ({fmt(ke4_summary['adversarial']['final_routing_quality'])} vs {fmt(ke4_summary['uniform']['final_routing_quality'])}) and had higher starvation ({fmt(ke4_summary['adversarial']['starvation_rate'])}), so the effect is robust but distribution-sensitive.")
    lines.append("")
    lines.append("## 3. KE-5 Conservation Interaction")
    lines.append("")
    lines.append("| Arm | Final routing | Final accuracy | Routing dip | Accuracy dip |")
    lines.append("|---|---:|---:|---:|---:|")
    for arm in ("without_conservation", "with_conservation"):
        item = ke5_summary[arm]
        lines.append(f"| {arm} | {fmt(item['final_routing_quality'])} | {fmt(item['final_accuracy'])} | {fmt(item['mean_routing_dip'])} | {fmt(item['mean_accuracy_dip'])} |")
    lines.append("")
    lines.append(f"Mean blocked updates: **{fmt(ke5_summary['blocked_updates_mean'])}**. Final routing cost: **{fmt(ke5_summary['final_routing_cost'])}**. Dip reduction: **{fmt(ke5_summary['dip_reduction'])}**.")
    lines.append("")
    lines.append("Under the experimental paper-formula gate, the DataOps trajectory stayed GREEN after the cold-start window, so conservation neither slowed nor improved K learning in this run. This is a neutral interaction result, not evidence that conservation is unnecessary under drift or poisoned verification.")
    lines.append("")
    lines.append("## 4. Combined Implications")
    lines.append("")
    lines.append("- For the paper: KE-4 strengthens the K-learning/RGI claim by showing the DataOps effect survives uniform, clustered, and adversarial training distributions, with the caveat that adversarial training raises starvation.")
    lines.append("- For §12.2: distribution sensitivity is validated as measured; risk-sensitive Q should be qualified or moved to a rejected/needs-redesign extension; conservation interaction is measured but neutral under this synthetic trajectory.")
    lines.append("- For production: extra budget should be justified by expected accuracy or harm reduction, not by Q scaling alone. Conservation remains a safety boundary for degradation regimes, but this experiment did not trigger it.")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    style()
    rv4 = load("rv4_risk_sensitive_results.json")
    ke4 = load("ke4_distribution_sensitivity_results.json")
    ke5 = load("ke5_conservation_interaction_results.json")
    save_rv4_charts(rv4)
    save_ke4_charts(ke4)
    save_ke5_charts(ke5)
    write_report(rv4, ke4, ke5)
    for path in sorted(CHARTS.glob("pub_rv4_*.png")) + sorted(CHARTS.glob("pub_ke4_*.png")) + sorted(CHARTS.glob("pub_ke5_*.png")):
        print(path)
    print(REPORT)


if __name__ == "__main__":
    main()
