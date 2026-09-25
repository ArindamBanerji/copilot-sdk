"""Explicit historical-import timestamps without rewriting storage creation time."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

HISTORY_IMPORT_KEY = "demo:historical_checkpoint_imports"


def project_historical_checkpoints(checkpoints: list[dict[str, Any]], manifest: dict[str, Any] | None,
                                  *, include_superseded: bool = False) -> list[dict[str, Any]]:
    """Apply explicit synthetic revisions without deleting immutable audit records."""
    manifest = manifest or {}
    supersessions = manifest.get("supersessions", {})
    imported = manifest.get("checkpoints", [])
    rows = []
    for original in [*checkpoints, *imported]:
        row = dict(original)
        metadata = dict(row.get("metadata") or {})
        if metadata.get("historical_import"):
            marker = {**metadata, **supersessions.get(row.get("checkpoint_id"), {})}
            if marker.get("superseded") is True and marker.get("superseded_by"):
                metadata.update(superseded=True, superseded_by=marker["superseded_by"])
                row.update(superseded=True, superseded_by=marker["superseded_by"], metadata=metadata)
                if not include_superseded:
                    continue
        elif original in imported:
            raise ValueError("Historical import must have synthetic provenance")
        rows.append(normalize_historical_checkpoint(row))
    return rows


class HistoricalCheckpointImport(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    observed_at: float = Field(gt=0)
    planted: Literal[True]
    provenance: Literal["synthetic"]
    evidence_tier: Literal["T-sim"]
    description: str = Field(min_length=1)


def normalize_historical_checkpoint(checkpoint: dict[str, Any]) -> dict[str, Any]:
    """Expose imported event time, retaining ingestion time and provenance.

    This only changes the read-only timeline. Graph storage, latest-checkpoint
    selection, and scorer restoration continue to use their ingestion clocks.
    """
    metadata = checkpoint.get("metadata")
    imported = metadata.get("historical_import") if isinstance(metadata, dict) else None
    if imported is None:
        return checkpoint
    event = HistoricalCheckpointImport.model_validate(imported)
    return {**checkpoint, "ingested_at": checkpoint.get("created_at"),
            "created_at": event.observed_at, "timestamp_basis": "synthetic_observation",
            "planted": True, "provenance": "synthetic", "evidence_tier": "T-sim"}
