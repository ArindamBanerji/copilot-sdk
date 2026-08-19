"""Measured 90-day shadow-pilot transfer service.

The service records paired live/frozen outcomes and computes site evidence from
those observations.  It deliberately does not mutate the Frozen Twin,
promotion engine, outcome processor, or evidence-gate implementation.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any, cast

from .models import _json_safe


@dataclass(frozen=True)
class PilotSession:
    session_id: str
    copilot: str
    started_at: str
    duration_days: int
    ends_at: str
    frozen_baseline_ref: str
    status: str = "active"

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "copilot": self.copilot,
            "started_at": self.started_at,
            "duration_days": self.duration_days,
            "ends_at": self.ends_at,
            "frozen_baseline_ref": self.frozen_baseline_ref,
            "status": self.status,
        }


class MeasuredTransferStore:
    """Thread-safe SQLite persistence for pilot sessions and paired outcomes."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = RLock()
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pilot_sessions (
                session_id TEXT PRIMARY KEY,
                copilot TEXT NOT NULL,
                started_at TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                ends_at TEXT NOT NULL,
                frozen_baseline_ref TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pilot_observations (
                session_id TEXT NOT NULL,
                decision_id TEXT NOT NULL,
                category TEXT NOT NULL,
                live_correct INTEGER NOT NULL,
                frozen_correct INTEGER NOT NULL,
                value REAL NOT NULL,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY (session_id, decision_id),
                FOREIGN KEY (session_id) REFERENCES pilot_sessions(session_id)
            )
            """
        )
        self._connection.commit()

    def save_session(self, session: PilotSession) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO pilot_sessions
                (session_id, copilot, started_at, duration_days, ends_at,
                 frozen_baseline_ref, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    session.copilot,
                    session.started_at,
                    session.duration_days,
                    session.ends_at,
                    session.frozen_baseline_ref,
                    session.status,
                ),
            )
            self._connection.commit()

    def get_session(self, session_id: str) -> PilotSession | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM pilot_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return _session_from_row(row) if row else None

    def latest_session(self, copilot: str) -> PilotSession | None:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT * FROM pilot_sessions
                WHERE copilot = ?
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (copilot,),
            ).fetchone()
        return _session_from_row(row) if row else None

    def active_sessions(self) -> list[PilotSession]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM pilot_sessions WHERE status = 'active' ORDER BY started_at DESC"
            ).fetchall()
        return [_session_from_row(row) for row in rows]

    def save_observation(self, observation: Mapping[str, Any]) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO pilot_observations
                (session_id, decision_id, category, live_correct,
                 frozen_correct, value, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(observation["session_id"]),
                    str(observation["decision_id"]),
                    str(observation["category"]),
                    int(bool(observation["live_correct"])),
                    int(bool(observation["frozen_correct"])),
                    float(observation["value"]),
                    str(observation["recorded_at"]),
                ),
            )
            self._connection.commit()

    def observations(self, session_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT session_id, decision_id, category, live_correct,
                       frozen_correct, value, recorded_at
                FROM pilot_observations
                WHERE session_id = ?
                ORDER BY recorded_at, decision_id
                """,
                (session_id,),
            ).fetchall()
        return [
            {
                "session_id": str(row[0]),
                "decision_id": str(row[1]),
                "category": str(row[2]),
                "live_correct": bool(row[3]),
                "frozen_correct": bool(row[4]),
                "value": float(row[5]),
                "recorded_at": str(row[6]),
            }
            for row in rows
        ]

    def close(self) -> None:
        with self._lock:
            self._connection.close()


