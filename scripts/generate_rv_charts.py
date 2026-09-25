"""Generate charts and report for RV-0/RV-1 routing experiments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "experiments" / "vld"
CHART_DIR = EXP_DIR / "charts"
RV0_PATH = EXP_DIR / "rv0_gru_ablation_results.json"
RV1_PATH = EXP_DIR / "rv1_bandit_results.json"
REPORT_PATH = EXP_DIR / "rv01_routing_variants_report.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save(fig: plt.Figure, name: str) -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    out = CHART_DIR / name
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"Wrote {out}")


def chart_rv0_routing(rv0: dict[str, Any]) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for variant in rv0["variants"]:
        rows = rv0["results"][variant]["checkpoints"]
        x = np.array([row["decision_count"] for row in rows])
        y = np.array([row["routing_mean"] for row in rows])
        s = np.array([row["routing_std"] for row in rows])
        ax.plot(x, y, label=variant.upper(), linewidth=2)
        ax.fill_between(x, y - s, y + s, alpha=0.14)
    ax.set_title("RV-0 Routing Quality")
    ax.set_xlabel("Decisions")
    ax.set_ylabel("Informative-read rate")
    ax.set_ylim(0, 1.02)
    ax.legend()
    ax.grid(alpha=0.25)
    save(fig, "pub_rv0_routing_comparison.png")


def chart_rv0_budget(rv0: dict[str, Any]) -> None:
    budgets = [int(b) for b in sorted(rv0["budget_sweep"], key=int)]
    variants = rv0["variants"]
    x = np.arange(len(budgets))
    width = 0.18
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for offset, variant in enumerate(variants):
        y = [rv0["budget_sweep"][str(b)][variant]["final_routing_mean"] for b in budgets]
        ax.bar(x + (offset - 1.5) * width, y, width, label=variant.upper())
    ax.set_title("RV-0 Budget Sweep")
    ax.set_xlabel("Budget")
    ax.set_ylabel("Final routing quality")
    ax.set_xticks(x)
    ax.set_xticklabels([str(b) for b in budgets])
    ax.set_ylim(0, 1.02)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    save(fig, "pub_rv0_budget_sweep.png")


def chart_rv0_cost(rv0: dict[str, Any]) -> None:
    variants = rv0["variants"]
    y = [rv0["results"][variant]["final_accuracy_per_scorer_eval"] for variant in variants]
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.bar([v.upper() for v in variants], y, color=["#6f7dff", "#3ea66b", "#d09035", "#b4588b"])
    ax.set_title("RV-0 Cost Efficiency")
    ax.set_ylabel("Accuracy per scorer evaluation")
    ax.grid(axis="y", alpha=0.25)
    save(fig, "pub_rv0_cost_efficiency.png")


def chart_rv1_starvation(rv1: dict[str, Any]) -> None:
    copilots = rv1["copilots"]
    variants = rv1["variants"]
    x = np.arange(len(copilots))
    width = 0.24
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for offset, variant in enumerate(variants):
        y = [rv1["results"][copilot][variant]["starvation"] * 100.0 for copilot in copilots]
        ax.bar(x + (offset - 1) * width, y, width, label=variant.upper())
    ax.set_title("RV-1 Starvation by Copilot")
    ax.set_ylabel("Starved category-dims (%)")
    ax.set_xticks(x)
    ax.set_xticklabels([c.upper() for c in copilots], rotation=20)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    save(fig, "pub_rv1_starvation_fix.png")


def chart_rv1_routing(rv1: dict[str, Any]) -> None:
    copilots = rv1["copilots"]
    variants = rv1["variants"]
    fig, axes = plt.subplots(len(copilots), 1, figsize=(8, 11), sharex=True, sharey=True)
    for ax, copilot in zip(axes, copilots):
        for variant in variants:
            rows = rv1["results"][copilot][variant]["checkpoints"]
            ax.plot([r["decision_count"] for r in rows], [r["routing_mean"] for r in rows], label=variant.upper())
        ax.set_title(copilot.upper(), loc="left", fontsize=10)
        ax.grid(alpha=0.25)
        ax.set_ylim(0, 1.02)
    axes[-1].set_xlabel("Decisions")
    axes[2].set_ylabel("Routing quality")
    axes[0].legend(ncol=3, loc="upper right")
    save(fig, "pub_rv1_routing_by_copilot.png")


def chart_rv1_speed(rv1: dict[str, Any]) -> None:
    copilots = rv1["copilots"]
    variants = rv1["variants"]
    x = np.arange(len(copilots))
    width = 0.24
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for offset, variant in enumerate(variants):
        y = [rv1["results"][copilot][variant]["decisions_to_90pct_asymptote"] for copilot in copilots]
        ax.bar(x + (offset - 1) * width, y, width, label=variant.upper())
    ax.set_title("RV-1 Learning Speed")
    ax.set_ylabel("Decisions to 90% asymptote")
    ax.set_xticks(x)
    ax.set_xticklabels([c.upper() for c in copilots], rotation=20)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    save(fig, "pub_rv1_learning_speed.png")


def pct(value: float) -> str:
    return f"{value * 100.0:.1f}%"


def report_table_rv0(rv0: dict[str, Any]) -> str:
    lines = ["| Variant | Routing | Accuracy | Accuracy / scorer eval | Starvation | Evals/decision |",
             "|---|---:|---:|---:|---:|---:|"]
    for variant in rv0["variants"]:
        row = rv0["results"][variant]
        lines.append(
            f"| {variant.upper()} | {pct(row['final_routing_mean'])} +/- {pct(row['final_routing_std'])} | "
            f"{pct(row['final_accuracy_mean'])} | {row['final_accuracy_per_scorer_eval']:.4f} | "
            f"{pct(row['starvation_rate'])} | {row['scorer_evals_per_decision']:.2f} |"
        )
    return "\n".join(lines)


def report_table_rv1(rv1: dict[str, Any]) -> str:
    lines = ["| Copilot | Variant | Routing | Accuracy | Starvation | Decisions to 90% |",
             "|---|---|---:|---:|---:|---:|"]
    for copilot in rv1["copilots"]:
        for variant in rv1["variants"]:
            row = rv1["results"][copilot][variant]
            lines.append(
                f"| {copilot} | {variant} | {pct(row['final_routing_mean'])} | "
                f"{pct(row['final_accuracy_mean'])} | {pct(row['starvation'])} | "
                f"{row['decisions_to_90pct_asymptote']} |"
            )
    return "\n".join(lines)


def write_report(rv0: dict[str, Any], rv1: dict[str, Any]) -> None:
    trading = rv1["results"]["trading"]
    greedy_starve = trading["greedy"]["starvation"]
    thompson_starve = trading["thompson"]["starvation"]
    ucb_starve = trading["ucb"]["starvation"]
    recurrence_winner = max(rv0["variants"], key=lambda variant: rv0["results"][variant]["final_routing_mean"])
    selector_winner = rv1["kill_keep_verdict"]
    recommendation = f"{recurrence_winner.upper()} + {selector_winner.upper() if selector_winner != 'greedy' else 'greedy'}"
    text = f"""# RV-0/RV-1 Routing Variant Report

