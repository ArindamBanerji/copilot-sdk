from __future__ import annotations

from unittest.mock import Mock
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.verify_router import REASON_CODES, create_verify_router


PURCHASING_FACTORS = {
    "expected_demand": 0.72,
    "day_of_week": 0.2,
    "weather_forecast": 0.35,
    "event_flag": 0.1,
    "historical_waste": 0.18,
    "supplier_lead_time": 0.45,
    "price_memory_index": 0.50,
}
VALID_ACTIONS = ("order_as_planned", "order_more", "order_less", "skip")


def _score(client: TestClient, category: str = "protein") -> dict:
    response = client.post(
        "/api/score",
        json={"category": category, "factors": PURCHASING_FACTORS},
    )
    assert response.status_code == 200
    return response.json()


def _verify(
    client: TestClient,
    decision_id: str,
    actual_action: str,
    reason_code: str = "supplier_preference",
    notes: str | None = None,
):
    payload = {
        "decision_id": decision_id,
        "actual_action": actual_action,
        "reason_code": reason_code,
    }
    if notes is not None:
        payload["notes"] = notes
    return client.post("/api/purchasing/verify", json=payload)


def _different_action(action: str) -> str:
    return next(candidate for candidate in VALID_ACTIONS if candidate != action)


def _stored_context(client: TestClient, decision_id: str) -> dict:
    store = client.app.state.purchasing_selected_graph_store
    verified = store.get_verified_decisions("purchasing")
    match = next(row for row in verified if row["decision_id"] == decision_id)
    return match["context"]


def test_verify_confirm(client):
    scored = _score(client)

    response = _verify(client, scored["decision_id"], scored["action"])

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision_id"] == scored["decision_id"]
    assert payload["recommended_action"] == scored["action"]
    assert payload["actual_action"] == scored["action"]
    assert payload["is_override"] is False
    assert payload["reason_code"] == "supplier_preference"


def test_verify_override(client):
    scored = _score(client)
    actual = _different_action(scored["action"])

    response = _verify(client, scored["decision_id"], actual, "price_override")

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_override"] is True
    assert payload["recommended_action"] == scored["action"]
    assert payload["actual_action"] == actual


def test_verify_conservation_in_response(client):
    scored = _score(client)

    response = _verify(client, scored["decision_id"], scored["action"])

    assert response.status_code == 200
    payload = response.json()
    assert payload["conservation_status"] in {"GREEN", "AMBER", "RED"}
    assert isinstance(payload["conservation_q"], float)
    assert payload["verified_count"] >= 1


def test_verify_conservation_q_in_response(client):
    scored = _score(client)

    response = _verify(client, scored["decision_id"], scored["action"])

    assert response.status_code == 200
    assert isinstance(response.json()["conservation_q"], float)


def test_verify_invalid_decision(client):
    response = _verify(client, "NONEXISTENT", "order_as_planned", "other")

    assert response.status_code == 404


def test_verify_invalid_action(client):
    scored = _score(client)

    response = _verify(client, scored["decision_id"], "approve_order")

    assert response.status_code == 400


def test_verify_invalid_reason(client):
    scored = _score(client)

    response = _verify(client, scored["decision_id"], scored["action"], "INVALID_CODE")

    assert response.status_code == 400


def test_verify_idempotent_409(client):
    scored = _score(client)

    first = _verify(client, scored["decision_id"], scored["action"])
    second = _verify(client, scored["decision_id"], scored["action"])

    assert first.status_code == 200
    assert second.status_code == 409


def test_verify_paused_learn_records_idempotency():
    app = FastAPI()
    state = _PausedState()
    app.include_router(create_verify_router(state))
    client = TestClient(app)

    first = _verify(client, "DEC-PAUSED", "order_as_planned")
    second = _verify(client, "DEC-PAUSED", "order_as_planned")

    assert first.status_code == 200
    assert first.json()["status"] == "paused"
    assert second.status_code == 409
    assert state.graph_store.get_decision("DEC-PAUSED", domain="purchasing")["status"] == "confirmed"
    assert state.graph_store.get_verified_decisions("purchasing")[0]["outcome_metadata"]["context"]["reason_code"] == "supplier_preference"


