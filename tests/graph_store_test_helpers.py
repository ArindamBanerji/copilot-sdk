"""Portable graph-store constructors used by backend-independent tests."""

from __future__ import annotations

from pathlib import Path

from copilot_sdk.graph.memory_store import InMemoryGraphStore


def make_memory_store(
    _legacy_path: str | Path | None = None,
    domain: str = "test",
    decision_id_prefix: str = "",
) -> InMemoryGraphStore:
    """Build the supported test/dev backend while ignoring retired file paths."""
    return InMemoryGraphStore(
        domain=domain,
        decision_id_prefix=decision_id_prefix,
    )
