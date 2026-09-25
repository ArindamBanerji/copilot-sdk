"""Fail-closed production bindings for the shared AGE graph.

Only reviewed store wrappers expose their primary through GraphStoreWrapper.
A backend='age' attribute, forwarded capability, or reachable secondary is
not evidence that writes are AGE-primary. SQL here is read-only connection
metadata; connection handling remains owned by ci-platform's AGEClient.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from copilot_sdk.config.graph_config import GraphConfig, GraphConfigError, GraphIdentity


class GraphStoreWrapper:
    """Opt-in for reviewed decorators whose reads/writes use this one primary."""

    _store: Any

    @property
    def graph_primary(self) -> Any:
        return self._store


@dataclass(frozen=True)
class GraphStoreCapabilities:
    authoritative_backend: str
    config: GraphConfig
    identity: GraphIdentity


def _probe_client_identity(client: Any) -> GraphIdentity:
    """Use a fresh, bounded connection; LOAD age and graph existence must succeed.

    pg_control_system's server-issued identifier avoids host aliases and equal
    database OIDs on different clusters being mistaken for the same database.
    The service role must be granted EXECUTE on pg_control_system(); permission
    errors fail closed rather than falling back to a DSN/name comparison.
    """
    try:
        with client._connect_fresh(autocommit=False) as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '5s'")
            row = conn.execute(
                "SELECT c.system_identifier::text, d.oid::bigint, d.datname, "
                "g.graphid::bigint, g.name::text "
                "FROM pg_control_system() c "
                "CROSS JOIN pg_database d CROSS JOIN ag_catalog.ag_graph g "
                "WHERE d.datname = current_database() AND g.name = %s",
                (client._graph,),
            ).fetchone()
            if row is None or len(row) != 5 or str(row[4]) != client._graph:
                raise ValueError("missing AGE graph identity")
            if not str(row[0]).isdigit() or int(row[1]) <= 0 or int(row[3]) <= 0:
                raise ValueError("invalid server identity")
            database_id = hashlib.sha256(
                f"{row[0]}:{row[1]}:{row[2]}".encode("utf-8")
            ).hexdigest()
            return GraphIdentity(database_id, str(row[4]), int(row[3]))
    except Exception:
        # Driver errors can include credentials/conninfo. Do not chain them.
        raise GraphConfigError(
            "AGE identity probe failed: verify connection, AGE graph and "
            "service-role permission for pg_control_system()"
        ) from None


def probe_graph_identity(dsn: str, graph: str) -> GraphIdentity:
    from ci_platform.graph.age_client import AGEClient

    return _probe_client_identity(AGEClient(dsn=dsn, graph_name=graph, use_pool=False))


def age_client_for_store(store: Any, *, domain: str) -> Any:
    """Follow declared primaries only, rejecting unknown wrappers and local stores."""
    from ci_platform.graph.age_client import AGEClient
    from ci_platform.graph.age_graph_store import AGEGraphStore
    from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

    visited: set[int] = set()
    while isinstance(store, GraphStoreWrapper):
        if id(store) in visited:
            raise GraphConfigError("cyclic graph primary binding")
        visited.add(id(store))
        if getattr(store, "domain", None) != domain:
            raise GraphConfigError("graph wrapper domain mismatch")
        store = store.graph_primary
    if type(store) is not AGEGraphStoreAdapter or store.domain != domain:
        raise GraphConfigError(
            "Production scorer requires an AGE-backed GraphStore primary; "
            "SQLite, InMemory, dual-write and undeclared wrappers are test/offline only"
        )
    primary = store._store
    if type(primary) is not AGEGraphStore or type(primary._client) is not AGEClient:
        raise GraphConfigError("AGE adapter does not own a verified AGE primary connection")
    return primary._client


def validate_production_store(store: Any, config: GraphConfig) -> GraphStoreCapabilities:
    """Revalidate an injected store, including decorators and its actual destination."""
    if config.profile != "production":
        raise GraphConfigError("production store validation requires production GraphConfig")
    client = age_client_for_store(store, domain=config.domain)
    expected = config.require_shared_graph()
    identity = _probe_client_identity(client)
    if identity != expected:
        raise GraphConfigError("injected AGE store destination differs from GraphConfig")
    return GraphStoreCapabilities("age", config, identity)
