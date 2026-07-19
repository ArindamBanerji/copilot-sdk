from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import RootModel

from copilot_sdk.state import (
    TabStateCache,
    create_invalidation_header_middleware,
    create_tab_state_router,
    register_tab_state_cache,
)
from copilot_sdk.scoring.mutation_lock import serialize_mutation


class DemoPayload(RootModel[Any]):
    pass


def register(cache: TabStateCache, key: str, compute, **kwargs):
    url = kwargs.pop("url", f"/api/{key}")
    cache.register(key, compute, schema=DemoPayload, service_fn=compute, url=url, **kwargs)


def test_tab_state_endpoint_returns_cached_values():
    cache = TabStateCache("demo")
    register(cache, "a", lambda: {"value": 1})
    app = FastAPI()
    app.include_router(create_tab_state_router(cache))
    client = TestClient(app)

    response = client.get("/api/demo/tab-state?keys=a")

    assert response.status_code == 200
    assert response.json()["a"] == {"data": {"value": 1}, "error": None, "status": "ready"}


def test_tab_state_endpoint_cold_warmup_once():
    calls = {"count": 0}
    cache = TabStateCache("demo")

    def compute():
        calls["count"] += 1
        return {"count": calls["count"]}

    register(cache, "a", compute)
    app = FastAPI()
    app.include_router(create_tab_state_router(cache))
    client = TestClient(app)

    assert client.get("/api/demo/tab-state?keys=a").json()["a"]["data"] == {"count": 1}
    assert client.get("/api/demo/tab-state?keys=a").json()["a"]["data"] == {"count": 1}
    assert calls["count"] == 1


def test_tab_state_endpoint_unknown_and_dynamic_key():
    cache = TabStateCache("demo")
    register(cache, "a", lambda: {"value": 1})
    cache.register_dynamic("ticker/{ticker}")
    app = FastAPI()
    app.include_router(create_tab_state_router(cache))
    client = TestClient(app)

    payload = client.get("/api/demo/tab-state?keys=missing,ticker/{ticker}").json()

    assert payload["missing"]["status"] == "unknown_key"
    assert payload["ticker/{ticker}"]["status"] == "dynamic"


def test_tab_state_endpoint_empty_keys_returns_empty_dict():
    cache = TabStateCache("demo")
    app = FastAPI()
    app.include_router(create_tab_state_router(cache))
    client = TestClient(app)

    assert client.get("/api/demo/tab-state").status_code == 200
    assert client.get("/api/demo/tab-state").json() == {}
    assert client.get("/api/demo/tab-state?keys=").json() == {}


def test_static_urls_endpoint():
    cache = TabStateCache("trading")
    register(cache, "a", lambda: {"value": 1}, url="/api/a")
    register(cache, "b", lambda: {"value": 2}, url="/api/b")
    register(cache, "c", lambda: {"value": 3}, url="/api/c")
    cache.register_dynamic("ticker/{ticker}")
    app = FastAPI()
    app.include_router(create_tab_state_router(cache))
    client = TestClient(app)

    response = client.get("/api/trading/static-urls")

    assert response.status_code == 200
    assert response.json() == ["/api/a", "/api/b", "/api/c"]


def test_static_urls_empty_copilot():
    cache = TabStateCache("trading")
    app = FastAPI()
    app.include_router(create_tab_state_router(cache))
    client = TestClient(app)

    response = client.get("/api/unknown/static-urls")

    assert response.status_code == 200
    assert response.json() == []


def test_mutation_response_sets_invalidated_urls_header():
    cache = TabStateCache("header-demo")
    register(cache, "score-a", lambda: {"value": 1}, invalidated_by=("score",), url="/api/score-a")
    register(cache, "score-b", lambda: {"value": 2}, invalidated_by=("score",), url="/api/score-b")
    register(cache, "learn-only", lambda: {"value": 3}, invalidated_by=("learn",), url="/api/learn-only", tier="COLD")
    register_tab_state_cache(cache)
    app = FastAPI()
    app.middleware("http")(
        create_invalidation_header_middleware(
            "header-demo",
            mutation_paths={("POST", "/api/demo/score"): "score"},
        )
    )

    @app.post("/api/demo/score")
    @serialize_mutation("header-demo", event="score")
    def score_mutation() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)

    response = client.post("/api/demo/score")

    assert response.status_code == 200
    assert response.headers["X-Invalidated-Urls"] == "/api/score-a,/api/score-b"
