from __future__ import annotations

import sys
from pathlib import Path

import pytest


CI_PLATFORM_ROOT = Path(__file__).resolve().parents[2] / "ci-platform"
if str(CI_PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(CI_PLATFORM_ROOT))

from ci_platform.copilot_core import EntityCache, EntityContextCacheAdapter  # noqa: E402
from copilot_sdk.backend.scoring_router import _stable_context  # noqa: E402


@pytest.mark.asyncio
async def test_context_cache_hit_on_repeated_entity() -> None:
    cache = EntityCache(max_size=200, ttl_seconds=300, source="test")
    adapter = EntityContextCacheAdapter(cache, enabled=True)
    calls = 0

    def load() -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"supplier_tier": "preferred"}

    assert await adapter.get_context("purchasing", "supplier", "supplier-1", load) == {
        "supplier_tier": "preferred"
    }
    assert await adapter.get_context("purchasing", "supplier", "supplier-1", load) == {
        "supplier_tier": "preferred"
    }
    assert calls == 1
    assert cache.stats().hits == 1
    assert cache.stats().misses == 1


@pytest.mark.asyncio
async def test_context_cache_excludes_mutable_authority_state() -> None:
    context = _stable_context(
        {
            "ticker": "SPY",
            "market_regime": "calm",
            "decision_id": "decision-1",
            "outcome": "confirmed",
            "conservation_status": "GREEN",
            "dk_weights": {"factor": 0.5},
            "l5_checkpoint": "checkpoint-1",
        }
    )
    assert context == {"ticker": "SPY", "market_regime": "calm"}

    cache = EntityCache(max_size=200, ttl_seconds=300, source="test")
    adapter = EntityContextCacheAdapter(cache, enabled=True)
    with pytest.raises(ValueError):
        await adapter.get_context("trading", "decision", "decision-1", lambda: context)


@pytest.mark.asyncio
async def test_context_cache_ttl_expires() -> None:
    now = [0.0]
    cache = EntityCache(
        max_size=200,
        ttl_seconds=1,
        source="test",
        time_fn=lambda: now[0],
    )
    adapter = EntityContextCacheAdapter(cache, enabled=True)
    await adapter.get_context("dataops", "pipeline", "pipe-1", lambda: {"owner": "ops"})
    now[0] = 2.0
    await adapter.get_context("dataops", "pipeline", "pipe-1", lambda: {"owner": "data"})
    assert cache.stats().misses == 2
    assert cache.stats().loads == 2


@pytest.mark.parametrize("copilot", ["trading", "purchasing", "dataops"])
def test_sdk_copilot_health_and_cache_wiring(copilot: str) -> None:
    path = Path(__file__).resolve().parents[1] / "apps" / copilot / "backend" / "app" / "main.py"
    source = path.read_text(encoding="utf-8")
    assert "EntityCache" in source
    assert "EntityContextCacheAdapter" in source
    assert "max_size=200" in source
    assert "ttl_seconds=300" in source
    assert "entity_context_cache=entity_context_cache" in source
    for field in ("cache_hits", "cache_misses", "cache_size"):
        assert field in source
