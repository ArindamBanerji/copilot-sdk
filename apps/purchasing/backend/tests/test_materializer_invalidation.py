from copilot_sdk.backend.response_materializer import ResponseMaterializer


def test_next_read_observes_mutation_without_invalidation():
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
    assert mat.get("data") == [{"value": 1}]
    store.value = 2
    assert store.reads == 1
    assert mat.get("data") == [{"value": 2}]
    assert store.reads == 2
