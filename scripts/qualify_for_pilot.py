#!/usr/bin/env python
"""Run the Day-0 qualification gate for one copilot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from copilot_sdk.pilot import QualificationCheck, QualificationGate, TruthPreflightCheck


COPILOTS = ("trading", "purchasing", "dataops", "soc", "s2p")


class _UnavailableCheck:
    def __init__(self, name: str) -> None:
        self.name = name

    def check(self, copilot: str):
        from copilot_sdk.pilot import CheckResult

        return CheckResult(False, "Dependency was not supplied to the CLI", {"copilot": copilot}, self.name)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Day-0 customer pilot qualification")
    parser.add_argument("--copilot", required=True, choices=COPILOTS)
    parser.add_argument("--dry-run", action="store_true", help="Validate CLI configuration without contacting services")
    parser.add_argument("--output", type=Path, help="Write the JSON qualification report")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.dry_run:
        print(json.dumps({"copilot": args.copilot, "configuration": "OK", "checks": 6}, sort_keys=True))
        return 0
    checks: list[QualificationCheck] = [
        _UnavailableCheck("frozen_twin"),
        _UnavailableCheck("evidence_gate"),
        _UnavailableCheck("promotion_records"),
        _UnavailableCheck("conservation_health"),
        _UnavailableCheck("verified_count"),
        TruthPreflightCheck(),
    ]
    report = QualificationGate().run(args.copilot, checks)
    if args.output:
        report.write_json(str(args.output))
    print(report.to_json())
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
