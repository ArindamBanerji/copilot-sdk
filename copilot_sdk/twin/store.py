"""Restart-safe persistence for immutable Frozen Twin snapshots."""

from __future__ import annotations

import json
import threading
from copilot_sdk.graph.protocol import GraphStore

from .models import FrozenSnapshot


class FrozenTwinStore:
    """Immutable Frozen Twin snapshots persisted in domain-scoped graph state."""

    def __init__(self, graph_store: GraphStore, domain: str) -> None:
        self._graph_store = graph_store
        self._domain = str(domain)
        self._lock = threading.RLock()

    @property
    def graph_store(self) -> GraphStore:
        """The application-owned graph, also used for comparison references."""
        return self._graph_store

    def save(self, snapshot: FrozenSnapshot) -> None:
        copilot = str(snapshot.metadata.get("copilot") or "")
        if not copilot:
            raise ValueError("Frozen Twin snapshot requires copilot metadata")
        with self._lock:
            if self.exists(copilot):
                raise FileExistsError(f"Frozen Twin already exists for copilot {copilot!r}")
            payload = json.loads(snapshot.to_json())
            self._graph_store.save_promotion(
                self._domain, f"frozen_twin:{copilot}", {"snapshot": payload}
            )

    def load(self, copilot: str) -> FrozenSnapshot | None:
        with self._lock:
            state = self._graph_store.get_promotion(
                self._domain, f"frozen_twin:{copilot}"
            )
            if state is None:
                return None
            payload = state.get("snapshot")
            if not isinstance(payload, dict):
                raise ValueError("graph Frozen Twin payload is not a snapshot")
            return FrozenSnapshot.from_json(json.dumps(payload))

    def exists(self, copilot: str) -> bool:
        return self._graph_store.get_promotion(
            self._domain, f"frozen_twin:{copilot}"
        ) is not None

    def delete(self, copilot: str, *, confirmation: str | None = None) -> None:
        if confirmation != copilot:
            raise PermissionError("Frozen Twin deletion requires confirmation=copilot")
        delete = getattr(self._graph_store, "delete_promotion", None)
        if not callable(delete):
            raise RuntimeError("graph GraphStore cannot delete Frozen Twin state")
        delete(self._domain, f"frozen_twin:{copilot}")


class GraphFrozenTwinStore(FrozenTwinStore):
    """Compatibility name for the graph-only snapshot store."""
