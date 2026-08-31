"""Purchasing-owned adapters for evidence, proof, twin, promotion, and legal controls."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Mapping, cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from copilot_sdk.evidence import ClaimRecord, EvidenceGate, EvidenceTier
from copilot_sdk.outcome import OutcomeLedger, OutcomeProcessor, VerifiedOutcome
from copilot_sdk.promotion import PromotionEngine, PromotionStage, PromotionStore, PurchasingPromotionPolicy
from copilot_sdk.evolution import GraphOutcomeLedger, GraphProofLedger, GraphPromotionStore
from copilot_sdk.twin import FrozenTwin, FrozenTwinStore


class PurchasingGraphUnavailableError(RuntimeError):
    """Raised when purchasing evidence cannot be read from the graph."""


CLAIMS = {
    "proof": "CLAIM-PUR-PROOF",
    "handoff": "CLAIM-PUR-HANDOFF",
    "readiness": "CLAIM-PUR-READINESS",
    "discovery": "CLAIM-PUR-DISCOVERY",
    "frozen_twin": "CLAIM-PUR-FROZEN-TWIN",
    "belief": "CLAIM-PUR-BELIEF",
    "yield_audit": "CLAIM-PUR-YIELD-AUDIT",
    "general": "CLAIM-PUR-GENERAL",
}

_ROUTES = (
    ("/api/purchasing/proof-ledger", CLAIMS["proof"]),
    ("/api/purchasing/handoff-pack", CLAIMS["handoff"]),
    ("/api/purchasing/day-0-readiness", CLAIMS["readiness"]),
    ("/api/purchasing/discovery-gate", CLAIMS["discovery"]),
    ("/api/purchasing/frozen-twin", CLAIMS["frozen_twin"]),
    ("/api/purchasing/promotion", CLAIMS["readiness"]),
    ("/api/purchasing/legal-exposure", CLAIMS["belief"]),
    ("/api/purchasing/yield-quote-audit", CLAIMS["yield_audit"]),
)


class PurchasingClaimRegistry:
    def __init__(self) -> None:
        self.gate = EvidenceGate()
        for key, claim_id in CLAIMS.items():
            self.gate.register(
                ClaimRecord(
                    claim_id=claim_id,
                    description=f"Purchasing {key.replace('_', ' ')} claim",
                    tier=EvidenceTier.T_S,
                    evidence_basis="Purchasing graph and proof ledger; measured tier requires verified outcomes",
                    copilot="purchasing",
                )
            )

    def refresh(self, graph_store: Any) -> None:
        try:
            has_outcomes = bool(graph_store.get_verified_decisions("purchasing"))
        except Exception:
            has_outcomes = False
        if not has_outcomes:
            return
        for key in ("proof", "readiness", "discovery"):
            self.gate.register(
                ClaimRecord(
                    claim_id=CLAIMS[key],
                    description=f"Purchasing {key.replace('_', ' ')} claim",
                    tier=EvidenceTier.T_O,
                    evidence_basis="Verified Purchasing outcome ledger",
                    copilot="purchasing",
                )
            )

    def claim_for_path(self, path: str) -> str | None:
        for prefix, claim_id in _ROUTES:
            if path.startswith(prefix):
                return claim_id
        return None


class PurchasingEvidenceMiddleware(BaseHTTPMiddleware):
    """Every response receives evidence headers; new claim surfaces receive fields."""

    def __init__(self, app: Any, registry: PurchasingClaimRegistry, context: str = "demo") -> None:
        super().__init__(app)
        self.registry = registry
        self.context = context

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = cast(Response, await call_next(request))
        claim_id = self.registry.claim_for_path(request.url.path)
        effective = claim_id or CLAIMS["general"]
        result = self.registry.gate.check(effective, self.context)
        response.headers["X-Evidence-Tier"] = result.tier.name
        response.headers["X-Evidence-Label"] = result.label.replace("—", "-")
        response.headers["X-Evidence-Gate"] = "passed" if result.passed else "blocked"
        if claim_id is None or response.status_code >= 400 or "application/json" not in response.headers.get("content-type", ""):
            return response
        body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return Response(body, response.status_code, dict(response.headers), response.media_type)
        metadata = {"evidence_tier": result.tier.name, "evidence_label": result.label, "evidence_gate": "passed" if result.passed else "blocked", "claim_id": claim_id}
        if isinstance(payload, dict):
            payload = {**payload, **metadata}
        elif isinstance(payload, list):
            payload = [{**item, **metadata} if isinstance(item, dict) else item for item in payload]
        else:
            return Response(body, response.status_code, dict(response.headers), response.media_type)
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(json.dumps(payload, allow_nan=False), response.status_code, headers, "application/json")


class ProofLedger:
    """Persistent, thread-safe decision/outcome evidence ledger."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("CREATE TABLE IF NOT EXISTS proof_entries (entry_id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL, created_at REAL NOT NULL DEFAULT (unixepoch('now')))" )
        self._db.commit()

    def record(self, kind: str, payload: Mapping[str, Any]) -> None:
        entry_id = hashlib.sha256(json.dumps([kind, payload], sort_keys=True, default=str).encode()).hexdigest()
        with self._lock:
            self._db.execute("INSERT OR IGNORE INTO proof_entries(entry_id, kind, payload) VALUES (?, ?, ?)", (entry_id, kind, json.dumps(dict(payload), sort_keys=True, default=str)))
            self._db.commit()

    def list_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._db.execute("SELECT kind, payload, created_at FROM proof_entries ORDER BY created_at DESC LIMIT ?", (max(1, min(int(limit), 1000)),)).fetchall()
        return [{"kind": str(row["kind"]), "payload": json.loads(str(row["payload"])), "created_at": row["created_at"]} for row in rows]


