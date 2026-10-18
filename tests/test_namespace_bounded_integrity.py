"""Bounded namespace regressions for opaque payloads and AGE-safe routing."""

from __future__ import annotations

import re

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.namespace import BoundedGraphStoreNamespace, GraphStoreNamespace
from copilot_sdk.graph.query import (
    DecisionGenerationChanged,
    DecisionPageRequest,
)
from copilot_sdk.graph.tenant_store import BoundedTenantScopedGraphStore


def _write(
    store: BoundedGraphStoreNamespace,
    *,
    options_domain: str = "customer-value",
    verifier_domain: str = "customer-value",
) -> str:
    return store.write_decision(
        "scoring",
        "risk",
        "accept",
        0.8,
        {},
        {
            "created_at": 1.0,
            "options_factors": {"domain": options_domain},
            "learning_metadata": {"verifier": {"domain": verifier_domain}},
        },
    )


def test_journal_options_factors_accepts_logical_domain_value() -> None:
    namespace = BoundedGraphStoreNamespace(InMemoryGraphStore(), "arm")
    _write(namespace)
    item = namespace.query_decisions("scoring", projection="journal").items[0]
    assert item["options_factors"] == {"domain": "customer-value"}


def test_journal_options_factors_preserves_old_separator_text() -> None:
    namespace = BoundedGraphStoreNamespace(InMemoryGraphStore(), "arm")
    _write(namespace, options_domain="arm::customer-value")
    item = namespace.query_decisions("scoring", projection="journal").items[0]
    assert item["options_factors"] == {"domain": "arm::customer-value"}


def test_scoring_learning_metadata_is_opaque() -> None:
    namespace = BoundedGraphStoreNamespace(InMemoryGraphStore(), "arm")
    _write(namespace)
    item = namespace.query_decisions("scoring", projection="scoring").items[0]
    assert item["learning_metadata"] == {
        "verifier": {"domain": "customer-value"},
    }


@pytest.mark.parametrize(
    ("options_domain", "verifier_domain"),
    [
        ("customer-value", "customer-value"),
        ("arm::customer-value", "customer-value"),
        ("customer-value", "arm::customer-value"),
    ],
)
def test_change_feed_preserves_opaque_projection_payloads(
    options_domain: str, verifier_domain: str,
) -> None:
    namespace = BoundedGraphStoreNamespace(InMemoryGraphStore(), "arm")
    _write(
        namespace,
        options_domain=options_domain,
        verifier_domain=verifier_domain,
    )
    event = namespace.get_decision_changes(
        "scoring", after_generation=0, projection="full",
    ).events[0]
    assert event["payload"]["options_factors"] == {"domain": options_domain}
    assert event["payload"]["learning_metadata"] == {
        "verifier": {"domain": verifier_domain},
    }


def test_physical_domain_is_age_safe_reversible_and_reserved() -> None:
    store = InMemoryGraphStore()
    namespace = GraphStoreNamespace(store, "arm_with_under_score")
    physical = namespace._domain("logical_domain_with_under_score")
    assert ":" not in physical
    assert re.fullmatch(r"[a-zA-Z0-9_-]{1,200}", physical)
    assert "__" in physical
    assert physical != "arm_with_under_score__logical_domain_with_under_score"
    assert GraphStoreNamespace._parse_physical_domain(physical) == (
        "arm_with_under_score", "logical_domain_with_under_score",
    )
    assert namespace._logical_domain(physical) == "logical_domain_with_under_score"


def test_cursor_and_generation_fence_are_preserved() -> None:
    primary = InMemoryGraphStore()
    namespace = BoundedGraphStoreNamespace(primary, "arm")
    _write(namespace)
    _write(namespace)
    generation = primary._current_generation(namespace._domain("scoring"))
    first = namespace.query_decisions(
        "scoring",
        page=DecisionPageRequest(limit=1),
        as_of_generation=generation,
    )
    assert first.next_cursor is not None
    second = namespace.query_decisions(
        "scoring",
        page=DecisionPageRequest(limit=1, after=first.next_cursor),
        as_of_generation=generation,
    )
    assert second.items
    namespace.write_decision("scoring", "risk", "accept", 0.7, {})
    with pytest.raises(DecisionGenerationChanged):
        namespace.query_decisions(
            "scoring",
            page=DecisionPageRequest(limit=1, after=first.next_cursor),
            as_of_generation=generation,
        )


def test_namespace_composed_with_tenant_keeps_tenants_isolated() -> None:
    primary = InMemoryGraphStore()
    tenant_a = BoundedGraphStoreNamespace(
        BoundedTenantScopedGraphStore(primary, "tenant-a"), "arm",
    )
    tenant_b = BoundedGraphStoreNamespace(
        BoundedTenantScopedGraphStore(primary, "tenant-b"), "arm",
    )
    _write(tenant_a)
    assert len(tenant_a.query_decisions("scoring").items) == 1
    assert tenant_b.query_decisions("scoring").items == ()
    assert tenant_b.get_decision_changes("scoring", after_generation=0).events == ()


def test_bounded_namespaces_do_not_leak() -> None:
    primary = InMemoryGraphStore()
    namespace_a = BoundedGraphStoreNamespace(primary, "arm-a")
    namespace_b = BoundedGraphStoreNamespace(primary, "arm-b")
    _write(namespace_a)
    _write(namespace_b, options_domain="other")
    assert len(namespace_a.query_decisions("scoring").items) == 1
    assert len(namespace_b.query_decisions("scoring").items) == 1
    assert namespace_a._domain("scoring") != namespace_b._domain("scoring")
    assert namespace_a.get_decision_changes("scoring", after_generation=0).events[0][
        "payload"
    ]["options_factors"] == {"domain": "customer-value"}
