"""GraphStore factory with fail-closed configuration-driven AGE selection."""

from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Any, Mapping, cast

from copilot_sdk.config import GraphConfig, GraphConfigError
from copilot_sdk.config.graph_config import resolve_profile
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.graph.tenant_store import TenantScopedGraphStore

logger = logging.getLogger(__name__)

_VALID_BACKENDS = {"sqlite", "memory", "age", "dual_write"}


def _tenant_store(store: GraphStore, env: Mapping[str, str]) -> GraphStore:
    enabled = str(env.get("TENANT_ISOLATION_ENABLED", "false")).strip().lower() == "true"
    return TenantScopedGraphStore(store) if enabled else store


def _env_value(env: Mapping[str, str], key: str) -> str | None:
    value = env.get(key)
    if value is None:
        return None
    return str(value)


def _normalize_backend(value: str | None) -> str:
    if value is None or not str(value).strip():
        raise GraphConfigError(
            "graph backend is required; pass backend explicitly or provide a domain "
            "for GraphConfig resolution"
        )
    backend = str(value).strip().lower()
    if backend not in _VALID_BACKENDS:
        raise ValueError(
            f"invalid graph backend {value!r}; expected one of {sorted(_VALID_BACKENDS)}"
        )
    return backend


def _resolve_sqlite_path(
    *,
    db_path: str | Path | None,
    domain: str,
    env: Mapping[str, str],
) -> str | Path:
    if db_path is not None:
        return db_path
    ci_data_dir = _env_value(env, "CI_DATA_DIR")
    if ci_data_dir:
        return Path(ci_data_dir) / f"{domain}.db"
    return ":memory:"


def _validate_graph_domain(env: Mapping[str, str], domain: str) -> None:
    env_domain = _env_value(env, "GRAPH_DOMAIN")
    if env_domain is not None and env_domain != domain:
        raise ValueError(
            f"GRAPH_DOMAIN {env_domain!r} does not match requested domain {domain!r}"
        )


def _load_age_adapter():
    try:
        module = importlib.import_module("ci_platform.graph.age_sdk_adapter")
    except ImportError as exc:
        raise RuntimeError(
            "AGE graph backend requires ci-platform with "
            "ci_platform.graph.age_sdk_adapter importable"
        ) from exc
    try:
        return module.AGEGraphStoreAdapter
    except AttributeError as exc:
        raise RuntimeError(
            "AGE graph backend requires ci_platform.graph.age_sdk_adapter."
            "AGEGraphStoreAdapter"
        ) from exc


def _validate_age_graph_name(
    graph_name: str | None,
    *,
    test_mode: bool,
    read_only_soc_projection: bool,
    domain: str | None = None,
    shared_graph_authorization: str | None = None,
) -> str:
    graph = str(graph_name or "").strip()
    if not graph:
        raise ValueError("AGE graph backend requires explicit non-blank GRAPH_NAME")
    authorized_pair = f"{domain}:{graph}" if domain else ""
    authorized_pairs = {
        pair.strip()
        for pair in str(shared_graph_authorization or "").split(",")
        if pair.strip()
    }
    if graph == "soc_graph" and authorized_pair not in authorized_pairs:
        raise ValueError("soc_graph is forbidden for generic GraphStore factory contexts")
    if graph.startswith("protocol_v2_test") and not test_mode:
        raise ValueError("protocol_v2_test* AGE graphs require test_mode=True")
    return graph


