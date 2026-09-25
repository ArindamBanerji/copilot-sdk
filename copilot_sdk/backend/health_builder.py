"""Shared, read-only AGE health contract for every copilot."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


def build_graph_health(
    graph_store: Any,
    graph_config: Any,
    domain: str,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the canonical graph health payload without writes or seeding."""
    backend = str(getattr(graph_config, "backend", "age") or "").lower()
    graph_name = str(
        getattr(graph_config, "graph", None)
        or getattr(graph_config, "shared_graph", None)
        or getattr(graph_store, "graph_name", None)
        or "soc_graph"
    )
    connected = (
        backend == "age"
        and graph_name == "soc_graph"
        and graph_store is not None
        and (
            callable(getattr(graph_store, "health_check", None))
            or hasattr(graph_store, "is_graph_connected")
            or callable(graph_store.get_all_decisions)
        )
    )
    probe = getattr(graph_store, "health_check", None)
    if callable(probe):
        try:
            result = probe()
            connected = connected and bool(result.get("connected", result.get("healthy", result))) if isinstance(result, dict) else connected and bool(result)
        except Exception:
            connected = False
    elif hasattr(graph_store, "is_graph_connected"):
        connected = connected and bool(getattr(graph_store, "is_graph_connected"))

    dsn = str(getattr(graph_config, "dsn", "") or "")
    identity_seed = f"{dsn}|{graph_name}".encode("utf-8")
    storage_identity = hashlib.sha256(identity_seed).hexdigest()[:24] if connected else "unavailable"
    source_keys = dict(getattr(graph_config, "source_keys", ()) or ())
    dsn_source = source_keys.get("dsn", "env:GRAPH_DSN")
    if dsn_source.startswith("toml:"):
        dsn_source = "file:graph_config.toml"
    elif not dsn_source.startswith("env:"):
        dsn_source = f"env:{dsn_source}" if dsn_source else "env:GRAPH_DSN"
    status = {
        "connected": connected,
        "graph_name": graph_name,
        "storage_identity": storage_identity,
        "dsn_source": dsn_source,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "components": {
            "decisions": "ready" if connected else "unavailable",
            "topology": "ready" if connected else "unavailable",
            "learning_restore": "ready" if connected else "unavailable",
        },
    }
    evidence = dict(evidence or getattr(graph_config, "cutover_evidence", {}) or {})
    components_ready = all(value == "ready" for value in status["components"].values())
    cutover_ready = bool(
        connected
        and components_ready
        and evidence.get("migration_parity_verified", False)
        and int(evidence.get("required_incomplete_operations", 0) or 0) == 0
        and int(evidence.get("gap_closure_records", 0) or 0) >= 66
        and int(evidence.get("open_production_candidates", 0) or 0) == 0
    )
    product_claim_allowed = bool(
        cutover_ready
        and evidence.get("live_verification_passed", False)
        and evidence.get("live_verification_authorized", False)
    )
    return {
        "ready": bool(connected),
        "status": "ok" if connected else "error",
        "domain": domain,
        "engine": (
            "copilot_sdk.scoring.CompoundingScorer + "
            "gae.profile_scorer.ProfileScorer + gae.evolution + AGE GraphStore"
        ),
        "graph_backend": "age",
        "graph_connected": bool(connected),
        "graph_name": graph_name,
        "graph_source": "graph" if connected else "unavailable",
        "graph_store_status": "available" if connected else "unavailable",
        "cutover_ready": cutover_ready,
        "product_claim_allowed": product_claim_allowed,
        "cutover_evidence": evidence,
        "graph_status": status,
    }


def health_status_code(payload: dict[str, Any]) -> int:
    return 200 if bool(payload.get("ready")) else 503
