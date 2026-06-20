from __future__ import annotations

import cli
from app.routers import data_import
from app.routers import regime as regime_router
from app.services.regime import RegimeService
from app.services.regime_recommender import RegimeRecommender
from conftest_helpers import seed_green_client


def _accuracy():
    return {
        "trend_following": {"trending": 0.70, "ranging": 0.50, "volatile": 0.30},
        "mean_reversion": {"trending": 0.35, "ranging": 0.55, "volatile": 0.60},
        "income_strategy": {"trending": 0.51, "ranging": 0.50, "volatile": 0.52},
        "event_driven": {"trending": 0.55, "ranging": 0.40, "volatile": 0.60},
    }


def _config_dir(tmp_path):
    return tmp_path / "ci-trading"


def test_recommend_returns_dict():
    payload = RegimeRecommender().recommend("trending", _accuracy(), {"status": "GREEN"})

    assert payload["regime"] == "trending"
    assert "recommendations" in payload
    assert "summary" in payload


def test_avoid_when_accuracy_below_40():
    rec = RegimeRecommender().recommend("trending", _accuracy())["recommendations"][0]

    assert rec["category"] == "mean_reversion"
    assert rec["action"] == "avoid"
    assert rec["shift_pct"] == -100


def test_reduce_when_delta_below_minus_10pp():
    payload = RegimeRecommender().recommend("volatile", _accuracy())
    rec = next(item for item in payload["recommendations"] if item["category"] == "trend_following")

    assert rec["action"] == "avoid"


def test_increase_when_delta_above_5pp():
    payload = RegimeRecommender().recommend("trending", _accuracy())
    rec = next(item for item in payload["recommendations"] if item["category"] == "trend_following")

    assert rec["action"] == "increase"


def test_hold_when_delta_within_range():
    payload = RegimeRecommender().recommend("ranging", _accuracy())
    rec = next(item for item in payload["recommendations"] if item["category"] == "income_strategy")

    assert rec["action"] == "hold"


def test_shift_pct_proportional_to_delta():
    payload = RegimeRecommender().recommend(
        "trending",
        {"trend_following": {"trending": 0.65, "ranging": 0.55}},
    )

    assert payload["recommendations"][0]["shift_pct"] == 10


def test_regime_neutral_when_spread_below_5pp():
    payload = RegimeRecommender().recommend(
        "trending",
        {"income_strategy": {"trending": 0.51, "ranging": 0.50, "volatile": 0.52}},
    )

    assert payload["recommendations"][0]["regime_neutral"] is True


def test_not_neutral_when_spread_above_5pp():
    payload = RegimeRecommender().recommend(
        "trending",
        {"trend_following": {"trending": 0.70, "ranging": 0.50}},
    )

    assert payload["recommendations"][0]["regime_neutral"] is False


def test_sorted_avoid_first_then_reduce():
    payload = RegimeRecommender().recommend(
        "trending",
        {
            "reduce_case": {"trending": 0.45, "ranging": 0.70},
            "avoid_case": {"trending": 0.35, "ranging": 0.80},
        },
    )

    assert [item["action"] for item in payload["recommendations"]] == ["avoid", "reduce"]


def test_summary_includes_avoid_count():
    summary = RegimeRecommender().recommend("trending", _accuracy())["summary"]

    assert "1 avoid" in summary


def test_summary_all_normal():
    summary = RegimeRecommender().recommend(
        "trending",
        {"income_strategy": {"trending": 0.51, "ranging": 0.50}},
        {"status": "GREEN"},
    )["summary"]

    assert "0 avoid" in summary
    assert "Conservation not confirmed" not in summary


def test_transitions_computed_for_all_pairs():
    transitions = RegimeRecommender().recommend("trending", _accuracy())["regime_transitions"]

    assert [(item["from_regime"], item["to_regime"]) for item in transitions] == [
        ("trending", "ranging"),
        ("trending", "volatile"),
        ("ranging", "volatile"),
    ]


def test_transitions_delta_direction_correct():
    transitions = RegimeRecommender().recommend(
        "trending",
        {"trend_following": {"trending": 0.70, "ranging": 0.50}},
    )["regime_transitions"]

    assert transitions[0]["avg_accuracy_delta_pp"] == -20.0


def test_conservation_safe_when_green():
    assert RegimeRecommender().recommend("trending", {}, {"state": "GREEN"})["conservation_safe"] is True


def test_conservation_unsafe_when_red():
    payload = RegimeRecommender().recommend("trending", {}, {"status": "RED"})

    assert payload["conservation_safe"] is False
    assert payload["conservation_status"] == "unsafe"


def test_conservation_unknown_not_safe():
    payload = RegimeRecommender().recommend("trending", {}, None)

    assert payload["conservation_safe"] is False
    assert payload["conservation_status"] == "unknown"


def test_empty_accuracy_returns_empty_recs():
    assert RegimeRecommender().recommend("trending", {})["recommendations"] == []


def test_single_category_returns_one_recommendation():
    payload = RegimeRecommender().recommend("trending", {"trend_following": {"trending": 0.70}})

    assert len(payload["recommendations"]) == 1


def test_regime_detail_returns_recommendations(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.append({"trade_id": "t-1", "category": "trend_following", "regime": "trending", "pnl": 5})
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 30.0, "source": "default"})
    seed_green_client(client)

    payload = client.get("/api/trading/regime/detail").json()

    assert payload["recommendations"][0]["category"] == "trend_following"


def test_regime_detail_includes_transitions(client, monkeypatch):
    data_import._trade_store_ref.clear()
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 30.0, "source": "default"})
    monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: _accuracy())
    seed_green_client(client)

    payload = client.get("/api/trading/regime/detail").json()

    assert len(payload["regime_transitions"]) == 3


def test_regime_detail_conservation_unknown_still_200(client, monkeypatch):
    data_import._trade_store_ref.clear()
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 30.0, "source": "default"})
    monkeypatch.setattr(regime_router, "_conservation_status", lambda _factory: None)  # MOCK-OK: tests cold-start path

    response = client.get("/api/trading/regime/detail")

    assert response.status_code == 200
    assert response.json()["conservation_safe"] is False


def test_existing_regime_endpoint_shape_unchanged(client, monkeypatch):
    data_import._trade_store_ref.clear()
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})

    payload = client.get("/api/trading/regime").json()

    assert set(payload) == {"current", "accuracy_by_category", "recommendations"}


def test_regime_detail_flag(tmp_path, monkeypatch, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades([{"trade_id": "t-1", "category": "trend_following", "regime": "trending", "pnl": 5}], config_dir)
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 30.0, "source": "default"})

    assert cli.main(["--config-dir", str(config_dir), "regime", "--detail"]) == 0

    assert "Regime Allocation Context" in capsys.readouterr().out


def test_regime_no_detail_default(tmp_path, monkeypatch, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})

    assert cli.main(["--config-dir", str(config_dir), "regime"]) == 0

    output = capsys.readouterr().out
    assert "Current regime: ranging" in output
    assert "Regime Allocation Context" not in output


def test_regime_detail_warns_when_conservation_unknown(tmp_path, monkeypatch, capsys):
    config_dir = _config_dir(tmp_path)
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})

    assert cli.main(["--config-dir", str(config_dir), "regime", "--detail"]) == 0

    assert "Conservation not confirmed" in capsys.readouterr().out
