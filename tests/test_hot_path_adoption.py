from __future__ import annotations

from pathlib import Path
import inspect

import pytest

from copilot_sdk.backend.scoring_router import create_scoring_router


@pytest.mark.parametrize("copilot", ["trading", "purchasing", "dataops"])
def test_sdk_copilot_has_no_entity_context_cache_wiring(copilot: str) -> None:
    path = Path(__file__).resolve().parents[1] / "apps" / copilot / "backend" / "app" / "main.py"
    source = path.read_text(encoding="utf-8")
    assert "EntityContextCacheAdapter" not in source
    assert "entity_context_cache=" not in source


def test_scoring_router_has_no_cross_request_context_hook() -> None:
    parameters = inspect.signature(create_scoring_router).parameters
    assert "entity_context_cache" not in parameters
    assert "query_cache_invalidator" not in parameters


def test_apps_do_not_retain_entity_cache_state() -> None:
    for copilot in ("trading", "purchasing", "dataops"):
        path = Path(__file__).resolve().parents[1] / "apps" / copilot / "backend" / "app" / "main.py"
        source = path.read_text(encoding="utf-8")
        assert "app.state.entity_cache" not in source
        assert "app.state.entity_context_cache" not in source
