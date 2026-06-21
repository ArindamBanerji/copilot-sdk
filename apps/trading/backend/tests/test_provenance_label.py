from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.data_helpers import assert_no_sample_in_metric, is_sample_data
from copilot_sdk.substantiation import populate_default_registry


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
EXPECTED_TRADING_CLAIMS = {
    "P49-regime",
    "P50-market-data",
    "P53-trust-radar",
    "P54-factor-computers",
    "P55-patterns",
    "P57-trade-journal",
    "P59-ibkr-connector",
    "P60-csv-import",
    "P63-evidence-nl",
}


def _fixture_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("*.json"))


def _load_fixture(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_fixture_jsons_have_provenance():
    paths = _fixture_paths()

    assert len(paths) == 7
    for path in paths:
        data = _load_fixture(path)
        if isinstance(data, list):
            assert data, f"{path.name} should not be empty"
            assert all("provenance" in record for record in data)
        else:
            assert "provenance" in data


def test_all_provenance_is_sample():
    for path in _fixture_paths():
        data = _load_fixture(path)
        if isinstance(data, list):
            assert all(record.get("provenance") == "sample" for record in data)
        else:
            assert data.get("provenance") == "sample"


def test_synthetic_trades_have_provenance():
    trades = _load_fixture(DATA_DIR / "synthetic_trades_2000.json")

    assert len(trades) == 2000
    assert all(record.get("provenance") == "sample" for record in trades)


def test_seed_records_have_provenance():
    seed_records = _load_fixture(DATA_DIR / "trading_seed_v2.json")

    assert len(seed_records) == 40
    assert all(record.get("provenance") == "sample" for record in seed_records)


def test_is_sample_data_true():
    assert is_sample_data({"provenance": "sample"}) is True


def test_is_sample_data_false():
    assert is_sample_data({"provenance": "scraped_external"}) is False


def test_is_sample_data_missing():
    assert is_sample_data({}) is False


def test_assert_no_sample_raises():
    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        assert_no_sample_in_metric([{"provenance": "sample"}], "trust_radar")


def test_assert_no_sample_passes():
    assert_no_sample_in_metric([{"provenance": "scraped_external"}], "trust_radar")


def test_trading_claims_complete():
    registry = populate_default_registry()
    claim_ids = [claim.claim_id for claim in registry.all_claims()]
    trading_claim_ids = {claim.claim_id for claim in registry.all_claims() if claim.copilot == "trading"}

    assert len(claim_ids) == len(set(claim_ids))
    assert EXPECTED_TRADING_CLAIMS <= trading_claim_ids
