"""Backfill AGE SNAPSHOT_AFTER edges for protocol-v2 checkpoints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", required=True, choices=["soc", "s2p", "trading", "purchasing", "dataops"])
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    ci_platform = repo.parent / "ci-platform"
    if str(ci_platform) not in sys.path:
        sys.path.insert(0, str(ci_platform))

    from copilot_sdk.graph.factory import create_graph_store

    store = create_graph_store(domain=args.domain, profile="production")
    try:
        backfill = getattr(store, "backfill_snapshot_after", None)
        if not callable(backfill):
            raise RuntimeError("configured GraphStore does not support SNAPSHOT_AFTER backfill")
        report = backfill(args.domain)
        print(json.dumps({"domain": args.domain, **report}, sort_keys=True))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
