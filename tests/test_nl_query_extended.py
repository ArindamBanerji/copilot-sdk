from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from copilot_sdk.di import (
    AccuracyPattern,
    AggregationPattern,
    BaseSourceProfiler,
    ComparisonPattern,
    MultiEntityPattern,
    NLQueryRouter,
    ProfileConfig,
    QueryPattern,
    QueryResult,
    SourceProfile,
    TimeWindowPattern,
)


class FakeGraphStore:
    def __init__(self, decisions: list[dict], verified: list[dict] | None = None) -> None:
        self.decisions = decisions
        self.verified = verified if verified is not None else decisions
        self.calls: list[str] = []

    def get_verified_decisions(self, domain: str = "dataops") -> list[dict]:
        self.calls.append(f"verified:{domain}")
        return list(self.verified)

    def get_all_decisions(self, domain: str = "dataops") -> list[dict]:
        self.calls.append(f"all:{domain}")
        return list(self.decisions)


class StrictNoDbStore(FakeGraphStore):
    def __getattr__(self, name: str):
        if name.startswith("_run") or "query" in name.lower() or "connection" in name.lower():
            raise AssertionError(f"raw DB access attempted: {name}")
        raise AttributeError(name)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _decision(
    decision_id: str,
    *,
    category: str = "quality",
    supplier_id: str = "SUP-A",
    source_id: str = "erp",
    system: str = "erp",
    confidence: float = 0.8,
    amount: float = 100.0,
    created_at: datetime | float | str | None = None,
    is_correct: bool | None = True,
    recommended_action: str = "approve",
    actual_action: str | None = None,
) -> dict:
    data = {
        "decision_id": decision_id,
        "category": category,
        "supplier_id": supplier_id,
        "source_id": source_id,
        "system": system,
        "confidence": confidence,
        "amount": amount,
        "recommended_action": recommended_action,
        "factors": {"amount": amount, "exception_rate": amount / 1000.0},
        "metadata": {"supplier_id": supplier_id, "source_id": source_id, "system": system},
    }
    if created_at is not None:
        data["created_at"] = created_at
    if is_correct is not None:
        data["is_correct"] = is_correct
    if actual_action is not None:
        data["actual_action"] = actual_action
    return data


def _sample_decisions() -> list[dict]:
    current = _now()
    return [
        _decision("d1", category="quality", supplier_id="SUP-A", confidence=0.9, created_at=current - timedelta(days=2), is_correct=True),
        _decision("d2", category="quality", supplier_id="SUP-A", confidence=0.7, created_at=current - timedelta(days=9), is_correct=False),
        _decision("d3", category="freshness", supplier_id="SUP-B", confidence=0.8, created_at=current - timedelta(days=35), is_correct=True),
        _decision("d4", category="freshness", supplier_id="SUP-B", confidence=0.6, created_at=current - timedelta(days=70), is_correct=None),
    ]


def test_multi_entity_all_suppliers():
    result = NLQueryRouter().query("which suppliers have decisions", _sample_decisions())

    assert result["intent"] == "multi_entity"
    assert result["result"]["entities"][0]["entity"] == "SUP-A"
    assert result["metadata"]["dimension"] == "supplier"


def test_multi_entity_filtered_threshold():
    result = NLQueryRouter().query("list suppliers > 1", _sample_decisions())

    assert result["intent"] == "multi_entity"
    assert [row["entity"] for row in result["result"]["entities"]] == ["SUP-A", "SUP-B"]


def test_multi_entity_empty():
    result = NLQueryRouter().query("list all suppliers", [])

    assert result["intent"] == "multi_entity"
    assert result["metadata"]["count"] == 0
    assert "No decision evidence" in result["answer"]


def test_time_window_7_days():
    result = NLQueryRouter().query("show last 7 days", _sample_decisions())

    assert result["intent"] == "time_window"
    assert result["metadata"]["count"] == 1
    assert result["result"]["items"][0]["decision_id"] == "d1"


