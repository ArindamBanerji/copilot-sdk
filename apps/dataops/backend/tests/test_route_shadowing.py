from __future__ import annotations

from collections import defaultdict

from fastapi.testclient import TestClient


RESOLVED_ROUTES = {
    ("GET", "/api/health"),
    ("GET", "/api/di/profiles"),
    ("GET", "/api/dataops/di/profiles"),
    ("GET", "/api/di/intelligence-map"),
    ("GET", "/api/dataops/di/intelligence-map"),
    ("GET", "/api/dataops/di/acquisition-advice"),
    ("GET", "/api/dataops/enterprise-health"),
}


def test_dataops_app_has_no_known_shadowed_routes(client: TestClient) -> None:
    seen: dict[tuple[str, str], list[str]] = defaultdict(list)
    for route in client.app.routes:
        path = getattr(route, "path", None)
        if not isinstance(path, str):
            continue
        methods: set[str] = set(getattr(route, "methods", set()) or set())
        endpoint = getattr(route, "endpoint", None)
        endpoint_name = getattr(endpoint, "__name__", "unknown")
        for method in methods - {"HEAD", "OPTIONS"}:
            seen[(method, path)].append(endpoint_name)

    duplicates = {
        key: names
        for key, names in seen.items()
        if key in RESOLVED_ROUTES and len(names) > 1
    }
    assert duplicates == {}


def test_api_health_uses_dataops_handler(client: TestClient) -> None:
    payload = client.get("/api/health").json()

    assert payload["domain"] == "dataops"
    assert "graph_connected" in payload
    assert "cache_hits" in payload


def test_di_profile_paths_share_dataops_profile_source(client: TestClient) -> None:
    base = client.get("/api/di/profiles").json()
    prefixed = client.get("/api/dataops/di/profiles").json()

    assert base == prefixed
    assert base["total"] == 3
    assert all(source["has_profile"] for source in base["sources"])


def test_intelligence_map_paths_share_enriched_dataops_handler(client: TestClient) -> None:
    base = client.get("/api/di/intelligence-map").json()
    prefixed = client.get("/api/dataops/di/intelligence-map").json()

    assert base == prefixed
    assert "nodes" in base
    assert "gold_lines" in base


def test_dataops_acquisition_advice_uses_demo_beat_handler(client: TestClient) -> None:
    payload = client.get("/api/dataops/di/acquisition-advice").json()

    assert {"recommendations", "gold_lines", "current_sources", "conservation"} <= set(payload)
    assert payload["provenance"] == "catalog valuation; connect live history for measured ROI"


def test_enterprise_health_uses_ci_platform_handler(client: TestClient) -> None:
    payload = client.get("/api/dataops/enterprise-health").json()

    assert payload["engine_version"] == "ci-platform-connectors"
    assert "combined_impact" in payload
