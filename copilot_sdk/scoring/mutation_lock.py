"""Per-domain mutation serialization for shared scorer state."""

from __future__ import annotations

import functools
import inspect
import threading
from contextlib import contextmanager
from collections.abc import Iterator
from typing import Any, Callable, get_type_hints

_LOCKS_GUARD = threading.Lock()
_MUTATION_LOCKS: dict[str, threading.Lock] = {}
_HELD_LOCKS = threading.local()


def get_mutation_lock(domain: str) -> threading.Lock:
    """Return the mutation lock for one copilot/scorer domain."""
    normalized = str(domain or "default")
    with _LOCKS_GUARD:
        lock = _MUTATION_LOCKS.get(normalized)
        if lock is None:
            lock = threading.Lock()
            _MUTATION_LOCKS[normalized] = lock
        return lock


@contextmanager
def mutation_lock_scope(domain: str) -> Iterator[None]:
    normalized = str(domain or "default")
    with get_mutation_lock(normalized):
        held = getattr(_HELD_LOCKS, "domains", None)
        if held is None:
            held = set()
            _HELD_LOCKS.domains = held
        held.add(normalized)
        try:
            yield
        finally:
            held.discard(normalized)


def mutation_lock_held(domain: str) -> bool:
    held: set[str] = getattr(_HELD_LOCKS, "domains", set())
    return str(domain or "default") in held


def serialize_mutation(
    domain_fn: Callable[..., str | None] | str | None = None,
    *,
    event: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Serialize a mutating handler on a per-domain threading.Lock."""

    def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(handler)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            domain = _resolve_domain(domain_fn, args, kwargs)
            with mutation_lock_scope(domain):
                result = handler(*args, **kwargs)
                if event:
                    from copilot_sdk.state.invalidation import apply_cache_invalidation_event

                    apply_cache_invalidation_event(domain, event)
                return result

        setattr(wrapper, "__mutation_lock_domain__", domain_fn)
        setattr(wrapper, "__mutation_lock_event__", event)
        setattr(wrapper, "__signature__", _resolved_signature(handler))
        return wrapper

    return decorator


def _resolved_signature(handler: Callable[..., Any]) -> inspect.Signature:
    signature = inspect.signature(handler)
    try:
        hints = get_type_hints(handler)
    except Exception:
        hints = {}
    parameters = [
        parameter.replace(annotation=hints.get(name, parameter.annotation))
        for name, parameter in signature.parameters.items()
    ]
    return_annotation = hints.get("return", signature.return_annotation)
    return signature.replace(parameters=parameters, return_annotation=return_annotation)


def _resolve_domain(
    domain_fn: Callable[..., str | None] | str | None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    if callable(domain_fn):
        value = domain_fn(*args, **kwargs)
    elif domain_fn is not None:
        value = domain_fn
    else:
        value = kwargs.get("domain") or kwargs.get("copilot")
        if value is None and args:
            value = getattr(args[0], "domain", None)
    return str(value or "default")