def test_time_window_30_days():
    result = NLQueryRouter().query("show past 30 days", _sample_decisions())

    assert result["intent"] == "time_window"
    assert result["metadata"]["count"] == 2


def test_time_window_no_timestamp_data_is_safe():
    result = NLQueryRouter().query("show last 7 days", [_decision("missing", created_at=None)])

    assert result["intent"] == "time_window"
    assert result["metadata"]["count"] == 0
    assert result["metadata"]["warnings"]


def test_time_window_no_matches():
    old = [_decision("old", created_at=_now() - timedelta(days=400))]
    result = NLQueryRouter().query("show last 7 days", old)

    assert result["intent"] == "time_window"
    assert result["metadata"]["count"] == 0
    assert "No timestamped decision evidence" in result["answer"]


def test_time_window_since_iso_date_filters_correctly():
    since = (_now() - timedelta(days=20)).date().isoformat()
    result = NLQueryRouter().query(f"show decisions since {since}", _sample_decisions())

    assert result["intent"] == "time_window"
    assert result["metadata"]["window"] == f"since {since}"
    assert result["metadata"]["count"] == 2


def test_time_window_since_invalid_date_returns_unsupported():
    result = NLQueryRouter().query("show decisions since 2026-99-99", _sample_decisions())

    assert result["intent"] == "time_window"
    assert result["metadata"]["supported"] is False
    assert result["metadata"]["reason"] == "invalid_since_date"
    assert result["metadata"]["count"] == 0


def test_time_window_unrecognized_window_does_not_default_to_30_days():
    result = NLQueryRouter().query("show last decisions", _sample_decisions())

    assert result["intent"] == "time_window"
    assert result["metadata"]["supported"] is False
    assert result["metadata"]["reason"] == "unsupported_time_window"
    assert result["metadata"]["count"] == 0


def test_time_window_missing_timestamp_count_metadata():
    result = NLQueryRouter().query("show last 7 days", [_decision("missing", created_at=None)])

    assert result["intent"] == "time_window"
    assert result["metadata"]["missing_timestamp_count"] == 1


def test_aggregation_average_confidence_by_category():
    result = NLQueryRouter().query("average confidence by category", _sample_decisions())

    assert result["intent"] == "aggregation"
    rows = {row["group"]: row for row in result["result"]["groups"]}
    assert rows["quality"]["operation"] == "average"
    assert rows["quality"]["value"] == 0.8


def test_aggregation_count_decisions_by_supplier():
    result = NLQueryRouter().query("count decisions by supplier", _sample_decisions())

    assert result["intent"] == "aggregation"
    assert result["metadata"]["group_by"] == "supplier"
    assert result["result"]["groups"][0]["count"] == 2


def test_aggregation_handles_empty_data():
    result = NLQueryRouter().query("count decisions by supplier", [])

    assert result["intent"] == "aggregation"
    assert result["metadata"]["count"] == 0


def test_aggregation_handles_missing_metric():
    rows = [_decision("d1")]
    rows[0].pop("confidence")
    result = NLQueryRouter().query("average confidence by category", rows)

    assert result["intent"] == "aggregation"
    assert result["result"]["groups"][0]["value"] is None
    assert result["metadata"]["warnings"]


def test_comparison_this_month_vs_last_month():
    now = _now()
    rows = [
        _decision("this", created_at=now - timedelta(days=1)),
        _decision("last", created_at=(now.replace(day=1) - timedelta(days=1))),
    ]
    result = NLQueryRouter().query("compare this month vs last month", rows)

    assert result["intent"] == "comparison"
    assert result["result"]["period_a"]["count"] == 1
    assert result["result"]["period_b"]["count"] == 1


def test_comparison_missing_period_data_is_safe():
    result = NLQueryRouter().query("compare this month vs last month", [_decision("missing", created_at=None)])

    assert result["intent"] == "comparison"
    assert result["result"]["period_a"]["count"] == 0
    assert result["metadata"]["warnings"]


