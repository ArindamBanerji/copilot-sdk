from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.di_router import create_di_router
from copilot_sdk.di.query_models import QueryPlan, RawQueryResult
from copilot_sdk.di.query_providers import FixtureProvider
from copilot_sdk.di.query_service import DIQueryService


class FakeProfiler:
    def __init__(self, source_id: str, trust: float) -> None:
        self.source_id = source_id
        self.trust = trust

    def to_dict(self) -> dict[str, Any]:
        return {"source_id": self.source_id, "source_name": self.source_id, "trust": self.trust}


class FakeProvider(FixtureProvider):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.executed_plans: list[QueryPlan] = []

    def execute(self, plan: QueryPlan) -> RawQueryResult:
        self.executed_plans.append(plan)
        return super().execute(plan)


class DisagreementProvider(FakeProvider):
    def execute(self, plan: QueryPlan) -> RawQueryResult:
        result = super().execute(plan)
        result.disagreement_ratio = 0.08
        return result


def _rows(count: int = 12) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    return [
        {
            "decision_id": f"d-{index}",
            "source_id": "sap_s4hana" if index % 2 == 0 else "salesforce",
            "category": "invoice",
            "amount": 100.0 + index,
            "confidence": 0.8,
            "is_correct": index % 3 != 0,
            "created_at": now - timedelta(days=index),
            "match_status": "unmatched" if index == 1 else "matched",
        }
        for index in range(count)
    ]


def _service(
    rows: list[dict[str, Any]] | None = None,
    *,
    provider: FixtureProvider | None = None,
    profiles: dict[str, Any] | None = None,
    source_id_map: dict[str, str] | None = None,
    minimum_sample: int = 10,
) -> DIQueryService:
    resolved = provider or FakeProvider(
        rows or _rows(),
        profiles=profiles
        if profiles is not None
        else {
            "sap_s4hana": FakeProfiler("sap_s4hana", 0.99).to_dict(),
            "salesforce": FakeProfiler("salesforce", 0.87).to_dict(),
        },
    )
    return DIQueryService(resolved, minimum_sample=minimum_sample, source_id_map=source_id_map)


def _client(service: DIQueryService) -> TestClient:
    app = FastAPI()
    app.include_router(create_di_router({}, query_service=service), prefix="/api")

    @app.post("/api/dataops/query")
    def compatibility_query(payload: dict[str, Any]) -> dict[str, Any]:
        return service.execute(payload).model_dump()

    return TestClient(app)


def test_valid_question_accepted() -> None:
    response = _client(_service()).post("/api/di/query", json={"question": "How many decisions?"})
    assert response.status_code == 200
    assert response.json()["answer"] == "12"


def test_empty_question_returns_400() -> None:
    response = _client(_service()).post("/api/di/query", json={"question": ""})
    assert response.status_code == 400


def test_whitespace_question_returns_400() -> None:
    response = _client(_service()).post("/api/di/query", json={"question": "   "})
    assert response.status_code == 400


def test_unsupported_metric_returns_honest_response() -> None:
    response = _client(_service()).post("/api/di/query", json={"question": "What was EBITDA last month?"})
    body = response.json()
    assert response.status_code == 200
    assert body["confidence_label"] == "insufficient"
    assert body["query"]["supported"] is False


def test_raw_sql_rejected() -> None:
    body = _client(_service()).post("/api/di/query", json={"question": "SELECT * FROM invoices"}).json()
    assert body["query"]["reason"] == "raw_query_rejected"
    assert body["confidence"] is None


def test_raw_cypher_rejected() -> None:
    body = _client(_service()).post("/api/di/query", json={"question": "MATCH (d:Decision) RETURN d"}).json()
    assert body["query"]["reason"] == "raw_query_rejected"


def test_canonical_and_compat_share_behavior() -> None:
    client = _client(_service())
    canonical = client.post("/api/di/query", json={"question": "How many decisions?"}).json()
    compatibility = client.post("/api/dataops/query", json={"question": "How many decisions?"}).json()
    assert canonical["answer"] == compatibility["answer"]
    assert canonical["confidence_label"] == compatibility["confidence_label"]


def test_aggregation_executes_through_provider() -> None:
    provider = FakeProvider(_rows())
    body = _client(_service(provider=provider)).post("/api/di/query", json={"question": "Total revenue"}).json()
    assert provider.executed_plans[0].metric == "revenue"
    assert body["answer"] == "$1,266"


def test_time_window_filtering() -> None:
    body = _client(_service()).post("/api/di/query", json={"question": "How many decisions last 3 days?"}).json()
    assert body["query"]["time_window"] == "last_3_days"
    assert body["answer"] == "3"


def test_source_attribution_reflects_participation() -> None:
    body = _client(_service()).post("/api/di/query", json={"question": "How many decisions?"}).json()
    attributions = {item["source_id"]: item for item in body["source_attribution"]}
    assert set(attributions) == {"sap_s4hana", "salesforce"}
    assert attributions["sap_s4hana"]["records_used"] == 6
    assert attributions["sap_s4hana"]["weight"] == 0.5


def test_results_bounded() -> None:
    service = DIQueryService(FixtureProvider(_rows(1100)), max_records=1000)
    response = service.execute({"question": "How many decisions?"})
    assert response.metadata.query_id
    assert response.evidence.startswith("1000 governed records")


def test_provider_outage_returns_insufficient() -> None:
    service = _service(provider=FixtureProvider(unavailable=True))
    response = service.execute({"question": "How many decisions?"})
    assert response.confidence_label == "insufficient"
    assert "no fixture substitution" in (response.quality_warning or "")