@dataclass(frozen=True)
class ImprovementReport:
    """Measured live-vs-frozen improvement and authority evidence."""

    session_id: str
    copilot: str
    generated_at: str
    per_category: list[dict[str, Any]]
    overall: dict[str, Any]
    authority_recommendations: list[dict[str, Any]] = field(default_factory=list)
    evidence_upgrades: list[dict[str, Any]] = field(default_factory=list)
    report_hash: str = ""

    @classmethod
    def create(
        cls,
        session_id: str,
        copilot: str,
        per_category: list[dict[str, Any]],
        overall: dict[str, Any],
        authority_recommendations: list[dict[str, Any]],
        evidence_upgrades: list[dict[str, Any]],
    ) -> "ImprovementReport":
        stable = {
            "session_id": session_id,
            "copilot": copilot,
            "per_category": _json_safe(per_category),
            "overall": _json_safe(overall),
            "authority_recommendations": _json_safe(authority_recommendations),
            "evidence_upgrades": _json_safe(evidence_upgrades),
        }
        digest = hashlib.sha256(
            json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return cls(
            session_id=session_id,
            copilot=copilot,
            generated_at=datetime.now(timezone.utc).isoformat(),
            per_category=per_category,
            overall=overall,
            authority_recommendations=authority_recommendations,
            evidence_upgrades=evidence_upgrades,
            report_hash=digest,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "copilot": self.copilot,
            "generated_at": self.generated_at,
            "per_category": _json_safe(self.per_category),
            "overall": _json_safe(self.overall),
            "authority_recommendations": _json_safe(self.authority_recommendations),
            "evidence_upgrades": _json_safe(self.evidence_upgrades),
            "report_hash": self.report_hash,
            "evidence_tier": "T_O" if self.overall["total_decisions"] else "T_S",
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


class MeasuredTransfer:
    """Run a measured shadow pilot against an immutable day-0 baseline."""

    def __init__(
        self,
        twin: Any | None = None,
        *,
        evidence_gate: Any | None = None,
        promotion_engine: Any | None = None,
        store: MeasuredTransferStore | None = None,
        db_path: str = ":memory:",
        average_value: float = 0.0,
        authority_threshold: float = 0.0,
        minimum_decisions: int = 1,
        claim_ids: list[str] | None = None,
    ) -> None:
        self.twin = twin
        self.evidence_gate = evidence_gate
        self.promotion_engine = promotion_engine
        self.store = store or MeasuredTransferStore(db_path)
        self.average_value = float(average_value)
        self.authority_threshold = float(authority_threshold)
        self.minimum_decisions = max(int(minimum_decisions), 1)
        self.claim_ids = list(claim_ids or [])
        self._lock = RLock()

    def start_pilot(self, copilot: str, duration_days: int = 90) -> PilotSession:
        if duration_days <= 0:
            raise ValueError("duration_days must be positive")
        baseline_ref = self._frozen_baseline_ref()
        started = datetime.now(timezone.utc)
        session = PilotSession(
            session_id=f"pilot-{uuid.uuid4().hex}",
            copilot=copilot,
            started_at=started.isoformat(),
            duration_days=duration_days,
            ends_at=(started + timedelta(days=duration_days)).isoformat(),
            frozen_baseline_ref=baseline_ref,
        )
        with self._lock:
            self.store.save_session(session)
        return session

    def record_decision(
        self,
        session_id: str,
        decision_id: str,
        live_result: Any,
        frozen_result: Any,
        category: str | None = None,
        value: float | None = None,
    ) -> dict[str, Any]:
        session = self._require_session(session_id)
        live_correct = _correctness(live_result)
        frozen_correct = _correctness(frozen_result)
        selected_category = category or _field(live_result, ("category", "decision_class")) or _field(frozen_result, ("category", "decision_class")) or "uncategorized"
        selected_value = self.average_value if value is None else float(value)
        if value is None:
            raw_value = _field(live_result, ("value", "amount", "financial_value"))
            if raw_value is not None:
                selected_value = float(raw_value)
        observation = {
            "session_id": session.session_id,
            "decision_id": decision_id,
            "category": str(selected_category),
            "live_correct": live_correct,
            "frozen_correct": frozen_correct,
            "value": selected_value,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self.store.save_observation(observation)
        return cast(dict[str, Any], _json_safe(observation))

    def generate_report(self, session_id: str) -> ImprovementReport:
        session = self._require_session(session_id)
        observations = self.store.observations(session_id)
        grouped: dict[str, list[dict[str, Any]]] = {}
        for observation in observations:
            grouped.setdefault(str(observation["category"]), []).append(observation)
        per_category: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []
        for category in sorted(grouped):
            rows = grouped[category]
            decisions = len(rows)
            live_accuracy = sum(bool(row["live_correct"]) for row in rows) / decisions
            frozen_accuracy = sum(bool(row["frozen_correct"]) for row in rows) / decisions
            delta = live_accuracy - frozen_accuracy
            financial = decisions * delta * (sum(float(row["value"]) for row in rows) / decisions)
            sufficient = decisions >= self.minimum_decisions
            entry = {
                "category": category,
                "live_accuracy": live_accuracy,
                "frozen_accuracy": frozen_accuracy,
                "delta": delta,
                "decisions": decisions,
                "financial_impact": financial,
                "sufficient_data": sufficient,
                "evidence_tier": "T_O" if sufficient else "T_S",
            }
            per_category.append(entry)
            if sufficient and delta > self.authority_threshold:
                current = self._current_stage(session.copilot, category)
                recommendations.append(
                    {
                        "category": category,
                        "current_stage": current,
                        "recommended_stage": "promoted",
                        "evidence": {
                            "evidence_tier": "T_O",
                            "decisions": decisions,
                            "delta": delta,
                            "threshold": self.authority_threshold,
                        },
                    }
                )
        total = len(observations)
        live_correct_total = sum(bool(row["live_correct"]) for row in observations)
        frozen_correct_total = sum(bool(row["frozen_correct"]) for row in observations)
        overall_delta = (live_correct_total - frozen_correct_total) / total if total else 0.0
        overall = {
            "total_decisions": total,
            "live_accuracy": live_correct_total / total if total else 0.0,
            "frozen_accuracy": frozen_correct_total / total if total else 0.0,
            "overall_delta": overall_delta,
            "total_financial_impact": sum(float(item["financial_impact"]) for item in per_category),
            "evidence_tier": "T_O" if total else "T_S",
        }
        upgrades = [
            {"claim_id": claim_id, "old_tier": "T_S", "new_tier": "T_O", "evidence_ref": session.session_id}
            for claim_id in self.claim_ids
        ] if total else []
        return ImprovementReport.create(session.session_id, session.copilot, per_category, overall, recommendations, upgrades)

    def latest_report(self, copilot: str) -> ImprovementReport:
        session = self.store.latest_session(copilot)
        if session is None:
            raise ValueError(f"No pilot session exists for copilot {copilot!r}")
        return self.generate_report(session.session_id)

    def status(self) -> list[dict[str, Any]]:
        return [session.to_dict() for session in self.store.active_sessions()]

    def _require_session(self, session_id: str) -> PilotSession:
        session = self.store.get_session(session_id)
        if session is None:
            raise KeyError(f"Unknown pilot session: {session_id}")
        return session

    def _frozen_baseline_ref(self) -> str:
        if self.twin is None:
            raise RuntimeError("Measured transfer requires a Frozen Twin")
        if not bool(self.twin.is_frozen()):
            raise RuntimeError("Measured transfer requires a frozen day-0 baseline")
        snapshot_getter = getattr(self.twin, "get_snapshot", None)
        if callable(snapshot_getter):
            snapshot = snapshot_getter()
            checksum = getattr(snapshot, "checksum", None)
            if checksum:
                return str(checksum)
        return "frozen-twin"

    def _current_stage(self, copilot: str, category: str) -> str:
        if self.promotion_engine is None:
            return "discovered"
        getter = getattr(self.promotion_engine, "get_authority", None)
        if not callable(getter):
            return "discovered"
        stage = getter(copilot, category)
        return str(getattr(stage, "value", stage))


def _session_from_row(row: tuple[Any, ...]) -> PilotSession:
    return PilotSession(
        session_id=str(row[0]),
        copilot=str(row[1]),
        started_at=str(row[2]),
        duration_days=int(row[3]),
        ends_at=str(row[4]),
        frozen_baseline_ref=str(row[5]),
        status=str(row[6]),
    )


def _field(value: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(value, Mapping):
        for key in keys:
            if key in value:
                return value[key]
        return None
    for key in keys:
        candidate = getattr(value, key, None)
        if candidate is not None:
            return candidate
    return None


def _correctness(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    explicit = _field(value, ("correct", "is_correct"))
    if isinstance(explicit, bool):
        return explicit
    actual = _field(value, ("actual_action", "expected_action", "ground_truth"))
    predicted = _field(value, ("action", "predicted_action", "recommended_action"))
    if actual is not None and predicted is not None:
        return str(actual) == str(predicted)
    raise ValueError("result must provide correct or comparable action fields")
