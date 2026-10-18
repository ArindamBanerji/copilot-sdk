"""Contract tests for policy-preserving bounded graph wrappers."""

from __future__ import annotations

import sys
import types
from typing import Any, cast

import pytest

from copilot_sdk.graph.capabilities import (
    has_bounded_projection,
    require_bounded_projection_store,
)
from copilot_sdk.graph import factory as graph_factory
from copilot_sdk.graph.factory import _tenant_store, create_graph_store
from copilot_sdk.graph.legacy_signal_filter import (
    BoundedLegacySignalFilteringGraphStore,
    LegacySignalFilteringGraphStore,
)
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.namespace import (
    BoundedGraphStoreNamespace,
    GraphStoreNamespace,
)
from copilot_sdk.graph.protocol import (
    BoundedProjectionStore,
    GraphStore,
    ProtocolV2GraphStore,
)
from copilot_sdk.graph.query import DecisionFilter, DecisionPageRequest
from copilot_sdk.graph.tenant_store import (
    BoundedTenantScopedGraphStore,
    TenantScopedGraphStore,
)


def _plain_store() -> GraphStore:
    bounded = InMemoryGraphStore(domain="test")
    return cast(GraphStore, LegacySignalFilteringGraphStore(bounded, domain="test"))


def _write(
    store: Any, *, domain: str = "test", metadata: dict[str, Any] | None = None,
) -> str:
    return str(store.write_decision(
        domain, "risk", "approve", 0.8, {"cost": 0.2}, metadata or {},
    ))


def _activation_module() -> tuple[types.ModuleType, type[ValueError], type[ValueError]]:
    class ActivationAbsentError(ValueError):
        pass

    class ActivationCorruptError(ValueError):
        pass

    module = types.ModuleType("ci_platform.graph.bounded_projection_migration")
    setattr(module, "ActivationAbsentError", ActivationAbsentError)
    setattr(module, "ActivationCorruptError", ActivationCorruptError)
    return module, ActivationAbsentError, ActivationCorruptError


class TestBoundedLegacySignalFilteringGraphStore:
    def test_construction_and_protocol_membership(self) -> None:
        wrapped = BoundedLegacySignalFilteringGraphStore(InMemoryGraphStore())
        assert isinstance(wrapped, BoundedProjectionStore)

    def test_rejects_plain_graph_store(self) -> None:
        with pytest.raises(TypeError, match="BoundedProjectionStore"):
            BoundedLegacySignalFilteringGraphStore(cast(Any, _plain_store()))

    def test_all_bounded_reads_inject_legacy_filter(self) -> None:
        primary = InMemoryGraphStore()
        visible = _write(primary)
        _write(primary, metadata={"signal_detail": "", "signal_timestamp": ""})
        wrapped = BoundedLegacySignalFilteringGraphStore(primary)

        page = wrapped.query_decisions("test")
        assert [row["decision_id"] for row in page.items] == [visible]
        assert wrapped.count_decisions("test") == 1
        aggregates = wrapped.aggregate_decisions("test")
        assert aggregates[0].values["count"] == 1.0
        changes = wrapped.get_decision_changes("test", after_generation=0)
        assert [event["decision_id"] for event in changes.events] == [visible]

    def test_existing_reads_remain_filtered(self) -> None:
        primary = InMemoryGraphStore()
        visible = _write(primary)
        _write(primary, metadata={"signal_detail": False, "signal_timestamp": ""})
        wrapped = BoundedLegacySignalFilteringGraphStore(primary)
        assert [row["decision_id"] for row in wrapped.get_all_decisions("test")] == [visible]

    def test_filter_injection_preserves_other_fields(self) -> None:
        wrapped = BoundedLegacySignalFilteringGraphStore(InMemoryGraphStore())
        result = wrapped._inject_legacy_filter(DecisionFilter(categories=("risk",)))
        assert result.categories == ("risk",)
        assert result.exclude_legacy_signals is True


