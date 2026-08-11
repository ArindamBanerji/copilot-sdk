"""Module entry point for the Purchasing CLI."""

from __future__ import annotations

from cli import cli, main

__all__ = ["cli", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
