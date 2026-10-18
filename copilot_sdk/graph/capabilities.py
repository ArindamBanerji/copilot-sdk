"""Runtime capability checks for optional graph-store interfaces."""

from __future__ import annotations

from typing import TypeVar

from copilot_sdk.graph.protocol import BoundedProjectionStore, GraphStore

_W = TypeVar("_W")


def require_bounded_projection_store(
    store: GraphStore,
    *,
    feature: str = "",
) -> BoundedProjectionStore:
    """Narrow to the bounded capability or fail configuration early."""
    if not isinstance(store, BoundedProjectionStore):
        label = f" for feature {feature!r}" if feature else ""
        raise RuntimeError(
            f"store does not support bounded projections{label}; "
            f"got {type(store).__name__}"
        )
    return store


def has_bounded_projection(store: GraphStore) -> bool:
    """Return whether a store supports bounded projections at runtime."""
    return isinstance(store, BoundedProjectionStore)


__all__ = ["has_bounded_projection", "require_bounded_projection_store"]
