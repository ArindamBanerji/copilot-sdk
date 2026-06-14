from __future__ import annotations

import sys
from dataclasses import asdict
from importlib import import_module
from pathlib import Path

import pytest

from copilot_sdk.evidence.provenance import Provenanced
from copilot_sdk.graph.enrichment import (
    EnrichmentSourceSet,
    EntityEnrichmentReceipt,
    EntityEnrichmentRecord,
    ProvenancedValue,
)
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


def _source_set() -> EnrichmentSourceSet:
    return EnrichmentSourceSet(
        verified_decision_count=2,
        unverified_decision_count=1,
        decision_ids=["DEC-1", "DEC-2"],
        outcome_ids=["OUT-1"],
        fixture_sources=["fixture.json"],
        computation_version="test-v1",
    )


def _metric(value: float = 0.15) -> ProvenancedValue:
    return ProvenancedValue.from_verified(
        value,
        source_count=25,
        computed_at="2026-06-14T00:00:00Z",
    )


def test_provenanced_value_from_verified_sets_learned_verified_measured():
    value = ProvenancedValue.from_verified(0.2, source_count=25, computed_at="t")

    assert value.source == "verified_outcomes"
    assert value.provenance_tier == "learned"
    assert value.verified is True
    assert value.measured is True
    assert value.factor_eligible is True


def test_provenanced_value_from_fixture_is_context_not_measured():
    value = ProvenancedValue.from_fixture(0.5, computed_at="t")

    assert value.source == "fixture"
    assert value.provenance_tier == "context"
    assert value.verified is False
    assert value.measured is False
    assert value.factor_eligible is False


def test_provenanced_value_unavailable_is_safe():
    value = ProvenancedValue.unavailable(computed_at="t")

    assert value.value is None
    assert value.source == "unavailable"
    assert value.provenance_tier == "unavailable"
    assert value.factor_eligible is False


def test_fixture_cannot_claim_verified():
    with pytest.raises(ValueError):
        ProvenancedValue(value=1, source="fixture", provenance_tier="context", verified=True)


def test_fixture_cannot_claim_measured():
    with pytest.raises(ValueError):
        ProvenancedValue(value=1, source="fixture", provenance_tier="context", measured=True)


def test_unavailable_cannot_be_factor_eligible():
    with pytest.raises(ValueError):
        ProvenancedValue(
            value=None,
            source="unavailable",
            provenance_tier="unavailable",
            factor_eligible=True,
        )


def test_verified_outcomes_requires_verified_and_measured():
    with pytest.raises(ValueError):
        ProvenancedValue(
            value=1,
            source="verified_outcomes",
            provenance_tier="learned",
            verified=False,
            measured=True,
        )
    with pytest.raises(ValueError):
        ProvenancedValue(
            value=1,
            source="verified_outcomes",
            provenance_tier="learned",
            verified=True,
            measured=False,
        )


def test_learned_tier_requires_verified():
    with pytest.raises(ValueError):
        ProvenancedValue(value=1, source="integration", provenance_tier="learned")


def test_factory_factor_eligible_requires_n_min():
    below = ProvenancedValue.from_verified(0.1, source_count=19, n_min=20, computed_at="t")
    at_threshold = ProvenancedValue.from_verified(0.1, source_count=20, n_min=20, computed_at="t")

    assert below.factor_eligible is False
    assert at_threshold.factor_eligible is True


def test_to_display_downcasts_to_evidence_provenanced():
    value = ProvenancedValue.from_fixture(0.5, label="integration pending", computed_at="t")

    display = value.to_display()

    assert isinstance(display, Provenanced)
    assert display.value == 0.5
    assert display.source == "fixture"
    assert display.label == "supplier context · integration pending"


def test_source_set_shape_and_defaults():
    source_set = EnrichmentSourceSet()

    assert source_set.verified_decision_count == 0
    assert source_set.decision_ids == []


