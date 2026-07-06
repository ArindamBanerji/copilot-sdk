from __future__ import annotations

import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import cli  # noqa: E402
from app.evolution import (  # noqa: E402
    DEFAULT_VARIANTS,
    TRADING_EVOLVER_CONFIG,
    TRADING_VARIANT_DIMENSIONS,
    TRADING_VARIANTS,
    get_trading_variant_specs,
    get_trading_variants,
)
from copilot_sdk.scoring.presets.trading import TradingPreset  # noqa: E402


FORBIDDEN_SEMANTICS = {
    "buy",
    "sell",
    "partial_execution",
    "poor_execution",
}


EXPECTED_FAMILIES = {
    "execution_threshold",
    "revenge_cooldown",
    "alert_threshold",
    "pattern_sensitivity",
    "regime_boundary",
}


def test_trading_variant_dimensions_have_expected_entries():
    assert {dimension["name"] for dimension in TRADING_VARIANT_DIMENSIONS} == EXPECTED_FAMILIES


def test_each_dimension_has_required_shape_and_default_value():
    for dimension in TRADING_VARIANT_DIMENSIONS:
        assert set(dimension) == {"name", "description", "values", "default"}
        assert dimension["default"] in dimension["values"]
        assert dimension["values"]


def test_get_trading_variants_returns_non_empty_defensive_copy():
    variants = get_trading_variants()
    variants[0]["status"] = "mutated"
    variants[0]["metadata"]["strong_execution_confidence"] = -1

    assert variants
    assert get_trading_variants()[0]["status"] == DEFAULT_VARIANTS[0]["status"]
    assert get_trading_variants()[0]["metadata"]["strong_execution_confidence"] == 0.75


def test_variants_have_required_shape_and_unique_ids():
    variants = get_trading_variants()
    ids = [variant["variant_id"] for variant in variants]

    assert len(ids) == len(set(ids))
    assert len(variants) >= 4
    for variant in variants:
        assert set(variant) == {
            "id",
            "variant_id",
            "family",
            "version",
            "name",
            "description",
            "dimensions",
            "status",
            "metadata",
        }
        assert variant["id"] == variant["variant_id"]
        assert variant["status"] in {"active", "shadow"}


def test_variant_dimensions_are_valid():
    valid_families = {dimension["name"] for dimension in TRADING_VARIANT_DIMENSIONS}
    for variant in get_trading_variants():
        assert variant["family"] in valid_families
        assert variant["dimensions"]["family"] == variant["family"]
        assert variant["dimensions"]["version"] == variant["version"]


def test_variant_specs_define_expected_families_and_statuses():
    specs = get_trading_variant_specs()
    families = {spec.family for spec in specs}

    assert len(specs) == 10
    assert families == EXPECTED_FAMILIES
    for family in families:
        statuses = {spec.status for spec in specs if spec.family == family}
        assert statuses == {"active", "shadow"}


def test_execution_threshold_metadata_values_are_ordered():
    by_id = {variant["id"]: variant for variant in get_trading_variants()}
    v1 = by_id["EXECUTION_THRESHOLD_v1"]["metadata"]
    v2 = by_id["EXECUTION_THRESHOLD_v2"]["metadata"]

    assert v1["strong_execution_confidence"] == 0.75
    assert v1["skip_threshold"] == 0.40
    assert v2["strong_execution_confidence"] == 0.82
    assert v2["skip_threshold"] == 0.35
    assert v2["strong_execution_confidence"] > v1["strong_execution_confidence"]
    assert v2["skip_threshold"] < v1["skip_threshold"]


def test_revenge_cooldown_metadata_values_are_ordered():
    by_id = {variant["id"]: variant for variant in get_trading_variants()}
    v1 = by_id["REVENGE_COOLDOWN_v1"]["metadata"]
    v2 = by_id["REVENGE_COOLDOWN_v2"]["metadata"]

    assert v1["cooldown_minutes"] == 30
    assert v1["max_size_ratio"] == 1.3
    assert v2["cooldown_minutes"] == 45
    assert v2["max_size_ratio"] == 1.2
    assert v2["cooldown_minutes"] > v1["cooldown_minutes"]
    assert v2["max_size_ratio"] < v1["max_size_ratio"]


def test_alert_threshold_family_loads_with_correct_dimensions():
    by_id = {variant["id"]: variant for variant in get_trading_variants()}
    v1 = by_id["ALERT_THRESHOLD_v1"]["metadata"]
    v2 = by_id["ALERT_THRESHOLD_v2"]["metadata"]

    assert v1["revenge_window_minutes"] == 30
    assert v2["revenge_window_minutes"] == 45
    assert v1["candidate_revenge_window_minutes"] == [30, 45, 60]
    assert v2["candidate_revenge_window_minutes"] == [30, 45, 60]


