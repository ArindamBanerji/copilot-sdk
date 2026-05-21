import pytest

from copilot_sdk.evolution import (
    InMemoryVariantStore,
    VariantSpec,
)


def _variant(
    variant_id: str = "variant-a",
    family: str = "family-a",
    *,
    status: str = "active",
) -> VariantSpec:
    return VariantSpec(id=variant_id, family=family, status=status)


def test_register_and_retrieve_variant():
    store = InMemoryVariantStore()
    spec = _variant()

    store.register_variant(spec)

    retrieved = store.get_variant("variant-a")
    assert retrieved == spec
    assert retrieved is not spec


def test_register_duplicate_variant_rejected():
    store = InMemoryVariantStore()
    store.register_variant(_variant())

    with pytest.raises(ValueError, match="already registered"):
        store.register_variant(_variant())


def test_get_variants_by_family():
    store = InMemoryVariantStore()
    store.register_variant(_variant("variant-a", "family-a"))
    store.register_variant(_variant("variant-b", "family-b"))
    store.register_variant(_variant("variant-c", "family-a"))

    assert [spec.id for spec in store.get_variants_by_family("family-a")] == [
        "variant-a",
        "variant-c",
    ]


def test_get_active_variants_filters_status():
    store = InMemoryVariantStore()
    store.register_variant(_variant("variant-a", status="active"))
    store.register_variant(_variant("variant-b", status="shadow"))
    store.register_variant(_variant("variant-c", status="retired"))

    assert [spec.id for spec in store.get_active_variants()] == ["variant-a"]


def test_update_variant_status_validates_status():
    store = InMemoryVariantStore()
    store.register_variant(_variant())

    store.update_variant_status("variant-a", "retired")
    assert store.get_variant("variant-a").status == "retired"

    with pytest.raises(ValueError, match="Unsupported"):
        store.update_variant_status("variant-a", "unknown")


def test_record_outcome_updates_global_stats():
    store = InMemoryVariantStore()
    store.register_variant(_variant())

    store.record_outcome("variant-a", True)
    store.record_outcome("variant-a", False)

    stats = store.get_global_stats("variant-a")
    assert stats.successes == 1
    assert stats.failures == 1
    assert stats.total == 2
    assert stats.success_rate == 0.5


def test_record_outcome_updates_category_stats():
    store = InMemoryVariantStore()
    store.register_variant(_variant())

    store.record_outcome("variant-a", True, category="finance")
    store.record_outcome("variant-a", False, category="finance")

    stats = store.get_category_stats("finance", "variant-a")
    assert stats.category == "finance"
    assert stats.variant_id == "variant-a"
    assert stats.successes == 1
    assert stats.failures == 1
    assert stats.total == 2
    assert stats.success_rate == 0.5


def test_record_outcome_without_category_global_only():
    store = InMemoryVariantStore()
    store.register_variant(_variant())

    store.record_outcome("variant-a", True)

    assert store.get_global_stats("variant-a").total == 1
    assert store.get_all_category_stats("finance") == {}


def test_record_outcome_unknown_variant_rejected():
    store = InMemoryVariantStore()

    with pytest.raises(ValueError, match="Unknown variant"):
        store.record_outcome("missing", True)


def test_reset_clears_everything():
    store = InMemoryVariantStore()
    store.register_variant(_variant())
    store.record_outcome("variant-a", True, category="finance")

    store.reset()

    assert store.get_all_variants() == []
    assert store.get_global_stats("variant-a").total == 0
    assert store.get_all_category_stats("finance") == {}


def test_reset_stats_only_keeps_registrations():
    store = InMemoryVariantStore()
    store.register_variant(_variant())
    store.record_outcome("variant-a", True, category="finance")

    store.reset_stats_only()

    assert store.get_variant("variant-a") is not None
    assert store.get_global_stats("variant-a").total == 0
    assert store.get_all_category_stats("finance") == {}


def test_instance_local_store_no_shared_state():
    first = InMemoryVariantStore()
    second = InMemoryVariantStore()
    first.register_variant(_variant())

    assert first.get_variant("variant-a") is not None
    assert second.get_variant("variant-a") is None


def test_variant_spec_metadata_is_independent():
    first = VariantSpec(id="variant-a", family="family-a")
    second = VariantSpec(id="variant-b", family="family-a")

    first.metadata["key"] = "value"

    assert second.metadata == {}
