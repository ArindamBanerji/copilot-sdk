"""Materialized tab-state cache infrastructure."""

from copilot_sdk.state.invalidation import (
    MUTATION_PATHS,
    apply_cache_invalidation_event,
    create_invalidation_header_middleware,
    get_tab_state_cache,
    invalidate_cache_event,
    register_tab_state_cache,
    scan_mutation_routes,
)
from copilot_sdk.state.cached_static import cached_static
from copilot_sdk.state.tab_state_cache import CacheEntry, KeySpec, TabStateCache
from copilot_sdk.state.tab_state_router import create_tab_state_router

__all__ = [
    "CacheEntry",
    "KeySpec",
    "MUTATION_PATHS",
    "TabStateCache",
    "apply_cache_invalidation_event",
    "cached_static",
    "create_invalidation_header_middleware",
    "create_tab_state_router",
    "get_tab_state_cache",
    "invalidate_cache_event",
    "register_tab_state_cache",
    "scan_mutation_routes",
]
