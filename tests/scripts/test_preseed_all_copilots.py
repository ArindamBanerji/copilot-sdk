from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import scripts.preseed_all_copilots as preseed


def test_preseed_learn_payload_does_not_send_privileged_preseed_flag(monkeypatch):
    seen: list[dict[str, Any]] = []

    class FakeTransport:
        def check_health(self, base_url: str):
            return True, {"ok": True}

        def check_already_seeded(self, base_url: str):
            return False, {"decisions_total": 0}

        def has_regime_checkpoint(self, base_url: str) -> bool:
            return True

        def api_post(self, base_url: str, path: str, body: dict[str, Any]):
            if path == "/api/score":
                return {"decision_id": "seed-decision", "action": "order_as_planned"}
            if path == "/api/learn":
                seen.append(body)
                return {"outcome_id": "learned", "reward": 1.0}
            if path == "/api/context/order-metadata":
                return {"ok": True}
            raise AssertionError(path)

        def verify_domain(self, config, base_url: str, successes: int, failures: int, total_reward: float) -> None:
            return None

    seed = {
        "item": "chicken_breast",
        "expected_demand": 0.7,
        "day_of_week_factor": 0.5,
        "weather_forecast": 0.4,
        "event_flag": 0.2,
        "historical_waste": 0.3,
        "supplier_lead_time": 0.6,
        "category": "produce",
        "actual_action": "order_as_planned",
    }
    monkeypatch.setattr(preseed, "load_seed", lambda path: [seed])
    monkeypatch.setattr(preseed, "expanded_seed", lambda source, *args, **kwargs: list(source))
    config = next(c for c in preseed.DOMAINS if c.name == "purchasing")
    args = SimpleNamespace(dry_run=False, force=True)

    result = preseed.seed_domain(config, args, FakeTransport())

    assert result.successes == 1
    assert seen
    assert seen[0]["context"]["seed_domain"] == "purchasing"
    assert "preseed" not in seen[0]["context"]
