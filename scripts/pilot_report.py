#!/usr/bin/env python
"""Generate the measured-transfer report for a copilot's latest pilot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.pilot import MeasuredTransfer, MeasuredTransferStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a measured 90-day pilot report")
    parser.add_argument("--copilot", required=True)
    parser.add_argument("--profile", default="production", choices=("production", "offline", "test"))
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    graph = create_graph_store(domain=args.copilot, profile=args.profile)
    store = MeasuredTransferStore(graph, args.copilot)
    try:
        report = MeasuredTransfer(store=store).latest_report(args.copilot)
        print(report.to_json())
        return 0
    except ValueError as exc:
        print(f"pilot report unavailable: {exc}", file=sys.stderr)
        return 1
    finally:
        graph.close()


if __name__ == "__main__":
    raise SystemExit(main())
