from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from copilot_sdk.di.models import ProfileConfig, SourceProfile
from copilot_sdk.di.profiler import BaseSourceProfiler, _clamp


class FakeConnector:
    source_name = "erp"
    entity_type = "invoice"
    trust_tier = 1

    def __init__(self, records_by_id: dict[str, list[dict]], invalid_ids: set[str] | None = None) -> None:
        self.records_by_id = records_by_id
        self.invalid_ids = invalid_ids or set()

    def fetch(self, entity_id: str) -> list[dict]:
        return self.records_by_id.get(entity_id, [])

    def validate(self, record: dict) -> bool:
        return str(record.get("id")) not in self.invalid_ids


class FetchErrorConnector(FakeConnector):
    def fetch(self, entity_id: str) -> list[dict]:
        raise RuntimeError("source unavailable")


def test_clamp_normal():
    assert _clamp(0.5) == 0.5


def test_clamp_below():
    assert _clamp(-0.1) == 0.0


def test_clamp_above():
    assert _clamp(1.1) == 1.0


def test_source_profile_to_dict():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    profile = SourceProfile(
        source_name="erp",
        entity_type="invoice",
        trust_tier=1,
        freshness_score=0.9,
        completeness_score=0.8,
        consistency_score=0.5,
        validation_pass_rate=1.0,
        record_count=2,
        last_profiled=now,
        overall_quality=0.82,
    )

    payload = profile.to_dict()

    assert payload["source_name"] == "erp"
    assert payload["last_profiled"] == now.isoformat()
    assert payload["overall_quality"] == 0.82


def test_source_profile_default_errors_empty():
    profile = SourceProfile(
        source_name="erp",
        entity_type="invoice",
        trust_tier=1,
        freshness_score=0.0,
        completeness_score=0.0,
        consistency_score=0.5,
        validation_pass_rate=0.0,
        record_count=0,
    )

    assert profile.errors == []


def test_empty_entities():
    profiler = BaseSourceProfiler(FakeConnector({}))

    profile = profiler.profile([])

    assert profile.record_count == 0
    assert profile.overall_quality == pytest.approx(0.1)


def test_no_records_found():
    profiler = BaseSourceProfiler(FakeConnector({}))

    profile = profiler.profile(["missing"])

    assert profile.record_count == 0
    assert profile.validation_pass_rate == 0.0


def test_basic_profiling():
    now = datetime.now(timezone.utc)
    profiler = BaseSourceProfiler(FakeConnector({"A": [{"id": "r1", "timestamp": now.isoformat()}]}))

    profile = profiler.profile(["A"])

    assert profile.record_count == 1
    assert profile.source_name == "erp"
    assert profile.entity_type == "invoice"
    assert profile.trust_tier == 1


def test_validation_pass_rate():
    records = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]
    profiler = BaseSourceProfiler(FakeConnector({"A": records}, invalid_ids={"r2"}))

    profile = profiler.profile(["A"])

    assert profile.validation_pass_rate == pytest.approx(2 / 3)


def test_freshness_recent():
    now = datetime.now(timezone.utc)
    profiler = BaseSourceProfiler(FakeConnector({}))

    score = profiler._compute_freshness([{"timestamp": now}], now)

    assert score == 1.0


def test_freshness_stale():
    now = datetime.now(timezone.utc)
    stale = now - timedelta(hours=48)
    profiler = BaseSourceProfiler(FakeConnector({}))

    score = profiler._compute_freshness([{"timestamp": stale}], now)

    assert score == 0.0


def test_completeness_with_required_fields():
    config = ProfileConfig(required_fields=["id", "amount", "supplier"])
    profiler = BaseSourceProfiler(FakeConnector({}), config=config)
    records = [
        {"id": "r1", "amount": 10.0},
        {"id": "r2", "supplier": "Acme"},
    ]

    score = profiler._compute_completeness(records)

    assert score == pytest.approx(4 / 6)


def test_overall_quality_weighted():
    now = datetime.now(timezone.utc)
    config = ProfileConfig(required_fields=["id"])
    profiler = BaseSourceProfiler(
        FakeConnector({"A": [{"id": "r1", "timestamp": now.isoformat()}]}),
        config=config,
    )

    profile = profiler.profile(["A"])

    assert 0.0 <= profile.overall_quality <= 1.0
    assert profile.overall_quality == pytest.approx(0.9)


def test_fetch_error_captured():
    profiler = BaseSourceProfiler(FetchErrorConnector({}))

    profile = profiler.profile(["A"])

    assert profile.record_count == 0
    assert len(profile.errors) == 1
    assert "fetch failed for A" in profile.errors[0]


def test_consistency_defaults_to_half():
    profile = BaseSourceProfiler(FakeConnector({})).profile([])

    assert profile.consistency_score == 0.5


def test_profile_config_custom_weights():
    config = ProfileConfig(
        freshness_weight=1.0,
        completeness_weight=0.0,
        consistency_weight=0.0,
        validation_weight=0.0,
        freshness_window_hours=12.0,
        required_fields=["id"],
    )
    now = datetime.now(timezone.utc)
    profiler = BaseSourceProfiler(
        FakeConnector({"A": [{"id": "r1", "timestamp": now.isoformat()}]}),
        config=config,
    )

    profile = profiler.profile(["A"])

    assert profile.overall_quality == pytest.approx(1.0)
    assert profiler.config.freshness_window_hours == 12.0
    assert profiler.config.required_fields == ["id"]
