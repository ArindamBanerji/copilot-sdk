from __future__ import annotations

import asyncio
import re
from pathlib import Path

from app.services.regime_monitor import RegimeMonitor
from app.state.key_manifest import TradingKey
from app.state.trading_registry import TRADING_STATIC_KEYS, create_trading_tab_state_cache
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.presets.trading import TradingPreset


def run(coro):
    return asyncio.run(coro)


def build_cache():
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=store, enable_rl=False, profile="test")
    cache = create_trading_tab_state_cache(
        scorer_provider=lambda: scorer,
        graph_store_factory=lambda: store,
        regime_monitor=RegimeMonitor(config=TradingPreset()),
    )
    return cache, scorer


def test_trading_registry_registers_all_static_keys():
    cache, _ = build_cache()

    assert len(cache.registrations) == 43
    assert set(cache.registrations) == set(TRADING_STATIC_KEYS)
    assert "ticker/{ticker}" in cache.dynamic_keys
    assert "counterfactual-custom" in cache.dynamic_keys


def test_registry_covers_all_manifest_keys():
    cache, _ = build_cache()

    registered = set(cache.registrations)
    manifest = {key.value for key in TradingKey}

    assert manifest == registered, f"Missing: {manifest - registered}, Extra: {registered - manifest}"


def test_all_trading_keys_have_urls():
    cache, _ = build_cache()

    missing = [
        key
        for key, spec in cache.registrations.items()
        if not spec.url or not spec.url.startswith("/api/")
    ]

    assert missing == []


def test_no_duplicate_urls():
    cache, _ = build_cache()
    urls = [spec.url for spec in cache.registrations.values()]

    assert len(set(urls)) == len(urls)


def test_all_registry_urls_are_mounted():
    from app.main import app

    cache, _ = build_cache()
    mounted_paths = {str(getattr(route, "path", "")) for route in app.routes}

    for spec in cache.registrations.values():
        url_path = spec.url.split("?", 1)[0]
        assert url_path in mounted_paths, f"{spec.url} not mounted"


def test_every_registered_key_warms_to_ready():
    cache, _ = build_cache()

    run(cache.warm_up())
    payload = run(cache.get([key.value for key in TradingKey]))

    not_ready = {
        key: envelope
        for key, envelope in payload.items()
        if envelope["status"] != "ready"
    }
    assert not_ready == {}


def test_frontend_manifest_matches_backend_manifest():
    trading_root = Path(__file__).resolve().parents[2]
    state_file = trading_root / "frontend" / "src" / "state" / "tradingKeys.ts"
    state_source = state_file.read_text(encoding="utf-8")

    frontend = set(re.findall(r"^\s+\w+: \"([^\"]+)\"", state_source, re.M))
    backend = {key.value for key in TradingKey}

    assert frontend == backend, f"Frontend/backend manifest drift. Missing: {backend - frontend}, Extra: {frontend - backend}"


def test_screen_keys_cover_direct_screen_use_tab_data_calls():
    trading_root = Path(__file__).resolve().parents[2]
    state_file = trading_root / "frontend" / "src" / "state" / "tradingKeys.ts"
    screen_dir = trading_root / "frontend" / "src" / "screens"
    component_dir = trading_root / "frontend" / "src" / "components"
    state_source = state_file.read_text(encoding="utf-8")

    screen_lists = {
        "DashboardScreen.tsx": "DASHBOARD_KEYS",
        "PerformanceScreen.tsx": "PERFORMANCE_KEYS",
        "AnalysisScreen.tsx": "ANALYSIS_KEYS",
        "JournalScreen.tsx": "JOURNAL_KEYS",
        "LogTradeScreen.tsx": "LOG_TRADE_KEYS",
    }

    key_values = dict(re.findall(r"(\w+): \"([^\"]+)\"", state_source))

    def collect_sources(path: Path, seen: set[Path]) -> list[str]:
        if path in seen or not path.exists():
            return []
        seen.add(path)
        source = path.read_text(encoding="utf-8")
        sources = [source]
        component_imports = re.findall(r"from \"\.\./components/([^\"]+)\"", source)
        component_imports += re.findall(r"from \"\./([^\"]+)\"", source)
        for import_path in component_imports:
            component_path = component_dir / f"{import_path}.tsx"
            sources.extend(collect_sources(component_path, seen))
        return sources

    for screen_file, list_name in screen_lists.items():
        list_match = re.search(rf"export const {list_name}:.*?= \[(.*?)\];", state_source, re.S)
        assert list_match, f"{list_name} missing"
        listed_props = re.findall(r"TRADING_KEYS\.(\w+)", list_match.group(1))
        listed = {key_values[prop] for prop in listed_props}

        combined_source = "\n".join(collect_sources(screen_dir / screen_file, set()))
        used_props = re.findall(r"use(?:TabData|DerivedData)(?:<[^;]*?>)?\(TRADING_KEYS\.(\w+)", combined_source, re.S)
        used = {key_values[prop] for prop in used_props}

        assert used <= listed, f"{screen_file} uses keys not in {list_name}: {used - listed}"


def test_trading_score_invalidation_recomputes_expected_waves():
    cache, scorer = build_cache()
    scorer.score(
        {
            "signal_alignment": 0.8,
            "market_regime": 0.7,
            "position_sizing": 0.6,
            "timing_quality": 0.6,
            "risk_reward_actual": 0.7,
            "emotional_indicator": 0.5,
            "signal_confidence": 0.5,
        },
        "trend_following",
    )

    result = run(cache.invalidate("score"))

    assert result["wave1"] == ["analytics", "trajectory", "conservation"]
    assert result["wave2"] == []
    assert "promotion" in result["deleted"]
    assert "fingerprint" not in result["deleted"]
    assert "archetypes" not in result["deleted"]
    assert "correlation-config" not in result["deleted"]
    expected = {
        key
        for key, spec in cache.registrations.items()
        if spec.tier == "CRITICAL" or "score" in spec.invalidated_by
    }
    assert set(result["wave1"]) | set(result["deleted"]) == expected


def test_trading_wave1_timing_under_budget():
    cache, scorer = build_cache()
    scorer.score(
        {
            "signal_alignment": 0.8,
            "market_regime": 0.7,
            "position_sizing": 0.6,
            "timing_quality": 0.6,
            "risk_reward_actual": 0.7,
            "emotional_indicator": 0.5,
            "signal_confidence": 0.5,
        },
        "trend_following",
    )

    result = run(cache.invalidate("score"))

    assert len(result["wave1"]) == 3
    assert result["wave1_ms"] <= 300.0


def test_standard_key_invalidation_completeness():
    cache, _ = build_cache()
    known_events = {
        "score",
        "verify",
        "learn",
        "regime_break",
        "reset",
        "evolution",
        "transfer",
        "market_data_refresh",
        "metadata_update",
    }

    incomplete = [
        key
        for key, spec in cache.registrations.items()
        if spec.tier == "STANDARD" and not spec.invalidated_by
    ]
    unknown = {
        key: sorted(set(spec.invalidated_by) - known_events)
        for key, spec in cache.registrations.items()
        if spec.tier == "STANDARD" and set(spec.invalidated_by) - known_events
    }

    assert incomplete == []
    assert unknown == {}