def test_all_reason_codes(client):
    for code in REASON_CODES:
        scored = _score(client)
        response = _verify(
            client,
            scored["decision_id"],
            scored["action"],
            code,
            notes="chef note" if code == "other" else None,
        )

        assert response.status_code == 200
        assert response.json()["reason_code"] == code


def test_verify_all_7_reason_codes(client):
    accepted: list[str] = []
    for code in REASON_CODES:
        scored = _score(client)
        response = _verify(
            client,
            scored["decision_id"],
            scored["action"],
            code,
            notes="custom note" if code == "other" else None,
        )

        assert response.status_code == 200
        accepted.append(response.json()["reason_code"])

    assert accepted == list(REASON_CODES)


def test_verify_reason_codes_endpoint(client):
    response = client.get("/api/purchasing/verify/reason-codes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 7
    assert [row["code"] for row in payload["reason_codes"]] == list(REASON_CODES)


def test_verify_calls_learn():
    app = FastAPI()
    state = _VerifyState()
    app.include_router(create_verify_router(state))
    client = TestClient(app)

    response = _verify(client, "DEC-1", "order_as_planned")

    assert response.status_code == 200
    state.scorer.learn.assert_called_once_with(
        "DEC-1", "order_as_planned", "confirmed",
        context={"reason_code": "supplier_preference", "reason_label": "Chose preferred supplier",
                 "notes": None, "source": "purchasing_verify"},
    )
    assert state.graph_store.count_verified("purchasing") == 1


def test_reason_code_stored(client):
    scored = _score(client)

    response = _verify(client, scored["decision_id"], scored["action"], "quality_concern")

    assert response.status_code == 200
    context = _stored_context(client, scored["decision_id"])
    assert context["reason_code"] == "quality_concern"
    assert context["reason_label"] == "Quality issue flagged"
    assert context["source"] == "purchasing_verify"


def test_verify_notes_for_other(client):
    scored = _score(client)

    response = _verify(
        client,
        scored["decision_id"],
        scored["action"],
        "other",
        notes="Sous chef requested smaller pack size.",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["notes"] == "Sous chef requested smaller pack size."
    assert payload["metadata"]["notes"] == "Sous chef requested smaller pack size."
    context = _stored_context(client, scored["decision_id"])
    assert context["reason_code"] == "other"
    assert context["notes"] == "Sous chef requested smaller pack size."


def test_verify_other_with_notes(client):
    scored = _score(client)

    response = _verify(
        client,
        scored["decision_id"],
        scored["action"],
        "other",
        notes="Custom ordering note.",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reason_code"] == "other"
    assert payload["metadata"]["notes"] == "Custom ordering note."






def _seed_verify_store(decision_id):
    store = InMemoryGraphStore(domain="purchasing")
    scorer = CompoundingScorer.from_preset("purchasing", graph_store=store, profile="test", enable_rl=False)
    factors = {name: 0.5 for name in scorer._preset.shape.factor_names}
    store.write_decision("purchasing", "protein", "order_as_planned", 0.8, factors,
                         metadata={"decision_id": decision_id})
    return store, scorer


class _VerifyState:
    _preset_name = "purchasing"

    def __init__(self) -> None:
        self.graph_store, self.scorer = _seed_verify_store("DEC-1")
        self.scorer.learn = Mock(wraps=self.scorer.learn)

    def _scorer(self) -> CompoundingScorer:
        return self.scorer




class _PausedScorer:
    def learn(self, decision_id: str, actual_action: str, outcome: str, *, context: dict):
        return {
            "status": "paused",
            "reason": "conservation_red",
            "q": 0.4,
            "theta_min": 0.5,
            "verified_count": 10,
            "correct_count": 4,
            "override_rate": 0.2,
        }


class _PausedState:
    _preset_name = "purchasing"

    def __init__(self) -> None:
        self.graph_store, _ = _seed_verify_store("DEC-PAUSED")
        self.scorer = _PausedScorer()

    def _scorer(self) -> _PausedScorer:
        return self.scorer
