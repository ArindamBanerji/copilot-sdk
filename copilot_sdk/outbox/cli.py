"""Outbox CLI commands."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Mapping, Sequence

from .store import OutboxStore
from .worker import OutboxWorker

logger = logging.getLogger(__name__)


def _default_db_path(domain: str) -> Path:
    safe_domain = domain.strip().lower()
    return Path.home() / ".ci-platform" / safe_domain / f"{safe_domain}_outbox.db"


def _store_for(domain: str, db_path: str | None) -> OutboxStore:
    return OutboxStore(db_path or _default_db_path(domain))


def status_command(domain: str, db_path: str | None = None) -> dict[str, int | str]:
    """Show outbox status counts."""

    store = _store_for(domain, db_path)
    try:
        return {
            "domain": domain,
            "total": store.count_total(),
            "pending": store.count_unprocessed(),
            "dead_letters": len(store.get_dead_letters(limit=1_000_000)),
        }
    finally:
        store.close()


def process_command(domain: str, db_path: str | None = None) -> dict[str, int | str]:
    """Process all pending events with registered CLI handlers."""

    store = _store_for(domain, db_path)
    try:
        worker = OutboxWorker(store)
        logger.warning(
            "No handlers registered. Events will remain unprocessed. "
            "Register handlers via worker.register() before calling process."
        )
        processed = worker.run_until_empty()
        return {
            "domain": domain,
            "processed": processed,
            "pending": store.count_unprocessed(),
        }
    finally:
        store.close()


def replay_command(
    domain: str,
    from_offset: int = 0,
    db_path: str | None = None,
) -> dict[str, int | str]:
    """Replay events from an event id offset."""

    store = _store_for(domain, db_path)
    try:
        worker = OutboxWorker(store)
        replayed = worker.replay(from_offset)
        return {"domain": domain, "replayed": replayed, "from_offset": from_offset}
    finally:
        store.close()


def dead_letters_command(
    domain: str,
    db_path: str | None = None,
) -> dict[str, object]:
    """Show dead-lettered events."""

    store = _store_for(domain, db_path)
    try:
        letters = store.get_dead_letters()
        return {
            "domain": domain,
            "dead_letters": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "error": event.error,
                    "processed_at": event.processed_at,
                }
                for event in letters
            ],
        }
    finally:
        store.close()


def build_parser() -> argparse.ArgumentParser:
    """Build the outbox CLI parser."""

    parser = argparse.ArgumentParser(prog="python -m copilot_sdk.outbox")
    subcommands = parser.add_subparsers(dest="command", required=True)

    for name in ("status", "process", "dead-letters"):
        cmd = subcommands.add_parser(name)
        cmd.add_argument("--domain", required=True)
        cmd.add_argument("--db-path")

    replay = subcommands.add_parser("replay")
    replay.add_argument("--domain", required=True)
    replay.add_argument("--from-offset", type=int, default=0)
    replay.add_argument("--db-path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the outbox CLI."""

    args = build_parser().parse_args(argv)
    result: Mapping[str, object]
    if args.command == "status":
        result = status_command(args.domain, args.db_path)
    elif args.command == "process":
        result = process_command(args.domain, args.db_path)
    elif args.command == "replay":
        result = replay_command(args.domain, args.from_offset, args.db_path)
    elif args.command == "dead-letters":
        result = dead_letters_command(args.domain, args.db_path)
    else:
        raise ValueError(f"Unknown command: {args.command}")
    print(json.dumps(result, sort_keys=True))
    return 0
