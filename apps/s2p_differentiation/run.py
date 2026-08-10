"""CLI entry point for the backend-only APP-4A harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import S2P_GENERATOR, S2P_ORACLE
from .engine import run_three_arms
from .report import write_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=int, default=500)
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()
    output = Path(args.output_dir)
    result = run_three_arms(S2P_GENERATOR, S2P_ORACLE, args.decisions, output)
    json_path, html_path = write_report(result, output)
    print(f"APP-4A complete: {args.decisions} shared S2P decisions")
    print(f"reports: {json_path} and {html_path}")
    for key in ("arm_1_ci", "arm_2_reward_max", "arm_3_hand_specified"):
        arm = result[key]
        print(f"{arm['name']}: final_quality={arm['quality_curve'][-1]:.1%}")
    print(f"T-G1: {result['tg1']}")


if __name__ == "__main__":
    main()

