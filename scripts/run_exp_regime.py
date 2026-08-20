"""Run the synthetic EXP-REGIME re-convergence experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from copilot_sdk.regime import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description="Run EXP-REGIME: cold-start vs regime-indexed recovery.")
    parser.add_argument("--regime", default="volatile", choices=("calm", "ranging", "trending", "volatile"))
    parser.add_argument("--decisions", type=int, default=500, help="Decisions per side of the regime break.")
    parser.add_argument("--period", default="2020-03", choices=("2020-03", "2022"))
    parser.add_argument("--seed", type=int, default=202003)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path.")
    args = parser.parse_args()
    report = run_experiment(
        post_regime=args.regime,
        decisions_per_regime=args.decisions // 2,
        period=args.period,
        seed=args.seed,
    ).to_dict()
    rendered = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
