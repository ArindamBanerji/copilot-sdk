from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.di import (
    AccuracyPattern,
    BaseGraphEnricher,
    CombinationDiscoveryEngine,
    GraphEnrichmentReport,
    GraphEnrichmentResult,
    NLQueryRouter,
    ProfileConfig,
    SourceProfile,
)
from copilot_sdk.di.enrichment import GraphEnricher
from copilot_sdk.graph.enrichment import (
    EnrichmentSourceSet,
    EntityEnrichmentReceipt,
    ProvenancedValue,
)
from copilot_sdk.graph.memory_store import InMemoryGraphStore


def _decision(decision_id: str, supplier_id: str | None, correct: bool = True) -> dict[str, Any]:
    row: dict[str, Any] = {
        "decision_id": decision_id,
        "is_correct": correct,
    }
    if supplier_id is not None:
        row["supplier_id"] = supplier_id
    return row


def _decisions() -> list[dict[str, Any]]:
    return [
        _decision("d-1", "SUP-1", True),
        _decision("d-2", "SUP-1", False),
        _decision("d-3", "SUP-2", True),
        _decision("d-4", "SUP-2", True),
        _decision("d-5", "SUP-2", False),
    ]


class MockSupplierEnricher(BaseGraphEnricher):
    def __init__(self, *, min_decisions: int = 2) -> None:
        super().__init__(
            domain="s2p",
            entity_type="supplier",
            namespace="supplier_metrics",
            min_decisions=min_decisions,
            computation_version="test-v1",
        )

    def group_key(self, decision: dict[str, Any]) -> str | None:
        value = decision.get("supplier_id")
        return str(value) if value not in (None, "") else None

    def compute_metrics(self, entity_id: str, decisions: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(decisions)
        correct = sum(1 for decision in decisions if decision.get("is_correct") is True)
        exceptions = total - correct
        return {
            "accuracy": round(correct / total, 4),
            "exception_rate": round(exceptions / total, 4),
            "total_decisions": ProvenancedValue(
                value=total,
                source="graph_store",
                provenance_tier="context",
                source_count=total,
                measured=True,
                verified=False,
                provenance_label="GraphStore decision count",
            ),
        }


class FixtureMetricEnricher(MockSupplierEnricher):
    def compute_metrics(self, entity_id: str, decisions: list[dict[str, Any]]) -> dict[str, Any]:
        return {"fixture_score": ProvenancedValue.from_fixture(0.42)}


class UnavailableMetricEnricher(MockSupplierEnricher):
    def compute_metrics(self, entity_id: str, decisions: list[dict[str, Any]]) -> dict[str, Any]:
        return {"missing_score": ProvenancedValue.unavailable("missing score")}


class ExplicitVerifiedMetricEnricher(MockSupplierEnricher):
    def compute_metrics(self, entity_id: str, decisions: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "accuracy": ProvenancedValue.from_verified(
                1.0,
                source_count=len(decisions),
                n_min=1,
                label="explicit verified metric",
            )
        }


class ExplicitVerifiedNormalizeEnricher(MockSupplierEnricher):
    def normalize_metric(
        self,
        metric_name: str,
        value: Any,
        decisions: list[dict[str, Any]],
    ) -> ProvenancedValue | Any:
        return ProvenancedValue.from_verified(
            value,
            source_count=len(decisions),
            n_min=1,
            label=f"explicit override for {metric_name}",
        )


class FakeGraphStore:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.persisted: list[dict[str, Any]] = []
        self.verified_decisions = _decisions()

    def write_entity_enrichment(self, **kwargs: Any) -> EntityEnrichmentReceipt:
        self.calls.append(dict(kwargs))
        if not kwargs.get("dry_run"):
            self.persisted.append(dict(kwargs))
        return EntityEnrichmentReceipt(
            domain=kwargs["domain"],
            entity_type=kwargs["entity_type"],
            entity_id=kwargs["entity_id"],
            namespace=kwargs["namespace"],
            persisted=not bool(kwargs.get("dry_run")),
            dry_run=bool(kwargs.get("dry_run")),
            metrics_written=list(kwargs["metrics"]),
            metrics_rejected=[],
            protected_fields_rejected=[],
            idempotency_key=str(kwargs.get("idempotency_key") or ""),
            computed_at="receipt-time",
            warnings=[],
        )

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        assert domain == "s2p"
        return list(self.verified_decisions)


class UnsupportedGraphStore:
    def write_entity_enrichment(self, **kwargs: Any) -> EntityEnrichmentReceipt:
        raise NotImplementedError("entity enrichment writes unsupported")


class ReadOnlyGraphStore:
    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        return _decisions()


def _stable_report(report: GraphEnrichmentReport) -> list[dict[str, Any]]:
    stable = []
    for result in report.results:
        metrics = {
            name: replace(value, computed_at="")
            for name, value in result.metrics.items()
            if isinstance(value, ProvenancedValue)
        }
        stable.append(
            {
                "entity_id": result.entity_id,
                "sample_count": result.sample_count,
                "metrics": metrics,
                "persisted": result.persisted,
                "warnings": list(result.warnings),
            }
        )
    return stable


def test_enrich_basic_groups_entities():
    report = MockSupplierEnricher().enrich(_decisions())

    assert isinstance(report, GraphEnrichmentReport)
    assert report.entities_enriched == 2
    assert [result.entity_id for result in report.results] == ["SUP-1", "SUP-2"]
    assert report.total_decisions_used == 5


def test_enrich_min_decisions_skips_small_group():
    report = MockSupplierEnricher(min_decisions=3).enrich(_decisions())

    assert [result.entity_id for result in report.results] == ["SUP-2"]
    assert report.entities_skipped == 1
    assert any("SUP-1" in warning for warning in report.warnings)


def test_enrich_none_group_key_skipped():
    rows = [*_decisions(), _decision("d-missing", None, True)]

    report = MockSupplierEnricher().enrich(rows)

    assert report.entities_skipped == 0
    assert report.skipped_decisions == 1
    assert "decisions_skipped_without_group=1" in report.warnings


def test_enrich_empty_decisions():
    report = MockSupplierEnricher().enrich([])

    assert report.entities_enriched == 0
    assert report.total_decisions_used == 0
    assert report.results == []


def test_enrich_compute_only_without_graph_store():
    report = MockSupplierEnricher().enrich(_decisions())

    assert all(result.persisted is False for result in report.results)
    assert all(any("computed only" in warning for warning in result.warnings) for result in report.results)


def test_enrich_dry_run_does_not_persist():
    store = FakeGraphStore()

    report = MockSupplierEnricher().enrich(_decisions(), graph_store=store, dry_run=True)

    assert len(store.calls) == 2
    assert store.persisted == []
    assert all(result.persisted is False for result in report.results)
    assert all(result.receipt and result.receipt.dry_run is True for result in report.results)


def test_enrich_persist_calls_write_entity_enrichment():
    store = FakeGraphStore()

    report = MockSupplierEnricher().enrich(_decisions(), graph_store=store, dry_run=False)

    assert len(store.calls) == 2
    assert len(store.persisted) == 2
    assert all(call["namespace"] == "supplier_metrics" for call in store.calls)
    assert all(result.persisted is True for result in report.results)


def test_enrich_unsupported_store_returns_warning_not_false_success():
    report = MockSupplierEnricher().enrich(_decisions(), graph_store=UnsupportedGraphStore())

    assert all(result.persisted is False for result in report.results)
    assert all("unsupported" in " ".join(result.warnings) for result in report.results)


def test_enrich_idempotent_ignoring_timestamp():
    enricher = MockSupplierEnricher()

    first = enricher.enrich(_decisions())
    second = enricher.enrich(_decisions())

    assert _stable_report(first) == _stable_report(second)


def test_result_order_deterministic():
    rows = list(reversed(_decisions()))

    report = MockSupplierEnricher().enrich(rows)

    assert [result.entity_id for result in report.results] == ["SUP-1", "SUP-2"]


def test_source_set_contains_verified_decision_count_and_ids():
    store = FakeGraphStore()

    MockSupplierEnricher().enrich_from_store(store)

    source_set = store.calls[0]["computed_from"]
    assert isinstance(source_set, EnrichmentSourceSet)
    assert source_set.verified_decision_count == 2
    assert source_set.decision_ids == ["d-1", "d-2"]
    assert source_set.computation_version == "test-v1"


def test_metrics_use_provenanced_values_if_available():
    report = MockSupplierEnricher().enrich(_decisions())

    metrics = report.results[0].metrics
    assert isinstance(metrics["total_decisions"], ProvenancedValue)
    assert not isinstance(metrics["accuracy"], ProvenancedValue)


def test_raw_metrics_direct_enrich_are_not_auto_verified():
    report = MockSupplierEnricher().enrich(_decisions())

    accuracy = report.results[0].metrics["accuracy"]
    assert accuracy == 0.5
    assert not isinstance(accuracy, ProvenancedValue)
    assert "raw_metric_without_provenance=accuracy" in report.results[0].warnings
    assert "raw_metric_without_provenance=exception_rate" in report.results[0].warnings


def test_explicit_verified_provenanced_value_passthrough():
    report = ExplicitVerifiedMetricEnricher().enrich(_decisions())

    accuracy = report.results[0].metrics["accuracy"]
    assert accuracy.source == "verified_outcomes"
    assert accuracy.provenance_tier == "learned"
    assert accuracy.verified is True
    assert accuracy.measured is True


def test_normalize_metric_override_can_claim_verified_when_explicit():
    report = ExplicitVerifiedNormalizeEnricher().enrich(_decisions())

    accuracy = report.results[0].metrics["accuracy"]
    assert accuracy.source == "verified_outcomes"
    assert accuracy.verified is True
    assert "raw_metric_without_provenance=accuracy" not in report.results[0].warnings


def test_context_metric_cannot_claim_verified_if_hook_used():
    report = FixtureMetricEnricher().enrich(_decisions())

    metric = report.results[0].metrics["fixture_score"]
    assert metric.source == "fixture"
    assert metric.verified is False
    assert metric.measured is False


def test_unavailable_metric_provenance_boundary():
    report = UnavailableMetricEnricher().enrich(_decisions())

    metric = report.results[0].metrics["missing_score"]
    assert metric.source == "unavailable"
    assert metric.verified is False
    assert metric.factor_eligible is False


def test_confidence_low_moderate_good_high_if_confidence_model_kept():
    enricher = MockSupplierEnricher(min_decisions=10)

    assert enricher._compute_confidence(0) == 0.0
    assert enricher._compute_confidence(5) == 0.5
    assert enricher._compute_confidence(10) == 1.0
    assert enricher._compute_confidence(20) == 1.0


def test_base_hooks_required():
    with pytest.raises(TypeError):
        BaseGraphEnricher(domain="x", entity_type="entity")


def test_init_exports_preserve_existing_symbols():
    assert NLQueryRouter
    assert ProfileConfig
    assert SourceProfile
    assert AccuracyPattern
    assert CombinationDiscoveryEngine
    assert BaseGraphEnricher
    assert GraphEnrichmentResult
    assert GraphEnrichmentReport


def test_no_graphstore_protocol_or_scorer_dependency():
    source = Path("copilot_sdk/di/enrichment.py").read_text(encoding="utf-8")

    assert "copilot_sdk.graph.protocol" not in source
    assert "copilot_sdk.scoring" not in source
    assert "scorer" not in source.lower()


def test_no_raw_sql_or_cypher_dependency():
    source = Path("copilot_sdk/di/enrichment.py").read_text(encoding="utf-8").lower()

    assert "sqlite3" not in source
    assert "cypher" not in source
    assert "merge " not in source
    assert "match (" not in source


def test_existing_entity_enrichment_api_compatibility_if_present():
    store = InMemoryGraphStore()

    report = MockSupplierEnricher().enrich(_decisions(), graph_store=store)
    read_back = store.read_entity_enrichment(
        domain="s2p",
        entity_type="supplier",
        entity_id=report.results[0].entity_id,
        namespace="supplier_metrics",
    )

    assert report.results[0].persisted is True
    assert "total_decisions" in read_back


def test_enrich_from_store_uses_get_verified_decisions():
    store = FakeGraphStore()

    report = MockSupplierEnricher().enrich_from_store(store)

    assert report.entities_enriched == 2
    assert len(store.calls) == 2


def test_enrich_from_store_missing_read_method_safe():
    report = MockSupplierEnricher().enrich_from_store(UnsupportedGraphStore())

    assert report.entities_enriched == 0
    assert "get_verified_decisions" in report.warnings[0]


def test_protected_metric_names_report_receipt_rejections():
    class ProtectedMetricEnricher(MockSupplierEnricher):
        def compute_metrics(self, entity_id: str, decisions: list[dict[str, Any]]) -> dict[str, Any]:
            return {
                "supplier_id": ProvenancedValue.from_verified(1.0, source_count=len(decisions)),
                "accuracy": ProvenancedValue.from_verified(1.0, source_count=len(decisions)),
            }

    store = InMemoryGraphStore()

    report = ProtectedMetricEnricher().enrich(_decisions(), graph_store=store)

    assert report.results[0].receipt is not None
    assert report.results[0].receipt.protected_fields_rejected == ["supplier_id"]
    assert report.results[0].receipt.metrics_written == ["accuracy"]


def test_factor_eligible_carried_not_consumed():
    report = ExplicitVerifiedMetricEnricher(min_decisions=1).enrich(_decisions())

    assert report.results[0].metrics["accuracy"].factor_eligible is True
    assert report.results[0].persisted is False


def test_concrete_graph_enricher_callable_hooks():
    enricher = GraphEnricher(
        domain="s2p",
        entity_type="supplier",
        namespace="supplier_metrics",
        min_decisions=2,
        group_key_fn=lambda decision: decision.get("supplier_id"),
        compute_metrics_fn=lambda entity_id, decisions: {"total": len(decisions)},
    )

    report = enricher.enrich(_decisions())

    assert report.entities_enriched == 2
    assert report.results[0].metrics["total"] == 2
    assert "raw_metric_without_provenance=total" in report.results[0].warnings


def test_entities_skipped_counts_entity_groups_not_decision_rows():
    rows = [
        _decision("d-none", None, True),
        _decision("d-small", "SUP-SMALL", True),
        _decision("d-1", "SUP-OK", True),
        _decision("d-2", "SUP-OK", False),
    ]

    report = MockSupplierEnricher(min_decisions=2).enrich(rows)

    assert report.skipped_decisions == 1
    assert report.entities_skipped == 1
    assert [result.entity_id for result in report.results] == ["SUP-OK"]
