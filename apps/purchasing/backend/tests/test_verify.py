from __future__ import annotations

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
    assert state.graph_store.decision["status"] == "confirmed"
    assert state.graph_store.outcome["context"]["reason_code"] == "supplier_preference"


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
    state = _FakeState()
    app.include_router(create_verify_router(state))
    client = TestClient(app)

    response = _verify(client, "DEC-1", "order_as_planned")

    assert response.status_code == 200
    assert state.scorer.calls == [
        {
            "decision_id": "DEC-1",
            "actual_action": "order_as_planned",
            "outcome": "confirmed",
            "context": {
                "reason_code": "supplier_preference",
                "reason_label": "Chose preferred supplier",
                "notes": None,
                "source": "purchasing_verify",
            },
        }
    ]


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


class _FakeStore:
    domain = "purchasing"

    def __init__(self) -> None:
        self.decision = {
            "decision_id": "DEC-1",
            "domain": "purchasing",
            "recommended_action": "order_as_planned",
            "action": "order_as_planned",
            "status": "pending",
        }
        self.verified = 0
        self.correct = 0

    def get_decision(self, decision_id: str) -> dict | None:
        if decision_id == self.decision["decision_id"]:
            return dict(self.decision)
        return None

    def count_verified(self, domain: str) -> int:
        return self.verified if domain == "purchasing" else 0

    def count_correct(self, domain: str) -> int:
        return self.correct if domain == "purchasing" else 0

    def count_verified_decisions(self, domain: str) -> int:
        return self.verified if domain == "purchasing" else 0


class _FakeScorer:
    def __init__(self, store: _FakeStore) -> None:
        self.store = store
        self.calls: list[dict] = []

    def learn(self, decision_id: str, actual_action: str, outcome: str, *, context: dict):
        self.calls.append(
            {
                "decision_id": decision_id,
                "actual_action": actual_action,
                "outcome": outcome,
                "context": dict(context),
            }
        )
        self.store.decision["status"] = "confirmed"
        self.store.verified = 1
        self.store.correct = int(actual_action == self.store.decision["recommended_action"])
        return {
            "decision_id": decision_id,
            "outcome": outcome,
            "reward": 1.0,
            "iks_before": 0.0,
            "iks_after": 0.0,
        }


class _FakeState:
    _preset_name = "purchasing"

    def __init__(self) -> None:
        self.graph_store = _FakeStore()
        self.scorer = _FakeScorer(self.graph_store)

    def _scorer(self) -> _FakeScorer:
        return self.scorer


class _PausedStore:
    domain = "purchasing"

    def __init__(self) -> None:
        self.decision = {
            "decision_id": "DEC-PAUSED",
            "domain": "purchasing",
            "recommended_action": "order_as_planned",
            "action": "order_as_planned",
            "status": "pending",
        }
        self.outcome: dict | None = None

    def get_decision(self, decision_id: str) -> dict | None:
        if decision_id == self.decision["decision_id"]:
            return dict(self.decision)
        return None

    def get_verified_decisions(self, domain: str) -> list[dict]:
        if self.outcome is None or domain != "purchasing":
            return []
        return [{**self.decision, **self.outcome}]

    def write_outcome(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict | None = None,
        domain: str | None = None,
    ) -> None:
        if domain is not None and domain != self.domain:
            raise KeyError(f"unknown domain: {domain}")
        if self.outcome is not None:
            raise ValueError(f"outcome already exists for decision_id: {decision_id}")
        meta = metadata or {}
        self.outcome = {
            "decision_id": decision_id,
            "actual_action": actual_action,
            "is_correct": is_correct,
            "context": dict(meta.get("context") or {}),
        }
        self.decision["status"] = "confirmed" if is_correct else "overridden"

    def count_verified(self, domain: str) -> int:
        return 1 if self.outcome is not None and domain == "purchasing" else 0

    def count_correct(self, domain: str) -> int:
        return int(bool(self.outcome and self.outcome["is_correct"] and domain == "purchasing"))

    def count_verified_decisions(self, domain: str) -> int:
        return self.count_verified(domain)


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
        self.graph_store = _PausedStore()
        self.scorer = _PausedScorer()

    def _scorer(self) -> _PausedScorer:
        return self.scorer
