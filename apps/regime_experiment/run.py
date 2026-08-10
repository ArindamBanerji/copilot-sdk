"""CLI entrypoint for the EXP-REGIME bake-off."""

from __future__ import annotations

import argparse

from .experiment import run_experiment
from .report import generate_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the EXP-REGIME A/B/C bake-off")
    parser.add_argument("--decisions", type=int, default=500)
    parser.add_argument("--break-point", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=0.15)
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()
    results = run_experiment(
        total_decisions=args.decisions,
        break_point=args.break_point,
        convergence_threshold=args.threshold,
        output_dir=args.output_dir,
    )
    generate_report(results, args.output_dir)
    print("Arm | Strategy | Convergence step | gamma_regime")
    for name, arm in results["arms"].items():
        gamma = arm["gamma_regime"]
        gamma_text = "∞" if gamma == float("inf") else ("None" if gamma is None else f"{gamma:.3f}")
        print(f"{name} | {arm['strategy']} | {arm['convergence_step']} | {gamma_text}")
    print(f"Winner: {results['winner'] or 'none'}")
    print(f"TRD-S7: move to {results['recommendation']} only when measured gamma_regime > 1.")


if __name__ == "__main__":
    main()