def test_confidence_matches_trust_weights() -> None:
    rows = [{**row, "match_status": "matched"} for row in _rows()]
    response = _service(rows=rows).execute({"question": "How many decisions?"})
    assert response.confidence is not None
    assert 0.92 < response.confidence < 0.95


def test_stale_data_lowers_confidence() -> None:
    fresh = _service().execute({"question": "How many decisions?"})
    stale = _service(
        profiles={
            "sap_s4hana": {"source_id": "sap_s4hana", "trust": 0.99, "freshness_hours": 30},
            "salesforce": {"source_id": "salesforce", "trust": 0.87, "freshness_hours": 30},
        }
    ).execute({"question": "How many decisions?"})
    assert stale.confidence is not None and fresh.confidence is not None
    assert stale.confidence < fresh.confidence


def test_unmatched_records_produce_evidence() -> None:
    response = _service().execute({"question": "How many decisions?"})
    assert "1 unmatched" in response.evidence
    assert "unmatched" in (response.quality_warning or "")


def test_small_sample_low_confidence() -> None:
    response = _service(rows=_rows(2)).execute({"question": "How many decisions?"})
    assert response.confidence_label in {"low", "insufficient"}


def test_confidence_clamped_0_1() -> None:
    response = _service(
        profiles={"sap_s4hana": {"source_id": "sap_s4hana", "trust": 9.0}}
    ).execute({"question": "How many decisions?"})
    assert response.confidence is not None
    assert 0.0 <= response.confidence <= 1.0


def test_missing_trust_not_full_trust() -> None:
    response = _service(profiles={}).execute({"question": "How many decisions?"})
    assert response.confidence is not None
    assert response.confidence < 0.2
    assert "unavailable" in (response.quality_warning or "")


def test_source_disagreement_warning() -> None:
    provider = DisagreementProvider(
        _rows(),
        profiles={"sap_s4hana": {"source_id": "sap_s4hana", "trust": 0.99}, "salesforce": {"source_id": "salesforce", "trust": 0.87}},
    )
    response = _service(provider=provider).execute({"question": "How many decisions?"})
    assert "disagree" in (response.quality_warning or "")


def test_confidence_label_correct() -> None:
    response = _service().execute({"question": "How many decisions?"})
    assert response.confidence_label == "high"


def test_domain_authorization_rejects_other_domain() -> None:
    response = _client(_service()).post(
        "/api/di/query",
        json={"question": "How many decisions?", "context": {"domain": "other"}},
    )
    assert response.status_code == 400


def test_query_response_has_computation_path_and_metadata() -> None:
    body = _client(_service()).post("/api/di/query", json={"question": "How many decisions?"}).json()
    assert body["computation_path"]
    assert body["metadata"]["engine_version"] == "di3-v1"
    assert body["metadata"]["query_id"]


def test_preferred_source_scopes_participation() -> None:
    body = _client(_service()).post(
        "/api/di/query",
        json={"question": "How many decisions?", "context": {"preferred_sources": ["sap_s4hana"]}},
    ).json()
    assert [item["source_id"] for item in body["source_attribution"]] == ["sap_s4hana"]


def test_source_mapping_translates_internal_to_profile_ids() -> None:
    rows = [{**row, "source_id": "compounding_scorer"} for row in _rows()]
    service = _service(
        rows=rows,
        profiles={"airflow": {"source_name": "airflow", "trust_tier": 2}},
        source_id_map={"compounding_scorer": "airflow"},
    )
    response = service.execute({"question": "How many decisions?"})
    assert response.source_attribution[0].source_id == "airflow"
    assert response.source_attribution[0].source == "airflow"
    assert response.source_attribution[0].trust == 0.66


def test_trust_tier_conversion_covers_all_supported_tiers() -> None:
    response = _service(
        profiles={
            "sap_s4hana": {"source_name": "sap_s4hana", "trust_tier": 3},
            "salesforce": {"source_name": "salesforce", "trust_tier": 1},
        }
    ).execute({"question": "How many decisions?"})
    trust = {item.source: item.trust for item in response.source_attribution}
    assert trust["sap_s4hana"] == 0.33
    assert trust["salesforce"] == 1.0


def test_missing_trust_produces_moderate_confidence_not_zero() -> None:
    response = _service(rows=_rows(417), profiles={}).execute({"question": "How many decisions?"})
    assert response.confidence is not None
    assert response.confidence > 0.0
    assert response.source_attribution[0].trust_available is False


def test_source_reliability_ranks_by_trust() -> None:
    service = _service(
        profiles={
            "snowflake": {"source_name": "snowflake", "trust_tier": 1},
            "airflow": {"source_name": "airflow", "trust_tier": 2},
            "dbt": {"source_name": "dbt", "trust_tier": 3},
        }
    )
    response = service.execute({"question": "Which source is most reliable?"})
    assert response.query.intent == "source_reliability"
    assert response.source_attribution[0].source_id == "snowflake"
    assert response.source_attribution[0].trust > response.source_attribution[1].trust


def test_source_reliability_returns_answer() -> None:
    service = _service(
        profiles={"snowflake": {"source_name": "snowflake", "trust_tier": 1}}
    )
    response = service.execute({"question": "Which source is most reliable?"})
    assert response.confidence == 1.0
    assert "snowflake" in response.answer
    assert "trust tier 1" in response.answer


def test_unmapped_source_preserved_as_is() -> None:
    rows = [{**row, "source_id": "unknown_source"} for row in _rows()]
    response = _service(
        rows=rows,
        profiles={"unknown_source": {"source_id": "unknown_source", "trust": 0.61}},
        source_id_map={"other_source": "sap_s4hana"},
    ).execute({"question": "How many decisions?"})
    assert response.source_attribution[0].source_id == "unknown_source"
