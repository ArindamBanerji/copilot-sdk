"""ci-trading CLI entry point."""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_source_backend_path() -> None:
    """Allow source-tree execution before editable install path setup."""
    backend = Path(__file__).resolve().parent.parent / "backend"
    if backend.is_dir() and str(backend) not in sys.path:
        sys.path.insert(0, str(backend))


_ensure_source_backend_path()

from app.cli_sdk import main as _main  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    return int(_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
