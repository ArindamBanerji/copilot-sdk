from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
import importlib.util
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PURCHASING_BACKEND = ROOT / "apps" / "purchasing" / "backend"
S2P_BACKEND = WORKSPACE / "s2p-copilot" / "backend"

from copilot_sdk.outbox import OutboxEventType, OutboxStore
from copilot_sdk.graph.memory_store import InMemoryGraphStore

_s2p_path = WORKSPACE / "s2p-copilot" / "backend" / "app" / "services" / "cross_copilot_signals.py"
_spec = importlib.util.spec_from_file_location("s2p_cross_copilot_signals", _s2p_path)
assert _spec is not None and _spec.loader is not None
_s2p_signals = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_s2p_signals)


@pytest.fixture(autouse=True)
def isolated_app_imports():
    original_path = list(sys.path)
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)
    if str(PURCHASING_BACKEND) not in sys.path:
        sys.path.insert(0, str(PURCHASING_BACKEND))
    yield
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)
    sys.path[:] = original_path


def _publisher_class():
    return import_module("app.services.supplier_signal_publisher").SupplierSignalPublisher


def _active_supplier_signals(*args, **kwargs):
    return import_module("app.services.supplier_signal_publisher").active_supplier_signals(*args, **kwargs)


def _import_s2p_router():
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)
    if str(S2P_BACKEND) in sys.path:
        sys.path.remove(str(S2P_BACKEND))
    sys.path.insert(0, str(S2P_BACKEND))
    return import_module("app.routers.s2p"), import_module("app.domains.s2p.config").S2PDomainConfig


@dataclass
class Card:
    supplier_name: str = "Sysco"
    reliability_pct: float = 74.0
    previous_reliability_pct: float = 93.0
    trend: str = "declining"


def test_purchasing_reliability_drop_signal_can_be_consumed(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    _publisher_class()(store).check_and_publish(Card())

    rows = _active_supplier_signals(store, "Sysco")

    assert rows
    assert rows[0]["supplier_name"] == "Sysco"


def test_signal_maps_to_s2p_supplier_risk_fields(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    _publisher_class()(store).check_and_publish(Card(reliability_pct=74.0))
    latest = _active_supplier_signals(store, "Sysco")[0]

    supplier_risk_rating = float(latest["reliability_pct"]) / 100.0
    supplier_exception_history = _s2p_signals.supplier_exception_from_reliability(latest["reliability_pct"])

    assert supplier_risk_rating == 0.74
    assert supplier_exception_history == 0.26


def test_s2p_score_path_injects_cross_copilot_signal_context(monkeypatch):
    s2p_router, config = _import_s2p_router()
    calls = []

    class Consumer:
        def fetch_supplier_signals(self, supplier_name):
            assert supplier_name == "Sysco"
            return [
                {
                    "supplier_name": "Sysco",
                    "reliability_pct": 74.0,
                    "previous_pct": None,
                    "delta": None,
                    "trend": "declining",
                    "source_copilot": "purchasing",
                    "target_copilot": "s2p",
                    "timestamp": time.time(),
                    "ttl_days": 7,
                    "provenance": "signal",
                }
            ]

    class Scorer:
        graph_store = InMemoryGraphStore(domain="s2p")

        def score(self, factors, category, metadata=None):
            return SimpleNamespace(
                action="hold_for_review",
                action_index=1,
                confidence=0.91,
                probabilities=[0.1, 0.9, 0.0, 0.0, 0.0],
                decision_id="S2P-SIGNAL-1",
            )

    def fake_compute_all_factors(invoice, context=None):
        calls.append(dict(invoice))
        return {name: 0.2 for name in config.factors}

    from fastapi import FastAPI

    app = FastAPI()
    app.state.scorer = Scorer()
    # Match current S2P startup: the route calls this writer synchronously;
    # async_record_* methods on a store would not be called by this path.
    app.state.audit_writer = s2p_router.S2PScoreAuditWriter()
    app.include_router(s2p_router.router)
    monkeypatch.setattr(s2p_router, "CrossCopilotSignalConsumer", Consumer)
    monkeypatch.setattr(s2p_router, "compute_all_factors", fake_compute_all_factors)
    monkeypatch.setattr(s2p_router, "_score_conservation_status", lambda _request: "GREEN")
    monkeypatch.setattr(s2p_router, "_record_score_novelty", lambda *args, **kwargs: None)
    monkeypatch.setattr(s2p_router, "_record_score_shadow", lambda *args, **kwargs: None)
    monkeypatch.setattr(s2p_router, "_link_decision_to_invoice", lambda *args, **kwargs: None)

    response = TestClient(app).post(
        "/api/s2p/score",
        json={
            "event_id": "INV-SIGNAL",
            "category": "price_variance",
            "amount": 5000.0,
            "supplier_id": "SUP-001",
            "supplier_name": "Sysco",
        },
    )

    assert response.status_code == 200
    data = response.json()
    signal = data["process_context"]["cross_copilot_signal"]
    assert signal["supplier"] == "Sysco"
    assert signal["delta"] is None
    assert signal["warning"] == "Purchasing: reliability 74%"
    assert calls[0]["supplier_exception_history"] == 0.26

    store = app.state.scorer.graph_store
    entries = s2p_router.audit._read_entries(store)
    assert len(entries) == 1
    decision = entries[0]
    assert decision.decision_id == data["decision_id"]
    assert decision.action == data["action"]
    assert decision.entry_hash == decision.compute_hash()
    assert decision.prev_hash == "0" * 64

    # Exercise the outcome half of the same real writer/store contract too.
    app.state.audit_writer.record_outcome(
        store, decision_id=data["decision_id"], actual_action=data["action"], outcome="confirm",
    )
    entries = s2p_router.audit._read_entries(store)
    assert len(entries) == 2
    assert entries[1].decision_id == decision.decision_id
    assert entries[1].prev_hash == decision.entry_hash
    assert entries[1].entry_hash == entries[1].compute_hash()


def test_no_signal_leaves_s2p_context_unchanged(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")

    assert _active_supplier_signals(store, "Sysco") == []


def test_expired_signal_is_not_consumed(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    store.append(
        OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL,
        "purchasing",
        {
            "supplier_name": "Sysco",
            "reliability_pct": 74.0,
            "previous_pct": 93.0,
            "delta": -19.0,
            "trend": "declining",
            "source_copilot": "purchasing",
            "target_copilot": "s2p",
            "timestamp": time.time() - 8 * 86400,
            "ttl_days": 7,
            "provenance": "signal",
        },
    )

    assert _active_supplier_signals(store, "Sysco") == []


def test_signal_provenance_preserved_through_publish_consume(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    _publisher_class()(store).check_and_publish(Card())

    latest = _active_supplier_signals(store, "Sysco")[0]

    assert latest["provenance"] == "signal"
