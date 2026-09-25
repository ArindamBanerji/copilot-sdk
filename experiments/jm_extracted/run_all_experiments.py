#!/usr/bin/env python3
"""
Judgment Memory Experiments — Runner
======================================
Runs all 4 experiments and collects results.

Usage:
  python run_all_experiments.py           # run all
  python run_all_experiments.py 1         # run E-JM-1 only
  python run_all_experiments.py 1 3       # run E-JM-1 and E-JM-3

Requirements:
  pip install numpy matplotlib scipy

Output:
  results/e_jm_1/  — Personnel Change Resilience
  results/e_jm_2/  — Signal-Confidence Inversion Prevalence
  results/e_jm_3/  — Cross-Domain Transfer
  results/e_jm_4/  — Conservation vs Unconstrained Learning

Each directory contains:
  - PNG charts (150 DPI, publication-ready)
  - PDF charts (vector, for papers)
  - JSON summary with all statistics
"""

import sys
import time
import subprocess
from pathlib import Path

EXPERIMENTS = {
    1: ("E-JM-1: Personnel Change Resilience",
        "e_jm_1_personnel_change.py"),
    2: ("E-JM-2: Signal-Confidence Inversion Prevalence",
        "e_jm_2_inversion_prevalence.py"),
    3: ("E-JM-3: Cross-Domain Transfer",
        "e_jm_3_cross_domain_transfer.py"),
    4: ("E-JM-4: Conservation vs Unconstrained Learning",
        "e_jm_4_conservation_vs_unconstrained.py"),
}


def run_experiment(num: int):
    name, script = EXPERIMENTS[num]
    script_path = Path(__file__).parent / script

    print(f"\n{'='*70}")
    print(f"  Running {name}")
    print(f"  Script: {script}")
    print(f"{'='*70}\n")

    start = time.time()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(Path(__file__).parent),
        capture_output=False,
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"\n✅ {name} completed in {elapsed:.1f}s")
    else:
        print(f"\n❌ {name} FAILED (exit code {result.returncode})")

    return result.returncode == 0


def main():
    # Parse which experiments to run
    if len(sys.argv) > 1:
        to_run = [int(x) for x in sys.argv[1:]]
    else:
        to_run = list(EXPERIMENTS.keys())

    print("=" * 70)
    print("  Judgment Memory Experiments")
    print(f"  Running: {', '.join(EXPERIMENTS[n][0] for n in to_run)}")
    print("=" * 70)

    results = {}
    total_start = time.time()

    for num in to_run:
        if num not in EXPERIMENTS:
            print(f"  Unknown experiment: {num}. Valid: {list(EXPERIMENTS.keys())}")
            continue
        results[num] = run_experiment(num)

    total_elapsed = time.time() - total_start

    print(f"\n{'='*70}")
    print("  RESULTS SUMMARY")
    print(f"{'='*70}")
    for num in to_run:
        name = EXPERIMENTS[num][0]
        status = "✅ PASS" if results.get(num) else "❌ FAIL"
        print(f"  {status} — {name}")

    print(f"\n  Total time: {total_elapsed:.1f}s")
    print(f"  Results in: results/e_jm_*/")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
