from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_preseed_module() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "scripts" / "preseed_all_copilots.py"
    spec = importlib.util.spec_from_file_location("preseed_all_copilots", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _args(force: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        trading_only=False,
        purchasing_only=False,
        dataops_only=False,
        dry_run=False,
        force=force,
    )


def _source_seed() -> list[dict[str, Any]]:
    return [
        {
            "category": "demo_category",
            "factors": {
                "signal_alignment": 0.7,
                "expected_demand": 0.8,
                "impact_scope": 0.9,
            },
            "trade_id": "T-1",
            "order_id": "O-1",
            "alert_id": "A-1",
        },
        {
            "category": "demo_category",
            "factors": {
                "market_regime": 0.4,
                "weather_forecast": 0.3,
                "data_freshness": 0.6,
            },
            "trade_id": "T-2",
            "order_id": "O-2",
            "alert_id": "A-2",
        },
    ]


def test_preseed_creates_200_decisions(monkeypatch) -> None:
    preseed = _load_preseed_module()

    for config in preseed.DOMAINS:
        learn_bodies: list[dict[str, Any]] = []

        def fake_api_post(base_url: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
            assert base_url == config.default_url
            if path == "/api/score":
                return {
                    "decision_id": f"{config.name}-{len(learn_bodies) + 1}",
                    "action": config.actions[0],
                    "confidence": 0.8,
                }
            if path == "/api/learn":
                learn_bodies.append(body)
                return {"reward": 1.0}
            return {}

        monkeypatch.setattr(preseed, "load_seed", lambda _path: _source_seed())
        monkeypatch.setattr(preseed, "check_health", lambda _base_url: (True, {}))
        monkeypatch.setattr(preseed, "check_already_seeded", lambda _base_url: (False, {"decisions_total": 0}))
        monkeypatch.setattr(preseed, "verify_domain", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(preseed, "api_post", fake_api_post)

        result = preseed.seed_domain(config, _args())

        assert result.total == 200
        assert result.successes == 200
        assert result.failures == 0
        assert len(learn_bodies) == 200


def test_preseed_partial_count_tops_up_only_remaining(monkeypatch) -> None:
    preseed = _load_preseed_module()
    learn_bodies: list[dict[str, Any]] = []
    config = preseed.DOMAINS[0]

    def fake_api_post(_base_url: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if path == "/api/score":
            return {
                "decision_id": f"{config.name}-{len(learn_bodies) + 1}",
                "action": config.actions[0],
                "confidence": 0.8,
            }
        if path == "/api/learn":
            learn_bodies.append(body)
            return {"reward": 1.0}
        return {}

    monkeypatch.setattr(preseed, "load_seed", lambda _path: _source_seed())
    monkeypatch.setattr(preseed, "check_health", lambda _base_url: (True, {}))
    monkeypatch.setattr(preseed, "check_already_seeded", lambda _base_url: (False, {"decisions_total": 50}))
    monkeypatch.setattr(preseed, "verify_domain", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(preseed, "api_post", fake_api_post)

    result = preseed.seed_domain(config, _args())

    assert result.total == 150
    assert result.successes == 150
    assert len(learn_bodies) == 150
    assert learn_bodies[0]["context"]["seed_index"] == 51
    assert learn_bodies[-1]["context"]["seed_index"] == 200


def test_preseed_nearly_complete_count_tops_up_one(monkeypatch) -> None:
    preseed = _load_preseed_module()
    learn_bodies: list[dict[str, Any]] = []
    config = preseed.DOMAINS[0]

    def fake_api_post(_base_url: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if path == "/api/score":
            return {
                "decision_id": f"{config.name}-{len(learn_bodies) + 1}",
                "action": config.actions[0],
                "confidence": 0.8,
            }
        if path == "/api/learn":
            learn_bodies.append(body)
            return {"reward": 1.0}
        return {}

    monkeypatch.setattr(preseed, "load_seed", lambda _path: _source_seed())
    monkeypatch.setattr(preseed, "check_health", lambda _base_url: (True, {}))
    monkeypatch.setattr(preseed, "check_already_seeded", lambda _base_url: (False, {"decisions_total": 199}))
    monkeypatch.setattr(preseed, "verify_domain", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(preseed, "api_post", fake_api_post)

    result = preseed.seed_domain(config, _args())

    assert result.total == 1
    assert result.successes == 1
    assert len(learn_bodies) == 1
    assert learn_bodies[0]["context"]["seed_index"] == 200


def test_preseed_has_overrides(monkeypatch) -> None:
    preseed = _load_preseed_module()

    for config in preseed.DOMAINS:
        learn_bodies: list[dict[str, Any]] = []
        recommended_action = config.actions[0]

        def fake_api_post(_base_url: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
            if path == "/api/score":
                return {
                    "decision_id": f"{config.name}-{len(learn_bodies) + 1}",
                    "action": recommended_action,
                    "confidence": 0.8,
                }
            if path == "/api/learn":
                learn_bodies.append(body)
                return {"reward": 1.0}
            return {}

        monkeypatch.setattr(preseed, "load_seed", lambda _path: _source_seed())
        monkeypatch.setattr(preseed, "check_health", lambda _base_url: (True, {}))
        monkeypatch.setattr(preseed, "check_already_seeded", lambda _base_url: (False, {"decisions_total": 0}))
        monkeypatch.setattr(preseed, "verify_domain", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(preseed, "api_post", fake_api_post)

        preseed.seed_domain(config, _args())
        overrides = [
            body
            for body in learn_bodies
            if body["actual_action"] != recommended_action
            and body["outcome"] == "overridden"
            and body["context"]["is_preseed_override"] is True
        ]
        confirmations = [
            body
            for body in learn_bodies
            if body["actual_action"] == recommended_action
            and body["outcome"] == "confirmed"
            and body["context"]["is_preseed_override"] is False
        ]

        assert len(overrides) == 50
        assert len(overrides) >= 24
        assert len(confirmations) == 150


def test_preseed_idempotent(monkeypatch) -> None:
    preseed = _load_preseed_module()
    calls: list[tuple[str, dict[str, Any]]] = []

    monkeypatch.setattr(preseed, "load_seed", lambda _path: _source_seed())
    monkeypatch.setattr(preseed, "check_health", lambda _base_url: (True, {}))
    monkeypatch.setattr(
        preseed,
        "check_already_seeded",
        lambda _base_url: (True, {"decisions_total": preseed.PRESEED_DECISIONS_PER_COPILOT}),
    )
    monkeypatch.setattr(preseed, "verify_domain", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(preseed, "api_post", lambda _base_url, path, body: calls.append((path, body)) or {})

    result = preseed.seed_domain(preseed.DOMAINS[0], _args())

    assert result.skipped is True
    assert result.total == 200
    assert calls == []
