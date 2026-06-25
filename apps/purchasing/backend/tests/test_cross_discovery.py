from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.cross_discovery import PurchasingCrossDiscovery, demo_discovery_decisions


@dataclass
class Candidate:
    factor_a: str = "protein_supplier_reliability"
    factor_b: str = "produce_waste"
    correlation: float = 0.8
    sample_size: int = 40


class FakeReport:
    candidates = [Candidate()]


class FakeEngine:
    def __init__(self):
        self.called = False

    def discover(self, decisions):
        self.called = True
        return FakeReport()


def test_discover_correlated():
    insights = PurchasingCrossDiscovery().discover(demo_discovery_decisions())
    assert insights


def test_discover_no_correlation():
    decisions = [{"factors": {"protein": 0.1, "produce": 0.2}, "correct": True} for _ in range(3)]
    assert PurchasingCrossDiscovery().discover(decisions) == []


def test_explanation_kitchen_language():
    insight = PurchasingCrossDiscovery(FakeEngine()).discover(demo_discovery_decisions())[0]
    assert "move together" in insight.explanation


def test_no_jargon_terms():
    text = PurchasingCrossDiscovery(FakeEngine()).discover(demo_discovery_decisions())[0].explanation.lower()
    assert "centroid" not in text
    assert "sigma" not in text
    assert "n=" not in text


def test_suggested_action():
    insight = PurchasingCrossDiscovery(FakeEngine()).discover(demo_discovery_decisions())[0]
    assert "Check" in insight.suggested_action


def test_uses_p43_engine():
    engine = FakeEngine()
    PurchasingCrossDiscovery(engine).discover(demo_discovery_decisions())
    assert engine.called is True


def test_weekly_digest_top3():
    digest = PurchasingCrossDiscovery(FakeEngine()).weekly_digest(demo_discovery_decisions())
    assert len(digest) <= 3


def test_digest_capped():
    class ManyEngine:
        def discover(self, decisions):
            report = FakeReport()
            report.candidates = [Candidate(factor_a=f"protein_{i}", factor_b=f"produce_{i}") for i in range(10)]
            return report

    digest = PurchasingCrossDiscovery(ManyEngine()).weekly_digest(demo_discovery_decisions())
    assert len(digest) == 3


def test_empty_decisions():
    assert PurchasingCrossDiscovery().discover([]) == []


def test_evidence_count():
    insight = PurchasingCrossDiscovery(FakeEngine()).discover(demo_discovery_decisions())[0]
    assert insight.evidence_count == 40


def test_router_insights():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/discovery/insights")
    assert response.status_code == 200
    assert isinstance(response.json()["insights"], list)


def test_router_digest():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/discovery/digest")
    assert response.status_code == 200
    assert response.json()["provenance"] == "demo"