class TestBoundedTenantScopedGraphStore:
    def test_construction_and_protocol_membership(self) -> None:
        wrapped = BoundedTenantScopedGraphStore(InMemoryGraphStore(), "tenant-a")
        assert isinstance(wrapped, BoundedProjectionStore)

    def test_rejects_plain_graph_store(self) -> None:
        with pytest.raises(TypeError, match="BoundedProjectionStore"):
            BoundedTenantScopedGraphStore(cast(Any, _plain_store()), "tenant-a")

    def test_all_bounded_reads_inject_tenant(self) -> None:
        primary = InMemoryGraphStore()
        tenant = BoundedTenantScopedGraphStore(primary, "tenant-a")
        own = _write(tenant)
        _write(primary, metadata={"tenant_id": "tenant-b"})

        assert [row["decision_id"] for row in tenant.query_decisions("test").items] == [own]
        assert tenant.count_decisions("test") == 1
        assert tenant.aggregate_decisions("test")[0].values["count"] == 1.0
        assert [event["decision_id"] for event in tenant.get_decision_changes(
            "test", after_generation=0,
        ).events] == [own]

    def test_conflicting_tenant_rejected_for_every_bounded_read(self) -> None:
        wrapped = BoundedTenantScopedGraphStore(InMemoryGraphStore(), "tenant-a")
        conflict = DecisionFilter(tenant_id="tenant-b")
        calls = (
            lambda: wrapped.query_decisions("test", filters=conflict),
            lambda: wrapped.count_decisions("test", filters=conflict),
            lambda: wrapped.aggregate_decisions("test", filters=conflict),
            lambda: wrapped.get_decision_changes(
                "test", after_generation=0, filters=conflict,
            ),
        )
        for call in calls:
            with pytest.raises(ValueError, match="tenant conflict"):
                call()

    def test_filter_injection_preserves_other_fields(self) -> None:
        wrapped = BoundedTenantScopedGraphStore(InMemoryGraphStore(), "tenant-a")
        result = wrapped._inject_tenant_filter(
            DecisionFilter(exclude_legacy_signals=True),
        )
        assert result.tenant_id == "tenant-a"
        assert result.exclude_legacy_signals is True

    def test_inherited_write_stamps_tenant(self) -> None:
        primary = InMemoryGraphStore()
        wrapped = BoundedTenantScopedGraphStore(primary, "tenant-a")
        decision_id = _write(wrapped)
        row = primary.get_decision(decision_id, "test")
        assert row is not None and row["metadata"]["tenant_id"] == "tenant-a"

    def test_governed_write_stamps_tenant_and_preserves_metadata(self) -> None:
        primary = InMemoryGraphStore()
        wrapped = BoundedTenantScopedGraphStore(primary, "tenant-a")
        decision_id = primary.generate_decision_id("test")
        wrapped.write_governed_decision(
            decision_id, "test", "risk", 0, "approve", 0, 0.8,
            [0.8, 0.2], [0.2], ["cost"], metadata={"trace": "kept"},
        )
        row = primary.get_decision(decision_id, "test")
        assert row is not None
        assert row["metadata"]["trace"] == "kept"
        assert row["metadata"]["tenant_id"] == "tenant-a"


