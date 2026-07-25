"""Domain-aware configuration shared by migration and cutover scripts."""

from __future__ import annotations

import argparse
import os
import sys
from uuid import uuid4
from pathlib import Path
from typing import Any

from copilot_sdk.config import GraphConfig

SDK_ROOT = Path(__file__).resolve().parent.parent


def _default_score_payload(*, category: str, factors: dict[str, float], cycle_num: int) -> dict[str, Any]:
    """Build the shared SDK score request used by non-S2P copilots."""
    return {"category": category, "factors": factors}


def _s2p_score_payload(*, category: str, factors: dict[str, float], cycle_num: int) -> dict[str, Any]:
    """Build the procurement-event request required by S2P's score route."""
    return {
        "event_id": f"GATE-{uuid4().hex[:8]}",
        "category": category,
        "amount": 5000.0,
        "supplier_id": f"SUP-{cycle_num:04d}",
        "supplier_risk_rating": 0.5,
    }

COPILOT_CONFIG: dict[str, dict[str, Any]] = {
    "trading": {"prefix": "TRD-", "db_path": SDK_ROOT / "apps/trading/backend/data/trading.db", "port": 8010, "score_path": "/api/score", "learn_path": "/api/learn", "score_payload_fn": _default_score_payload},
    "purchasing": {"prefix": "PUR-", "db_path": SDK_ROOT / "apps/purchasing/backend/data/purchasing.db", "port": 8020, "score_path": "/api/score", "learn_path": "/api/learn", "score_payload_fn": _default_score_payload},
    "dataops": {"prefix": "DOPS-", "db_path": SDK_ROOT / "apps/dataops/backend/data/dataops.db", "port": 8030, "score_path": "/api/score", "learn_path": "/api/learn", "score_payload_fn": _default_score_payload},
    "s2p": {
        "prefix": "S2P-",
        "db_path": os.path.abspath(
            os.path.join(SDK_ROOT, "..", "s2p-copilot", "backend", "app", "data", "s2p.db")
        ),
        "port": 8002,
        "score_path": "/api/s2p/score",
        "learn_path": "/api/learn",
        "score_payload_fn": _s2p_score_payload,
    },
}


def add_domain_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--domain", choices=sorted(COPILOT_CONFIG), help="Copilot domain; defaults to MIGRATION_DOMAIN or trading")


def get_config(domain: str | None = None) -> dict[str, Any]:
    """Return paths and typed graph settings for ``domain`` without mutating env."""
    selected = domain or os.environ.get("MIGRATION_DOMAIN", "trading")
    if selected not in COPILOT_CONFIG:
        print(f"ERROR: unknown domain '{selected}'. Valid: {', '.join(sorted(COPILOT_CONFIG))}")
        raise SystemExit(1)
    graph_config = GraphConfig.load(selected)
    cfg = dict(COPILOT_CONFIG[selected])
    configured_path = os.environ.get("MIGRATION_SQLITE_PATH")
    cfg.update(
        domain=selected,
        prefix=graph_config.prefix,
        port=graph_config.port if graph_config.port is not None else cfg["port"],
        backend=graph_config.backend,
        expected_backend=graph_config.expected_backend,
        graph_name=graph_config.graph,
        authorized=graph_config.authorized,
        sources=dict(graph_config.sources),
        db_path=str(Path(configured_path) if configured_path else cfg["db_path"]),
        age_dsn=graph_config.dsn or os.environ.get("GRAPH_DSN", os.environ.get("AGE_DSN", "")),
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
    parser.add_argument("--print-config", action="store_true", help="Print resolved config with DSN redacted")
    args = parser.parse_args()
    config = get_config(args.domain)
    config["age_dsn"] = "<configured>" if config["age_dsn"] else "<unset>"
    print(config)


if __name__ == "__main__":
    main()
