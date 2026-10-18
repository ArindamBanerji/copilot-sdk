"""Run the frozen Trading integrity benchmark and print a compact report."""

from __future__ import annotations

from typing import Any, cast

from integrity.load_benchmark import (
    BENCHMARK,
    decisions_to_threshold,
    inject_category_disruption,
    inject_disruption,
    load_benchmark,
    load_dk_benchmark_split,
    measure_accuracy,
    measure_dk_weight_effect,
    train_scorer,
    train_scorer_dk,
)


def _percent(value: float) -> str:
    return f"{value:.1%}"


def _print_table(rows: list[tuple[str, str]]) -> None:
    width = max(len(name) for name, _value in rows)
    print("\nTrading frozen benchmark")
    print(f"{'Metric':<{width}} | Value")
    print(f"{'-' * width}-+----------------")
    for name, value in rows:
        print(f"{name:<{width}} | {value}")


def run() -> dict[str, Any]:
    """Execute the standard and DK Trading benchmarks."""
    train, evaluation = load_benchmark()
    n_train = len(train)

    baseline_scorer = train_scorer("trading", train, n_train)
    baseline_accuracy = measure_accuracy(baseline_scorer, evaluation)
    threshold_50 = decisions_to_threshold(
        baseline_scorer,
        train,
        evaluation,
        0.50,
    )
    inject_disruption(baseline_scorer, magnitude=0.3)
    disrupted_accuracy = measure_accuracy(baseline_scorer, evaluation)

    category_scorer = train_scorer("trading", train, n_train)
    category_names = tuple(category_scorer._preset.shape.category_names)
    selected_categories = category_names[:2]
    category_accuracy_before = measure_accuracy(category_scorer, evaluation)
    selected_eval = [
        row for row in evaluation if str(row["category"]) in selected_categories
    ]
    unaffected_eval = [
        row for row in evaluation if str(row["category"]) not in selected_categories
    ]
    selected_accuracy_before = measure_accuracy(category_scorer, selected_eval)
    unaffected_accuracy_before = measure_accuracy(category_scorer, unaffected_eval)
    affected = inject_category_disruption(
        category_scorer,
        selected_categories,
        magnitude=0.5,
        seed=cast(int, BENCHMARK["seed"]),
    )
    category_accuracy_after = measure_accuracy(category_scorer, evaluation)
    selected_accuracy_after = measure_accuracy(category_scorer, selected_eval)
    unaffected_accuracy_after = measure_accuracy(category_scorer, unaffected_eval)

    threshold_45_scorer = train_scorer("trading", train, n_train)
    threshold_45 = decisions_to_threshold(
        threshold_45_scorer,
        train,
        evaluation,
        0.45,
    )
    threshold_55_scorer = train_scorer("trading", train, n_train)
    threshold_55 = decisions_to_threshold(
        threshold_55_scorer,
        train,
        evaluation,
        0.55,
    )

    dk_train, dk_evaluation = load_dk_benchmark_split()
    dk_scorer = train_scorer_dk(dk_train)
    dk_accuracy = measure_accuracy(dk_scorer, dk_evaluation)
    dk_effect = measure_dk_weight_effect(dk_scorer, dk_evaluation)

    results: dict[str, Any] = {
        "fixture_seed": BENCHMARK["seed"],
        "train_size": n_train,
        "eval_size": len(evaluation),
        "tensor_shape": tuple(baseline_scorer._preset.shape.tensor_shape),
        "baseline_accuracy": baseline_accuracy,
        "threshold_50_decisions": threshold_50,
        "post_disruption_accuracy": disrupted_accuracy,
        "category_accuracy_before": category_accuracy_before,
        "post_category_disruption_accuracy": category_accuracy_after,
        "selected_categories": affected,
        "selected_accuracy_before": selected_accuracy_before,
        "selected_accuracy_after": selected_accuracy_after,
        "unaffected_accuracy_before": unaffected_accuracy_before,
        "unaffected_accuracy_after": unaffected_accuracy_after,
        "threshold_45_decisions": threshold_45,
        "threshold_55_decisions": threshold_55,
        "dk_train_size": len(dk_train),
        "dk_eval_size": len(dk_evaluation),
        "dk_accuracy": dk_accuracy,
        "dk_effect": dk_effect,
    }

    _print_table(
        [
            ("Fixture split", f"{n_train} train / {len(evaluation)} eval"),
            ("Tensor shape", str(results["tensor_shape"])),
            ("Baseline accuracy", _percent(baseline_accuracy)),
            ("Decisions to 0.50", str(threshold_50)),
            ("Post-global-disruption accuracy", _percent(disrupted_accuracy)),
            (
                "Post-category-disruption accuracy",
                _percent(category_accuracy_after),
            ),
            ("Selected-category accuracy", f"{_percent(selected_accuracy_before)} -> {_percent(selected_accuracy_after)}"),
            ("Unaffected-category accuracy", f"{_percent(unaffected_accuracy_before)} -> {_percent(unaffected_accuracy_after)}"),
            ("Decisions to 0.45", str(threshold_45)),
            ("Decisions to 0.55", str(threshold_55)),
            ("DK split", f"{len(dk_train)} train / {len(dk_evaluation)} eval"),
            ("DK accuracy", _percent(dk_accuracy)),
            ("DK learned margin", f"{float(dk_effect['learned_metric']):.6f}"),
            ("DK uniform margin", f"{float(dk_effect['uniform_metric']):.6f}"),
            ("DK margin delta", f"{float(dk_effect['delta']):.6f}"),
            (
                "DK weight max/min ratio",
                f"{float(dk_effect['weights_non_uniform_ratio']):.6f}",
            ),
        ]
    )
    print(f"\nSelected categories: {', '.join(affected)}")
    print(f"DK active categories: {', '.join(map(str, dk_effect['vl_categories']))}")
    return results


if __name__ == "__main__":
    run()
