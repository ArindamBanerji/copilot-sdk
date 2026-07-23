"""Resumable baseline reconciliation for SQLite and AGE archive state."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ci_platform.graph.age_client import AGEClient
from copilot_sdk.graph.read_diff_runner import ReadDiffRunner


class ArchiveReconciler:
    """Mark AGE Decisions archived when SQLite has archived the same IDs."""

    def __init__(
        self,
        sqlite_store: Any,
        age_store: Any,
        domain: str,
        checkpoint_file: str | Path | None = None,
    ) -> None:
        self.sqlite_store = sqlite_store
        self.age_store = age_store
        self.domain = str(domain)
        data_dir = Path(getattr(sqlite_store, "db_path", ".")).parent
        self.checkpoint_file = (
            Path(checkpoint_file)
            if checkpoint_file is not None
            else data_dir / f"{self.domain}_reconciliation_checkpoint.json"
        )

    @property
    def _age(self) -> Any:
        """Unwrap the SDK adapter while retaining the AGE query boundary."""
        store = getattr(self.age_store, "_store", self.age_store)
        if not all(hasattr(store, attribute) for attribute in ("_run_query", "_domain_clause")):
            raise TypeError("Archive reconciliation requires an AGEGraphStore or AGEGraphStoreAdapter")
        return store

    def reconcile(self, batch_size: int = 100, dry_run: bool = False) -> dict[str, Any]:
        """Reconcile one domain, checkpointing only after each completed batch."""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        source_ids = sorted(
            {
                str(record["decision_id"])
                for record in self.sqlite_store.get_archived_decisions(self.domain)
                if record.get("decision_id") is not None
            }
        )
        checkpoint = self._read_checkpoint()
        if checkpoint is not None:
            if checkpoint.get("domain") != self.domain:
                raise ValueError("reconciliation checkpoint domain does not match current domain")
            if checkpoint.get("source_ids") != source_ids:
                raise ValueError("reconciliation checkpoint source IDs do not match SQLite archive")

        processed_ids = set(checkpoint.get("processed_ids", [])) if checkpoint else set()
        report: dict[str, Any] = {
            "status": "PASS",
            "reconciled": int(checkpoint.get("reconciled", 0)) if checkpoint else 0,
            "already_archived": int(checkpoint.get("already_archived", 0)) if checkpoint else 0,
            "not_found_in_age": int(checkpoint.get("not_found_in_age", 0)) if checkpoint else 0,
            "total_sqlite_archived": len(source_ids),
            "checkpoint_file": str(self.checkpoint_file),
            "dry_run": bool(dry_run),
        }
        started_at = checkpoint.get("started_at") if checkpoint else self._timestamp()

        for start in range(0, len(source_ids), batch_size):
            batch = [decision_id for decision_id in source_ids[start : start + batch_size] if decision_id not in processed_ids]
            if not batch:
                continue
            found = self._age_rows(batch)
            found_ids = set(found)
            active_ids = [
                decision_id
                for decision_id in batch
                if decision_id in found and not self._is_archived(found[decision_id])
            ]
            report["already_archived"] += sum(
                1 for decision_id in batch if decision_id in found and self._is_archived(found[decision_id])
            )
            report["not_found_in_age"] += len(set(batch) - found_ids)

            if not dry_run and active_ids:
                marked = self._mark_archived(active_ids)
                if marked != len(active_ids):
                    raise RuntimeError(
                        f"AGE reconciliation marked {marked} decisions but expected {len(active_ids)}"
                    )
            report["reconciled"] += len(active_ids)
            processed_ids.update(batch)
            if not dry_run:
                self._write_checkpoint(
                    source_ids=source_ids,
                    processed_ids=processed_ids,
                    report=report,
                    started_at=started_at,
                    status="in_progress",
                )

        if report["not_found_in_age"]:
            report["status"] = "FAIL"
            report["fail_reason"] = (
                f"{report['not_found_in_age']} SQLite archived decision IDs were not found in AGE"
            )
        if not dry_run:
            self._write_checkpoint(
                source_ids=source_ids,
                processed_ids=processed_ids,
                report=report,
                started_at=started_at,
                status="complete" if report["status"] == "PASS" else "failed",
            )
        return report

    def verify(self) -> dict[str, Any]:
        """Return the independent active and history parity reports."""
        runner = ReadDiffRunner(self.sqlite_store, self.age_store, self.domain)
        return {"active": runner.compare_active(), "history": runner.compare_history()}

    def _age_rows(self, decision_ids: list[str]) -> dict[str, Any]:
        age = self._age
        literal_ids = "[" + ", ".join(self._string_literal(age, value) for value in decision_ids) + "]"
        rows = age._run_query(
            f"""
            MATCH (d:Decision)
            WHERE {age._domain_clause(self.domain)}
              AND d.decision_id IN {literal_ids}
            RETURN d.decision_id AS decision_id, d.archived AS archived
            """
        )
        return {
            str(row["decision_id"]): row.get("archived")
            for row in rows
            if row.get("decision_id") is not None
        }

    def _mark_archived(self, decision_ids: list[str]) -> int:
        age = self._age
        literal_ids = "[" + ", ".join(self._string_literal(age, value) for value in decision_ids) + "]"
        archived_at = datetime.now(timezone.utc)
        rows = age._run_query(
            f"""
            MATCH (d:Decision)
            WHERE {age._domain_clause(self.domain)}
              AND (d.archived IS NULL OR d.archived = false)
              AND d.decision_id IN {literal_ids}
            SET d.archived = true,
                d.archived_at = {archived_at.timestamp()},
                d.archive_reason = 'sqlite_baseline_reconciliation',
                d.archive_status = 'archived',
                d.archived_from_status = d.status
            RETURN count(d) AS cnt
            """
        )
        return sum(int(row.get("cnt", 0) or 0) for row in rows)

    @staticmethod
    def _is_archived(value: Any) -> bool:
        return value is True or str(value).lower() == "true"

    @staticmethod
    def _string_literal(age_store: Any, value: str) -> str:
        serializer = getattr(age_store, "_S", AGEClient.serialize_for_age)
        return str(serializer(value))

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _read_checkpoint(self) -> dict[str, Any] | None:
        if not self.checkpoint_file.exists():
            return None
        try:
            return json.loads(self.checkpoint_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Reconciliation checkpoint is corrupted: {self.checkpoint_file}") from exc

    def _write_checkpoint(
        self,
        *,
        source_ids: list[str],
        processed_ids: set[str],
        report: dict[str, Any],
        started_at: str,
        status: str,
    ) -> None:
        payload = {
            "domain": self.domain,
            "source_ids": source_ids,
            "processed_ids": sorted(processed_ids),
            "reconciled": report["reconciled"],
            "already_archived": report["already_archived"],
            "not_found_in_age": report["not_found_in_age"],
            "source_sqlite_archive_count": report["total_sqlite_archived"],
            "started_at": started_at,
            "finished_at": self._timestamp() if status != "in_progress" else None,
            "status": status,
        }
        temporary = self.checkpoint_file.with_suffix(self.checkpoint_file.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.checkpoint_file)