def create_graph_store(
    *,
    backend: str | None = None,
    domain: str | None = None,
    db_path: str | Path | None = None,
    decision_id_prefix: str = "",
    dsn: str | None = None,
    graph_name: str | None = None,
    env: Mapping[str, str] | None = None,
    test_mode: bool = False,
    read_only_soc_projection: bool = False,
    shared_graph_authorization: str | None = None,
    profile: str | None = None,
    config: GraphConfig | None = None,
) -> GraphStore:
    """Create a GraphStore.

    Every path uses GraphConfig, including explicit legacy arguments. A supplied
    config is immutable: conflicting overrides are rejected. Local/dual-write
    stores require an explicit test/offline profile; test_mode is not a profile.
    """

    env_map: Mapping[str, str] = os.environ if env is None else env
    config_driven = backend is None and dsn is None and graph_name is None
    if backend is not None:
        _normalize_backend(backend)
    if domain is not None:
        _validate_graph_domain(env_map, domain)
    if config is None:
        if not domain:
            raise GraphConfigError("create_graph_store requires an explicit domain or GraphConfig")
        overrides: dict[str, Any] = {key: value for key, value in (
            ("backend", backend), ("dsn", dsn), ("graph", graph_name),
        ) if value is not None}
        if test_mode:
            overrides["active_test_mode"] = True
        config = GraphConfig.load(domain, profile=profile, env=env_map, overrides=overrides)
    else:
        for key, value, resolved in (
            ("domain", domain, config.domain), ("backend", backend, config.backend),
            ("dsn", dsn, config.dsn), ("graph", graph_name, config.graph),
        ):
            if value is not None and value != resolved:
                raise GraphConfigError(f"{key} override conflicts with supplied GraphConfig")
        if profile is not None and resolve_profile(profile) != config.profile:
            raise GraphConfigError("profile conflicts with supplied GraphConfig")
        if test_mode and not config.active_test_mode:
            raise GraphConfigError("test_mode conflicts with supplied GraphConfig")
        config_driven = True
    config.validate()
    # Probe before constructing any stateful adapter or SQLite outbox.
    config.require_shared_graph()
    selected_backend = config.backend
    selected_domain = config.domain
    dsn, graph_name = config.dsn, config.graph
    test_mode = config.active_test_mode
    if config_driven and shared_graph_authorization is None:
        shared_graph_authorization = config.authorized
    _validate_graph_domain(env_map, selected_domain)

    if selected_backend == "memory":
        from copilot_sdk.graph.memory_store import InMemoryGraphStore

        return _tenant_store(InMemoryGraphStore(domain=selected_domain), env_map)

    if selected_backend == "sqlite":
        sqlite_path = _resolve_sqlite_path(
            db_path=db_path,
            domain=selected_domain,
            env=env_map,
        )
        logger.info(
            "creating SQLite GraphStore for domain=%s path=%s",
            selected_domain,
            sqlite_path,
        )
        return _tenant_store(cast(
            GraphStore,
            SQLiteGraphStore(
                sqlite_path,
                domain=selected_domain,
                decision_id_prefix=decision_id_prefix,
            ),
        ), env_map)

    if selected_backend == "dual_write":
        sqlite_path = _resolve_sqlite_path(
            db_path=db_path,
            domain=selected_domain,
            env=env_map,
        )
        primary = SQLiteGraphStore(
            sqlite_path,
            domain=selected_domain,
            decision_id_prefix=decision_id_prefix,
        )
        selected_dsn = config.dsn
        if not selected_dsn or not str(selected_dsn).strip():
            primary.close()
            raise GraphConfigError(
                "dual_write backend requires an AGE DSN; set GRAPH_DSN or "
                f"{selected_domain.upper()}_ACTIVE_AGE_DSN"
            )
        selected_graph = config.graph
        dual_write_authorization = (
            shared_graph_authorization
            if shared_graph_authorization is not None
            else _env_value(env_map, "SHARED_GRAPH_AUTHORIZED")
        )
        if str(selected_graph or "").strip() == "soc_graph":
            required_pair = f"{selected_domain}:soc_graph"
            authorized_pairs = {
                pair.strip()
                for pair in str(dual_write_authorization or "").split(",")
                if pair.strip()
            }
            if required_pair not in authorized_pairs:
                primary.close()
                raise ValueError(
                    f"soc_graph requires SHARED_GRAPH_AUTHORIZED={required_pair}"
                )
        selected_graph = _validate_age_graph_name(
            selected_graph,
            test_mode=test_mode,
            read_only_soc_projection=read_only_soc_projection,
            domain=selected_domain,
            shared_graph_authorization=dual_write_authorization,
        )
        from copilot_sdk.graph.dual_write_store import DualWriteStore

        adapter_cls = _load_age_adapter()
        secondary_adapter = adapter_cls(
            dsn=str(selected_dsn), graph_name=selected_graph
        )
        setattr(secondary_adapter, "domain", selected_domain)
        secondary = cast(GraphStore, secondary_adapter)
        logger.info(
            "creating dual-write GraphStore for domain=%s path=%s graph_name=%s",
            selected_domain,
            sqlite_path,
            selected_graph,
        )
        outbox_path = Path(sqlite_path).parent / f"{selected_domain}_dual_write_outbox.db"
        return _tenant_store(cast(
            GraphStore,
            DualWriteStore(
                cast(GraphStore, primary), secondary, outbox_path=str(outbox_path)
            ),
        ), env_map)

    if not selected_domain.strip():
        raise ValueError("AGE graph backend requires explicit non-blank domain")

    selected_dsn = config.dsn
    if not selected_dsn or not str(selected_dsn).strip():
        raise ValueError("AGE graph backend requires explicit GRAPH_DSN")

    selected_graph = config.graph
    selected_graph = _validate_age_graph_name(
        selected_graph,
        test_mode=test_mode,
        read_only_soc_projection=read_only_soc_projection,
        domain=selected_domain,
        shared_graph_authorization=shared_graph_authorization,
    )

    adapter_cls = _load_age_adapter()
    logger.info(
        "creating AGE GraphStore for domain=%s graph_name=%s read_only_soc_projection=%s",
        selected_domain,
        selected_graph,
        read_only_soc_projection,
    )
    adapter = adapter_cls(dsn=str(selected_dsn), graph_name=selected_graph)
    setattr(adapter, "domain", selected_domain)
    setattr(adapter, "graph_config", config)
    store = _tenant_store(cast(GraphStore, adapter), env_map)
    if config.profile == "production":
        from copilot_sdk.graph.production import validate_production_store

        try:
            capabilities = validate_production_store(store, config)
            setattr(adapter, "graph_capabilities", capabilities)
        except Exception:
            adapter.close()
            raise
    return store
