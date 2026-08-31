"""Restart-safe persistence for immutable Frozen Twin snapshots."""

from __future__ import annotations

import os
import json
import threading
from pathlib import Path
from typing import Any

from .models import FrozenSnapshot


class FrozenTwinStore:
    """Store one immutable JSON artifact per copilot.

    Creation uses exclusive file creation, so concurrent processes cannot
    silently replace the day-0 baseline.  A corrupted existing artifact is
    surfaced by ``load`` rather than treated as an unfrozen deployment.
    """

    def __init__(self, base_dir: str | os.PathLike[str] | None = None) -> None:
        configured = os.getenv("COPILOT_FROZEN_TWIN_DIR")
        self.base_dir = Path(base_dir or configured or (Path.home() / ".copilot_sdk" / "frozen_twins"))
        self._lock = threading.RLock()

    def _path(self, copilot: str) -> Path:
        normalized = "".join(char if char.isalnum() or char in "-_" else "_" for char in copilot.strip())
        if not normalized:
            raise ValueError("copilot must contain at least one non-whitespace character")
        return self.base_dir / f"{normalized}.json"

    def save(self, snapshot: FrozenSnapshot) -> None:
        """Create a snapshot file exactly once; never overwrite an artifact."""
        copilot = str(snapshot.metadata.get("copilot") or "")
        path = self._path(copilot)
        payload = snapshot.to_json()
        with self._lock:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            try:
                with path.open("x", encoding="utf-8", newline="\n") as handle:
                    handle.write(payload)
                    handle.write("\n")
            except FileExistsError as error:
                raise FileExistsError(f"Frozen Twin already exists for copilot {copilot!r}") from error

    def load(self, copilot: str) -> FrozenSnapshot | None:
        path = self._path(copilot)
        if not path.exists():
            return None
        with self._lock:
            return FrozenSnapshot.from_json(path.read_text(encoding="utf-8"))

    def exists(self, copilot: str) -> bool:
        return self._path(copilot).exists()

    def delete(self, copilot: str, *, confirmation: str | None = None) -> None:
        """Delete only with an explicit, exact copilot-name confirmation."""
        if confirmation != copilot:
            raise PermissionError("Frozen Twin deletion requires confirmation=copilot")
        with self._lock:
            self._path(copilot).unlink(missing_ok=True)


class GraphFrozenTwinStore(FrozenTwinStore):
    """Immutable Frozen Twin snapshots persisted in domain-scoped AGE state."""

    def __init__(self, graph_store: Any, domain: str) -> None:
        self._graph_store = graph_store
        self._domain = str(domain)
        self._lock = threading.RLock()

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
                raise ValueError("AGE Frozen Twin payload is not a snapshot")
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
            raise RuntimeError("AGE GraphStore cannot delete Frozen Twin state")
        delete(self._domain, f"frozen_twin:{copilot}")
