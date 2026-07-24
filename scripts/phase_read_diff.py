"""Compare active and archived SQLite/AGE records for one copilot."""
from __future__ import annotations
import argparse
from phase_config import add_domain_argument, get_config
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.graph.read_diff_runner import ReadDiffRunner
from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__); add_domain_argument(parser); args = parser.parse_args(); cfg = get_config(args.domain)
    if not cfg["age_dsn"]: parser.error("set GRAPH_DSN or AGE_DSN")
    primary = SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"])
    secondary = AGEGraphStoreAdapter(dsn=cfg["age_dsn"], graph_name=cfg["graph_name"])
    try:
        runner = ReadDiffRunner(primary, secondary, cfg["domain"])
        active, history = runner.compare_active(), runner.compare_history()
        print(active.summary()); print(history.summary())
        raise SystemExit(0 if active.passed and history.passed else 1)
    finally:
        primary.close(); secondary.close()
if __name__ == "__main__": main()
