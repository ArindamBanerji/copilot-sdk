"""Translate storage connection failures at graph I/O boundaries, not handlers."""

from __future__ import annotations

import logging
from typing import Any, Callable, ParamSpec, TypeVar

from fastapi import HTTPException

log = logging.getLogger(__name__)
P = ParamSpec("P")
T = TypeVar("T")

GRAPH_CONNECTION_ERRORS: tuple[type[Exception], ...] = (ConnectionError, TimeoutError)
try:
    from psycopg import InterfaceError, OperationalError
except ImportError:  # AGE is optional for local SDK installations.
    pass
else:
    GRAPH_CONNECTION_ERRORS += (OperationalError, InterfaceError)
try:
    from psycopg_pool import PoolClosed, PoolTimeout
except ImportError:
    pass
else:
    GRAPH_CONNECTION_ERRORS += (PoolClosed, PoolTimeout)
try:
    from ci_platform.graph.age_graph_store import GraphUnavailableError
except ImportError:
    pass
else:
    GRAPH_CONNECTION_ERRORS += (GraphUnavailableError,)


def graph_unavailable(error: Exception) -> HTTPException:
    log.error("Graph store operation failed", exc_info=error)
    return HTTPException(status_code=503, detail="Graph store unavailable")


def require_graph_store(store: Any) -> Any:
    if store is None:
        log.error("Graph store is not initialized")
        raise HTTPException(status_code=503, detail="Graph store unavailable")
    return store


def graph_call(operation: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Preserve results and programming errors; translate only storage outages."""
    try:
        return operation(*args, **kwargs)
    except GRAPH_CONNECTION_ERRORS as exc:
        raise graph_unavailable(exc) from exc
