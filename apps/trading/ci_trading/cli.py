"""Console entry point for the Trading CLI editable package."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Sequence


def _package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_backend_cli() -> ModuleType:
    package_root = _package_root()
    backend_dir = package_root / "backend"
    repo_root = package_root.parent.parent

    for path in (backend_dir, repo_root):
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))

    cli_path = backend_dir / "cli.py"
    spec = importlib.util.spec_from_file_location("_ci_trading_backend_cli", cli_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Trading backend CLI from {cli_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: Sequence[str] | None = None) -> int:
    """Run the existing backend CLI with package-safe import paths."""

    backend_cli = _load_backend_cli()
    return int(backend_cli.main(list(argv) if argv is not None else None))


if __name__ == "__main__":
    raise SystemExit(main())
