from types import SimpleNamespace

from app.main import _invalidate_materializer
from copilot_sdk.backend.response_materializer import ResponseMaterializer


def test_mutation_callback_invalidates_without_building():
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
    app = SimpleNamespace(state=SimpleNamespace(materializer=mat))
    mat.refresh()
    store.value = 2
    _invalidate_materializer(app)
    assert store.reads == 1
    assert mat.get("data") is None
    assert mat.get_or_refresh("data") == [{"value": 2}]
    assert store.reads == 2
