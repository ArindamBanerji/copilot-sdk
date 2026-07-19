"""Endpoint-level cache decorator for quasi-static parameterized data."""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable

from starlette.requests import Request


ParamFn = Callable[[Request], str]
CopilotRef = str | Callable[[], str]


def cached_quasi_static(key: str, param_fn: ParamFn, *, copilot: CopilotRef = "trading"):
    """Cache a parameterized endpoint by key plus parameter value.

    The HTTP request still reaches FastAPI. The decorator only changes
    handler timing: ready cache entries skip recomputation, misses run the
    original handler and cache that parameter variant once.
    """

    def deco(handler: Callable[..., Any]):
        if inspect.iscoroutinefunction(handler):

            @wraps(handler)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                param_value = _param_value(param_fn, args, kwargs)
                cached = _cached_value(key, copilot, param_value)
                if cached is not _MISS:
                    return cached
                expected_version = _base_version(key, copilot)
                result = await handler(*args, **_call_kwargs(handler, args, kwargs))
                _store_value(key, copilot, param_value, result, expected_version)
                return result

            return async_wrapper

        @wraps(handler)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            param_value = _param_value(param_fn, args, kwargs)
            cached = _cached_value(key, copilot, param_value)
            if cached is not _MISS:
                return cached
            expected_version = _base_version(key, copilot)
            result = handler(*args, **_call_kwargs(handler, args, kwargs))
            _store_value(key, copilot, param_value, result, expected_version)
            return result

        return sync_wrapper

    return deco


class _Miss:
    pass


_MISS = _Miss()


def _cached_value(key: str, copilot: CopilotRef, param_value: str | None) -> Any:
    if param_value is None:
        return _MISS
    cache = _cache(copilot)
    if cache is None:
        return _MISS
    spec = cache.registrations.get(key)
    if spec is None or spec.category != "QUASI_STATIC":
        return _MISS
    entry = cache.get_entry(key, param_value)
    if entry is not None and entry.status == "ready" and entry.data is not None:
        return entry.data
    return _MISS


def _store_value(
    key: str,
    copilot: CopilotRef,
    param_value: str | None,
    result: Any,
    expected_base_version: int | None,
) -> None:
    if param_value is None:
        return
    cache = _cache(copilot)
    if cache is None:
        return
    spec = cache.registrations.get(key)
    if spec is None or spec.category != "QUASI_STATIC":
        return
    cache.set_from_endpoint(key, result, param_value, expected_base_version=expected_base_version)


def _base_version(key: str, copilot: CopilotRef) -> int | None:
    cache = _cache(copilot)
    if cache is None:
        return None
    entry = cache.get_entry(key)
    return None if entry is None else entry.version


def _param_value(param_fn: ParamFn, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str | None:
    request = kwargs.get("request")
    if request is None:
        request = next((arg for arg in args if isinstance(arg, Request)), None)
    if not isinstance(request, Request):
        return None
    return str(param_fn(request))


def _cache(copilot: CopilotRef):
    from copilot_sdk.state.invalidation import get_tab_state_cache

    return get_tab_state_cache(_resolve_copilot(copilot))


def _resolve_copilot(copilot: CopilotRef) -> str:
    if callable(copilot):
        return str(copilot())
    return str(copilot)


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
