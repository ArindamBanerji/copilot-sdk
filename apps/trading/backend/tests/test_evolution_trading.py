from __future__ import annotations

import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import cli  # noqa: E402
from app.evolution import DEFAULT_VARIANTS, TRADING_VARIANT_DIMENSIONS, get_trading_variants  # noqa: E402


FORBIDDEN_SEMANTICS = {
    "buy",
    "sell",
    "hold",
    "strong_execution",
    "partial_execution",
    "poor_execution",
    "skip_recommended",
}


def test_trading_variant_dimensions_have_exactly_three_entries():
    assert len(TRADING_VARIANT_DIMENSIONS) == 3


def test_each_dimension_has_required_shape_and_default_value():
    for dimension in TRADING_VARIANT_DIMENSIONS:
        assert set(dimension) == {"name", "description", "values", "default"}
        assert dimension["default"] in dimension["values"]
        assert dimension["values"]


def test_get_trading_variants_returns_non_empty_defensive_copy():
    variants = get_trading_variants()
    variants[0]["status"] = "mutated"

    assert variants
    assert get_trading_variants()[0]["status"] == DEFAULT_VARIANTS[0]["status"]


def test_variants_have_required_shape_and_unique_ids():
    variants = get_trading_variants()
    ids = [variant["variant_id"] for variant in variants]

    assert len(ids) == len(set(ids))
    for variant in variants:
        assert set(variant) == {"variant_id", "name", "dimensions", "status"}
        assert variant["status"] in {"active", "shadow"}


def test_variant_dimensions_are_valid():
    valid_dimensions = {dimension["name"]: set(dimension["values"]) for dimension in TRADING_VARIANT_DIMENSIONS}

    for variant in get_trading_variants():
        assert set(variant["dimensions"]) == set(valid_dimensions)
        for name, value in variant["dimensions"].items():
            assert value in valid_dimensions[name]


def test_variants_do_not_include_directional_or_action_semantics():
    payload = str(get_trading_variants()).lower()

    for token in FORBIDDEN_SEMANTICS:
        assert token not in payload


def test_evolution_variants_route_returns_trading_variants(client):
    response = client.get("/api/evolution/variants")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "trading"
    assert payload["variants"]
    assert payload["variants"][0]["variant_id"].startswith("trd-ev-")
    assert "evidence_ordering" in payload["variants"][0]["dimensions"]


def test_cli_evolution_variants_prints_variant_info(tmp_path, capsys):
    result = cli.main(["--config-dir", str(tmp_path / "ci-trading"), "evolution", "variants"])

    assert result == 0
    output = capsys.readouterr().out
    assert "trd-ev-001" in output
    assert "Regime-first evidence" in output


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
    result = cli.main(["--config-dir", str(tmp_path / "ci-trading"), "evolution", "promote", "trd-ev-001"])

    captured = capsys.readouterr()
    assert result == 1
    assert "Variant found: trd-ev-001" in captured.out
    assert "Promotion blocked" in captured.err
    assert "/api/conservation/status" in captured.err


def test_trading_evolution_package_has_no_forbidden_imports():
    root = BACKEND_ROOT / "app" / "evolution"
    forbidden = [
        "copilot_sdk.scoring",
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
