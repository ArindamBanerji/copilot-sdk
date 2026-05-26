from __future__ import annotations

import math
from typing import Any


PURCHASING_FACTORS = {
    "expected_demand": 0.72,
    "day_of_week": 0.2,
    "weather_forecast": 0.35,
    "event_flag": 0.1,
    "historical_waste": 0.18,
    "supplier_lead_time": 0.45,
    "price_memory_index": 0.50,
}
VALID_CATEGORIES = {"protein", "produce", "dairy", "dry_goods", "beverages"}
VALID_ACTIONS = {"order_as_planned", "order_more", "order_less", "skip"}
VALID_FACTORS = set(PURCHASING_FACTORS)


def assert_json_safe(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_json_safe(item)
    elif isinstance(value, list):
        for item in value:
            assert_json_safe(item)
    elif isinstance(value, float):
        assert math.isfinite(value)
    else:
        assert value is None or isinstance(value, (str, int, bool))


def _score_and_learn(client, *, category: str = "protein") -> dict[str, Any]:
    score = client.post(
        "/api/score",
        json={"category": category, "factors": PURCHASING_FACTORS},
    )
    assert score.status_code == 200
    scored = score.json()
    learn = client.post(
        "/api/learn",
        json={
            "decision_id": scored["decision_id"],
            "actual_action": scored["action"],
        },
    )
    assert learn.status_code == 200
    return scored


def test_evidence_summary_empty_store_returns_defaults(client):
    response = client.get("/api/purchasing/evidence/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "purchasing"
    assert "iks_score" in payload
    assert "conservation_status" in payload
    assert payload["decision_count"] == 0
    assert payload["verified_count"] == 0
    assert payload["verification_rate"] == 0.0
    assert isinstance(payload["top_contributing_factors"], list)
    assert_json_safe(payload)


def test_evidence_decisions_empty_store_returns_list(client):
    response = client.get("/api/purchasing/evidence/decisions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "purchasing"
    assert payload["decisions"] == []
    assert payload["count"] == 0
    assert_json_safe(payload)


def test_audit_trail_empty_store_is_honest_fixture_structure(client):
    response = client.get("/api/purchasing/evidence/audit-trail")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "purchasing"
    assert payload["integrity_status"] in {"fixture", "unavailable"}
    assert payload["hash_chain_available"] is False
    assert isinstance(payload["chain"], list)
    assert_json_safe(payload)


def test_conservation_proof_empty_store_has_required_keys(client):
    response = client.get("/api/purchasing/evidence/conservation-proof")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "purchasing"
    assert "q" in payload
    assert "theta_min" in payload
    assert "days_in_green" in payload
    assert isinstance(payload["trajectory"], list)
    assert_json_safe(payload)


def test_purchasing_health_and_status_aliases(client):
    health = client.get("/api/purchasing/health")
    status = client.get("/api/purchasing/status")

    assert health.status_code == 200
    assert status.status_code == 200
    assert health.json()["domain"] == "purchasing"
    assert "status" in health.json()
    assert status.json()["domain"] == "purchasing"
    assert "evidence" in status.json()
    assert_json_safe(health.json())
    assert_json_safe(status.json())


def test_score_learn_populates_summary_and_decisions(client):
    scored = _score_and_learn(client, category="protein")

    summary = client.get("/api/purchasing/evidence/summary").json()
    decisions = client.get("/api/purchasing/evidence/decisions").json()

    assert summary["decision_count"] >= 1
    assert summary["verified_count"] >= 1
    assert decisions["count"] >= 1
    row = decisions["decisions"][-1]
    assert row["decision_id"] == scored["decision_id"]
    assert row["category"] in VALID_CATEGORIES
    assert row["action"] in VALID_ACTIONS
    assert row["is_correct"] is True
    assert set(row["factors"]).issubset(VALID_FACTORS)
    assert row["reasoning"]
    assert_json_safe(summary)
    assert_json_safe(decisions)


def test_audit_and_conservation_reflect_verified_decision_without_overclaim(client):
    scored = _score_and_learn(client, category="produce")

    audit = client.get("/api/purchasing/evidence/audit-trail").json()
    proof = client.get("/api/purchasing/evidence/conservation-proof").json()

    assert audit["hash_chain_available"] is False
    assert audit["integrity_status"] == "fixture"
    assert any(row["decision_id"] == scored["decision_id"] for row in audit["chain"])
    assert proof["q"] is not None
    assert proof["theta_min"] is not None
    assert proof["days_in_green"] is None
    assert_json_safe(audit)
    assert_json_safe(proof)


def test_evidence_uses_purchasing_domain_terms_only(client):
    _score_and_learn(client, category="dairy")

    summary = client.get("/api/purchasing/evidence/summary").json()
    decisions = client.get("/api/purchasing/evidence/decisions").json()

    for item in summary["top_contributing_factors"]:
        assert item["factor"] in VALID_FACTORS
    for decision in decisions["decisions"]:
        assert decision["category"] in VALID_CATEGORIES
        assert decision["action"] in VALID_ACTIONS
        assert set(decision["factors"]).issubset(VALID_FACTORS)