def test_pattern_sensitivity_family_loads_with_correct_dimensions():
    by_id = {variant["id"]: variant for variant in get_trading_variants()}
    v1 = by_id["PATTERN_SENSITIVITY_v1"]["metadata"]
    v2 = by_id["PATTERN_SENSITIVITY_v2"]["metadata"]

    assert v1["overconfidence_win_streak"] == 3
    assert v2["overconfidence_win_streak"] == 4
    assert v1["drawdown_size_increase_pct"] == 30
    assert v2["drawdown_size_increase_pct"] == 40
    assert v1["candidate_overconfidence_win_streak"] == [3, 4, 5]
    assert v1["candidate_drawdown_size_increase_pct"] == [30, 40, 50]


def test_regime_boundary_family_loads_with_correct_dimensions():
    by_id = {variant["id"]: variant for variant in get_trading_variants()}
    v1 = by_id["REGIME_BOUNDARY_v1"]["metadata"]
    v2 = by_id["REGIME_BOUNDARY_v2"]["metadata"]

    assert v1["vix_low_threshold"] == 20
    assert v1["vix_high_threshold"] == 30
    assert v2["vix_low_threshold"] == 22
    assert v2["vix_high_threshold"] == 32
    assert v1["candidate_vix_low_threshold"] == [18, 20, 22]
    assert v1["candidate_vix_high_threshold"] == [28, 30, 32]


def test_trading_evolver_config_matches_map_105_requirements():
    assert TRADING_EVOLVER_CONFIG.promotion_min_samples == 50
    assert TRADING_EVOLVER_CONFIG.exploration_constant == 1.414
    assert TRADING_EVOLVER_CONFIG.promotion_improvement_threshold == 0.05
    assert TRADING_EVOLVER_CONFIG.categories == list(TradingPreset().shape.category_names)
    assert {spec.id for spec in TRADING_VARIANTS} == {variant["id"] for variant in get_trading_variants()}


def test_variants_do_not_include_directional_or_action_semantics():
    payload = str(
        [
            value
            for variant in get_trading_variants()
            for value in (variant["id"], variant["family"], variant["name"], variant["description"])
        ]
    ).lower()

    for token in FORBIDDEN_SEMANTICS:
        assert token not in payload


def test_evolution_variants_route_returns_trading_variants(client):
    response = client.get("/api/evolution/variants")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "trading"
    assert payload["variants"]
    families = {variant["family"] for variant in payload["variants"]}
    assert families == EXPECTED_FAMILIES
    assert {variant["status"] for variant in payload["variants"]} == {"active", "shadow"}


def test_cli_evolution_variants_prints_variant_info(tmp_path, capsys):
    result = cli.main(["--config-dir", str(tmp_path / "ci-trading"), "evolution", "variants"])

    assert result == 0
    output = capsys.readouterr().out
    assert "EXECUTION_TH" in output
    assert "Execution threshold baseline" in output


def test_cli_evolution_status_prints_summary(tmp_path, capsys):
    result = cli.main(["--config-dir", str(tmp_path / "ci-trading"), "evolution", "status"])

    assert result == 0
    output = capsys.readouterr().out
    assert "Trading evolution status" in output
    assert "active:" in output
    assert "shadow:" in output
    assert "last promotion: unavailable" in output


def test_cli_evolution_promote_invalid_variant_fails(tmp_path, capsys):
    result = cli.main(["--config-dir", str(tmp_path / "ci-trading"), "evolution", "promote", "missing"])

    assert result == 1
    assert "Unknown Trading evolution variant" in capsys.readouterr().err


def test_cli_evolution_promote_known_variant_fails_closed(tmp_path, capsys):
    result = cli.main(["--config-dir", str(tmp_path / "ci-trading"), "evolution", "promote", "EXECUTION_THRESHOLD_v1"])

    captured = capsys.readouterr()
    assert result == 1
    assert "Variant found: EXECUTION_THRESHOLD_v1" in captured.out
    assert "Promotion blocked" in captured.err
    assert "/api/conservation/status" in captured.err


def test_trading_evolution_package_has_no_forbidden_imports():
    root = BACKEND_ROOT / "app" / "evolution"
    forbidden = [
        "copilot_sdk.rl",
        "apps.purchasing",
        "apps.dataops",
        "apps.s2p",
        "gen-ai-roi-demo",
        "s2p-copilot",
    ]
    bad = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        bad.extend((str(path), token) for token in forbidden if token in text)

    assert bad == []


def test_non_evolution_cli_command_still_works(tmp_path):
    config_dir = tmp_path / "ci-trading"

    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
