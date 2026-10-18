"""Completion regressions for the reserved namespace-domain representation."""

from __future__ import annotations

import inspect
from typing import Any, Callable

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.namespace import (
    BoundedGraphStoreNamespace,
    GraphStoreNamespace,
    _InternalNamespace,
    is_internal_namespace,
)


RESERVED_ALIAS = "jmns__61726d__scoring"


def _required_write_kwargs(
    method: Callable[..., Any], reserved: str = RESERVED_ALIAS,
) -> dict[str, object]:
    """Supply bindable placeholders; every tested guard must run before using them."""
    signature = inspect.signature(method)
    kwargs: dict[str, object] = {}
    for name, parameter in signature.parameters.items():
        if name == "domain":
            kwargs[name] = reserved
        elif name == "source_domain":
            kwargs[name] = reserved
        elif name == "target_domain":
            kwargs[name] = "ordinary_domain"
        elif parameter.default is inspect.Parameter.empty:
            kwargs[name] = object()
    return kwargs


def _assert_raw_reserved_domain_rejected(method: Callable[..., Any]) -> None:
    with pytest.raises(ValueError, match="reserved.*jmns__|jmns__.*reserved"):
        method(**_required_write_kwargs(method))


def _assert_forged_domain_rejected(method: Callable[..., Any]) -> None:
    class Forged(str):
        _copilot_namespace_internal = True

    with pytest.raises(ValueError, match="reserved.*jmns__|jmns__.*reserved"):
        method(**_required_write_kwargs(method, Forged(RESERVED_ALIAS)))


def test_raw_reserved_domain_decision_write_is_rejected() -> None:
    store = InMemoryGraphStore()

    with pytest.raises(ValueError, match="reserved for namespace routing"):
        store.write_decision(RESERVED_ALIAS, "risk", "accept", 0.8, {})


def test_raw_reserved_domain_governed_write_is_rejected() -> None:
    store = InMemoryGraphStore()

    with pytest.raises(ValueError, match="reserved for namespace routing"):
        store.write_governed_decision(
            "raw-alias", RESERVED_ALIAS, "risk", 0, "accept", 0, 0.8,
            [0.8], [1.0], ["factor"],
        )


def test_normal_domain_write_remains_supported() -> None:
    store = InMemoryGraphStore()
    decision_id = store.write_decision("my_domain", "risk", "accept", 0.8, {})

    assert store.get_decision(decision_id, "my_domain") is not None


def test_namespace_internal_write_round_trips_through_reserved_domain() -> None:
    primary = InMemoryGraphStore()
    namespace = BoundedGraphStoreNamespace(primary, "arm")

    decision_id = namespace.write_decision("scoring", "risk", "accept", 0.8, {})

    row = namespace.get_decision(decision_id, "scoring")
    assert row is not None
    assert row["decision_id"] == decision_id
    assert row["domain"] == "scoring"
    physical = namespace._domain("scoring")
    assert str(physical) == RESERVED_ALIAS
    assert is_internal_namespace(physical) is True


def test_two_namespaces_have_distinct_reserved_physical_domains() -> None:
    primary = InMemoryGraphStore()
    arm = GraphStoreNamespace(primary, "arm")
    hand = GraphStoreNamespace(primary, "hand")

    assert arm._domain("scoring") != hand._domain("scoring")
    assert GraphStoreNamespace._parse_physical_domain(arm._domain("scoring")) == (
        "arm", "scoring",
    )
    assert GraphStoreNamespace._parse_physical_domain(hand._domain("scoring")) == (
        "hand", "scoring",
    )


def test_raw_alias_cannot_be_created_after_namespace_owned_decision() -> None:
    primary = InMemoryGraphStore()
    namespace = BoundedGraphStoreNamespace(primary, "arm")
    namespace.write_decision("scoring", "risk", "accept", 0.8, {})

    with pytest.raises(ValueError, match="reserved for namespace routing"):
        primary.write_decision(RESERVED_ALIAS, "risk", "accept", 0.8, {})


