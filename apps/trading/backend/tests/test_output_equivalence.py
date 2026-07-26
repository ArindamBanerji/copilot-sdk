from __future__ import annotations

import asyncio
import inspect

from app.state.key_manifest import TradingKey
from app.state.trading_registry import create_trading_tab_state_cache
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer
from app.services.regime_monitor import RegimeMonitor


def run(coro):
    return asyncio.run(coro)


async def maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


def build_cache():
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=store, enable_rl=False, profile="test")
    return create_trading_tab_state_cache(
        scorer_provider=lambda: scorer,
        graph_store_factory=lambda: store,
        regime_monitor=RegimeMonitor(config=TradingPreset()),
    )


def test_all_trading_static_keys_have_schema_and_service_fn():
    cache = build_cache()

    missing = [
        key
        for key, spec in cache.registrations.items()
        if spec.schema is None or spec.service_fn is None
    ]

    assert missing == []
    assert set(cache.registrations) == {key.value for key in TradingKey}


def test_static_key_output_equivalence_to_service_fn():
    cache = build_cache()

    async def scenario():
        mismatches = {}
        for key, spec in cache.registrations.items():
            computed_raw = await maybe_await(spec.compute_fn())
            legacy_raw = await maybe_await(spec.service_fn())
            computed = spec.schema.model_validate(computed_raw)
            legacy = spec.schema.model_validate(legacy_raw)
            if computed != legacy:
                mismatches[key] = {"computed": computed.model_dump(), "legacy": legacy.model_dump()}
        return mismatches

    assert run(scenario()) == {}
