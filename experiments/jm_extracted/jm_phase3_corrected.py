"""Corrected, paired protocols for the 14 failed JM Phase 2 charts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, cast

import matplotlib
import numpy as np
from scipy import optimize, stats  # type: ignore[import]

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "charts"
SEED = 42
BLUE = "#2563eb"
ORANGE = "#f97316"
GREEN = "#16a34a"
RED = "#dc2626"
GRAY = "#6b7280"


def style() -> None:
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "axes.grid": True,
        "grid.color": "#d1d5db",
        "grid.alpha": 0.65,
        "grid.linewidth": 0.6,
    })


def save(fig: Any, name: str) -> None:
    fig.savefig(OUT / name, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def mean_ci(values: np.ndarray, axis: int = 0) -> tuple[np.ndarray, np.ndarray]:
    mean = np.mean(values, axis=axis)
    count = values.shape[axis]
    half = stats.t.ppf(0.975, max(count - 1, 1)) * np.std(values, axis=axis, ddof=1) / math.sqrt(count)
    return np.asarray(mean), np.asarray(half)


def rolling(binary: np.ndarray, window: int) -> np.ndarray:
    output = np.full(binary.shape, np.nan, dtype=float)
    kernel = np.ones(window, dtype=float) / window
    for row in range(binary.shape[0]):
        output[row, window - 1 :] = np.convolve(binary[row], kernel, mode="valid")
    return cast(np.ndarray, np.asarray(output, dtype=float))


def power_fit(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    def curve(x_value: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
        return cast(np.ndarray, np.asarray(a + b * np.power(x_value / np.max(x_value), c), dtype=float))

    params, _ = optimize.curve_fit(
        curve,
        x,
        y,
        p0=[float(y[0]), float(y[-1] - y[0]), 1.0],
        bounds=([-1.0, -2.0, 0.05], [2.0, 2.0, 5.0]),
        maxfev=50000,
    )
    predicted = curve(x, *params)
    denominator = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - float(np.sum((y - predicted) ** 2)) / max(denominator, 1e-12)
    return {"baseline": float(params[0]), "amplitude": float(params[1]), "exponent": float(params[2]), "r2": r2}


def classify(centroids: np.ndarray, category: int, observation: np.ndarray) -> int:
    distances = np.linalg.norm(centroids[category] - observation, axis=1)
    return int(np.argmin(distances))


def e_jm_1() -> dict[str, Any]:
    """Pair the retained-prior and cold-relearn arms on identical Person-B streams."""
    trials, n_a, n_b = 60, 500, 300
    categories, actions, factors = 5, 4, 7
    retained_accuracy = np.zeros((trials, n_b), dtype=float)
    cold_accuracy = np.zeros((trials, n_b), dtype=float)
    shift_size = np.zeros(trials, dtype=float)

    for trial in range(trials):
        rng = np.random.default_rng(SEED + trial)
        person_a = rng.uniform(0.15, 0.85, (categories, actions, factors))
        source = np.full_like(person_a, 0.5)
        source_counts = np.zeros((categories, actions), dtype=int)
        for _ in range(n_a):
            category = int(rng.integers(categories))
            action = int(rng.integers(actions))
            observation = np.clip(person_a[category, action] + rng.normal(0, 0.08, factors), 0, 1)
            source_counts[category, action] += 1
            eta = 1.0 / source_counts[category, action]
            source[category, action] += eta * (observation - source[category, action])

        shifted = rng.choice(factors, 4, replace=False)
        delta = np.zeros(factors)
        delta[shifted] = rng.normal(0, 0.12, 4)
        person_b = np.clip(person_a + delta, 0.02, 0.98)
        shift_size[trial] = float(np.linalg.norm(delta))

        labels = rng.integers(actions, size=n_b)
        cats = rng.integers(categories, size=n_b)
        noise = rng.normal(0, 0.10, (n_b, factors))
        observations = np.asarray([
            np.clip(person_b[cats[i], labels[i]] + noise[i], 0, 1) for i in range(n_b)
        ])

        retained = source.copy()
        cold = np.full_like(source, 0.5)
        retained_counts = np.maximum(source_counts // 4, 1)
        cold_counts = np.zeros_like(source_counts)
        for index in range(n_b):
            category = int(cats[index])
            action = int(labels[index])
            observation = observations[index]
            retained_accuracy[trial, index] = classify(retained, category, observation) == action
            cold_accuracy[trial, index] = classify(cold, category, observation) == action
            retained_counts[category, action] += 1
            cold_counts[category, action] += 1
            eta_retained = min(0.08, 1.0 / retained_counts[category, action])
            eta_cold = min(0.08, 1.0 / cold_counts[category, action])
            retained[category, action] += eta_retained * (observation - retained[category, action])
            cold[category, action] += eta_cold * (observation - cold[category, action])

    differences = np.mean(retained_accuracy - cold_accuracy, axis=1) * 100
    difference_mean, difference_ci = mean_ci(differences)
    fig, ax = plt.subplots(figsize=(9, 6), constrained_layout=True)
    ax.scatter(shift_size, differences, color=np.where(differences >= 0, GREEN, RED), alpha=0.78, edgecolor="white")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Person-B profile shift magnitude")
    ax.set_ylabel("Retained judgment advantage over cold relearn (pp)")
    ax.set_title("E-JM-1: Paired Personnel-Change Recovery")
    ax.text(
        0.02,
        0.97,
        f"Mean advantage {float(difference_mean):+.2f}pp\n95% CI [{float(difference_mean-difference_ci):+.2f}, {float(difference_mean+difference_ci):+.2f}]\nseed base 42",
        transform=ax.transAxes,
        va="top",
        bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "#9ca3af"},
    )
    save(fig, "e_jm_1_benefit_scatter.png")
    return {
        "diagnosis": "design_flaw",
        "fix": "Paired both arms on identical Person-B labels, observations, and noise; compared retained Person-A centroids with cold relearning; corrected the complete 300-decision window.",
        "mean_advantage_pp": float(difference_mean),
        "ci95": [float(difference_mean - difference_ci), float(difference_mean + difference_ci)],
        "trials": trials,
        "seed_base": SEED,
    }


def e_jm_3() -> dict[str, Any]:
    """Isolate transfer by changing only target centroid initialization."""
    similarities = np.asarray([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    trials, decisions = 60, 400
    categories, actions, factors = 5, 4, 7
    conditions = ("cold", "partial", "warm")
    trajectories: dict[str, np.ndarray] = {
        name: np.zeros((len(similarities), trials, decisions), dtype=float) for name in conditions
    }
    convergence: dict[str, np.ndarray] = {
        name: np.full((len(similarities), trials), decisions, dtype=float) for name in conditions
    }

    for sim_index, similarity in enumerate(similarities):
        for trial in range(trials):
            rng = np.random.default_rng(SEED + sim_index * 1000 + trial)
            source_true = rng.uniform(0.10, 0.90, (categories, actions, factors))
            independent = rng.uniform(0.10, 0.90, (categories, actions, factors))
            target_true = similarity * source_true + (1.0 - similarity) * independent
            source_estimate = source_true + rng.normal(0, 0.035, source_true.shape)
            labels = rng.integers(actions, size=decisions)
            cats = rng.integers(categories, size=decisions)
            noise = rng.normal(0, 0.11, (decisions, factors))
            observations = np.asarray([
                np.clip(target_true[cats[i], labels[i]] + noise[i], 0, 1) for i in range(decisions)
            ])
            starts = {
                "cold": np.full_like(source_estimate, 0.5),
                "partial": 0.5 * source_estimate + 0.25,
                "warm": source_estimate.copy(),
            }
            for condition in conditions:
                centroids = starts[condition].copy()
                for index in range(decisions):
                    category = int(cats[index])
                    action = int(labels[index])
                    observation = observations[index]
                    trajectories[condition][sim_index, trial, index] = classify(centroids, category, observation) == action
                    centroids[category, action] += 0.04 * (observation - centroids[category, action])
                curve = rolling(trajectories[condition][sim_index, trial : trial + 1], 40)[0]
                reached = np.where(curve >= 0.80)[0]
                if len(reached):
                    convergence[condition][sim_index, trial] = float(reached[0] + 1)

    fig, axes = plt.subplots(2, 3, figsize=(14, 7.5), sharex=True, sharey=True, constrained_layout=True)
    x = np.arange(1, decisions + 1)
    for index, (axis, similarity) in enumerate(zip(axes.flat, similarities)):
        for condition, color in (("cold", GRAY), ("partial", ORANGE), ("warm", GREEN)):
            curves = rolling(trajectories[condition][index], 40)
            mean, ci = mean_ci(curves[:, 39:])
            axis.plot(x[39:], mean, color=color, label=condition.title())
            axis.fill_between(x[39:], mean - ci, mean + ci, color=color, alpha=0.12)
        axis.set_title(f"Similarity {similarity:.1f}")
        axis.set_ylim(0.2, 1.02)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("E-JM-3: Paired Cross-Domain Transfer\nSame target stream; initialization is the only arm difference", fontsize=14)
    fig.supxlabel("Target-domain decisions")
    fig.supylabel("Rolling accuracy (40 decisions)")
    save(fig, "e_jm_3_trajectories.png")

    means = {condition: np.mean(convergence[condition], axis=1) for condition in conditions}
    cis = {condition: mean_ci(convergence[condition], axis=1)[1] for condition in conditions}
    speedup = means["cold"] / np.maximum(means["warm"], 1)
    fig, ax = plt.subplots(figsize=(9.5, 6), constrained_layout=True)
    for condition, color in (("cold", GRAY), ("partial", ORANGE), ("warm", GREEN)):
        ax.errorbar(similarities, means[condition], yerr=cis[condition], marker="o", capsize=4, color=color, label=condition.title())
    for similarity, ratio, y_value in zip(similarities, speedup, means["cold"]):
        ax.annotate(f"{ratio:.2f}×", (similarity, y_value), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=8)
    ax.set_xlabel("Source-target similarity")
    ax.set_ylabel("Decisions to 80% rolling accuracy")
    ax.set_title("E-JM-3: Relatedness-Gated Transfer Speed")
    ax.legend()
    save(fig, "e_jm_3_convergence_speed.png")
    correlation = float(stats.spearmanr(similarities, speedup).statistic)
    return {
        "diagnosis": "design_flaw",
        "fix": "Paired target streams and operator difficulty; only centroid initialization differs among cold, partial, and warm arms.",
        "similarities": similarities.tolist(),
        "speedup": speedup.tolist(),
        "speedup_spearman": correlation,
        "trials_per_similarity": trials,
        "seed_base": SEED,
    }


def quality_probability(kind: str, step: int, rng: np.random.Generator) -> float:
    if kind == "No degradation":
        return 0.88
    if kind == "Personnel change":
        return 0.58
    if kind == "Data corruption (30%)":
        return 0.88 if rng.random() >= 0.30 else 0.12
    if kind == "Gradual drift":
        return 0.88 - 0.33 * min(step / 299.0, 1.0)
    if kind == "Adversarial (10%)":
        return 0.08 if rng.random() < 0.10 else 0.88
    raise ValueError(kind)


def e_jm_4() -> dict[str, Any]:
    """Use the SDK recent-window conservation rule and clean-control calibration."""
    kinds = ("No degradation", "Personnel change", "Data corruption (30%)", "Gradual drift", "Adversarial (10%)")
    trials, healthy, degraded, window = 100, 500, 300, 100
    threshold, human_quality = 0.75, 0.92
    unconstrained = np.zeros((len(kinds), trials, healthy + degraded), dtype=float)
    conserved = np.zeros_like(unconstrained)
    detected = np.zeros((len(kinds), trials), dtype=bool)
    detect_at = np.full((len(kinds), trials), np.nan)

    for kind_index, kind in enumerate(kinds):
        for trial in range(trials):
            probability_rng = np.random.default_rng(SEED + kind_index * 10000 + trial)
            outcome_rng = np.random.default_rng(SEED + 500000 + kind_index * 10000 + trial)
            human_rng = np.random.default_rng(SEED + 900000 + kind_index * 10000 + trial)
            paused = False
            for decision in range(healthy + degraded):
                probability = 0.88 if decision < healthy else quality_probability(kind, decision - healthy, probability_rng)
                base_outcome = outcome_rng.random() < probability
                unconstrained[kind_index, trial, decision] = base_outcome
                conserved[kind_index, trial, decision] = human_rng.random() < human_quality if paused else base_outcome
                if decision + 1 >= window and not paused:
                    recent = conserved[kind_index, trial, decision - window + 1 : decision + 1]
                    if float(np.mean(recent)) < threshold:
                        paused = True
                        detected[kind_index, trial] = True
                        detect_at[kind_index, trial] = decision

    x = np.arange(healthy + degraded)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=True, sharey=True, constrained_layout=True)
    degradation_indices = range(1, len(kinds))
    for axis, kind_index in zip(axes.flat, degradation_indices):
        for values, color, label in ((unconstrained, RED, "Unconstrained"), (conserved, GREEN, "Conservation-routed")):
            curves = rolling(values[kind_index], 50)
            mean, ci = mean_ci(curves[:, 49:])
            axis.plot(x[49:], mean, color=color, label=label)
            axis.fill_between(x[49:], mean - ci, mean + ci, color=color, alpha=0.12)
        axis.axvline(healthy, color="black", linestyle="--", linewidth=0.8)
        axis.set_title(kinds[kind_index])
        axis.set_ylim(0.35, 1.0)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("E-JM-4: Calibrated Conservation Intervention\nSDK recent-window rule; paused cases route to human review", fontsize=14)
    fig.supxlabel("Decision")
    fig.supylabel("Rolling downstream accuracy")
    save(fig, "e_jm_4_trajectories.png")

    fig, axes = plt.subplots(1, 4, figsize=(14, 4), sharey=True, constrained_layout=True)
    for axis, kind_index in zip(axes, degradation_indices):
        status = np.mean(np.arange(healthy + degraded)[None, :] >= detect_at[kind_index, :, None], axis=0) * 100
        status = np.nan_to_num(status)
        axis.fill_between(x, 0, 100 - status, color="#86efac", alpha=0.9, label="GREEN")
        axis.fill_between(x, 100 - status, 100, color="#fca5a5", alpha=0.9, label="PAUSED")
        axis.axvline(healthy, color="black", linestyle="--", linewidth=0.8)
        axis.set_title(kinds[kind_index], fontsize=9)
        axis.set_ylim(0, 100)
    axes[0].set_ylabel("Trials (%)")
    axes[0].legend(fontsize=8)
    fig.suptitle("E-JM-4: Conservation Status After Degradation", fontsize=14)
    save(fig, "e_jm_4_conservation_status.png")

    post_unconstrained = np.mean(unconstrained[:, :, healthy:], axis=2)
    post_conserved = np.mean(conserved[:, :, healthy:], axis=2)
    advantage = (post_conserved - post_unconstrained) * 100
    advantage_mean, advantage_ci = mean_ci(advantage[1:], axis=1)
    fig, ax = plt.subplots(figsize=(10, 5.8), constrained_layout=True)
    labels = [kind.replace(" ", "\n") for kind in kinds[1:]]
    positions = np.arange(4)
    ax.bar(positions, advantage_mean, yerr=advantage_ci, capsize=4, color=GREEN, edgecolor="white")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(positions, labels)
    ax.set_ylabel("Conservation downstream advantage (pp)")
    ax.set_title("E-JM-4: Quality Protected After Gate Activation")
    for position, value in zip(positions, advantage_mean):
        ax.text(position, value + 0.6, f"{value:+.1f}pp", ha="center", fontweight="bold")
    save(fig, "e_jm_4_degradation_depth.png")

    detection_rates = np.mean(detected, axis=1) * 100
    fig, ax = plt.subplots(figsize=(10, 5.8), constrained_layout=True)
    colors = [GRAY] + [GREEN] * 4
    bars = ax.bar(np.arange(5), detection_rates, color=colors, edgecolor="white")
    ax.set_xticks(np.arange(5), [kind.replace(" ", "\n") for kind in kinds], fontsize=8)
    ax.set_ylabel("Detection rate (%)")
    ax.set_ylim(0, 105)
    ax.set_title("E-JM-4: Detection and Clean-Control False Positives")
    for bar, value in zip(bars, detection_rates):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 1.5, f"{value:.0f}%", ha="center", fontweight="bold")
    save(fig, "e_jm_4_detection_rates.png")
    return {
        "diagnosis": "design_flaw",
        "fix": "Replaced the toy cumulative gate with the SDK's 100-decision recent-quality threshold (0.75), retained a clean control, and measured downstream quality after fail-safe human routing.",
        "detection_rates_pct": {kind: float(rate) for kind, rate in zip(kinds, detection_rates)},
        "advantage_pp": {kind: float(value) for kind, value in zip(kinds[1:], advantage_mean)},
        "advantage_ci95": {kind: float(value) for kind, value in zip(kinds[1:], advantage_ci)},
        "trials": trials,
        "seed_base": SEED,
    }


class OnlineVariance:
    def __init__(self, dimensions: int) -> None:
        self.count = 0
        self.mean = np.zeros(dimensions)
        self.m2 = np.zeros(dimensions)

    def update(self, values: np.ndarray) -> None:
        self.count += 1
        delta = values - self.mean
        self.mean += delta / self.count
        self.m2 += delta * (values - self.mean)

    def variance(self) -> np.ndarray:
        result = self.m2 / max(self.count - 1, 1) if self.count > 1 else np.ones_like(self.mean)
        return cast(np.ndarray, np.asarray(result, dtype=float))


def e_jm_5() -> dict[str, Any]:
    """Correct Spearman/Kendall by correlating factor values directly."""
    factors, domains, trials, decisions = 7, 100, 5, 2000
    checkpoints = np.asarray([50, 100, 200, 400, 800, 1200, 1600, 2000])
    metrics: dict[str, list[list[float]]] = {name: [[] for _ in checkpoints] for name in ("spearman", "top3", "cosine", "kendall")}
    domain_rng = np.random.default_rng(SEED)
    domain_specs: list[tuple[np.ndarray, np.ndarray]] = []
    for _ in range(domains):
        raw = domain_rng.exponential(1.0, factors)
        true_weights = raw / raw.sum()
        noise = 0.08 + 0.35 * (1.0 - true_weights / true_weights.max())
        domain_specs.append((true_weights, noise))

    for domain_index, (true_weights, noise) in enumerate(domain_specs):
        for trial in range(trials):
            rng = np.random.default_rng(SEED + domain_index * 100 + trial)
            confirmed, overridden, all_stats = OnlineVariance(factors), OnlineVariance(factors), OnlineVariance(factors)
            learned = np.ones(factors) / factors
            checkpoint_index = 0
            person_accuracy = float(rng.uniform(0.65, 0.85))
            for decision in range(1, decisions + 1):
                vector = rng.normal(0, 1, factors) * noise + true_weights * 2
                quality = float(np.dot(vector, true_weights))
                correct = rng.random() < np.clip(person_accuracy * (0.5 + 0.3 * np.tanh(quality)), 0.15, 0.95)
                all_stats.update(vector)
                (confirmed if correct else overridden).update(vector)
                if confirmed.count >= 15 and overridden.count >= 10:
                    separation = np.abs(confirmed.mean - overridden.mean)
                    pooled = np.sqrt((confirmed.variance() + overridden.variance()) / 2 + 1e-6)
                    combined = separation / pooled / (np.sqrt(all_stats.variance()) + 1e-6)
                    learned = combined / (combined.sum() + 1e-8)
                elif all_stats.count >= 20:
                    inverse = 1.0 / (all_stats.variance() + 1e-6)
                    learned = inverse / inverse.sum()
                if checkpoint_index < len(checkpoints) and decision == checkpoints[checkpoint_index]:
                    spearman = float(stats.spearmanr(true_weights, learned).statistic)
                    kendall = float(stats.kendalltau(true_weights, learned).statistic)
                    top3 = len(set(np.argsort(true_weights)[-3:]) & set(np.argsort(learned)[-3:])) / 3
                    cosine = float(np.dot(true_weights, learned) / (np.linalg.norm(true_weights) * np.linalg.norm(learned)))
                    for name, value in (("spearman", spearman), ("top3", top3), ("cosine", cosine), ("kendall", kendall)):
                        metrics[name][checkpoint_index].append(value)
                    checkpoint_index += 1

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    labels = (("spearman", "Spearman rank correlation"), ("top3", "Top-3 overlap"), ("cosine", "Cosine similarity"), ("kendall", "Kendall tau"))
    for axis, (name, label) in zip(axes.flat, labels):
        array = np.asarray(metrics[name])
        mean = np.mean(array, axis=1)
        ci = stats.t.ppf(0.975, array.shape[1] - 1) * np.std(array, axis=1, ddof=1) / math.sqrt(array.shape[1])
        axis.errorbar(checkpoints, mean, yerr=ci, marker="o", color=BLUE, capsize=3)
        axis.set_xscale("log")
        axis.set_xlabel("Verified decisions")
        axis.set_ylabel(label)
        axis.annotate(f"Final {mean[-1]:.3f}", (checkpoints[-1], mean[-1]), xytext=(-55, 12), textcoords="offset points", fontweight="bold")
    fig.suptitle("E-JM-5: Corrected Factor-Weight Convergence\nDirect rank statistics; 100 domains × 5 paired trials", fontsize=14)
    save(fig, "e_jm_5_convergence.png")
    finals = {name: float(np.mean(np.asarray(values)[-1])) for name, values in metrics.items()}
    final_cis = {
        name: float(stats.t.ppf(0.975, len(values[-1]) - 1) * np.std(values[-1], ddof=1) / math.sqrt(len(values[-1])))
        for name, values in metrics.items()
    }
    return {
        "diagnosis": "bug",
        "fix": "Replaced Spearman/Kendall on argsort arrays with direct value-based rank correlations; preserved the archived online estimator and seeds.",
        "final_metrics": finals,
        "final_ci95_half_width": final_cis,
        "runs": domains * trials,
        "seed": SEED,
    }


def load_k_curves() -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray, list[int]]:
    labels = ["dataops", "trading", "purchasing", "soc", "s2p"]
    files = ["results", "trading", "purchasing", "soc", "s2p"]
    learning: list[list[float]] = []
    control: list[list[float]] = []
    accuracies: list[list[float]] = []
    seeds: list[int] = []
    checkpoints: np.ndarray | None = None
    for suffix in files:
        payload = json.loads((ROOT / "experiments" / "vld" / f"k_learning_curve_{suffix}.json").read_text(encoding="utf-8"))
        rows = payload["checkpoints"]
        checkpoints = np.asarray([row["decision_count"] for row in rows], dtype=float)
        learning.append([row["learning_arm"]["routing_quality"] * row["learning_arm"]["accuracy"] for row in rows])
        control.append([row["control_arm"]["routing_quality"] * row["control_arm"]["accuracy"] for row in rows])
        accuracies.append([row["learning_arm"]["accuracy"] for row in rows])
        seeds.append(int(payload["random_seed"]))
    assert checkpoints is not None
    return labels, checkpoints, np.asarray(learning), np.asarray(control), seeds


def e_jm_6_and_6b() -> dict[str, Any]:
    """Use the real five-copilot K-learning outputs and bootstrap deployments."""
    labels, checkpoints, learning, control, seeds = load_k_curves()
    learning_mean, learning_ci = mean_ci(learning)
    control_mean, control_ci = mean_ci(control)
    learning_fit = power_fit(checkpoints, learning_mean)
    control_fit = power_fit(checkpoints, control_mean)

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    for mean, ci, color, label in ((control_mean, control_ci, GRAY, "Frozen K control"), (learning_mean, learning_ci, GREEN, "Real K learning")):
        ax.plot(checkpoints, mean, marker="o", color=color, linewidth=2, label=label)
        ax.fill_between(checkpoints, mean - ci, mean + ci, color=color, alpha=0.14)
    ax.set_xlabel("Verified decisions")
    ax.set_ylabel("Decision utility (routing quality × accuracy)")
    ax.set_title("E-JM-6: Real SDK K-Learning Trajectory")
    ax.legend()
    ax.text(0.02, 0.97, f"Learning c={learning_fit['exponent']:.3f} (R²={learning_fit['r2']:.3f})\nFinal gain={(learning_mean[-1]-control_mean[-1])*100:+.2f}pp", transform=ax.transAxes, va="top", bbox={"facecolor": "white", "alpha": 0.9})
    save(fig, "e_jm_6_trajectories.png")

    accuracy = np.zeros_like(learning)
    files = ["results", "trading", "purchasing", "soc", "s2p"]
    for index, suffix in enumerate(files):
        payload = json.loads((ROOT / "experiments" / "vld" / f"k_learning_curve_{suffix}.json").read_text(encoding="utf-8"))
        accuracy[index] = [row["learning_arm"]["accuracy"] for row in payload["checkpoints"]]
    eligible = np.sum(accuracy >= 0.75, axis=0)
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True, constrained_layout=True)
    top.plot(checkpoints, learning_mean * 100, marker="o", color=BLUE)
    top.fill_between(checkpoints, (learning_mean - learning_ci) * 100, (learning_mean + learning_ci) * 100, color=BLUE, alpha=0.14)
    top.set_ylabel("Institutional utility index")
    top.set_title("Real K utility across five deployments")
    bottom.step(checkpoints, eligible, where="mid", color=GREEN, linewidth=2.5)
    bottom.scatter(checkpoints, eligible, color=GREEN)
    bottom.set_ylabel("Deployments meeting q ≥ 0.75")
    bottom.set_xlabel("Verified decisions")
    bottom.set_ylim(0, len(labels) + 0.4)
    bottom.set_title(f"Eligible scope expands from {int(eligible[0])}/5 to {int(eligible[-1])}/5")
    fig.suptitle("E-JM-6: Knowledge Utility and Conservation-Eligible Scope", fontsize=14)
    save(fig, "e_jm_6_iks_trajectory.png")

    combined = learning_mean * eligible / len(labels)
    combined_fit = power_fit(checkpoints, combined)
    fig, ax = plt.subplots(figsize=(10, 5.8), constrained_layout=True)
    ax.plot(checkpoints, combined, marker="o", color=GREEN, linewidth=2.5)
    ax.set_xlabel("Verified decisions")
    ax.set_ylabel("Mean utility × eligible deployment fraction")
    ax.set_title("E-JM-6: Real K-Learning Combined Value")
    ax.text(0.02, 0.97, f"Power exponent c={combined_fit['exponent']:.3f}\n95% deployment bootstrap below\nR²={combined_fit['r2']:.3f}", transform=ax.transAxes, va="top", bbox={"facecolor": "white", "alpha": 0.9})
    save(fig, "e_jm_6_combined_metric.png")

    bootstrap_rng = np.random.default_rng(6042)
    exponents: list[float] = []
    for _ in range(2000):
        indices = bootstrap_rng.integers(0, len(labels), size=len(labels))
        sample_learning = learning[indices]
        sample_accuracy = accuracy[indices]
        sample_mean = np.mean(sample_learning, axis=0)
        sample_scope = np.mean(sample_accuracy >= 0.75, axis=0)
        try:
            exponents.append(power_fit(checkpoints, sample_mean * sample_scope)["exponent"])
        except (RuntimeError, ValueError):
            continue
    exponent_array = np.asarray(exponents)
    percentile_bounds = np.asarray(np.percentile(exponent_array, [2.5, 97.5]), dtype=float)
    ci_low = float(percentile_bounds[0])
    ci_high = float(percentile_bounds[1])
    fig, ax = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
    ax.hist(exponent_array, bins=35, color=BLUE, alpha=0.82, edgecolor="white")
    ax.axvline(1.0, color=RED, linestyle="--", label="Linear boundary c=1")
    ax.axvline(combined_fit["exponent"], color=GREEN, linewidth=2, label=f"Observed c={combined_fit['exponent']:.3f}")
    ax.axvspan(ci_low, ci_high, color=ORANGE, alpha=0.18, label=f"95% CI [{ci_low:.3f}, {ci_high:.3f}]")
    ax.set_xlabel("Power exponent c")
    ax.set_ylabel("Deployment bootstrap samples")
    ax.set_title("E-JM-6b: Deployment-Resampled Exponent Uncertainty")
    ax.legend()
    save(fig, "e_jm_6b_exponent_ci.png")
    return {
        "diagnosis": "design_flaw",
        "fix": "Replaced the toy DK loop with existing real five-copilot K-learning outputs; utility is routing quality times action accuracy and scope uses the SDK recent-q threshold 0.75.",
        "copilots": labels,
        "seeds": seeds,
        "learning_fit": learning_fit,
        "control_fit": control_fit,
        "final_utility_gain_pp": float((learning_mean[-1] - control_mean[-1]) * 100),
        "eligible_scope": eligible.tolist(),
        "combined_fit": combined_fit,
        "bootstrap_seed": 6042,
        "bootstrap_samples": len(exponents),
        "bootstrap_ci95": [float(ci_low), float(ci_high)],
    }


def logistic(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def e_jm_7() -> dict[str, Any]:
    """Compare global, independent stores, and hierarchical entity-specific learning."""
    trials, decisions, entities, factors = 50, 2000, 3, 7
    conditions = ("global", "separate", "hierarchical")
    accuracy: dict[str, np.ndarray] = {name: np.zeros((trials, decisions)) for name in conditions}
    frequencies = np.asarray([0.65, 0.25, 0.10])
    for trial in range(trials):
        rng = np.random.default_rng(SEED + trial)
        base = rng.normal(0, 0.45, factors)
        truths = np.asarray([base + rng.normal(0, 0.55, factors) for _ in range(entities)])
        entity_stream = rng.choice(entities, size=decisions, p=frequencies)
        vectors = rng.normal(0, 1, (decisions, factors))
        probabilities = np.asarray([logistic(float(np.dot(truths[entity_stream[i]], vectors[i]))) for i in range(decisions)])
        outcomes = rng.random(decisions) < probabilities
        global_weights = np.zeros(factors)
        separate_weights = np.zeros((entities, factors))
        hierarchy_global = np.zeros(factors)
        hierarchy_local = np.zeros((entities, factors))
        for index in range(decisions):
            entity = int(entity_stream[index])
            vector = vectors[index]
            outcome = float(outcomes[index])
            predictions = {
                "global": logistic(float(np.dot(global_weights, vector))),
                "separate": logistic(float(np.dot(separate_weights[entity], vector))),
                "hierarchical": logistic(float(np.dot(hierarchy_global + hierarchy_local[entity], vector))),
            }
            for condition, prediction in predictions.items():
                accuracy[condition][trial, index] = (prediction >= 0.5) == bool(outcome)
            global_weights += 0.025 * (outcome - predictions["global"]) * vector
            separate_weights[entity] += 0.025 * (outcome - predictions["separate"]) * vector
            error = outcome - predictions["hierarchical"]
            hierarchy_global += 0.0125 * error * vector
            hierarchy_local[entity] += 0.025 * error * vector - 0.0005 * hierarchy_local[entity]

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    x = np.arange(1, decisions + 1)
    for condition, color, label in (("global", ORANGE, "Global weights"), ("separate", GRAY, "Independent entity stores"), ("hierarchical", GREEN, "Entity weights + shared prior")):
        curves = rolling(accuracy[condition], 100)
        mean, ci = mean_ci(curves[:, 99:])
        ax.plot(x[99:], mean, color=color, label=label)
        ax.fill_between(x[99:], mean - ci, mean + ci, color=color, alpha=0.12)
    late = {name: np.mean(accuracy[name][:, decisions // 2 :], axis=1) for name in conditions}
    hierarchical_gain = (late["hierarchical"] - late["global"]) * 100
    gain_mean, gain_ci = mean_ci(hierarchical_gain)
    ax.set_xlabel("Decisions")
    ax.set_ylabel("Rolling predictive accuracy")
    ax.set_title("E-JM-7: Correct Entity-Store Isolation")
    ax.legend()
    ax.text(0.02, 0.97, f"Hierarchical vs global {float(gain_mean):+.2f}pp\n95% CI [{float(gain_mean-gain_ci):+.2f}, {float(gain_mean+gain_ci):+.2f}]", transform=ax.transAxes, va="top", bbox={"facecolor": "white", "alpha": 0.9})
    save(fig, "e_jm_7_accuracy.png")
    return {
        "diagnosis": "design_flaw",
        "fix": "Implemented truly independent per-entity stores and a distinct hierarchical semantic-times-judgment arm with shared global prior; all arms use the same imbalanced entity stream.",
        "late_accuracy": {name: float(np.mean(values)) for name, values in late.items()},
        "hierarchical_vs_global_pp": float(gain_mean),
        "hierarchical_vs_global_ci95": [float(gain_mean - gain_ci), float(gain_mean + gain_ci)],
        "trials": trials,
        "seed_base": SEED,
    }


def silhouette(points: np.ndarray, labels: np.ndarray) -> float:
    values: list[float] = []
    for index, point in enumerate(points):
        same = labels == labels[index]
        same[index] = False
        a = float(np.mean(np.linalg.norm(points[same] - point, axis=1)))
        b = min(
            float(np.mean(np.linalg.norm(points[labels == label] - point, axis=1)))
            for label in np.unique(labels)
            if label != labels[index]
        )
        values.append((b - a) / max(a, b, 1e-12))
    return float(np.mean(values))


def figure_2() -> dict[str, Any]:
    """Learn identifiable action-conditioned centroids and use one fixed PCA basis."""
    rng = np.random.default_rng(SEED)
    categories, actions, factors, decisions = 6, 4, 7, 3000
    snapshots_at = (50, 500, 3000)
    category_offsets = rng.normal(0, 0.025, (categories, 1, factors))
    action_prototypes = np.full((1, actions, factors), 0.5)
    for action in range(actions):
        action_prototypes[0, action, action] = 0.15 + 0.22 * action
        action_prototypes[0, action, (action + 3) % factors] = 0.85 - 0.18 * action
    truth = np.clip(action_prototypes + category_offsets, 0.05, 0.95)
    centroids = np.full_like(truth, 0.5)
    counts = np.zeros((categories, actions), dtype=int)
    snapshots: dict[int, np.ndarray] = {}
    for decision in range(1, decisions + 1):
        category = int(rng.integers(categories))
        action = int(rng.integers(actions))
        observation = np.clip(truth[category, action] + rng.normal(0, 0.06, factors), 0, 1)
        counts[category, action] += 1
        eta = min(0.10, 1.0 / counts[category, action])
        centroids[category, action] += eta * (observation - centroids[category, action])
        if decision in snapshots_at:
            snapshots[decision] = centroids.copy()
    late = snapshots[snapshots_at[-1]].reshape(-1, factors)
    center = np.mean(late, axis=0)
    _, _, right = np.linalg.svd(late - center, full_matrices=False)
    basis = right[:2]
    labels = np.tile(np.arange(actions), categories)
    scores: dict[str, float] = {}
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5), constrained_layout=True)
    colors = (BLUE, ORANGE, GREEN, "#9333ea")
    for axis, decision in zip(axes, snapshots_at):
        projected = (snapshots[decision].reshape(-1, factors) - center) @ basis.T
        score = silhouette(projected, labels)
        scores[str(decision)] = score
        for action in range(actions):
            mask = labels == action
            axis.scatter(projected[mask, 0], projected[mask, 1], s=42, color=colors[action], edgecolor="white", label=f"Action {action + 1}")
        axis.set_title(f"{decision:,} decisions\nSilhouette {score:.3f}")
        axis.set_xlabel("Late-basis PC1")
    axes[0].set_ylabel("Late-basis PC2")
    axes[-1].legend(fontsize=8)
    fig.suptitle("FIGURE-2: Identifiable Centroid Geometry\nAction-conditioned observations; fixed late PCA basis", fontsize=14)
    save(fig, "fig2_centroid_geometry.png")
    return {
        "diagnosis": "bug",
        "fix": "The Phase 2 generator ignored action when sampling factors. The corrected stream samples around action-conditioned ground-truth centroids and updates the matching cell.",
        "snapshots": list(snapshots_at),
        "silhouette_scores": scores,
        "seed": SEED,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    style()
    results = {
        "E-JM-1": e_jm_1(),
        "E-JM-3": e_jm_3(),
        "E-JM-4": e_jm_4(),
        "E-JM-5": e_jm_5(),
        "E-JM-6": e_jm_6_and_6b(),
        "E-JM-7": e_jm_7(),
        "FIGURE-2": figure_2(),
    }
    (Path(__file__).resolve().parent / "jm_phase3_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