class PurchasingControlService:
    def __init__(self, graph_store_factory: Any, scorer_provider: Any, data_dir: Path) -> None:
        self.graph_store_factory = graph_store_factory
        self.scorer_provider = scorer_provider
        graph_store = graph_store_factory()
        age_events = callable(getattr(graph_store, "write_evolution_event", None)) and callable(getattr(graph_store, "get_evolution_events", None))
        self.proof = GraphProofLedger(graph_store, "purchasing") if age_events else ProofLedger(data_dir / "purchasing_proof_ledger.sqlite3")
        self.outcomes = GraphOutcomeLedger(graph_store, "purchasing") if age_events else OutcomeLedger(data_dir / "purchasing_verified_outcomes.sqlite3")
        self.processor = OutcomeProcessor(self.outcomes)
        self.twin = FrozenTwin(FrozenTwinStore(data_dir / "frozen_twins"))
        try:
            self.twin.load("purchasing")
        except FileNotFoundError:
            pass
        promotion_store = GraphPromotionStore(graph_store, "purchasing") if age_events else PromotionStore(str(data_dir / "purchasing_promotion.sqlite3"))
        self.promotion = PromotionEngine(PurchasingPromotionPolicy(), promotion_store)

    def _store(self) -> Any:
        return self.graph_store_factory()

    def _decisions(self) -> list[dict[str, Any]]:
        try:
            return [row for row in self._store().get_all_decisions("purchasing") if isinstance(row, dict)]
        except Exception as exc:
            raise PurchasingGraphUnavailableError(
                "Purchasing graph read failed: get_all_decisions"
            ) from exc

    def _verified(self) -> list[dict[str, Any]]:
        try:
            return [row for row in self._store().get_verified_decisions("purchasing") if isinstance(row, dict)]
        except Exception as exc:
            raise PurchasingGraphUnavailableError(
                "Purchasing graph read failed: get_verified_decisions"
            ) from exc

    def proof_ledger(self) -> dict[str, Any]:
        decisions, verified = self._decisions(), self._verified()
        for row in decisions:
            self.proof.record("decision", {"decision_id": row.get("decision_id"), "category": row.get("category"), "evidence_provenance": "graphstore"})
        for row in verified:
            self.proof.record("outcome", {"decision_id": row.get("decision_id"), "correct": row.get("is_correct"), "evidence_provenance": "verified_outcome"})
        entries = self.list_entries()
        correct = sum(1 for row in verified if row.get("is_correct") is True)
        return {"proof_curve": {"decisions": len(decisions), "verified": len(verified), "correct": correct}, "competence_curve": {"accuracy": round(correct / len(verified), 4) if verified else 0.0}, "entries": entries, "attribution": "verified outcomes only; no synthetic uplift", "honest_dollars": 0.0, "source": "graphstore + proof ledger"}

    def list_entries(self) -> list[dict[str, Any]]:
        return self.proof.list_entries()

    def readiness(self) -> dict[str, Any]:
        ledger = self.proof_ledger()
        verified = int(ledger["proof_curve"]["verified"])
        conservation = "GREEN" if verified and ledger["competence_curve"]["accuracy"] >= 0.5 else ("BOOTSTRAP" if not verified else "AMBER")
        return {"ready": conservation == "GREEN", "day_zero": {"immutable": False, "frozen_twin_available": self.twin.is_frozen()}, "coverage": ledger["proof_curve"], "conservation_status": conservation, "evidence_floor": "T_O" if verified else "T_S", "not_yet": conservation != "GREEN"}

    def handoff(self) -> dict[str, Any]:
        ledger = self.proof_ledger()
        return {"schema_version": "purchasing-handoff-v1", "decision_change": "observed", "proof_ledger": ledger, "evidence_chain": [entry for entry in ledger["entries"][:20]], "transfer_boundary": "same legal entity only; no cross-customer supplier inference", "observation_only": True}

    def legal_exposure(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        order_path = Path(__file__).resolve().parents[2] / "data" / "purchasing_orders.json"
        try:
            payload = json.loads(order_path.read_text(encoding="utf-8"))
            rows = [row for row in payload if isinstance(row, dict) and (row.get("legal_flag") or row.get("compliance_flag") or row.get("legal_review"))]
        except (OSError, json.JSONDecodeError):
            rows = []
        return {"compliance_status": "REVIEW_REQUIRED" if rows else "NO_FLAGS_RECORDED", "flagged_orders": rows, "controls": ["de-identify supplier comparisons", "no auto-approval", "same legal entity transfer boundary", "revoke and audit overrides"], "separation_of_duties": True}

    def frozen_status(self) -> dict[str, Any]:
        if not self.twin.is_frozen():
            return {"available": False, "status": "NOT_INITIALIZED", "evidence_tier": "T_S"}
        snapshot = self.twin.get_snapshot()
        return {"available": True, "status": "FROZEN", "snapshot_time": snapshot.metadata.get("timestamp"), "checksum": snapshot.checksum, "evidence_tier": "T_O"}

    def frozen_comparison(self) -> dict[str, Any]:
        if not self.twin.is_frozen():
            return {"available": False, "status": "NOT_INITIALIZED", "evidence_tier": "T_S"}
        scorer = self.scorer_provider()
        raw = getattr(scorer, "_scorer", lambda: scorer)()
        report = self.twin.get_drift_report(raw)
        return {
            "available": True,
            "status": "MEASURED",
            "centroid_drift": report.centroid_drift,
            "weight_drift": report.weight_drift,
            "conservation_drift": report.conservation_drift,
            "iks_delta": report.iks_delta,
            "decisions_since_freeze": report.decision_count_since_freeze,
            "evidence_tier": "T_O",
            "evidence_label": "measured",
        }

    def freeze(self) -> dict[str, Any]:
        scorer = self.scorer_provider()
        raw = getattr(scorer, "_scorer", lambda: scorer)()
        if self.twin.is_frozen():
            return self.frozen_status()
        snapshot = self.twin.freeze(raw, {"status": self.readiness()["conservation_status"]}, 0.0, "purchasing")
        return {"available": True, "status": "FROZEN", "checksum": snapshot.checksum, "snapshot_time": snapshot.metadata.get("timestamp")}

    def record_outcome(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        outcome = VerifiedOutcome.from_dict(dict(payload))
        result = self.processor.process(outcome)
        self.proof.record("outcome", {"decision_id": outcome.decision_id, "receipt_id": result.receipt_id, "evidence_provenance": outcome.evidence_provenance, "processed": result.processed})
        return cast(dict[str, Any], result.to_dict())
