"""DataOps-local governance adapters for shared evidence services."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict
from typing import Any, cast

from copilot_sdk.evidence import ClaimRecord, EvidenceGate, EvidenceTier
from copilot_sdk.outcome import OutcomeProcessor, VerifiedOutcome
from copilot_sdk.evolution import GraphOutcomeLedger, GraphPromotionStore
from copilot_sdk.promotion import DataOpsPromotionPolicy, PromotionEngine, PromotionStage
from copilot_sdk.twin import FrozenTwin
from copilot_sdk.twin.store import GraphFrozenTwinStore
from copilot_sdk.config.graph_config import resolve_profile
from copilot_sdk.graph.protocol import GraphStore, ScoringPersistenceStore
from copilot_sdk.graph.scoring_persistence import GraphScoringPersistence
from copilot_sdk.graph.production import age_client_for_store


class DataOpsGovernance:
    """Own DataOps policy state while delegating scoring mechanisms to the SDK."""

    def __init__(self, graph_store: GraphStore, scorer: Any, conservation: Any, *, profile: str | None = None) -> None:
        active_profile = resolve_profile(profile, domain="dataops")
        if active_profile == "production":
            age_client_for_store(graph_store, domain="dataops")
        self.persistence: ScoringPersistenceStore = GraphScoringPersistence(graph_store)
        self.graph_store = graph_store
        self.scorer = scorer
        self.conservation = conservation
        self.evidence = EvidenceGate()
        self._lock = threading.RLock()
        self._outcomes = GraphOutcomeLedger(graph_store, "dataops")
        self.outcome_processor = OutcomeProcessor(self._outcomes)
        promotion_store_type = GraphPromotionStore
        promotion_store = promotion_store_type(graph_store, "dataops")
        self.promotions = PromotionEngine(policy=DataOpsPromotionPolicy(), store=promotion_store, conservation_provider=conservation)
        self.frozen_twin = FrozenTwin(
            GraphFrozenTwinStore(graph_store, "dataops")
            if callable(getattr(graph_store, "save_promotion", None))
            else None
        )
        self.claim_ids = ("DATAOPS-TRUST", "DATAOPS-ACCURACY", "DATAOPS-IKS")
        self._register_default_claims()

    def _register_default_claims(self) -> None:
        for claim_id, description in {"DATAOPS-TRUST": "DataOps source trust score", "DATAOPS-ACCURACY": "DataOps decision accuracy", "DATAOPS-IKS": "DataOps improvement knowledge score"}.items():
            self.evidence.register(ClaimRecord(claim_id=claim_id, description=description, tier=EvidenceTier.T_S, evidence_basis="DataOps fixture or modelled estimate; no verified outcome yet", copilot="dataops"))

    def claim_status(self, context: str = "demo") -> list[dict[str, Any]]:
        return [self._claim_payload(claim_id, context) for claim_id in self.claim_ids]

    def evidence_gate_summary(self, context: str = "demo") -> dict[str, Any]:
        claims = self.claim_status(context)
        if not claims:
            state = "NONE"
        elif any(claim["evidence_state"] == "FAILED" for claim in claims):
            state = "FAILED"
        elif all(claim["evidence_state"] == "VALIDATED" for claim in claims):
            state = "VALIDATED"
        else:
            state = "PENDING"
        return {"state": state, "label": _evidence_state_label(state), "claims": claims}

    def _rows(self, source_id: str | None = None) -> list[dict[str, Any]]:
        rows = [dict(record["metadata"], decision_id=record["decision_id"])
                for record in self.persistence.get_holdout_decisions("dataops", source_id)]
        return sorted(rows, key=lambda row: (row.get("verified_at") or 0, row["decision_id"]), reverse=True)

    def _find(self, decision_id: str) -> dict[str, Any] | None:
        return next((row for row in self._rows() if row["decision_id"] == decision_id), None)

    def register_holdout(self, decision_id: str, source_id: str, decision_class: str, factor_vector: list[float] | None = None, score_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            row = self._find(decision_id) or {
                "evidence_tier": EvidenceTier.T_S.value, "verdict": None,
                "verified_at": None, "outcome_receipt_id": None,
            }
            row.update(decision_id=decision_id, source_id=source_id,
                       decision_class=decision_class, factor_vector=factor_vector,
                       score_payload=score_payload or {})
            self.persistence.save_holdout_decision("dataops", decision_id, source_id, row)
            return self._row_payload(row)

    def holdout_status(self, source_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            return [self._row_payload(row) for row in self._rows(source_id)]

    def verify_holdout(self, decision_id: str, verdict: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            row = self._find(decision_id)
            if row is None:
                raise KeyError(decision_id)
            verified_at = time.time()
            receipt_id: str | None = None
            factor_vector = row["factor_vector"]
            score_payload = row["score_payload"]
            predicted_action = score_payload.get("action") or score_payload.get("recommended_action")
            if isinstance(factor_vector, list) and predicted_action:
                outcome = VerifiedOutcome.create(copilot="dataops", decision_id=decision_id, category=str(row["decision_class"]), factor_vector=factor_vector, predicted_action=str(predicted_action), human_disposition="override" if verdict.get("override_action") else "confirm", override_action=verdict.get("override_action"), override_reason=verdict.get("override_reason"), correct=bool(verdict.get("correct", False)), measured_impact=verdict.get("financial_impact"), evidence_provenance="dataops.30_day_holdout.expert_verification")
                result = self.outcome_processor.process(outcome)
                receipt_id = result.receipt_id
            row.update(evidence_tier=EvidenceTier.T_O.value, verdict=verdict,
                       verified_at=verified_at, outcome_receipt_id=receipt_id)
            self.persistence.save_holdout_decision("dataops", decision_id, row["source_id"], row)
            self.evidence.register(ClaimRecord(claim_id=f"DATAOPS-CLASS-{row['decision_class']}", description=f"Verified DataOps decisions in class {row['decision_class']}", tier=EvidenceTier.T_O, evidence_basis="expert-verified holdout outcome", copilot="dataops"))
            return self._row_payload(row)

    def abstention(self, source_id: str, evidence_floor: int = 10) -> dict[str, Any]:
        verified = sum(1 for row in self._rows(source_id) if row["evidence_tier"] == EvidenceTier.T_O.value)
        should_abstain = verified < evidence_floor
        return {"source_id": source_id, "should_abstain": should_abstain, "reason": "insufficient_verified_evidence" if should_abstain else "evidence_floor_met", "evidence_floor": evidence_floor, "current_evidence": verified, "evidence_tier": EvidenceTier.T_O.value if verified else EvidenceTier.T_S.value, "evidence_label": "measured" if verified else "synthetic / modelled — not measured"}

    def provenance(self, decision_id: str) -> dict[str, Any]:
        decision = self.graph_store.get_decision(decision_id, domain="dataops")
        if decision is None:
            row = self._find(decision_id)
            if row is None:
                raise KeyError(decision_id)
            holdout = self._row_payload(row)
            verified = holdout["verified_at"] is not None
            tier = EvidenceTier.T_O.value if verified else EvidenceTier.T_S.value
            return {
                "decision_id": decision_id,
                "complete": verified,
                "steps": [
                    {"type": "holdout_registration", "value": holdout["source_id"], "evidence_tier": EvidenceTier.T_S.value},
                    {"type": "factor_vector", "value": holdout["factor_vector"], "evidence_tier": tier},
                    {"type": "score", "value": holdout["score_payload"], "evidence_tier": tier},
                    {"type": "outcome", "value": holdout["verdict"], "evidence_tier": tier},
                ],
                "evidence_tier": tier,
                "evidence_label": "measured" if verified else "synthetic / modelled — not measured",
            }
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
        scorer = self.scorer._scorer()
        snapshot_source = getattr(scorer, "_scorer", scorer)
        snapshot = self.frozen_twin.freeze(snapshot_source, state, iks, "dataops")
        return cast(dict[str, Any], json.loads(snapshot.to_json()))

    def frozen_twin_status(self) -> dict[str, Any]:
        snapshot = None
        try:
            loaded = self.frozen_twin.get_snapshot()
        except RuntimeError:
            try:
                loaded = self.frozen_twin.load("dataops")
            except (FileNotFoundError, RuntimeError, ValueError):
                loaded = None
        if loaded is not None:
            snapshot = json.loads(loaded.to_json())
        return {
            "frozen": snapshot is not None,
            "copilot": "dataops",
            "baseline_captured": snapshot is not None,
            "frozen_snapshot": snapshot,
        }

    def _claim_payload(self, claim_id: str, context: str) -> dict[str, Any]:
        result = self.evidence.check(claim_id, context)
        payload = asdict(result)
        state = _claim_state(payload)
        payload["evidence_state"] = state
        payload["evidence_gate_label"] = _evidence_state_label(state)
        return payload

    @staticmethod
    def _row_payload(row: dict[str, Any]) -> dict[str, Any]:
        return {key: row.get(key) for key in (
            "decision_id", "source_id", "decision_class", "factor_vector", "score_payload",
            "evidence_tier", "verdict", "verified_at", "outcome_receipt_id",
        )}



def _claim_state(payload: dict[str, Any]) -> str:
    if payload.get("error"):
        return "FAILED"
    if payload.get("tier") in {EvidenceTier.T_O.value, EvidenceTier.T_R.value} and payload.get("passed") is True:
        return "VALIDATED"
    if payload.get("passed") is False:
        return "FAILED"
    return "PENDING"


def _evidence_state_label(state: str) -> str:
    return {
        "VALIDATED": "Evidence gate: passed",
        "PENDING": "Evidence gate: pending review",
        "FAILED": "Evidence gate: failed",
        "NONE": "Evidence gate: not evaluated",
    }.get(state, "Evidence gate: not evaluated")
