"""Command-line entrypoint for Copilot SDK migrations."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Sequence

from .sqlite_to_age import _default_source_path, run_migration


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m copilot_sdk.migrate")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sqlite_to_age = subparsers.add_parser(
        "sqlite_to_age",
        help="Migrate verified SQLite decision logs into AGE Decision nodes.",
    )
    sqlite_to_age.add_argument("--domain", required=True)
    sqlite_to_age.add_argument("--source", default=None)
    sqlite_to_age.add_argument("--age-dsn", required=True)
    sqlite_to_age.add_argument("--graph-name", default="soc_graph")
    sqlite_to_age.add_argument("--dry-run", action="store_true")
    sqlite_to_age.add_argument(
        "--all-decisions",
        action="store_true",
        help="Include pending decisions; default migrates verified decisions only.",
    )
    sqlite_to_age.add_argument(
        "--include-archived",
        action="store_true",
        help="Also migrate decisions_archive as directly archived AGE Decisions.",
    )
    sqlite_to_age.add_argument("--batch-size", type=int, default=1000)
    sqlite_to_age.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the domain checkpoint file if it is in progress.",
    )
    sqlite_to_age.add_argument("--no-verify", action="store_true")
    sqlite_to_age.add_argument(
        "--use-scratch-graph",
        action="store_true",
        help="Write to a scratch graph, verify, then copy to live.",
    )

    reconcile_archive = subparsers.add_parser(
        "reconcile_archive",
        help="Mark AGE Decisions archived when SQLite has archived their IDs.",
    )
    reconcile_archive.add_argument("--domain", required=True)
    reconcile_archive.add_argument("--source", required=True)
    reconcile_archive.add_argument("--age-dsn", required=True)
    reconcile_archive.add_argument("--graph-name", default="soc_graph")
    reconcile_archive.add_argument("--dry-run", action="store_true")
    reconcile_archive.add_argument("--batch-size", type=int, default=100)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "sqlite_to_age":
        source = args.source or str(_default_source_path(args.domain))
        result = run_migration(
            domain=args.domain,
            source_db=source,
            age_dsn=args.age_dsn,
            graph_name=args.graph_name,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
            verify=not args.no_verify,
            use_scratch=args.use_scratch_graph,
            all_decisions=args.all_decisions,
            include_archived=args.include_archived,
            resume=args.resume,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        if result.get("status") == "FAIL":
            print(f"Migration failed: {result.get('fail_reason', 'unknown failure')}")
            sys.exit(1)
        sys.exit(0)

    if args.command == "reconcile_archive":
        from ci_platform.graph.age_graph_store import AGEGraphStore
        from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
        from copilot_sdk.migrate.reconcile_archive import ArchiveReconciler

        sqlite_store = SQLiteGraphStore(args.source, domain=args.domain)
        age_store = AGEGraphStore(dsn=args.age_dsn, graph_name=args.graph_name)
        try:
            reconciler = ArchiveReconciler(sqlite_store, age_store, args.domain)
            result = reconciler.reconcile(batch_size=args.batch_size, dry_run=args.dry_run)
            if result["status"] == "PASS" and not args.dry_run:
                verification = reconciler.verify()
                result["verification"] = {
                    name: asdict(report) for name, report in verification.items()
                }
                if not all(report.passed for report in verification.values()):
                    result["status"] = "FAIL"
                    result["fail_reason"] = "Active or history read-diff verification failed"
            print(json.dumps(result, indent=2, sort_keys=True))
            sys.exit(0 if result["status"] == "PASS" else 1)
        finally:
            sqlite_store.close()
            age_store.close()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
