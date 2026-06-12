"""Command-line entrypoint for Copilot SDK migrations."""

from __future__ import annotations

import argparse
import json
import sys
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
    sqlite_to_age.add_argument("--batch-size", type=int, default=50)
    sqlite_to_age.add_argument("--no-verify", action="store_true")

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
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        if result.get("status") == "FAIL":
            print(f"Migration failed: {result.get('fail_reason', 'unknown failure')}")
            sys.exit(1)
        sys.exit(0)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