## 1. Protocol and Pre-Registration

RV-0 compared STATIC, RNN, GRU, and LSTM routing on DataOps exported centroids with 10 seeds, 500 decisions, 10 checkpoints, 50 evaluation scenarios per checkpoint, and budget sweeps B=1..4. LSTM is kept only if it exceeds GRU by at least 2 percentage points at matched scorer-evaluation cost.

RV-1 compared greedy Q, Thompson Q, and UCB Q across DataOps, Trading, Purchasing, SOC, and S2P. A bandit variant is kept only if it lowers worst-copilot starvation by at least 10 percentage points, does not reduce final routing quality, and reaches the K-learning asymptote in no more decisions than greedy.

## 2. RV-0 Results -- GRU vs LSTM

{report_table_rv0(rv0)}

Verdict: **{rv0['kill_keep_verdict']}**. {rv0['kill_keep_reason']}

Budget sensitivity: the budget sweep is written in `rv0_gru_ablation_results.json` and charted in `pub_rv0_budget_sweep.png`. The paper decision should use B=2 unless a deployment explicitly operates at B=1 or B=4.

## 3. RV-1 Results -- Bandit Exploration

{report_table_rv1(rv1)}

Trading starvation: greedy={pct(greedy_starve)}, Thompson={pct(thompson_starve)}, UCB={pct(ucb_starve)}.

Verdict: **{rv1['kill_keep_verdict']}**. {rv1['kill_keep_reason']}

## 4. Combined Verdict

Recommended paper configuration from these experiments: **{recommendation}**. RV-0 keeps GRU over LSTM for the specific recurrent-cell ablation, but the best tested RV-0 routing quality at B=2 was {recurrence_winner.upper()}. RV-1 determines whether greedy selection should be replaced with exploration.

## 5. Three-Metric Summary

M-VALUE: RV-0 value is final informative-read routing quality; RV-1 value is final routing quality plus decisions to 90% asymptote. M-COST is accuracy per scorer evaluation for RV-0 and unchanged budget/scorer loop for RV-1. M-GOV remains pass for all tested variants because each hidden/exploration state is dimension-aligned to named factors.

## 6. Implications for Section 12.2

The routing section should report the pre-registered kill/keep criteria, then cite the exact RV-0 and RV-1 verdicts above. If GRU is retained, describe LSTM as an ablated higher-cost recurrence. If a bandit is retained, frame it as an exploration guardrail for high-starvation domains, with Trading as the motivating case.
"""
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


def main() -> None:
    rv0 = load_json(RV0_PATH)
    rv1 = load_json(RV1_PATH)
    chart_rv0_routing(rv0)
    chart_rv0_budget(rv0)
    chart_rv0_cost(rv0)
    chart_rv1_starvation(rv1)
    chart_rv1_routing(rv1)
    chart_rv1_speed(rv1)
    write_report(rv0, rv1)


if __name__ == "__main__":
    main()
