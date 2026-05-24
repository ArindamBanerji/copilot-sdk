from __future__ import annotations

from datetime import datetime, timedelta, timezone

import cli
from app.routers import data_import
from app.routers import promotion as promotion_router
from app.services.promotion import PromotionService, _is_conservation_green, strategy_key


def _trade(
    index: int,
    *,
    category: str = "trend_following",
    strategy_tag: str = "momentum",
    win: bool = True,
) -> dict:
    timestamp = (datetime.now(timezone.utc) - timedelta(minutes=index)).isoformat()
    return {
        "trade_id": f"t-{index}",
        "ticker": "MSFT",
        "category": category,
        "strategy_tag": strategy_tag,
        "pnl": 10.0 if win else -10.0,
        "verified": True,
        "entry_time": timestamp,
    }


def _trades(total: int, wins: int, **kwargs) -> list[dict]:
    return [_trade(index, win=index <= wins, **kwargs) for index in range(1, total + 1)]


def _config_dir(tmp_path):
    return tmp_path / "ci-trading"


def test_default_tier_is_paper(tmp_path):
    assert PromotionService(_config_dir(tmp_path)).get_tier("trend_following:momentum") == "paper"


def test_strategy_key_format():
    assert strategy_key("trend_following", "momentum") == "trend_following:momentum"


def test_strategy_key_default_tag():
    assert strategy_key("trend_following") == "trend_following:default"


def test_promote_paper_to_small(tmp_path):
    service = PromotionService(_config_dir(tmp_path))

    events = service.evaluate(_trades(50, 30), {"status": "GREEN"})

    assert events[0]["action"] == "promote"
    assert events[0]["to_tier"] == "small_live"
    assert service.get_tier("trend_following:momentum") == "small_live"


def test_promote_paper_to_small_at_exact_threshold(tmp_path):
    service = PromotionService(_config_dir(tmp_path))

    events = service.evaluate(_trades(100, 55), {"status": "GREEN"})

    assert events[0]["to_tier"] == "small_live"


def test_no_promote_paper_to_small_below_win_rate(tmp_path):
    service = PromotionService(_config_dir(tmp_path))

    assert service.evaluate(_trades(100, 54), {"status": "GREEN"}) == []
    assert service.get_tier("trend_following:momentum") == "paper"


def test_promote_small_to_full(tmp_path):
    service = PromotionService(_config_dir(tmp_path))
    key = "trend_following:momentum"
    service._state["tiers"][key] = "small_live"

    events = service.evaluate(_trades(100, 60), {"status": "GREEN"})

    assert events[0]["to_tier"] == "full_live"
    assert service.get_tier(key) == "full_live"


def test_promote_small_to_full_at_exact_threshold(tmp_path):
    service = PromotionService(_config_dir(tmp_path))
    key = "trend_following:momentum"
    service._state["tiers"][key] = "small_live"

    events = service.evaluate(_trades(100, 58), {"status": "GREEN"})

    assert events[0]["to_tier"] == "full_live"


def test_no_promote_small_to_full_below_win_rate(tmp_path):
    service = PromotionService(_config_dir(tmp_path))
    key = "trend_following:momentum"
    service._state["tiers"][key] = "small_live"

    assert service.evaluate(_trades(100, 57), {"status": "GREEN"}) == []
    assert service.get_tier(key) == "small_live"


def test_no_promote_below_threshold(tmp_path):
    service = PromotionService(_config_dir(tmp_path))

    assert service.evaluate(_trades(50, 20), {"status": "GREEN"}) == []
    assert service.get_tier("trend_following:momentum") == "paper"


def test_no_promote_without_conservation_green(tmp_path):
    service = PromotionService(_config_dir(tmp_path))

    assert service.evaluate(_trades(50, 50), {"status": "RED"}) == []
    assert service.get_tier("trend_following:momentum") == "paper"


def test_missing_conservation_status_not_green():
    assert _is_conservation_green(None) is False
    assert _is_conservation_green({}) is False
    assert _is_conservation_green({"phase": "unknown"}) is False
    assert _is_conservation_green({"status": "GREEN"}) is True
    assert _is_conservation_green({"phase": "verified"}) is True
    assert _is_conservation_green({"overall_safe": True}) is True


def test_evaluate_no_promote_with_none_conservation(tmp_path):
    service = PromotionService(_config_dir(tmp_path))

    assert service.evaluate(_trades(50, 50), None) == []
    assert service.get_tier("trend_following:momentum") == "paper"


def test_demote_from_small_to_paper(tmp_path):
    service = PromotionService(_config_dir(tmp_path))
    key = "trend_following:momentum"
    service._state["tiers"][key] = "small_live"

    events = service.evaluate(_trades(20, 8), {"status": "GREEN"})

    assert events[0]["action"] == "demote"
    assert events[0]["to_tier"] == "paper"


