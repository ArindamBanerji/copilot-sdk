"""Shared, read-only AGE health contract for every copilot."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, cast

from copilot_sdk.backend.graph_access import GRAPH_CONNECTION_ERRORS
from copilot_sdk.graph.production import GraphStoreWrapper
from copilot_sdk.graph.protocol import GraphStore, ProductionReadyStore, ProtocolV2GraphStore

log = logging.getLogger(__name__)


def _primary_store(store: GraphStore | GraphStoreWrapper | None) -> GraphStore | None:
    """Follow declared primary ownership through GraphStoreWrapper."""
    seen: set[int] = set()
    while store is not None:
        if id(store) in seen:
            raise ValueError("Cyclic graph store ownership")
        seen.add(id(store))
        if isinstance(store, GraphStoreWrapper):
            store = store.graph_primary
        else:
            return cast(GraphStore, store)
    return None


def _backend(store: GraphStore | None) -> str:
    if store is None:
        return "unknown"
    if isinstance(store, ProductionReadyStore):
        return "age"
    return "memory"


def _connection_diagnostics(store: GraphStore | None) -> dict[str, Any]:
    """Find the AGE client through reviewed adapter layers."""
    pending: list[Any] = [store]
    seen: set[int] = set()
    while pending:
        candidate = pending.pop(0)
        if candidate is None or id(candidate) in seen:
            continue
        seen.add(id(candidate))
        client = getattr(candidate, "_client", None)
        diagnostics = getattr(client, "connection_diagnostics", None)
        if callable(diagnostics):
            return cast(dict[str, Any], diagnostics())
        for name in ("_store", "store", "_graph_store"):
            inner = getattr(candidate, name, None)
            if inner is not None:
                pending.append(inner)
    return {
        "connection_mode": "memory" if store is not None else "unavailable",
        "pool_requested": False,
        "pool_available": False,
        "pool_size": 0,
        "pool_available_connections": 0,
        "pool_requests_waiting": 0,
    }


def build_graph_health(
    graph_store: GraphStore | GraphStoreWrapper | None,
    graph_config: Any,
    domain: str,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the canonical graph health payload without writes or seeding."""
    store = _primary_store(graph_store)
    protocol_version = (
        "v2" if store is not None and isinstance(store, ProtocolV2GraphStore) else "v1"
    )
    production_ready = bool(
        store is not None and isinstance(store, ProductionReadyStore)
    )
    backend = _backend(store) if store is not None else str(
        getattr(graph_config, "backend", None)
        or getattr(graph_config, "requested_backend", None)
        or "unknown"
    ).lower()
    graph_name = str(
        getattr(graph_config, "graph", None)
        or getattr(graph_config, "shared_graph", None)
        or getattr(store, "graph_name", None)
        or "soc_graph"
    )
    connected = False
    node_count: int | None = None
    if store is not None and backend != "unknown":
        try:
            # A real read probes the selected primary on every health request.
            # Count Decision nodes in this domain, not a materialized payload.
            node_count = int(store.count_decisions(domain))
            connected = True
        except GRAPH_CONNECTION_ERRORS:
            log.exception("Graph health probe failed for %s", domain)
    # Connectivity and production AGE readiness are deliberately separate.
    ready = connected and backend == "age" and graph_name == "soc_graph"

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
        ready
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
        "ready": ready,
        "status": "ok" if ready else "error",
        "domain": domain,
        "engine": (
            "copilot_sdk.scoring.CompoundingScorer + "
            "gae.profile_scorer.ProfileScorer + gae.evolution + " + backend + " GraphStore"
        ),
        "graph_backend": backend,
        "protocol_version": protocol_version,
        "production_ready": production_ready,
        "node_count": node_count,
        "node_count_scope": "domain_decisions",
        "graph_connected": bool(connected),
        "graph_name": graph_name,
        "graph_source": "graph" if connected else "unavailable",
        "graph_store_status": "available" if connected else "unavailable",
        "graph_connection": _connection_diagnostics(store),
        "cutover_ready": cutover_ready,
        "product_claim_allowed": product_claim_allowed,
        "cutover_evidence": evidence,
        "graph_status": status,
    }


def health_status_code(payload: dict[str, Any]) -> int:
    return 200 if bool(payload.get("ready")) else 503