class TestBoundedGraphStoreNamespace:
    def test_construction_requires_v2_and_bounded(self) -> None:
        primary = InMemoryGraphStore()
        wrapped = BoundedGraphStoreNamespace(primary, "arm")
        assert isinstance(wrapped, BoundedProjectionStore)
        v2_only = GraphStoreNamespace(primary, "inner")
        assert isinstance(v2_only, ProtocolV2GraphStore)
        assert not isinstance(v2_only, BoundedProjectionStore)
        with pytest.raises(TypeError, match="BoundedProjectionStore"):
            BoundedGraphStoreNamespace(v2_only, "outer")

    def test_query_count_and_aggregate_use_physical_domain(self) -> None:
        primary = InMemoryGraphStore()
        wrapped = BoundedGraphStoreNamespace(primary, "arm")
        decision_id = _write(wrapped, domain="scoring")
        page = wrapped.query_decisions("scoring")
        assert page.items[0]["decision_id"] == decision_id
        assert page.items[0]["domain"] == "scoring"
        assert primary.get_decision(decision_id, wrapped._domain("scoring")) is not None
        assert wrapped.count_decisions("scoring") == 1
        assert wrapped.aggregate_decisions("scoring")[0].values["count"] == 1.0

    def test_query_preserves_cursor_and_generation_fence(self) -> None:
        primary = InMemoryGraphStore()
        wrapped = BoundedGraphStoreNamespace(primary, "arm")
        _write(wrapped, domain="scoring")
        _write(wrapped, domain="scoring")
        generation = primary._current_generation(wrapped._domain("scoring"))
        first = wrapped.query_decisions(
            "scoring", page=DecisionPageRequest(limit=1),
            as_of_generation=generation,
        )
        assert first.next_cursor is not None
        second = wrapped.query_decisions(
            "scoring",
            page=DecisionPageRequest(limit=1, after=first.next_cursor),
            as_of_generation=generation,
        )
        assert second.items and second.next_cursor is None

    def test_change_feed_rewrites_event_and_payload_domains_only(self) -> None:
        primary = InMemoryGraphStore()
        wrapped = BoundedGraphStoreNamespace(primary, "arm")
        _write(
            wrapped, domain="scoring",
            metadata={"domain": "user-payload", "note": "arm::scoring"},
        )
        page = wrapped.get_decision_changes("scoring", after_generation=0)
        event = page.events[0]
        assert event["domain"] == "scoring"
        assert event["payload"]["domain"] == "scoring"
        assert event["payload"]["metadata"]["domain"] == "user-payload"
        assert event["payload"]["metadata"]["note"] == "arm::scoring"
        assert page.next_generation == page.current_generation == 1

    def test_existing_namespace_reads_remain_isolated(self) -> None:
        primary = InMemoryGraphStore()
        wrapped = BoundedGraphStoreNamespace(primary, "arm")
        decision_id = _write(wrapped, domain="scoring")
        row = wrapped.get_decision(decision_id, "scoring")
        assert row is not None and row["domain"] == "scoring"


@pytest.mark.parametrize("wrapper", [
    lambda store: LegacySignalFilteringGraphStore(store),
    lambda store: TenantScopedGraphStore(store, "tenant-a"),
    lambda store: GraphStoreNamespace(store, "arm"),
])
@pytest.mark.parametrize(
    "name", ["query_decisions", "aggregate_decisions", "get_decision_changes"],
)
def test_legacy_variants_block_bounded_only_reads(
    wrapper: Any, name: str,
) -> None:
    value = wrapper(InMemoryGraphStore())
    with pytest.raises(AttributeError, match="bounded projection"):
        getattr(value, name)


@pytest.mark.parametrize("tenant_enabled", [False, True])
def test_factory_selector_preserves_bounded_capability(tenant_enabled: bool) -> None:
    env = {"TENANT_ISOLATION_ENABLED": str(tenant_enabled).lower()}
    result = _tenant_store(InMemoryGraphStore(), env, "test")
    expected = BoundedTenantScopedGraphStore if tenant_enabled else BoundedLegacySignalFilteringGraphStore
    assert isinstance(result, expected)
    assert isinstance(result, BoundedProjectionStore)


@pytest.mark.parametrize("tenant_enabled", [False, True])
def test_factory_selector_retains_legacy_fallback(tenant_enabled: bool) -> None:
    env = {"TENANT_ISOLATION_ENABLED": str(tenant_enabled).lower()}
    result = _tenant_store(_plain_store(), env, "test")
    expected = TenantScopedGraphStore if tenant_enabled else LegacySignalFilteringGraphStore
    assert type(result) is expected
    assert not isinstance(result, BoundedProjectionStore)


def test_capability_helpers() -> None:
    bounded = InMemoryGraphStore()
    assert has_bounded_projection(bounded)
    assert require_bounded_projection_store(bounded, feature="journal") is bounded
    plain = _plain_store()
    assert not has_bounded_projection(plain)
    with pytest.raises(RuntimeError, match="journal.*LegacySignalFilteringGraphStore"):
        require_bounded_projection_store(plain, feature="journal")


