"""Build-Your-Own Copilot — Level-3 template.

Usage:
    python -m examples.build_your_own.run --domain email
    python -m examples.build_your_own.run --domain reading --ungoverned
"""

from __future__ import annotations

import argparse
from pathlib import Path

from copilot_sdk.scoring.scorer import CompoundingScorer  # real governed primitive

from . import report
from .domains import email, reading
from .engine import run_domain, run_three_arms

DOMAINS = {"email": email, "reading": reading}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", choices=sorted(DOMAINS), required=True)
    parser.add_argument("--ungoverned", action="store_true")
    parser.add_argument("--decisions", type=int, default=300)
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()
    domain = DOMAINS[args.domain]
    # The shared engine wires CompoundingScorer, conservation, SQLite, and
    # the promotion gate; this module only selects the domain and mode.
    results = run_domain(domain, decisions=args.decisions, ungoverned=args.ungoverned)
    report.generate_report({"domain": domain.DOMAIN_NAME, "arms": {results["arm"]: results}, "decisions": args.decisions}, args.output_dir)
    print(f"{domain.DOMAIN_NAME}: {results['arm']} completed {len(results['decisions'])} decisions")
    print(f"report: {Path(args.output_dir) / 'report.html'}")


if __name__ == "__main__":
    main()


__all__ = ["DOMAINS", "main", "run_domain", "run_three_arms"]