def test_receipt_shape_and_defaults():
    receipt = EntityEnrichmentReceipt(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
        persisted=False,
        dry_run=True,
        metrics_written=[],
        metrics_rejected=[],
        protected_fields_rejected=[],
    )

    assert receipt.warnings == []
    assert receipt.idempotency_key == ""


class DefaultGraphStore(GraphStore):
    def write_decision(self, domain, category, action, confidence, factors, metadata=None):
        return "DEC-1"

    def write_outcome(self, decision_id, actual_action, is_correct, metadata=None):
        return None

    def get_decision(self, decision_id):
        return None

    def get_decisions(self, domain, category=None, limit=400):
        return []

    def get_all_decisions(self, domain):
        return []

    def get_verified_decisions(self, domain):
        return []

    def count_verified(self, domain):
        return 0

    def count_correct(self, domain):
        return 0

    def count_decisions(self, domain):
        return 0

    def save_centroids(self, domain, category, centroids, metadata=None, **kwargs):
        return None

    def load_latest_centroids(self, domain):
        return None

    def get_centroid_checkpoints(self, domain, **kwargs):
        return []

    def archive_old_decisions(self, domain, keep_recent=800):
        return 0

    def count_archived(self, domain):
        return 0

    def close(self):
        return None


def test_graphstore_default_write_entity_enrichment_raises():
    with pytest.raises(NotImplementedError):
        DefaultGraphStore().write_entity_enrichment(
            domain="s2p",
            entity_type="Supplier",
            entity_id="SUP-1",
            namespace="s2p_supplier_metrics",
            metrics={"exception_rate": _metric()},
            computed_from=_source_set(),
        )


def test_graphstore_default_read_entity_enrichment_empty():
    assert (
        DefaultGraphStore().read_entity_enrichment(
            domain="s2p",
            entity_type="Supplier",
            entity_id="SUP-1",
            namespace="s2p_supplier_metrics",
        )
        == {}
    )


def test_graphstore_default_list_entity_enrichments_empty():
    assert DefaultGraphStore().list_entity_enrichments(domain="s2p") == []


def test_runtime_graphstore_structural_compatibility_for_minimal_fake():
    assert isinstance(DefaultGraphStore(), GraphStore)


def _write_sample(store):
    return store.write_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
        metrics={"exception_rate": _metric()},
        computed_from=_source_set(),
        idempotency_key="idem-1",
    )


@pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
def test_store_write_read_entity_enrichment_roundtrip(store_factory):
    store = store_factory()

    receipt = _write_sample(store)
    read_back = store.read_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
    )

    assert receipt.persisted is True
    assert read_back["exception_rate"] == _metric()


@pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
def test_store_upsert_replaces_metric(store_factory):
    store = store_factory()
    _write_sample(store)
    store.write_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
        metrics={"exception_rate": _metric(0.22)},
        computed_from=_source_set(),
    )

    read_back = store.read_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
    )

    assert read_back["exception_rate"].value == 0.22


@pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
def test_store_dry_run_writes_nothing(store_factory):
    store = store_factory()
    receipt = store.write_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
        metrics={"exception_rate": _metric()},
        computed_from=_source_set(),
        dry_run=True,
    )

    assert receipt.persisted is False
    assert store.read_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
    ) == {}


@pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
def test_store_protected_metric_rejected(store_factory):
    store = store_factory()
    receipt = store.write_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
        metrics={"supplier_id": _metric(), "exception_rate": _metric()},
        computed_from=_source_set(),
    )

    assert receipt.protected_fields_rejected == ["supplier_id"]
    assert receipt.metrics_written == ["exception_rate"]


@pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
def test_store_protected_metric_does_not_reject_source_set_decision_ids(store_factory):
    store = store_factory()
    receipt = _write_sample(store)

    assert receipt.protected_fields_rejected == []
    assert store.list_entity_enrichments(domain="s2p")[0].computed_from.decision_ids == [
        "DEC-1",
        "DEC-2",
    ]


def test_sqlite_provenance_roundtrip():
    store = SQLiteGraphStore(":memory:")
    _write_sample(store)

    value = store.read_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
    )["exception_rate"]

    assert asdict(value) == asdict(_metric())


