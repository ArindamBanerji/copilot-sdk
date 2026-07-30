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
    else:
        _restore_dk(domain, scorer, learning_store, status, active_log)
        if welford_tracker is not None and isinstance(status.get("welford_tracker"), DKWelfordTracker):
            _copy_welford_tracker_state(welford_tracker, status["welford_tracker"])
            status["welford_tracker"] = welford_tracker
        _restore_centroids(domain, scorer, learning_store, status, active_log)
        _restore_conservation(domain, learning_store, status, active_log)

    _capture_existing_state(scorer, status, active_log)
    return status


def _capture_existing_state(
    scorer: Any,
    status: dict[str, Any],
    active_log: logging.Logger,
) -> None:
    capture = getattr(scorer, "capture_existing_state", None)
    if not callable(capture):
        scorer_factory = getattr(scorer, "_scorer", None)
        if callable(scorer_factory):
            try:
                capture = getattr(scorer_factory(), "capture_existing_state", None)
            except Exception as exc:
                active_log.warning("J6 startup state capture setup failed: %s", exc)
                return
    if not callable(capture):
        active_log.debug("J6 startup state capture unavailable")
        return
    try:
        capture_result = capture(capture_reason="startup_restore")
        status["state_capture"] = capture_result
        active_log.info(
            "J6 startup state capture: conservation=%s fingerprint=%s checkpoint=%s",
            capture_result.get("conservation", 0),
            capture_result.get("fingerprint", 0),
            capture_result.get("checkpoint", 0),
        )
    except Exception as exc:
        active_log.warning("J6 startup state capture failed: %s", exc)


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
            status["dk_weights_loaded"] = bool(load_dk(_pad_legacy_s2p_dk(domain, scorer, row.get("weight_json"))))
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
        status["centroids_loaded"] = bool(load_centroids(_pad_legacy_s2p_centroids(domain, scorer, rows)))
        status["centroid_source"] = "l5" if status["centroids_loaded"] else "missing"
    except Exception as exc:
        active_log.warning("L5 centroid startup restore failed for %s: %s", domain, exc)
        status["centroid_source"] = "error"


def _expected_factor_count(scorer: Any) -> int | None:
    preset = getattr(scorer, "_preset", None)
    shape = getattr(preset, "shape", None)
    value = getattr(shape, "n_factors", None)
    return int(value) if value is not None else None


def _pad_legacy_s2p_vector(domain: str, scorer: Any, vector: Any) -> Any:
    expected = _expected_factor_count(scorer)
    if domain != "s2p" or expected != 8:
        return vector
    try:
        values = list(vector)
    except TypeError:
        return vector
    if len(values) == 7:
        return [*values, 0.5]
    return vector


def _pad_legacy_s2p_dk(domain: str, scorer: Any, weight_json: Any) -> Any:
    expected = _expected_factor_count(scorer)
    if domain != "s2p" or expected != 8:
        return weight_json
    try:
        rows = list(weight_json)
    except TypeError:
        return weight_json
    padded = []
    changed = False
    for row in rows:
        try:
            values = list(row)
        except TypeError:
            return weight_json
        if len(values) == 7:
            padded.append([*values, 1.0])
            changed = True
        else:
            padded.append(row)
    return padded if changed else weight_json


def _pad_legacy_s2p_centroids(domain: str, scorer: Any, rows: Any) -> Any:
    if domain != "s2p" or _expected_factor_count(scorer) != 8:
        return rows
    padded = []
    changed = False
    for row in rows:
        if not isinstance(row, dict):
            padded.append(row)
            continue
        vector = _pad_legacy_s2p_vector(domain, scorer, row.get("vector_json"))
        if vector is not row.get("vector_json"):
            updated = dict(row)
            updated["vector_json"] = vector
            padded.append(updated)
            changed = True
        else:
            padded.append(row)
    return padded if changed else rows


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
