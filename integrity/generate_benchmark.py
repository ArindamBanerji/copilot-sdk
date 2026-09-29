"""Compatibility entry point for deterministic benchmark generation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrity.benchmark_fixture import (
    DOMAIN,
    FACTORS_PATH,
    FIXTURE_DIR,
    GENERATED,
    N_EVAL,
    N_TRAIN,
    OUTCOMES_PATH,
    SEED,
    VERSION,
    build_fixture,
    main,
)

__all__ = [
    "DOMAIN",
    "FACTORS_PATH",
    "FIXTURE_DIR",
    "GENERATED",
    "N_EVAL",
    "N_TRAIN",
    "OUTCOMES_PATH",
    "SEED",
    "VERSION",
    "build_fixture",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