def test_age_factory_selects_activated_bounded_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    class LegacyAdapter:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    class BoundedAdapter(InMemoryGraphStore):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(domain=str(kwargs.pop("domain")))
            self.__dict__.update(kwargs)

    module = types.ModuleType("ci_platform.graph.age_sdk_adapter")
    setattr(module, "AGEGraphStoreAdapter", LegacyAdapter)
    setattr(module, "BoundedAGEGraphStoreAdapter", BoundedAdapter)
    monkeypatch.setitem(sys.modules, "ci_platform.graph.age_sdk_adapter", module)
    activation_module, _, _ = _activation_module()
    monkeypatch.setitem(
        sys.modules,
        "ci_platform.graph.bounded_projection_migration",
        activation_module,
    )
    result = create_graph_store(
        backend="age", domain="s2p", dsn="postgresql://example/test",
        graph_name="product_graph", profile="test", env={},
    )
    assert isinstance(result, BoundedLegacySignalFilteringGraphStore)
    assert isinstance(result.graph_primary, BoundedAdapter)


def test_age_factory_uses_legacy_when_marker_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    activation_module, ActivationAbsentError, _ = _activation_module()

    class LegacyAdapter:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    class InactiveBoundedAdapter:
        def __init__(self, **kwargs: Any) -> None:
            raise ActivationAbsentError(
                "bounded projections are not activated for domain 's2p'"
            )

    module = types.ModuleType("ci_platform.graph.age_sdk_adapter")
    setattr(module, "AGEGraphStoreAdapter", LegacyAdapter)
    setattr(module, "BoundedAGEGraphStoreAdapter", InactiveBoundedAdapter)
    monkeypatch.setitem(sys.modules, "ci_platform.graph.age_sdk_adapter", module)
    monkeypatch.setitem(
        sys.modules,
        "ci_platform.graph.bounded_projection_migration",
        activation_module,
    )
    result = create_graph_store(
        backend="age", domain="s2p", dsn="postgresql://example/test",
        graph_name="product_graph", profile="test", env={},
    )
    assert type(result) is LegacySignalFilteringGraphStore
    assert isinstance(result.graph_primary, LegacyAdapter)


def test_age_factory_propagates_corrupt_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    activation_module, _, ActivationCorruptError = _activation_module()

    class LegacyAdapter:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    class CorruptBoundedAdapter:
        def __init__(self, **kwargs: Any) -> None:
            raise ActivationCorruptError("duplicate bounded activation markers")

    module = types.ModuleType("ci_platform.graph.age_sdk_adapter")
    setattr(module, "AGEGraphStoreAdapter", LegacyAdapter)
    setattr(module, "BoundedAGEGraphStoreAdapter", CorruptBoundedAdapter)
    monkeypatch.setitem(sys.modules, "ci_platform.graph.age_sdk_adapter", module)
    monkeypatch.setitem(
        sys.modules,
        "ci_platform.graph.bounded_projection_migration",
        activation_module,
    )
    with pytest.raises(ActivationCorruptError, match="duplicate bounded activation"):
        create_graph_store(
            backend="age", domain="s2p", dsn="postgresql://example/test",
            graph_name="product_graph", profile="test", env={},
        )


def test_age_factory_falls_back_when_bounded_adapter_import_fails(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class LegacyAdapter:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

        def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
            return [{"decision_id": "legacy", "domain": domain, "metadata": {}}]

        def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]:
            return []

    module = types.ModuleType("ci_platform.graph.age_sdk_adapter")
    setattr(module, "AGEGraphStoreAdapter", LegacyAdapter)
    original_import = graph_factory.importlib.import_module
    age_imports = 0

    def import_with_bounded_failure(name: str, package: str | None = None) -> Any:
        nonlocal age_imports
        if name == "ci_platform.graph.age_sdk_adapter":
            age_imports += 1
            if age_imports == 1:
                return module
            raise ImportError("bounded adapter unavailable")
        return original_import(name, package)

    monkeypatch.setattr(
        graph_factory.importlib,
        "import_module",
        import_with_bounded_failure,
    )
    with caplog.at_level("WARNING", logger="copilot_sdk.graph.factory"):
        result = create_graph_store(
            backend="age",
            domain="s2p",
            dsn="postgresql://example/test",
            graph_name="product_graph",
            profile="test",
            env={},
        )

    assert type(result) is LegacySignalFilteringGraphStore
    assert isinstance(result.graph_primary, LegacyAdapter)
    assert result.count_decisions("s2p") == 1
    assert not isinstance(result, BoundedProjectionStore)
    assert "falling back to legacy AGE" in caplog.text
