"""Purchasing-owned adapters for evidence, proof, twin, promotion, and legal controls."""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Mapping, cast

from starlette.datastructures import MutableHeaders

from copilot_sdk.evidence import ClaimRecord, EvidenceGate, EvidenceTier
from copilot_sdk.outcome import OutcomeLedger, OutcomeProcessor, VerifiedOutcome
from copilot_sdk.promotion import PromotionEngine, PromotionStage, PurchasingPromotionPolicy
from copilot_sdk.evolution import GraphOutcomeLedger, GraphProofLedger, GraphPromotionStore
from copilot_sdk.twin import FrozenTwin, FrozenTwinStore
from copilot_sdk.twin.store import GraphFrozenTwinStore
from copilot_sdk.config.graph_config import resolve_profile
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


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
PURCHASING_EVOLUTION_EVENT_CAP = 10_000
logger = logging.getLogger(__name__)

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
        self.last_refresh_available = False
        self.stale = True

    def refresh(self, graph_store: Any) -> None:
        try:
            verified = graph_store.get_verified_decisions("purchasing")
        except (ConnectionError, TimeoutError, OSError, RuntimeError) as exc:
            logger.warning(
                "Purchasing claim refresh could not read verified outcomes; "
                "claim qualification remains unmeasured: %s",
                exc,
            )
            self.last_refresh_available = False
            self.stale = True
            return
        if not isinstance(verified, list):
            self.last_refresh_available = False
            self.stale = True
            return
        has_outcomes = bool(verified)
        self.last_refresh_available = True
        self.stale = False
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