def test_comparison_missing_timestamp_count_metadata():
    result = NLQueryRouter().query("compare this month vs last month", [_decision("missing", created_at=None)])

    assert result["intent"] == "comparison"
    assert result["metadata"]["missing_timestamp_count"] == 1


def test_comparison_improvement_trend():
    now = _now()
    rows = [
        _decision("this-1", created_at=now - timedelta(days=1)),
        _decision("this-2", created_at=now - timedelta(days=2)),
        _decision("last", created_at=(now.replace(day=1) - timedelta(days=1))),
    ]
    result = NLQueryRouter().query("compare this month vs last month", rows)

    assert result["intent"] == "comparison"
    assert result["result"]["trend"] == "improved"
    assert result["result"]["delta"] == 1


def test_accuracy_overall():
    result = NLQueryRouter().query("accuracy overall", _sample_decisions())

    assert result["intent"] == "accuracy"
    assert result["result"]["groups"][0]["correct"] == 2
    assert result["result"]["groups"][0]["total"] == 3


def test_accuracy_by_category():
    result = NLQueryRouter().query("accuracy by category", _sample_decisions())

    assert result["intent"] == "accuracy"
    rows = {row["group"]: row for row in result["result"]["groups"]}
    assert rows["quality"]["accuracy"] == 0.5
    assert rows["freshness"]["accuracy"] == 1.0


def test_accuracy_by_source():
    result = NLQueryRouter().query("accuracy by source", _sample_decisions())

    assert result["intent"] == "accuracy"
    assert result["metadata"]["group_by"] == "source"
    rows = {row["group"]: row for row in result["result"]["groups"]}
    assert rows["erp"]["total"] == 3


def test_accuracy_by_supplier_or_entity():
    result = NLQueryRouter().query("accuracy by supplier", _sample_decisions())

    assert result["intent"] == "accuracy"
    assert result["metadata"]["group_by"] == "supplier"
    rows = {row["group"]: row for row in result["result"]["groups"]}
    assert rows["SUP-A"]["accuracy"] == 0.5


def test_accuracy_grouping_missing_field_is_unknown_or_unavailable():
    row = _decision("missing-supplier")
    row.pop("supplier_id")
    row["metadata"].pop("supplier_id")
    result = NLQueryRouter().query("accuracy by supplier", [row])

    assert result["intent"] == "accuracy"
    assert result["result"]["groups"][0]["group"] == "unknown"
    assert result["result"]["groups"][0]["total"] == 1


def test_accuracy_time_bounded():
    result = NLQueryRouter().query("accuracy last 7 days", _sample_decisions())

    assert result["intent"] == "accuracy"
    assert result["result"]["groups"][0]["total"] == 1
    assert result["result"]["groups"][0]["accuracy"] == 1.0


def test_accuracy_missing_correctness_fields_is_safe():
    result = NLQueryRouter().query("accuracy overall", [_decision("unknown", is_correct=None)])

    assert result["intent"] == "accuracy"
    assert result["result"]["groups"][0]["total"] == 0
    assert "No verified/correctness evidence" in result["answer"]


def test_router_dispatches_to_new_pattern_on_unknown_existing_intent():
    result = NLQueryRouter().query("which suppliers are present", _sample_decisions())

    assert result["intent"] == "multi_entity"


def test_multi_entity_percentage_threshold_applies_to_rate_metric():
    rows = [
        _decision("a", supplier_id="SUP-A", amount=200.0),
        _decision("b", supplier_id="SUP-B", amount=50.0),
    ]
    result = NLQueryRouter().query("list suppliers with exception rate > 10%", rows)

    assert result["intent"] == "multi_entity"
    assert [row["entity"] for row in result["result"]["entities"]] == ["SUP-A"]
    assert result["metadata"]["metric"] == "exception_rate"