def test_sqlite_source_set_roundtrip():
    store = SQLiteGraphStore(":memory:")
    _write_sample(store)

    record = store.list_entity_enrichments(domain="s2p")[0]

    assert record.computed_from == _source_set()


@pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
def test_store_absent_enrichment_returns_empty_dict(store_factory):
    assert store_factory().read_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
    ) == {}


@pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
def test_store_list_by_domain_entity_type_namespace(store_factory):
    store = store_factory()
    _write_sample(store)
    store.write_entity_enrichment(
        domain="s2p",
        entity_type="Invoice",
        entity_id="INV-1",
        namespace="s2p_invoice_metrics",
        metrics={"exception_rate": _metric()},
        computed_from=_source_set(),
    )

    records = store.list_entity_enrichments(
        domain="s2p",
        entity_type="Supplier",
        namespace="s2p_supplier_metrics",
    )

    assert len(records) == 1
    assert isinstance(records[0], EntityEnrichmentRecord)
    assert records[0].entity_id == "SUP-1"


@pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
def test_store_domain_scoped_reset_deletes_entity_enrichments(store_factory):
    store = store_factory()
    _write_sample(store)

    store.domain_scoped_reset("s2p")

    assert store.list_entity_enrichments(domain="s2p") == []


def test_sqlite_idempotent_rewrite_same_payload():
    store = SQLiteGraphStore(":memory:")
    _write_sample(store)
    _write_sample(store)

    records = store.list_entity_enrichments(domain="s2p")

    assert len(records) == 1
    assert records[0].value == _metric()
    assert records[0].computed_from == _source_set()


def test_memory_read_returns_deep_copy():
    store = InMemoryGraphStore()
    _write_sample(store)

    read_back = store.read_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
    )
    read_back["exception_rate"].warnings.append("mutated")

    reread = store.read_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
    )
    assert reread["exception_rate"].warnings == []


def _age_adapter_class():
    repo_root = Path(__file__).resolve().parents[2]
    ci_platform_path = repo_root / "ci-platform"
    if not ci_platform_path.exists():
        pytest.skip("ci-platform is not available")
    for module_name in list(sys.modules):
        if module_name == "ci_platform" or module_name.startswith("ci_platform."):
            sys.modules.pop(module_name, None)
    sys.path.insert(0, str(ci_platform_path))
    return import_module("ci_platform.graph.age_sdk_adapter").AGEGraphStoreAdapter


class FakeAGEStore:
    def close(self):
        return None


def test_age_adapter_write_entity_enrichment_unsupported():
    adapter = _age_adapter_class()(store=FakeAGEStore())
    with pytest.raises(NotImplementedError):
        adapter.write_entity_enrichment(
            domain="s2p",
            entity_type="Supplier",
            entity_id="SUP-1",
            namespace="s2p_supplier_metrics",
            metrics={"exception_rate": _metric()},
            computed_from=_source_set(),
        )


def test_age_adapter_read_entity_enrichment_empty():
    adapter = _age_adapter_class()(store=FakeAGEStore())
    assert adapter.read_entity_enrichment(
        domain="s2p",
        entity_type="Supplier",
        entity_id="SUP-1",
        namespace="s2p_supplier_metrics",
    ) == {}


def test_age_adapter_list_entity_enrichments_empty():
    adapter = _age_adapter_class()(store=FakeAGEStore())
    assert adapter.list_entity_enrichments(domain="s2p") == []


@pytest.mark.parametrize("store_factory", [InMemoryGraphStore, lambda: SQLiteGraphStore(":memory:")])
def test_existing_decision_and_outcome_paths_still_work(store_factory):
    store = store_factory()

    decision_id = store.write_decision(
        "s2p",
        "price_variance",
        "review",
        0.8,
        {"amount": 0.2},
    )
    store.write_outcome(decision_id, "review", True)

    assert store.get_decision(decision_id)["decision_id"] == decision_id
    assert len(store.get_verified_decisions("s2p")) == 1
