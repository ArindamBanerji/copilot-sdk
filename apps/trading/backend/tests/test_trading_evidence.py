from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from copilot_sdk.scoring.investigation import EvidenceProvider, VLDInvestigator
from copilot_sdk.scoring.situation_classifier import SituationClassifier

from apps.trading.backend.app.evidence_provider import (
    TRADING_VLD_FACTOR_NAMES,
    TradingEvidenceProvider,
    get_showcase_evidence,
)
from apps.trading.backend.app.main import create_app
from apps.trading.backend.app.vld_preseed import SHOWCASE_TRADES, seed_vld_trading_showcase


class FakeDataSource:
    def __init__(self):
        self.vld_evidence = {}

    def get_vld_evidence(self, trade_id, dimension, factor_name):
        return self.vld_evidence.get(trade_id, {}).get(dimension)


class FakeScorer:
    def __init__(self, mu):
        self.centroids = np.stack([np.asarray(mu, dtype=float)] * 5)
        self.sigma = np.full(self.centroids.shape[-1], 0.1)
        self.categories = ["trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"]
        self.actions = ["strong_execution", "partial_execution", "poor_execution", "skip_recommended"]
        self.tau = 0.1


class TrackingProvider(TradingEvidenceProvider):
    def __init__(self, data_source, trade_id):
        super().__init__(data_source, trade_id)
        self.reads = []

    def read_evidence(self, decision_id, dimension, factor_name):
        self.reads.append(int(dimension))
        return super().read_evidence(decision_id, dimension, factor_name)


def _trend_following_geometry():
    """Post-regen trend_following centroids used by the VLD showcase."""
    return np.array([
        [0.600000605616718, 0.21974901748453946, 0.24166252725836193, 0.024486591598455145, 0.40000225840407894, 0.6565905503324294, 0.5000016816202012, 0.5000000586834407, 0.49999988107515086, 0.4999996286844229],
        [0.750063807518631, 0.7463000000000001, 0.6968825862855643, 0.12880000000000003, 0.6525928816913874, 0.6490750859198553, 0.6749999999999999, 0.5075076502628748, 0.4847853813256782, 0.4524958412570301],
        [0.715, 0.7063, 0.665, 0.0888, 0.6438, 0.6183, 0.715, 0.5113, 0.4771, 0.4285],
        [0.715, 0.7063, 0.665, 0.0888, 0.6438, 0.6183, 0.715, 0.5113, 0.4771, 0.4285],
    ], dtype=float)


def test_evidence_provider_protocol():
    assert isinstance(TradingEvidenceProvider(FakeDataSource(), "VLD-TRD-1"), EvidenceProvider)


def test_evidence_correlation_with_data():
    source = FakeDataSource()
    seed_vld_trading_showcase(source)
    evidence = TradingEvidenceProvider(source, "VLD-TRD-1").read_evidence("VLD-TRD-1", 1, "market_regime")
    assert evidence is not None
    assert evidence["value"] > 0.8
    assert evidence["source"] == "correlation_engine"


def test_evidence_position_sizing():
    source = FakeDataSource()
    seed_vld_trading_showcase(source)
    evidence = TradingEvidenceProvider(source, "VLD-TRD-2").read_evidence("VLD-TRD-2", 2, "position_sizing")
    assert evidence is not None
    assert evidence["value"] > 0.8
    assert evidence["source"] == "portfolio_engine"


def test_evidence_empty_branch():
    source = FakeDataSource()
    seed_vld_trading_showcase(source)
    assert TradingEvidenceProvider(source, "VLD-TRD-1").read_evidence("VLD-TRD-1", 9, "options_gamma_risk") is None


def test_evidence_all_six_factor_concepts_map_to_lookup():
    provider = TradingEvidenceProvider(FakeDataSource(), "missing")
    for name in ["thesis_strength", "correlation_exposure", "momentum_signal", "fundamental_quality", "position_sizing", "volatility_regime"]:
        assert provider.lookup_description(name)


def test_preseed_creates_three_trades():
    source = FakeDataSource()
    result = seed_vld_trading_showcase(source)
    assert result["trade_count"] == 3
    assert {t["trade_id"] for t in SHOWCASE_TRADES} == {"VLD-TRD-1", "VLD-TRD-2", "VLD-TRD-S1"}
    assert get_showcase_evidence("VLD-TRD-1")[1]["value"] == pytest.approx(0.88)


