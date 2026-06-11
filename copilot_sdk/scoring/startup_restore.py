"""Startup restore helpers for L5 runtime state."""

from __future__ import annotations

import logging
from typing import Any

from copilot_sdk.scoring.dk_persistence import DKWelfordTracker


log = logging.getLogger(__name__)


def restore_l5_runtime_state(
    *,
    domain: str,
    scorer: Any,
    learning_store: Any | None,
    welford_tracker: DKWelfordTracker | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Best-effort L5 startup restore with explicit source reporting."""
    active_log = logger or log
    status: dict[str, Any] = {
        "dk_source": "cold-start",
        "welford_source": "cold-start",
        "centroid_source": "cold-start",
        "conservation_source": "cold-start",
        "dk_weights_loaded": False,
        "centroids_loaded": False,
        "welford_tracker": None,
        "conservation_state": None,
    }
    if learning_store is None:
        status.update({
            "dk_source": "missing",
            "welford_source": "missing",
            "centroid_source": "missing",
            "conservation_source": "missing",
        })
        return status

    _restore_dk(domain, scorer, learning_store, status, active_log)
    if welford_tracker is not None and isinstance(status.get("welford_tracker"), DKWelfordTracker):
        _copy_welford_tracker_state(welford_tracker, status["welford_tracker"])
        status["welford_tracker"] = welford_tracker
    _restore_centroids(domain, scorer, learning_store, status, active_log)
    _restore_conservation(domain, learning_store, status, active_log)
    return status


def _copy_welford_tracker_state(target: DKWelfordTracker, source: DKWelfordTracker) -> None:
    target._confirmed = source._confirmed
    target._overridden = source._overridden
    target._all = source._all


def _restore_dk(
    domain: str,
    scorer: Any,
    learning_store: Any,
    status: dict[str, Any],
    active_log: logging.Logger,
) -> None:
    get_dk_weights = getattr(learning_store, "get_dk_weights", None)
    if not callable(get_dk_weights):
        status["dk_source"] = "missing"
        status["welford_source"] = "missing"
        return
    try:
        row = get_dk_weights(domain)
    except Exception as exc:
        active_log.warning("L5 DK startup read failed for %s: %s", domain, exc)
        status["dk_source"] = "error"
        status["welford_source"] = "error"
        return
    if not row:
        status["dk_source"] = "missing"
        status["welford_source"] = "missing"
        return

    load_dk = getattr(scorer, "load_dk_weights_from_l5", None)
    if callable(load_dk):
        try:
            status["dk_weights_loaded"] = bool(load_dk(row.get("weight_json")))
            status["dk_source"] = "l5"
        except Exception as exc:
            active_log.warning("L5 DK startup restore failed for %s: %s", domain, exc)
            status["dk_source"] = "error"
    else:
        status["dk_source"] = "deferred"

    welford_state = row.get("welford_state")
    if welford_state is None:
        status["welford_source"] = "missing"
        return
    try:
        tracker = DKWelfordTracker.from_welford_state(
            welford_state,
            n_confirmed=row.get("n_confirmed"),
            n_overridden=row.get("n_overridden"),
        )
    except Exception as exc:
        active_log.warning("L5 Welford startup restore failed for %s: %s", domain, exc)
        status["welford_source"] = "error"
        return
    status["welford_tracker"] = tracker
    status["welford_source"] = "l5"


def _restore_centroids(
    domain: str,
    scorer: Any,
    learning_store: Any,
    status: dict[str, Any],
    active_log: logging.Logger,
) -> None:
    get_centroids = getattr(learning_store, "get_centroids", None)
    if not callable(get_centroids):
        status["centroid_source"] = "missing"
        return
    try:
        rows = get_centroids(domain)
    except Exception as exc:
        active_log.warning("L5 centroid startup read failed for %s: %s", domain, exc)
        status["centroid_source"] = "error"
        return
    if not rows:
        status["centroid_source"] = "missing"
        return
    load_centroids = getattr(scorer, "load_centroids_from_l5", None)
    if not callable(load_centroids):
        status["centroid_source"] = "deferred"
        return
    try:
        status["centroids_loaded"] = bool(load_centroids(rows))
        status["centroid_source"] = "l5" if status["centroids_loaded"] else "missing"
    except Exception as exc:
        active_log.warning("L5 centroid startup restore failed for %s: %s", domain, exc)
        status["centroid_source"] = "error"


def _restore_conservation(
    domain: str,
    learning_store: Any,
    status: dict[str, Any],
    active_log: logging.Logger,
) -> None:
    get_conservation_state = getattr(learning_store, "get_conservation_state", None)
    if not callable(get_conservation_state):
        status["conservation_source"] = "missing"
        return
    try:
        state = get_conservation_state(domain)
    except Exception as exc:
        active_log.warning("L5 conservation startup read failed for %s: %s", domain, exc)
        status["conservation_source"] = "error"
        return
    if state is None:
        status["conservation_source"] = "missing"
        return
    status["conservation_state"] = dict(state)
    status["conservation_source"] = "l5"


__all__ = ["restore_l5_runtime_state"]
