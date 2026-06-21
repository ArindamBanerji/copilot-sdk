from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.connectors.dq_benchmark_provider import (
    DQBenchmarkProvider,
    MockDQBenchmarkProvider,
)
from app.data_helpers import assert_no_sample_in_metric


class FakeSchemaSource:
    provenance_tier = "scraped_external"

    def __init__(self, payload: dict | None = None, error: Exception | None = None):
        self.payload = payload or {
            "@context": "https://schema.org",
            "@type": "Class",
            "name": "Person",
            "properties": ["name", "email"],
        }
        self.error = error
        self.calls = 0

    def fetch_schema(self, entity_type: str) -> dict | None:
        self.calls += 1
        if self.error:
            raise self.error
        return {**self.payload, "name": entity_type}


class EmptySchemaSource:
    provenance_tier = "scraped_external"

    def fetch_schema(self, entity_type: str) -> None:
        return None


def test_provider_provenance_tier():
    assert DQBenchmarkProvider().provenance_tier == "scraped_external"


def test_mock_provenance_tier():
    assert MockDQBenchmarkProvider().provenance_tier == "sample"


def test_quality_dimensions_count():
    result = DQBenchmarkProvider().quality_dimensions()
    assert len(result.value) >= 6


def test_quality_dimensions_names():
    names = {row["name"] for row in DQBenchmarkProvider().quality_dimensions().value}
    assert {"completeness", "accuracy", "timeliness", "consistency", "uniqueness", "validity"} <= names


def test_quality_dimensions_provenance():
    result = DQBenchmarkProvider().quality_dimensions()
    assert result.source == "scraped_external"
    assert all(row["provenance"] == "scraped_external" for row in result.value)


def test_cascade_live_to_cached(tmp_path: Path):
    source = FakeSchemaSource()
    provider = DQBenchmarkProvider(cache_dir=tmp_path, source=source)
    result = provider.schema_for_entity("Person")

    assert result.source == "scraped_external"
    assert source.calls == 1
    assert (tmp_path / "person.json").exists()


def test_cascade_cached_serves(tmp_path: Path):
    source = FakeSchemaSource()
    provider = DQBenchmarkProvider(cache_dir=tmp_path, source=source)

    first = provider.schema_for_entity("Person")
    second = provider.schema_for_entity("Person")

    assert first.source == "scraped_external"
    assert second.source == "cached"
    assert source.calls == 1


def test_cascade_fixture_fallback(tmp_path: Path):
    provider = DQBenchmarkProvider(cache_dir=tmp_path, source=EmptySchemaSource())

    result = provider.schema_for_entity("Person")

    assert result.source == "sample"
    assert result.value["provenance"] == "sample"


def test_cascade_never_unlabeled(tmp_path: Path):
    provider = DQBenchmarkProvider(cache_dir=tmp_path, source=FakeSchemaSource())
    results = [
        provider.quality_dimensions(),
        provider.schema_for_entity("Organization"),
        provider.benchmark_scores({"completeness": 1.0}),
    ]
    assert all(result.source for result in results)


def test_benchmark_scores_perfect():
    result = DQBenchmarkProvider().benchmark_scores(_metrics(1.0))
    assert result.source == "scraped_external"
    assert result.value["overall_score"] == 1.0
    assert result.value["status"] == "strong"


def test_benchmark_scores_poor():
    result = DQBenchmarkProvider().benchmark_scores(_metrics(0.2))
    assert result.value["overall_score"] == 0.2
    assert result.value["status"] == "weak"


def test_benchmark_scores_partial():
    metrics = _metrics(0.5)
    metrics["accuracy"] = 1.0
    result = DQBenchmarkProvider().benchmark_scores(metrics)
    assert 0.5 < result.value["overall_score"] < 1.0


def test_schema_for_known_entity(tmp_path: Path):
    provider = DQBenchmarkProvider(cache_dir=tmp_path, source=FakeSchemaSource())
    result = provider.schema_for_entity("Person")
    assert result.source == "scraped_external"
    assert result.value["name"] == "Person"


def test_schema_for_unknown(tmp_path: Path):
    provider = DQBenchmarkProvider(cache_dir=tmp_path, source=EmptySchemaSource())
    result = provider.schema_for_entity("UnknownThing")
    assert result.source == "sample"
    assert result.value["name"] == "UnknownThing"


def test_schema_cache_hit(tmp_path: Path):
    source = FakeSchemaSource()
    provider = DQBenchmarkProvider(cache_dir=tmp_path, source=source)
    provider.schema_for_entity("Organization")

    cached = provider.schema_for_entity("Organization")

    assert cached.source == "cached"
    assert source.calls == 1


def test_network_error_uses_cache(tmp_path: Path):
    _write_cache(tmp_path, "Person", {"name": "Person", "properties": ["name"]})
    provider = DQBenchmarkProvider(
        cache_dir=tmp_path,
        source=FakeSchemaSource(error=ConnectionError("offline")),
    )
    result = provider.schema_for_entity("Person")
    assert result.source == "cached"


def test_timeout_uses_cache(tmp_path: Path):
    _write_cache(tmp_path, "Person", {"name": "Person", "properties": ["name"]})
    provider = DQBenchmarkProvider(
        cache_dir=tmp_path,
        source=FakeSchemaSource(error=TimeoutError("slow")),
    )
    result = provider.schema_for_entity("Person")
    assert result.source == "cached"


def test_malformed_response_uses_cache(tmp_path: Path):
    _write_cache(tmp_path, "Person", {"name": "Person", "properties": ["name"]})
    provider = DQBenchmarkProvider(
        cache_dir=tmp_path,
        source=FakeSchemaSource(error=ValueError("bad json")),
    )
    result = provider.schema_for_entity("Person")
    assert result.source == "cached"


def test_empty_cache_uses_fixture(tmp_path: Path):
    provider = DQBenchmarkProvider(
        cache_dir=tmp_path,
        source=FakeSchemaSource(error=ConnectionError("offline")),
    )
    result = provider.schema_for_entity("Organization")
    assert result.source == "sample"
    assert result.value["provenance"] == "sample"


def test_mock_not_labeled_live():
    result = MockDQBenchmarkProvider().schema_for_entity("Person")
    assert result.source != "scraped_external"
    assert result.source == "sample"


def test_f26_gate_rejects_sample():
    rows = MockDQBenchmarkProvider().quality_dimensions().value
    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        assert_no_sample_in_metric(rows, "dq_benchmark")


def test_f26_gate_passes_real():
    rows = DQBenchmarkProvider().quality_dimensions().value
    assert_no_sample_in_metric(rows, "dq_benchmark")


def _metrics(value: float) -> dict[str, float]:
    return {
        "completeness": value,
        "accuracy": value,
        "timeliness": value,
        "consistency": value,
        "uniqueness": value,
        "validity": value,
    }


def _write_cache(tmp_path: Path, entity_type: str, value: dict) -> None:
    timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
    (tmp_path / f"{entity_type.lower()}.json").write_text(
        json.dumps({"as_of": timestamp.isoformat(), "value": value}),
        encoding="utf-8",
    )
