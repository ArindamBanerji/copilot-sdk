"""Invalidation registry, headers, and route scanning."""

from __future__ import annotations

import inspect
import logging
from typing import Any, Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from copilot_sdk.state.tab_state_cache import TabStateCache

log = logging.getLogger(__name__)

MUTATION_PATHS: dict[tuple[str, str], str] = {
    ("POST", "/api/score"): "score",
    ("POST", "/api/learn"): "learn",
    ("POST", "/api/trading/score-as"): "score",
    ("POST", "/api/trading/webhook/tradingview"): "score",
    ("POST", "/api/trading/webhook/test"): "score",
    ("POST", "/api/trading/evolution/promote"): "evolution",
    ("POST", "/api/trading/evolution/generate"): "evolution",
    ("POST", "/api/trading/evolution/shadow-test"): "evolution",
    ("POST", "/api/trading/evolution/apply"): "evolution",
    ("POST", "/api/trading/evolution/rollback"): "evolution",
    ("POST", "/api/trading/promotion/{category}/promote"): "evolution",
    ("POST", "/api/trading/promotion/{category}/demote"): "evolution",
    ("POST", "/api/transfer/execute"): "transfer",
    ("POST", "/api/broker/orders"): "market_data_refresh",
    ("POST", "/api/broker/sync"): "market_data_refresh",
    ("POST", "/api/trading/market/refresh"): "market_data_refresh",
    ("POST", "/api/trading/import/csv"): "reset",
    ("POST", "/api/trading/import/broker"): "reset",
    ("POST", "/api/trading/journal/entry"): "score",
    ("POST", "/api/context/trade-metadata"): "metadata_update",
    ("POST", "/api/archetypes/apply/{name}"): "reset",
}

_CACHES: dict[str, TabStateCache] = {}


def register_tab_state_cache(cache: TabStateCache) -> TabStateCache:
    _CACHES[cache.copilot] = cache
    return cache


def get_tab_state_cache(copilot: str) -> TabStateCache | None:
    return _CACHES.get(str(copilot))


def invalidate_cache_event(copilot: str, event: str) -> None:
    """Invalidate an out-of-band event under the domain mutation lock.

    Callers must not already hold the non-reentrant domain mutation lock.
    In-lock mutation handlers should use apply_cache_invalidation_event().
    """
    cache = get_tab_state_cache(copilot)
    if cache is None:
        return
    from copilot_sdk.scoring.mutation_lock import mutation_lock_held, mutation_lock_scope

    if mutation_lock_held(copilot):
        apply_cache_invalidation_event(copilot, event)
        return
    with mutation_lock_scope(copilot):
        apply_cache_invalidation_event(copilot, event)


def apply_cache_invalidation_event(copilot: str, event: str) -> list[str]:
    """Apply recompute/delete while the caller holds the mutation lock."""
    cache = get_tab_state_cache(copilot)
    if cache is None:
        return []
    urls = cache.get_urls_for_event(event)
    try:
        cache.invalidate_sync(event)
    except Exception as exc:
        log.warning("Cache event %s.%s failed, deleting affected entries: %s", copilot, event, exc)
        cache.delete_critical(event)
        cache.delete_standard(event)
    return urls


def create_invalidation_header_middleware(
    copilot: str,
    *,
    mutation_paths: dict[tuple[str, str], str] | None = None,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    paths = mutation_paths or MUTATION_PATHS

    async def middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        if response.status_code < 400:
            event = _event_for_request(request, paths)
            cache = get_tab_state_cache(copilot)
            if event and cache is not None:
                _set_invalidated_urls_header(response, cache.get_urls_for_event(event))
        return response

    return middleware


def scan_mutation_routes(app: Any, mutation_paths: dict[tuple[str, str], str] | None = None) -> list[dict[str, str]]:
    paths = mutation_paths or MUTATION_PATHS
    missing: list[dict[str, str]] = []
    markers = (
        "scorer.score(",
        "scorer.score (",
        "scorer.learn(",
        "scorer.learn (",
        "write_outcome(",
        "verify(",
        "promote(",
        "apply(",
        "transfer(",
        "reset(",
        "refresh(",
        "append(",
        "place_order(",
        "sync(",
        "import(",
    )
    for route in getattr(app, "routes", []):
        methods = {str(method).upper() for method in getattr(route, "methods", set())}
        if "POST" not in methods:
            continue
        path = str(getattr(route, "path", ""))
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        source = ""
        try:
            source = inspect.getsource(endpoint)
        except (OSError, TypeError):
            pass
        has_configured_event = ("POST", path) in paths
        has_atomic_decorator = getattr(endpoint, "__mutation_lock_event__", None) is not None
        has_manual_atomic_invalidation = (
            "get_mutation_lock(" in source
            and "apply_cache_invalidation_event(" in source
        )
        if has_configured_event and not has_atomic_decorator and not has_manual_atomic_invalidation:
            missing.append({"method": "POST", "path": path, "endpoint": getattr(endpoint, "__name__", "")})
            continue
        if any(marker in source for marker in markers) and not has_configured_event:
            missing.append({"method": "POST", "path": path, "endpoint": getattr(endpoint, "__name__", "")})
    return missing


def _set_invalidated_urls_header(response: Response | None, urls: list[str]) -> None:
    if response is not None and urls:
        response.headers["X-Invalidated-Urls"] = ",".join(urls)


def _event_for_request(
    request: Request,
    paths: dict[tuple[str, str], str],
) -> str | None:
    method = request.method.upper()
    raw_path = request.url.path
    direct = paths.get((method, raw_path))
    if direct is not None:
        return direct
    route = request.scope.get("route")
    route_path = str(getattr(route, "path", "") or "")
    return paths.get((method, route_path))
