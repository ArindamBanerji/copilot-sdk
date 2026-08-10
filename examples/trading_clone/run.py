"""SQLite-backed, oracle-separated Trading clone-and-compound demo.

This example generates synthetic market factor vectors, scores them with the
real Trading preset, labels correctness only through the ground-truth oracle,
and records verified outcomes in a temporary SQLite graph.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from typing import Any

from .config import RUN_A_GENERATOR, RUN_A_ORACLE, RUN_B_GENERATOR, RUN_B_ORACLE
from .generator import GeneratorConfig, SyntheticGenerator
from .oracle import GroundTruthOracle, OracleConfig
from .report import generate_report
from examples.jm_reference.run import run_experiment as _run_reference_experiment


def run_experiment(
    label: str,
    gen_config: GeneratorConfig,
    oracle_config: OracleConfig,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Run one Trading experiment through the shared APP-1 implementation."""

    return _run_reference_experiment(label, gen_config, oracle_config, db_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline Trading clone")
    parser.add_argument("--decisions", type=int, default=None)
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()
    if args.decisions is not None and args.decisions <= 0:
        parser.error("--decisions must be positive")

    gen_a = replace(RUN_A_GENERATOR, n_decisions=args.decisions) if args.decisions else RUN_A_GENERATOR
    gen_b = replace(RUN_B_GENERATOR, n_decisions=args.decisions) if args.decisions else RUN_B_GENERATOR
    trajectory_a = run_experiment("trading_run_a", gen_a, RUN_A_ORACLE)
    trajectory_b = run_experiment("trading_run_b", gen_b, RUN_B_ORACLE)
    generate_report(trajectory_a, trajectory_b, args.output_dir)
    print("Trading clone complete. Synthetic factors, SQLite, and paper-only scoring.")


if __name__ == "__main__":
    main()
