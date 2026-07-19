"""Endpoint-level cache decorator for materialized static tab data."""

from __future__ import annotations

import inspect
import logging
import threading
from functools import wraps
from typing import Any, Callable

from starlette.requests import Request


CopilotRef = str | Callable[[], str]


class _Miss:
    pass


_MISS = _Miss()
_INFLIGHT_TIMEOUT_SECONDS = 3.0
_inflight: dict[str, "_Flight"] = {}
_inflight_lock = threading.Lock()
log = logging.getLogger(__name__)


class _Flight:
    def __init__(self) -> None:
        self.event = threading.Event()
        self.result: Any = _MISS
        self.error: BaseException | None = None


def cached_static(key: str, *, copilot: CopilotRef = "trading", url: str | None = None):
    """Read from TabStateCache inside an endpoint handler.

    Decorator order matters:
        @router.get("/api/trajectory")
        @cached_static("trajectory")
        def get_trajectory(): ...

    FastAPI must register the outer route decorator; this wrapper only
    changes handler timing by avoiding recomputation on warm cache hits.
    """

    def deco(handler: Callable[..., Any]):
        if inspect.iscoroutinefunction(handler):

            @wraps(handler)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                cached = _cached_value(key, copilot, url, args, kwargs)
                if cached is not _MISS:
                    return cached
                flight_key = _flight_key(key, copilot)
                flight, should_compute = _begin_flight(flight_key)
                if not should_compute:
                    if await _await_flight(flight):
                        return _flight_result(flight)
                    log.warning("cached_static inflight wait timed out for %s; recomputing", flight_key)
                    flight, should_compute = _begin_flight(flight_key, force_new=True)
                try:
                    result = await _call_handler_async(handler, key, copilot, args, kwargs)
                    _store_value(key, copilot, result, url, args, kwargs)
                    _finish_flight(flight_key, flight, result=result)
                    return result
                except BaseException as exc:
                    _finish_flight(flight_key, flight, error=exc)
                    raise

            return async_wrapper

        @wraps(handler)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            cached = _cached_value(key, copilot, url, args, kwargs)
            if cached is not _MISS:
                return cached
            flight_key = _flight_key(key, copilot)
            flight, should_compute = _begin_flight(flight_key)
            if not should_compute:
                if _wait_for_flight(flight):
                    return _flight_result(flight)
                log.warning("cached_static inflight wait timed out for %s; recomputing", flight_key)
                flight, should_compute = _begin_flight(flight_key, force_new=True)
            try:
                result = _call_handler_sync(handler, key, copilot, args, kwargs)
                _store_value(key, copilot, result, url, args, kwargs)
                _finish_flight(flight_key, flight, result=result)
                return result
            except BaseException as exc:
                _finish_flight(flight_key, flight, error=exc)
                raise

        return sync_wrapper

    return deco


