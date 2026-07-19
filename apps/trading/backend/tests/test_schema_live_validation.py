from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from copilot_sdk.state.invalidation import get_tab_state_cache


def test_all_schemas_validate_against_live_endpoints():
    """Every registered schema must validate its endpoint's actual response."""
    client = TestClient(app)
    cache = get_tab_state_cache("trading")
    assert cache is not None

    failures: dict[str, str] = {}
    for name, spec in cache.registrations.items():
        if spec.category == "DYNAMIC":
            continue
        response = client.get(spec.url)
        if response.status_code != 200:
            failures[name] = f"HTTP {response.status_code}"
            continue
        try:
            spec.schema.model_validate(response.json())
        except Exception as exc:  # pragma: no cover - assertion reports exact drift
            failures[name] = str(exc)

    assert failures == {}
