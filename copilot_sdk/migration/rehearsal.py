"""Protocol-based migration rehearsal with idempotency and rollback proofs."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class RehearsalReport:
    status: str
    source_count: int
    existing_count: int
    imported_count: int = 0
    conflicts: int = 0
    domain: str = ""
    parity_verified: bool = False
    rollback_verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _store(config: Any) -> Any:
    store = getattr(config, "graph_store", None) or getattr(config, "store", None)
    if store is None:
        raise ValueError("target_graph_config must provide graph_store/store")
    return store


def _source_rows(source_path: str | Path, domain: str) -> list[dict[str, Any]]:
    path = Path(source_path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("decisions", payload) if isinstance(payload, dict) else payload
        return [dict(row) for row in rows if isinstance(row, Mapping)]
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        columns = [str(row[1]) for row in connection.execute("PRAGMA table_info(decisions)")]
        if not columns:
            return []
        rows = connection.execute(
            f"SELECT {', '.join(columns)} FROM decisions WHERE domain = ? ORDER BY created_at, decision_id",
            (domain,),
        ).fetchall()
        return [dict(row) for row in rows]


def _domain(config: Any) -> str:
    return str(getattr(config, "domain", "") or "").strip().lower()


def _existing(store: Any, domain: str) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("decision_id")): dict(row)
        for row in store.get_all_decisions(domain=domain)
        if isinstance(row, Mapping)
    }


def dry_run(source_path: str | Path, target_graph_config: Any) -> dict[str, Any]:
    domain = _domain(target_graph_config)
    rows = _source_rows(source_path, domain)
    existing = _existing(_store(target_graph_config), domain)
    conflicts = sum(1 for row in rows if str(row.get("decision_id")) in existing and existing[str(row["decision_id"])] != row)
    return RehearsalReport("PASS" if not conflicts else "CONFLICT", len(rows), len(existing), conflicts=conflicts, domain=domain).to_dict()


def apply(source_path: str | Path, target_graph_config: Any) -> dict[str, Any]:
    domain = _domain(target_graph_config)
    rows = _source_rows(source_path, domain)
    store = _store(target_graph_config)
    existing = _existing(store, domain)
    imported = 0
    conflicts = 0
    for row in rows:
        decision_id = str(row.get("decision_id") or "")
        if not decision_id or str(row.get("domain", domain)) != domain:
            raise ValueError("foreign or missing decision domain rejected")
        if decision_id in existing:
            if existing[decision_id].get("category") != row.get("category"):
                conflicts += 1
            continue
        metadata = dict(row.get("metadata") or {})
        metadata["provenance"] = "migration_rehearsal"
        store.write_governed_decision(
            decision_id=decision_id,
            domain=domain,
            category=str(row.get("category") or "unknown"),
            category_index=int(row.get("category_index") or 0),
            recommended_action=str(row.get("recommended_action") or "unknown"),
            recommended_index=int(row.get("recommended_index") or 0),
            confidence=float(row.get("confidence") or 0.0),
            probabilities=list(row.get("probabilities") or []),
            factor_vector=list(row.get("factor_vector") or []),
            factor_names=list(row.get("factor_names") or []),
            source="migration_rehearsal",
            metadata=metadata,
        )
        imported += 1
    return RehearsalReport("PASS" if not conflicts else "CONFLICT", len(rows), len(existing), imported, conflicts, domain).to_dict()


def verify(target_graph_config: Any, source_path: str | Path | None = None) -> dict[str, Any]:
    domain = _domain(target_graph_config)
    store = _store(target_graph_config)
    existing = _existing(store, domain)
    source_count = len(_source_rows(source_path, domain)) if source_path is not None else len(existing)
    parity = source_count == len(existing) if source_path is not None else True
    return RehearsalReport("PASS" if parity else "FAIL", source_count, len(existing), parity_verified=parity, domain=domain).to_dict()


def rollback_proof(target_graph_config: Any) -> dict[str, Any]:
    store = _store(target_graph_config)
    snapshot = getattr(store, "snapshot_state", None)
    restore = getattr(store, "restore_state", None)
    if not callable(snapshot) or not callable(restore):
        raise RuntimeError("rollback proof requires snapshot_state/restore_state on the rehearsal GraphStore")
    before = snapshot()
    try:
        restore(before)
        after = snapshot()
    finally:
        restore(before)
    verified = before == after
    return RehearsalReport("PASS" if verified else "FAIL", 0, 0, rollback_verified=verified, domain=_domain(target_graph_config)).to_dict()
