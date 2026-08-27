"""DataOps-local governance adapters for shared evidence services."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from copilot_sdk.evidence import ClaimRecord, EvidenceGate, EvidenceTier
from copilot_sdk.outcome import OutcomeLedger, OutcomeProcessor, VerifiedOutcome
from copilot_sdk.promotion import DataOpsPromotionPolicy, PromotionEngine, PromotionStage, PromotionStore
from copilot_sdk.twin import FrozenTwin


class DataOpsGovernance:
    """Own DataOps policy state while delegating scoring mechanisms to the SDK."""

    def __init__(self, db_path: str | Path, graph_store: Any, scorer: Any, conservation: Any) -> None:
        self.graph_store = graph_store
        self.scorer = scorer
        self.conservation = conservation
        self.evidence = EvidenceGate()
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("""CREATE TABLE IF NOT EXISTS dataops_holdout (
            decision_id TEXT PRIMARY KEY, source_id TEXT NOT NULL,
            decision_class TEXT NOT NULL, factor_vector TEXT,
            score_payload TEXT, evidence_tier TEXT NOT NULL,
            verdict TEXT, verified_at REAL, outcome_receipt_id TEXT)""")
        self._db.commit()
        try:
            self._db.execute("ALTER TABLE dataops_holdout ADD COLUMN outcome_receipt_id TEXT")
            self._db.commit()
        except sqlite3.OperationalError:
            pass
        self._outcomes = OutcomeLedger(":memory:" if str(db_path) == ":memory:" else str(Path(db_path).with_name("dataops_outcomes.sqlite3")))
        self.outcome_processor = OutcomeProcessor(self._outcomes)
        promotion_db = str(Path(db_path).with_name("dataops_promotion.sqlite3"))
        self.promotions = PromotionEngine(policy=DataOpsPromotionPolicy(), store=PromotionStore(promotion_db), conservation_provider=conservation)
        self.frozen_twin = FrozenTwin()
        self.claim_ids = ("DATAOPS-TRUST", "DATAOPS-ACCURACY", "DATAOPS-IKS")
        self._register_default_claims()

    def _register_default_claims(self) -> None:
        for claim_id, description in {"DATAOPS-TRUST": "DataOps source trust score", "DATAOPS-ACCURACY": "DataOps decision accuracy", "DATAOPS-IKS": "DataOps improvement knowledge score"}.items():
            self.evidence.register(ClaimRecord(claim_id=claim_id, description=description, tier=EvidenceTier.T_S, evidence_basis="DataOps fixture or modelled estimate; no verified outcome yet", copilot="dataops"))

    def claim_status(self, context: str = "demo") -> list[dict[str, Any]]:
        return [asdict(self.evidence.check(claim_id, context)) for claim_id in self.claim_ids]

    def _rows(self, source_id: str | None = None) -> list[sqlite3.Row]:
        query = "SELECT * FROM dataops_holdout"
        args: tuple[Any, ...] = ()
        if source_id:
            query += " WHERE source_id = ?"
            args = (source_id,)
        query += " ORDER BY COALESCE(verified_at, 0) DESC, decision_id DESC"
        return list(self._db.execute(query, args).fetchall())

    def register_holdout(self, decision_id: str, source_id: str, decision_class: str, factor_vector: list[float] | None = None, score_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            self._db.execute("""INSERT INTO dataops_holdout
                (decision_id, source_id, decision_class, factor_vector, score_payload, evidence_tier)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_id) DO UPDATE SET source_id=excluded.source_id,
                decision_class=excluded.decision_class, factor_vector=excluded.factor_vector,
                score_payload=excluded.score_payload""", (decision_id, source_id, decision_class, json.dumps(factor_vector), json.dumps(score_payload or {}), EvidenceTier.T_S.value))
            self._db.commit()
            return self.holdout_status(source_id=source_id)[0]

    def holdout_status(self, source_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            return [self._row_payload(row) for row in self._rows(source_id)]

    def verify_holdout(self, decision_id: str, verdict: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            row = self._db.execute("SELECT * FROM dataops_holdout WHERE decision_id = ?", (decision_id,)).fetchone()
            if row is None:
                raise KeyError(decision_id)
            verified_at = time.time()
            receipt_id: str | None = None
            factor_vector = json.loads(row["factor_vector"] or "null")
            score_payload = json.loads(row["score_payload"] or "{}")
            predicted_action = score_payload.get("action") or score_payload.get("recommended_action")
            if isinstance(factor_vector, list) and predicted_action:
                outcome = VerifiedOutcome.create(copilot="dataops", decision_id=decision_id, category=str(row["decision_class"]), factor_vector=factor_vector, predicted_action=str(predicted_action), human_disposition="override" if verdict.get("override_action") else "confirm", override_action=verdict.get("override_action"), override_reason=verdict.get("override_reason"), correct=bool(verdict.get("correct", False)), measured_impact=verdict.get("financial_impact"), evidence_provenance="dataops.30_day_holdout.expert_verification")
                result = self.outcome_processor.process(outcome)
                receipt_id = result.receipt_id
            self._db.execute("UPDATE dataops_holdout SET evidence_tier = ?, verdict = ?, verified_at = ?, outcome_receipt_id = ? WHERE decision_id = ?", (EvidenceTier.T_O.value, json.dumps(verdict), verified_at, receipt_id, decision_id))
            self._db.commit()
            self.evidence.register(ClaimRecord(claim_id=f"DATAOPS-CLASS-{row['decision_class']}", description=f"Verified DataOps decisions in class {row['decision_class']}", tier=EvidenceTier.T_O, evidence_basis="expert-verified holdout outcome", copilot="dataops"))
            return self._row_payload(self._db.execute("SELECT * FROM dataops_holdout WHERE decision_id = ?", (decision_id,)).fetchone())

    def abstention(self, source_id: str, evidence_floor: int = 10) -> dict[str, Any]:
        verified = sum(1 for row in self._rows(source_id) if row["evidence_tier"] == EvidenceTier.T_O.value)
        should_abstain = verified < evidence_floor
        return {"source_id": source_id, "should_abstain": should_abstain, "reason": "insufficient_verified_evidence" if should_abstain else "evidence_floor_met", "evidence_floor": evidence_floor, "current_evidence": verified, "evidence_tier": EvidenceTier.T_O.value if verified else EvidenceTier.T_S.value, "evidence_label": "measured" if verified else "synthetic / modelled — not measured"}

    def provenance(self, decision_id: str) -> dict[str, Any]:
        decision = self.graph_store.get_decision(decision_id, domain="dataops")
        if decision is None:
            raise KeyError(decision_id)
        raw = dict(decision)
        fixture = str(raw.get("provenance", "")).lower() == "sample"
        verified = raw.get("is_correct") is not None or raw.get("status") in {"confirmed", "overridden"}
        tier = EvidenceTier.T_O.value if verified else (EvidenceTier.T_S.value if fixture else EvidenceTier.T_A.value)
        vector = raw.get("factor_vector") or raw.get("factors") or []
        impact = raw.get("financial_impact", raw.get("impact"))
        return {"decision_id": decision_id, "complete": impact is not None and verified, "steps": [{"type": "factor_vector", "value": vector, "evidence_tier": tier}, {"type": "score", "value": {"confidence": raw.get("confidence"), "action": raw.get("recommended_action")}, "evidence_tier": tier}, {"type": "decision", "value": raw.get("recommended_action"), "evidence_tier": tier}, {"type": "outcome", "value": raw.get("is_correct"), "evidence_tier": EvidenceTier.T_O.value if verified else EvidenceTier.T_S.value}, {"type": "financial_impact", "value": impact, "available": impact is not None, "evidence_tier": tier}], "evidence_tier": tier, "evidence_label": "measured" if tier == EvidenceTier.T_O.value else "modelled / computed — not measured"}

    def promotion_status(self, decision_class: str) -> dict[str, Any]:
        record = self.promotions.store.load_by_class("dataops", decision_class)
        if record is None:
            record = self.promotions.create("dataops", decision_class)
        return cast(dict[str, Any], record.to_dict())

    def advance_promotion(self, record_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
        record = self.promotions.store.load(record_id)
        if record is None:
            raise KeyError(record_id)
        if record.current_stage in {PromotionStage.SHADOWING, PromotionStage.PROMOTED} and evidence.get("evidence_tier") != EvidenceTier.T_O.value:
            return {"advanced": False, "new_stage": record.current_stage.value, "reason": "evidence_below_T_O"}
        return asdict(self.promotions.advance(record_id, evidence))

    def freeze_twin(self) -> dict[str, Any]:
        state = self.conservation.get_state()
        trajectory = self.scorer.trajectory()
        iks = float(trajectory.get("iks", trajectory.get("current_iks", 0.0))) if isinstance(trajectory, dict) else 0.0
        snapshot = self.frozen_twin.freeze(self.scorer._scorer(), state, iks, "dataops")
        return cast(dict[str, Any], json.loads(snapshot.to_json()))

    @staticmethod
    def _row_payload(row: sqlite3.Row) -> dict[str, Any]:
        return {"decision_id": row["decision_id"], "source_id": row["source_id"], "decision_class": row["decision_class"], "factor_vector": json.loads(row["factor_vector"] or "null"), "score_payload": json.loads(row["score_payload"] or "{}"), "evidence_tier": row["evidence_tier"], "verdict": json.loads(row["verdict"] or "null"), "verified_at": row["verified_at"], "outcome_receipt_id": row["outcome_receipt_id"]}
