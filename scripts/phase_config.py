"""Domain-aware configuration shared by migration and cutover scripts."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

SDK_ROOT = Path(__file__).resolve().parent.parent

COPILOT_CONFIG: dict[str, dict[str, Any]] = {
    "trading": {"prefix": "TRD-", "db_path": SDK_ROOT / "apps/trading/backend/data/trading.db", "port": 8010},
    "purchasing": {"prefix": "PUR-", "db_path": SDK_ROOT / "apps/purchasing/backend/data/purchasing.db", "port": 8020},
    "dataops": {"prefix": "DOPS-", "db_path": SDK_ROOT / "apps/dataops/backend/data/dataops.db", "port": 8030},
    "s2p": {"prefix": "S2P-", "db_path": Path.home() / ".ci-platform/s2p/s2p.db", "port": 8002},
}


def add_domain_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--domain", choices=sorted(COPILOT_CONFIG), help="Copilot domain; defaults to MIGRATION_DOMAIN or trading")


def get_config(domain: str | None = None) -> dict[str, Any]:
    """Return paths and runtime settings for ``domain`` without mutating env."""
    selected = domain or os.environ.get("MIGRATION_DOMAIN", "trading")
    if selected not in COPILOT_CONFIG:
        print(f"ERROR: unknown domain '{selected}'. Valid: {', '.join(sorted(COPILOT_CONFIG))}")
        raise SystemExit(1)
    cfg = dict(COPILOT_CONFIG[selected])
    configured_path = os.environ.get("MIGRATION_SQLITE_PATH")
    cfg.update(
        domain=selected,
        db_path=str(Path(configured_path) if configured_path else cfg["db_path"]),
        age_dsn=os.environ.get("GRAPH_DSN", os.environ.get("AGE_DSN", "")),
        graph_name=os.environ.get("GRAPH_NAME", os.environ.get("AGE_GRAPH_NAME", "soc_graph")),
        api_base=os.environ.get(f"{selected.upper()}_API_BASE", f"http://127.0.0.1:{cfg['port']}"),
    )
    cfg["checkpoint_path"] = str(Path(cfg["db_path"]).parent / "phase_cycle_checkpoint.json")
    cfg["outbox_path"] = str(Path(cfg["db_path"]).parent / f"{selected}_dual_write_outbox.db")
    return cfg


def scoring_shape(domain: str) -> tuple[list[str], dict[str, float]]:
    """Read categories and neutral factor payload from the domain preset."""
    from copilot_sdk.scoring.presets import PRESET_REGISTRY

    preset = PRESET_REGISTRY[domain]()
    return list(preset.shape.category_names), {name: 0.5 for name in preset.shape.factor_names}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_domain_argument(parser)
    args = parser.parse_args()
    config = get_config(args.domain)
    config["age_dsn"] = "<configured>" if config["age_dsn"] else "<unset>"
    print(config)


if __name__ == "__main__":
    main()
