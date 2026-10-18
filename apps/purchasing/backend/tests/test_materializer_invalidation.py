from copilot_sdk.backend.response_materializer import ResponseMaterializer
from types import SimpleNamespace

import pytest

from apps.purchasing.backend.app.main import _coordinated_materializer_refresh


def test_next_generation_observes_mutation_after_invalidation():
    class Store:
        value = 1
        reads = 0

        def get_all_decisions(self, domain):
            self.reads += 1
            return [{"value": self.value}]

        def get_verified_decisions(self, domain):
            return []

    store = Store()
    mat = ResponseMaterializer("test", lambda: store, {"data": lambda s: s["decisions"]})
    assert mat.get_or_refresh("data") == [{"value": 1}]
    store.value = 2
    assert store.reads == 1
    mat.invalidate()
    assert mat.get_or_refresh("data") == [{"value": 2}]
    assert store.reads == 2


@pytest.mark.asyncio
async def test_governance_mutation_refreshes_projection_before_generation():
    source = {"value": 1}
    projection = {"value": 0}

    class Store:
        def get_all_decisions(self, domain):
            return []

        def get_verified_decisions(self, domain):
            return []

    def refresh_projection():
        projection["value"] = source["value"]

    materializer = ResponseMaterializer(
        "purchasing",
        Store,
        {"conservation": lambda shared: {"projection": projection["value"]}},
    )
    app = SimpleNamespace(state=SimpleNamespace(
        materializer=materializer,
        refresh_projection_inputs=refresh_projection,
    ))
    await _coordinated_materializer_refresh(app)
    assert materializer.get("conservation") == {"projection": 1}

    source["value"] = 2
    materializer.invalidate_mutation()
    await _coordinated_materializer_refresh(app)

    assert materializer.get("conservation") == {"projection": 2}


@pytest.mark.asyncio
async def test_projection_failure_uses_stale_data_and_publishes_generation(caplog):
    projection = {"value": 7}

    class Store:
        def get_all_decisions(self, domain):
            return []

        def get_verified_decisions(self, domain):
            return []

    materializer = ResponseMaterializer(
        "purchasing",
        Store,
        {"conservation": lambda shared: {"projection": projection["value"]}},
    )
    materializer.refresh()
    materializer.invalidate_mutation()

    def failed_projection():
        raise RuntimeError("projection unavailable")

    app = SimpleNamespace(state=SimpleNamespace(
        materializer=materializer,
        refresh_projection_inputs=failed_projection,
    ))
    with caplog.at_level("WARNING"):
        await _coordinated_materializer_refresh(app)

    assert materializer.get("conservation") == {"projection": 7}
    assert "[MATERIALIZER] Projection refresh failed" in caplog.text
