"""Read a live shared graph and print a governed cross-copilot finding."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from copilot_sdk.config import GraphConfig
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.transfer import CrossDomainTraversal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", default=None)
    parser.add_argument("--graph", default=None)
    args = parser.parse_args()
    config = GraphConfig.load("soc")
    dsn = args.dsn or os.environ.get("GRAPH_DSN") or config.dsn
    graph = args.graph or os.environ.get("GRAPH_NAME") or config.graph
    if not dsn:
        print(json.dumps({"status": "unavailable", "reason": "GRAPH_DSN is not configured"}))
        return 1
    store = create_graph_store(
        backend="age",
        domain="soc",
        dsn=dsn,
        graph_name=graph,
        env={},
        profile="production",
    )
    try:
        finding = CrossDomainTraversal(store).dollar_finding()
        payload: dict[str, Any] = {
            "status": "found" if finding is not None else "no_finding",
            "finding": None if finding is None else finding.to_dict(),
            "source": "live_graph_traversal",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if finding is not None else 1
    finally:
        close = getattr(store, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    raise SystemExit(main())