class PurchasingEvidenceMiddleware:
    """Every response receives evidence headers; new claim surfaces receive fields."""

    def __init__(self, app: Any, registry: PurchasingClaimRegistry, context: str = "demo") -> None:
        self.app = app
        self.registry = registry
        self.context = context

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = str(scope.get("path", ""))
        method = str(scope.get("method", ""))
        claim_id = self.registry.claim_for_path(path)
        effective = claim_id or CLAIMS["general"]
        result = self.registry.gate.check(effective, self.context)
        messages: list[dict[str, Any]] = []

        async def capture(message: dict[str, Any]) -> None:
            messages.append(message)

        await self.app(scope, receive, capture)
        if not messages:
            return
        start = messages[0]
        headers = MutableHeaders(scope=start)
        headers["X-Evidence-Tier"] = result.tier.name
        headers["X-Evidence-Label"] = result.label.replace("—", "-")
        headers["X-Evidence-Gate"] = "passed" if result.passed else "blocked"
        should_annotate = (
            method != "GET"
            and claim_id is not None
            and int(start.get("status", 500)) < 400
            and "application/json" in headers.get("content-type", "")
        )
        if not should_annotate:
            for message in messages:
                await send(message)
            return
        body = b"".join(bytes(message.get("body", b"")) for message in messages[1:] if message["type"] == "http.response.body")
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            for message in messages:
                await send(message)
            return
        metadata = {"evidence_tier": result.tier.name, "evidence_label": result.label, "evidence_gate": "passed" if result.passed else "blocked", "claim_id": claim_id}
        if isinstance(payload, dict):
            payload = {**payload, **metadata}
        elif isinstance(payload, list):
            payload = [{**item, **metadata} if isinstance(item, dict) else item for item in payload]
        else:
            for message in messages:
                await send(message)
            return
        encoded = json.dumps(payload, allow_nan=False).encode("utf-8")
        headers["content-length"] = str(len(encoded))
        await send(start)
        await send({"type": "http.response.body", "body": encoded})


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
    def __init__(self, graph_store_factory: Any, scorer_provider: Any, data_dir: Path, *, profile: str | None = None) -> None:
        self.graph_store_factory = graph_store_factory
        self.scorer_provider = scorer_provider
        graph_store = graph_store_factory()
        age_events = callable(getattr(graph_store, "write_evolution_event", None)) and callable(getattr(graph_store, "get_evolution_events", None))
        if resolve_profile(profile, domain="purchasing") == "production" and not age_events:
            raise RuntimeError("production Purchasing control requires graph-backed proof and outcome ledgers")
        self.proof = GraphProofLedger(graph_store, "purchasing") if age_events else ProofLedger(data_dir / "purchasing_proof_ledger.sqlite3")
        self.outcomes = GraphOutcomeLedger(graph_store, "purchasing") if age_events else OutcomeLedger(data_dir / "purchasing_verified_outcomes.sqlite3")
        self.processor = OutcomeProcessor(self.outcomes)
        self.twin = FrozenTwin(
            GraphFrozenTwinStore(graph_store, "purchasing")
            if callable(getattr(graph_store, "save_promotion", None))
            else FrozenTwinStore(data_dir / "frozen_twins")
        )
        try:
            self.twin.load("purchasing")
        except FileNotFoundError:
            pass
        promotion_store_type = GraphPromotionStore
        promotion_store = promotion_store_type(graph_store, "purchasing")
        self.promotion = PromotionEngine(PurchasingPromotionPolicy(), promotion_store)
        self.retention_pruned = self._prune_evolution_events(graph_store)

    def _store(self) -> Any:
        return self.graph_store_factory()

    def _prune_evolution_events(self, graph_store: Any | None = None) -> int:
        store = graph_store if graph_store is not None else self._store()
        pruner = getattr(store, "prune_evolution_events", None)
        if not callable(pruner):
            return 0
        return int(pruner("purchasing", keep_recent=PURCHASING_EVOLUTION_EVENT_CAP))

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
        # Decisions/outcomes already persist in GraphStore. Project them for
        # display; reading a page must not append duplicate proof events.
        entries = self.list_entries()
        represented = {(entry.get("kind"), entry.get("payload", {}).get("decision_id"))
                       for entry in entries}
        for kind, rows in (("outcome", verified), ("decision", decisions)):
            for row in reversed(rows):
                if len(entries) >= 100:
                    break
                identity = (kind, row.get("decision_id"))
                if identity in represented:
                    continue
                payload = {"decision_id": row.get("decision_id"),
                           "evidence_provenance": "verified_outcome" if kind == "outcome" else "graphstore"}
                payload["correct" if kind == "outcome" else "category"] = row.get("is_correct" if kind == "outcome" else "category")
                entries.append({"kind": kind, "payload": payload, "created_at": row.get("created_at")})
                represented.add(identity)
        correct = sum(1 for row in verified if row.get("is_correct") is True)
        return {"proof_curve": {"decisions": len(decisions), "verified": len(verified), "correct": correct}, "competence_curve": {"accuracy": round(correct / len(verified), 4) if verified else 0.0}, "entries": entries, "attribution": "verified outcomes only; no synthetic uplift", "honest_dollars": 0.0, "source": "graphstore + proof ledger"}

    def list_entries(self) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], self.proof.list_entries())

    def readiness(self) -> dict[str, Any]:
        decisions, outcomes = self._decisions(), self._verified()
        verified = len(outcomes)
        correct = sum(row.get("is_correct") is True for row in outcomes)
        accuracy = round(correct / verified, 4) if verified else 0.0
        conservation = "GREEN" if verified and accuracy >= 0.5 else ("BOOTSTRAP" if not verified else "AMBER")
        coverage = {"decisions": len(decisions), "verified": verified, "correct": correct}
        return {"ready": conservation == "GREEN", "day_zero": {"immutable": False, "frozen_twin_available": self.twin.is_frozen()}, "coverage": coverage, "conservation_status": conservation, "evidence_floor": "T_O" if verified else "T_S", "not_yet": conservation != "GREEN"}

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
            return {"available": False, "status": "NOT_INITIALIZED", "evidence_tier": "T_S",
                    "learning_curve": [], "frozen_curve": []}
        snapshot = self.twin.get_snapshot()
        return {"available": True, "status": "FROZEN", "snapshot_time": snapshot.metadata.get("timestamp"),
                "checksum": snapshot.checksum, "evidence_tier": "T_O", **self._twin_curves()}

    def _twin_curves(self) -> dict[str, Any]:
        """Paired read-only replay; not fabricated historical accuracy or waste."""
        scorer = self.scorer_provider()
        unwrap = getattr(scorer, "_scorer", None)
        if callable(unwrap):
            scorer = unwrap()
        shape = PurchasingPreset().shape
        learning: list[dict[str, Any]] = []
        frozen: list[dict[str, Any]] = []
        live_correct = frozen_correct = excluded = 0
        rows = sorted(self._verified(), key=lambda row: str(row.get("created_at", "")))[-200:]
        for row in rows:
            factors = row.get("factors") or row.get("factor_vector")
            if isinstance(factors, list) and len(factors) == shape.n_factors:
                factors = dict(zip(shape.factor_names, factors))
            category, actual = row.get("category"), row.get("actual_action")
            if (not isinstance(factors, dict) or not all(name in factors for name in shape.factor_names)
                    or category not in shape.category_names or actual not in shape.action_names):
                excluded += 1
                continue
            live = scorer.score_read_only(factors, category)
            pinned = self.twin.score_frozen([factors[name] for name in shape.factor_names],
                                          shape.category_names.index(category))
            live_action = live.get("action") if isinstance(live, dict) else live.action
            live_correct += int(live_action == actual)
            frozen_correct += int(pinned.action_name == actual)
            count = len(learning) + 1
            common = {"decision_id": row.get("decision_id"), "decisions": count,
                      "timestamp": row.get("created_at")}
            learning.append({**common, "accuracy": live_correct / count})
            frozen.append({**common, "accuracy": frozen_correct / count})
        return {"learning_curve": learning, "frozen_curve": frozen,
                "curve_kind": "retrospective_paired_replay", "metric": "accuracy",
                "curve_note": "Current and immutable frozen models replay the same verified cohort; not historical learning or waste curves.",
                "excluded_decisions": excluded}

    def frozen_comparison(self) -> dict[str, Any]:
        if not self.twin.is_frozen():
            return {"available": False, "status": "NOT_INITIALIZED", "evidence_tier": "T_S"}
        scorer = self.scorer_provider()
        unwrap = getattr(scorer, "_scorer", None)
        if callable(unwrap):
            scorer = unwrap()
        raw = getattr(scorer, "gae_scorer", scorer)
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
        unwrap = getattr(scorer, "_scorer", None)
        if callable(unwrap):
            scorer = unwrap()
        raw = getattr(scorer, "gae_scorer", scorer)
        if self.twin.is_frozen():
            return self.frozen_status()
        self.twin.freeze(raw, {"status": self.readiness()["conservation_status"]}, 0.0, "purchasing")
        # Creation and subsequent GETs expose the same curve contract. Curves
        # replay observed labels against the pinned model, never invented points.
        return self.frozen_status()

    def record_outcome(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        outcome = VerifiedOutcome.from_dict(dict(payload))
        result = self.processor.process(outcome)
        self.proof.record("outcome", {"decision_id": outcome.decision_id, "receipt_id": result.receipt_id, "evidence_provenance": outcome.evidence_provenance, "processed": result.processed})
        self._prune_evolution_events()
        return cast(dict[str, Any], result.to_dict())