def _cached_value(
    key: str,
    copilot: CopilotRef,
    expected_url: str | None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    cache = _cache(copilot, args, kwargs)
    if cache is None:
        return _MISS
    expected_url = expected_url or _registered_url(cache, key)
    if expected_url is not None and not _request_matches(expected_url, args, kwargs):
        return _MISS
    entry = cache.get_entry(key)
    if entry is not None and entry.status == "ready" and entry.data is not None:
        return entry.data
    return _MISS


def _store_value(
    key: str,
    copilot: CopilotRef,
    result: Any,
    expected_url: str | None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    cache = _cache(copilot, args, kwargs)
    if cache is None:
        return
    spec = cache.registrations.get(key)
    if spec is None or getattr(spec, "tier", "STANDARD") == "CRITICAL":
        return
    expected_url = expected_url or getattr(spec, "url", None)
    if expected_url is not None and not _request_matches(expected_url, args, kwargs):
        return
    cache.set_from_endpoint(key, result)


def _reads_scorer(key: str, copilot: CopilotRef, args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
    cache = _cache(copilot, args, kwargs)
    if cache is None:
        return False
    spec = cache.registrations.get(key)
    return bool(getattr(spec, "reads_scorer", False))


def _call_handler_sync(
    handler: Callable[..., Any],
    key: str,
    copilot: CopilotRef,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    call_kwargs = _call_kwargs(handler, args, kwargs)
    if not _reads_scorer(key, copilot, args, kwargs):
        return handler(*args, **call_kwargs)
    from copilot_sdk.scoring.mutation_lock import get_mutation_lock

    with get_mutation_lock(_resolve_copilot(copilot)):
        return handler(*args, **call_kwargs)


async def _call_handler_async(
    handler: Callable[..., Any],
    key: str,
    copilot: CopilotRef,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    call_kwargs = _call_kwargs(handler, args, kwargs)
    if not _reads_scorer(key, copilot, args, kwargs):
        return await handler(*args, **call_kwargs)
    from copilot_sdk.scoring.mutation_lock import get_mutation_lock

    with get_mutation_lock(_resolve_copilot(copilot)):
        return await handler(*args, **call_kwargs)


def _cache(
    copilot: CopilotRef,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
):
    from copilot_sdk.state.invalidation import get_tab_state_cache

    resolved = _resolve_copilot(copilot)
    request = _request_from_args(args or (), kwargs or {})
    if request is not None and "app" in request.scope:
        state = getattr(request.app, "state", None)
        if state is None:
            return None
        return getattr(state, f"{resolved}_tab_state_cache", None)
    return get_tab_state_cache(resolved)


def _flight_key(key: str, copilot: CopilotRef) -> str:
    return f"{_resolve_copilot(copilot)}:{key}"


def _begin_flight(flight_key: str, *, force_new: bool = False) -> tuple[_Flight, bool]:
    with _inflight_lock:
        if not force_new:
            existing = _inflight.get(flight_key)
            if existing is not None:
                return existing, False
        flight = _Flight()
        _inflight[flight_key] = flight
        return flight, True


def _wait_for_flight(flight: _Flight) -> bool:
    return flight.event.wait(timeout=_INFLIGHT_TIMEOUT_SECONDS)


async def _await_flight(flight: _Flight) -> bool:
    import asyncio

    return await asyncio.to_thread(_wait_for_flight, flight)


def _flight_result(flight: _Flight) -> Any:
    if flight.error is not None:
        raise flight.error
    if flight.result is not _MISS:
        return flight.result
    return _MISS


def _finish_flight(
    flight_key: str,
    flight: _Flight,
    *,
    result: Any = _MISS,
    error: BaseException | None = None,
) -> None:
    flight.result = result
    flight.error = error
    with _inflight_lock:
        if _inflight.get(flight_key) is flight:
            _inflight.pop(flight_key, None)
        flight.event.set()


def _resolve_copilot(copilot: CopilotRef) -> str:
    if callable(copilot):
        return str(copilot())
    return str(copilot)


def _registered_url(cache: Any, key: str) -> str | None:
    spec = cache.registrations.get(key)
    return getattr(spec, "url", None)


def _call_kwargs(
    handler: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    if "request" in kwargs:
        return kwargs
    parameters = inspect.signature(handler).parameters
    if "request" not in parameters:
        return kwargs
    names = list(parameters)
    if names.index("request") < len(args):
        return kwargs
    return {**kwargs, "request": None}


def _request_matches(expected_url: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
    request = _request_from_args(args, kwargs)
    if not isinstance(request, Request):
        return False
    actual = str(request.url.path)
    if request.url.query:
        actual = f"{actual}?{request.url.query}"
    return bool(actual == expected_url)


def _request_from_args(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Request | None:
    request = kwargs.get("request")
    if request is None:
        request = next((arg for arg in args if isinstance(arg, Request)), None)
    return request if isinstance(request, Request) else None