def test_demote_from_full_to_small(tmp_path):
    service = PromotionService(_config_dir(tmp_path))
    key = "trend_following:momentum"
    service._state["tiers"][key] = "full_live"

    events = service.evaluate(_trades(20, 8), {"status": "GREEN"})

    assert events[0]["to_tier"] == "small_live"


def test_no_demote_above_floor(tmp_path):
    service = PromotionService(_config_dir(tmp_path))
    key = "trend_following:momentum"
    service._state["tiers"][key] = "small_live"

    assert service.evaluate(_trades(20, 10), {"status": "GREEN"}) == []
    assert service.get_tier(key) == "small_live"


def test_demote_requires_window_trades(tmp_path):
    service = PromotionService(_config_dir(tmp_path))
    key = "trend_following:momentum"
    service._state["tiers"][key] = "small_live"

    assert service.evaluate(_trades(19, 0), {"status": "GREEN"}) == []
    assert service.get_tier(key) == "small_live"


def test_history_records_events(tmp_path):
    service = PromotionService(_config_dir(tmp_path))

    service.evaluate(_trades(50, 30), {"status": "GREEN"})

    assert service.get_history()[0]["strategy_key"] == "trend_following:momentum"


def test_evaluate_returns_events_list(tmp_path):
    events = PromotionService(_config_dir(tmp_path)).evaluate(_trades(50, 30), {"status": "GREEN"})

    assert isinstance(events, list)


def test_evaluate_empty_trades(tmp_path):
    assert PromotionService(_config_dir(tmp_path)).evaluate([], {"status": "GREEN"}) == []


def test_tier_persists_to_file(tmp_path):
    service = PromotionService(_config_dir(tmp_path))

    service.evaluate(_trades(50, 30), {"status": "GREEN"})

    assert (_config_dir(tmp_path) / "promotion_tiers.json").exists()


def test_tier_loads_from_file(tmp_path):
    first = PromotionService(_config_dir(tmp_path))
    first.evaluate(_trades(50, 30), {"status": "GREEN"})

    second = PromotionService(_config_dir(tmp_path))

    assert second.get_tier("trend_following:momentum") == "small_live"


def test_promote_then_demote_round_trip(tmp_path):
    service = PromotionService(_config_dir(tmp_path))
    service.evaluate(_trades(50, 30), {"status": "GREEN"})

    events = service.evaluate(_trades(20, 8), {"status": "GREEN"})

    assert events[0]["from_tier"] == "small_live"
    assert events[0]["to_tier"] == "paper"


def test_no_duplicate_promotion_on_repeated_evaluate(tmp_path):
    service = PromotionService(_config_dir(tmp_path))

    first = service.evaluate(_trades(50, 30), {"status": "GREEN"})
    second = service.evaluate(_trades(50, 30), {"status": "GREEN"})

    assert len(first) == 1
    assert second == []


def test_promotion_endpoint_returns_strategies(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.extend(_trades(2, 1))
    monkeypatch.setattr(promotion_router, "_conservation_status", lambda _factory: {"status": "GREEN"})

    payload = client.get("/api/trading/promotion").json()

    assert payload["strategies"][0]["strategy_key"] == "trend_following:momentum"


def test_promotion_endpoint_includes_history(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.extend(_trades(50, 30))
    monkeypatch.setattr(promotion_router, "_conservation_status", lambda _factory: {"status": "GREEN"})
    client.post("/api/trading/promotion/evaluate")

    payload = client.get("/api/trading/promotion").json()

    assert payload["history"]


def test_promotion_evaluate_returns_events(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.extend(_trades(50, 30))
    monkeypatch.setattr(promotion_router, "_conservation_status", lambda _factory: {"status": "GREEN"})

    payload = client.post("/api/trading/promotion/evaluate").json()

    assert payload["events"][0]["to_tier"] == "small_live"


def test_promotion_no_trades_returns_empty(client):
    data_import._trade_store_ref.clear()

    payload = client.get("/api/trading/promotion").json()

    assert payload["strategies"] == []


def test_promotion_state_persists_between_service_instances(tmp_path):
    first = PromotionService(_config_dir(tmp_path))
    first.evaluate(_trades(50, 30), {"status": "GREEN"})

    assert PromotionService(_config_dir(tmp_path)).get_history()


def test_promote_shows_tiers(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades(_trades(2, 1), config_dir)

    assert cli.main(["--config-dir", str(config_dir), "promote"]) == 0

    output = capsys.readouterr().out
    assert "Strategy" in output
    assert "trend_following:momentum" in output


def test_cli_promote_evaluate_does_not_promote_without_conservation(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades(_trades(50, 30), config_dir)

    assert cli.main(["--config-dir", str(config_dir), "promote", "--evaluate"]) == 0

    output = capsys.readouterr().out
    assert "promotions require GREEN conservation" in output
    assert PromotionService(config_dir).get_tier("trend_following:momentum") == "paper"


def test_promote_no_strategies_message(tmp_path, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0

    assert cli.main(["--config-dir", str(config_dir), "promote"]) == 0

    assert "No strategies tracked yet" in capsys.readouterr().out