def test_multi_entity_percentage_threshold_not_applied_to_count():
    result = NLQueryRouter().query("list suppliers > 10%", _sample_decisions())

    assert result["intent"] == "multi_entity"
    assert result["metadata"]["supported"] is False
    assert result["metadata"]["reason"] == "percent_threshold_requires_rate_metric"
    assert result["result"]["entities"] == []


def test_multi_entity_count_threshold_requires_plain_number():
    result = NLQueryRouter().query("list suppliers > 1", _sample_decisions())

    assert result["intent"] == "multi_entity"
    assert [row["entity"] for row in result["result"]["entities"]] == ["SUP-A", "SUP-B"]


def test_multi_entity_rate_threshold_missing_metric_is_unavailable():
    row = _decision("missing-rate", amount=200.0)
    row["factors"].pop("exception_rate")
    result = NLQueryRouter().query("list suppliers with exception rate > 10%", [row])

    assert result["intent"] == "multi_entity"
    assert result["result"]["entities"] == []
    assert result["metadata"]["warnings"]


def test_existing_source_reliability_intent_preserved():
    result = NLQueryRouter().query("is this source reliable", FakeGraphStore(_sample_decisions()))

    assert result["intent"] == "source_reliability"
    assert result["query_template"].startswith("MATCH")


def test_existing_freshness_intent_preserved():
    result = NLQueryRouter().query("is the data fresh", FakeGraphStore(_sample_decisions()))

    assert result["intent"] == "freshness"
    assert result["query_template"].startswith("MATCH")


def test_existing_recurrence_intent_preserved():
    result = NLQueryRouter().query("did this repeat again", FakeGraphStore(_sample_decisions()))

    assert result["intent"] == "recurrence"
    assert result["query_template"].startswith("MATCH")


def test_existing_impact_intent_preserved():
    result = NLQueryRouter().query("what is affected downstream", FakeGraphStore(_sample_decisions()))

    assert result["intent"] == "impact"
    assert result["query_template"].startswith("MATCH")


def test_existing_metric_intent_preserved():
    result = NLQueryRouter().query("what was the metric", FakeGraphStore(_sample_decisions()))

    assert result["intent"] == "metric"
    assert result["query_template"].startswith("MATCH")


def test_unknown_query_fallback_preserved():
    result = NLQueryRouter().query("tell me a story", _sample_decisions())

    assert result == {
        "intent": "unknown",
        "answer": "I could not map that question to a DataOps graph query template.",
        "evidence": [],
    }


def test_empty_query_behavior_preserved():
    result = NLQueryRouter().query("", _sample_decisions())

    assert result == {
        "intent": "unknown",
        "answer": "Ask a DataOps question to query the graph.",
        "evidence": [],
    }


def test_init_exports_preserve_existing_symbols():
    assert NLQueryRouter
    assert ProfileConfig
    assert SourceProfile
    assert BaseSourceProfiler
    assert QueryResult
    assert QueryPattern
    assert MultiEntityPattern
    assert TimeWindowPattern
    assert AggregationPattern
    assert ComparisonPattern
    assert AccuracyPattern


def test_patterns_are_case_insensitive():
    result = NLQueryRouter().query("WHICH SUPPLIERS", _sample_decisions())

    assert result["intent"] == "multi_entity"


def test_patterns_do_not_require_graphstore_or_db():
    result = NLQueryRouter().query("count decisions by category", _sample_decisions())

    assert result["intent"] == "aggregation"
    assert result["metadata"]["count"] == 4


def test_no_external_api_or_llm_dependency():
    source = Path("copilot_sdk/di/query_patterns.py").read_text(encoding="utf-8").lower()

    assert "openai" not in source
    assert "requests" not in source
    assert "httpx" not in source
    assert "llm" not in source


def test_no_raw_db_access_for_patterns():
    store = StrictNoDbStore(_sample_decisions())

    result = NLQueryRouter().query("which suppliers are present", store)

    assert result["intent"] == "multi_entity"
    assert store.calls == ["verified:dataops"]