def test_preseed_idempotent():
    source = FakeDataSource()
    first = seed_vld_trading_showcase(source)
    second = seed_vld_trading_showcase(source)
    assert first == second
    assert sorted(source.vld_evidence) == ["VLD-TRD-1", "VLD-TRD-2", "VLD-TRD-S1"]


def test_thesis_reversal_flips_strong_to_partial():
    source = FakeDataSource()
    seed_vld_trading_showcase(source)
    provider = TrackingProvider(source, "VLD-TRD-1")
    investigator = VLDInvestigator(_trend_following_geometry(), np.full(10, 0.1), TRADING_VLD_FACTOR_NAMES)
    trace = investigator.investigate(
        "VLD-TRD-1", "trend_following", np.array(SHOWCASE_TRADES[0]["surface_factors"]), provider, budget=2,
        gated_sources={"correlation_engine"},
    )
    assert trace.surface_action == 0
    assert trace.final_action == 1
    assert trace.final_action != trace.surface_action
    assert provider.reads[:2] == [2, 1]


def test_concentration_risk_flips_strong_to_partial():
    source = FakeDataSource()
    seed_vld_trading_showcase(source)
    provider = TrackingProvider(source, "VLD-TRD-2")
    sigma = np.array([0.2, 0.08, 0.05, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])
    investigator = VLDInvestigator(_trend_following_geometry(), sigma, TRADING_VLD_FACTOR_NAMES)
    trace = investigator.investigate(
        "VLD-TRD-2", "trend_following", np.array(SHOWCASE_TRADES[1]["surface_factors"]), provider, budget=2,
        gated_sources={"portfolio_engine", "correlation_engine"},
    )
    assert trace.surface_action == 0
    assert trace.final_action == 1
    assert provider.reads[:2] == [2, 1]


def test_s1_conservation_no_investigation():
    mu = _trend_following_geometry()
    investigator = VLDInvestigator(mu, np.full(10, 0.1), TRADING_VLD_FACTOR_NAMES)
    v = np.array(SHOWCASE_TRADES[2]["surface_factors"])
    _, probabilities = investigator.score(v)
    Q = investigator.compute_Q(v, probabilities)
    assessment = SituationClassifier().classify(v, mu, np.full(10, 0.1), probabilities, Q)
    trace = investigator.investigate("VLD-TRD-S1", "trend_following", v, TradingEvidenceProvider(FakeDataSource(), "VLD-TRD-S1"), budget=assessment.recommended_budget)
    assert assessment.situation == "S1"
    assert assessment.recommended_budget == 0
    assert trace.steps == []


def test_thesis_reversal_trace_order():
    source = FakeDataSource()
    seed_vld_trading_showcase(source)
    provider = TrackingProvider(source, "VLD-TRD-1")
    investigator = VLDInvestigator(_trend_following_geometry(), np.full(10, 0.1), TRADING_VLD_FACTOR_NAMES)
    investigator.investigate("VLD-TRD-1", "trend_following", np.array(SHOWCASE_TRADES[0]["surface_factors"]), provider, budget=2)
    assert provider.reads[:2] == [2, 1]


def test_investigation_health():
    app = create_app(db_path=":memory:", demo_bundle_path=False, profile="test")
    client = TestClient(app)
    response = client.get("/api/investigation/health")
    assert response.status_code == 200
    assert response.json()["investigation_available"] is True


def test_investigation_endpoint(monkeypatch):
    app = create_app(db_path=":memory:", demo_bundle_path=False, profile="test")
    scorer_proxy = app.state.trading_regime_conditioning
    monkeypatch.setattr(scorer_proxy, "_scorer", lambda: FakeScorer(_trend_following_geometry()))
    client = TestClient(app)
    response = client.post(
        "/api/investigation/investigate",
        json={
            "decision_id": "VLD-TRD-1",
            "category": "trend_following",
            "factor_vector": SHOWCASE_TRADES[0]["surface_factors"],
            "budget": 2,
            "use_K": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["action_changed"] is True
    assert payload["steps"]