def test_is_internal_namespace_type_identity() -> None:
    class Forged(str):
        _copilot_namespace_internal = True

    class SubForged(_InternalNamespace):
        pass

    assert is_internal_namespace(_InternalNamespace("x")) is True
    assert is_internal_namespace("x") is False
    assert is_internal_namespace(Forged("x")) is False
    assert is_internal_namespace(SubForged("x")) is False
    assert is_internal_namespace("jmns__abc__test") is False


def test_internal_namespace_passes_guard() -> None:
    store = InMemoryGraphStore()
    domain = _InternalNamespace("jmns__x__y")

    try:
        store.write_decision(domain=domain, category="risk", action="accept", confidence=0.8, factors={})
    except ValueError as exc:
        if "reserved" in str(exc).lower() or "jmns__" in str(exc):
            pytest.fail(f"guard rejected internal namespace: {exc}")
        raise


def test_forged_subclass_rejected_by_write_decision() -> None:
    _assert_forged_domain_rejected(InMemoryGraphStore().write_decision)


def test_forged_subclass_rejected_by_write_observation() -> None:
    _assert_forged_domain_rejected(InMemoryGraphStore().write_observation)


def test_forged_subclass_rejected_by_write_fingerprint() -> None:
    _assert_forged_domain_rejected(InMemoryGraphStore().write_fingerprint)


def test_save_k_utility_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().save_k_utility)


def test_save_holdout_decision_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().save_holdout_decision)


def test_enqueue_to_outbox_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().enqueue_to_outbox)


def test_write_decision_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().write_decision)


def test_write_governed_decision_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().write_governed_decision)


def test_write_outcome_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().write_outcome)


def test_write_observation_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().write_observation)


def test_append_evidence_receipt_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().append_evidence_receipt)


def test_write_conservation_status_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().write_conservation_status)


def test_write_fingerprint_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().write_fingerprint)


def test_write_centroid_checkpoint_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().write_centroid_checkpoint)


def test_write_evolution_event_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().write_evolution_event)


def test_prune_evolution_events_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().prune_evolution_events)


def test_write_transfer_pattern_rejects_raw_reserved_domain() -> None:
    store = InMemoryGraphStore()
    _assert_raw_reserved_domain_rejected(store.write_transfer_pattern)
    kwargs = _required_write_kwargs(store.write_transfer_pattern)
    kwargs["source_domain"] = "ordinary_domain"
    kwargs["target_domain"] = RESERVED_ALIAS
    with pytest.raises(ValueError, match="reserved.*jmns__|jmns__.*reserved"):
        store.write_transfer_pattern(**kwargs)  # type: ignore[arg-type]


def test_link_entity_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().link_entity)


def test_update_centroid_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().update_centroid)


def test_update_dk_weights_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().update_dk_weights)


def test_update_conservation_state_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().update_conservation_state)


def test_save_centroids_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().save_centroids)


def test_save_evolution_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().save_evolution)


def test_delete_evolution_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().delete_evolution)


def test_save_evolution_state_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().save_evolution_state)


def test_save_posterior_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().save_posterior)


def test_delete_posterior_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().delete_posterior)


def test_save_promotion_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().save_promotion)


def test_delete_promotion_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().delete_promotion)


def test_save_ledger_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().save_ledger)


def test_delete_ledger_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().delete_ledger)


def test_save_governance_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().save_governance)


def test_delete_governance_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().delete_governance)


def test_save_evolution_event_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().save_evolution_event)


def test_write_entity_enrichment_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().write_entity_enrichment)


def test_archive_old_decisions_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().archive_old_decisions)


def test_archive_decisions_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().archive_decisions)


def test_domain_scoped_reset_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().domain_scoped_reset)


def test_link_decision_to_entity_rejects_raw_reserved_domain() -> None:
    _assert_raw_reserved_domain_rejected(InMemoryGraphStore().link_decision_to_entity)
