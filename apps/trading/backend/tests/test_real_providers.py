"""Tier 5D domain computations and their investigation adapters."""
from copy import deepcopy
import math
import pytest

from app.evidence_providers import PROVIDER_REGISTRY
from app.investigation_config import create_evidence_provider

CASES = [["risk_reward_actual",{"actual_risk_reward":2,"planned_risk_reward":2},0.75,{"actual_risk_reward":1e+300,"planned_risk_reward":1e-300}],["emotional_indicator",{"last_trade_was_loss":True,"minutes_since_last_trade":10},0.6,{"last_trade_was_loss":True,"minutes_since_last_trade":-1e+300,"consecutive_wins":1e+300,"size_vs_rolling_avg":1e+300,"entry_at_day_extreme":True}],["signal_confidence",{"factors_with_data":8,"category_accuracy":0.9,"similar_trade_count":60},0.7666666666666667,{"similar_trade_count":1e+300}],["options_delta_exposure",{"options":{"delta":-0.35}},0.35,{"delta":-1e+300}],["options_iv_percentile",{"iv_percentile":75},0.75,{"iv_percentile":1e+300}],["options_gamma_risk",{"gamma":0.025},0.25,{"gamma":-1e+300}]]


@pytest.mark.parametrize("name,context,expected,edge", CASES, ids=[row[0] for row in CASES])
def test_factor_normal(name, context, expected, edge):
    original = deepcopy(context)
    assert PROVIDER_REGISTRY[name].provide(context) == pytest.approx(expected)
    assert context == original


@pytest.mark.parametrize("name,context,expected,edge", CASES, ids=[row[0] for row in CASES])
def test_factor_missing_data(name, context, expected, edge):
    assert PROVIDER_REGISTRY[name].provide({}) == 0.5
    assert PROVIDER_REGISTRY[name].provide({"unrelated": 123}) == 0.5


@pytest.mark.parametrize("name,context,expected,edge", CASES, ids=[row[0] for row in CASES])
def test_factor_edge(name, context, expected, edge):
    value = PROVIDER_REGISTRY[name].provide(edge)
    assert math.isfinite(value) and 0 <= value <= 1


@pytest.mark.parametrize("name", list(PROVIDER_REGISTRY))
def test_all_providers_empty_context(name):
    assert PROVIDER_REGISTRY[name].provide({}) == 0.5
    for invalid in (None, [], "bad"):
        assert PROVIDER_REGISTRY[name].provide(invalid) == 0.5


@pytest.mark.parametrize("name,context,expected,edge", CASES, ids=[row[0] for row in CASES])
def test_computation_reaches_investigation_adapter(name, context, expected, edge):
    class Source:
        def get_decision(self, decision_id, domain):
            return {"decision_id": decision_id, "entity_id": "entity-1"}
        def get_vld_context(self, entity_id):
            assert entity_id == "entity-1"
            return deepcopy(context)
    provider = create_evidence_provider(Source(), "decision-1")
    index = PROVIDER_REGISTRY[name].dimension_index
    result = provider.read_evidence("decision-1", index, name)
    assert result["value"] == pytest.approx(expected)
    assert result["evidence_tier"] == "DOMAIN_DATA"
    assert result["missing_data"] is False


@pytest.mark.parametrize("name,context,expected,edge", CASES, ids=[row[0] for row in CASES])
def test_fixture_provenance_is_preserved(name, context, expected, edge):
    source = {"trades": {"entity-1": context}}
    result = PROVIDER_REGISTRY[name].read_payload("entity-1", fixture_data=source)
    assert result["value"] == pytest.approx(expected)
    assert result["source"].startswith("SYNTHETIC:fixture:")
    assert result["evidence_tier"] == "SYNTHETIC"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), "invalid", [], {}])
def test_invalid_numeric_input_is_neutral(bad):
    for name, key in (("risk_reward_actual", "actual_risk_reward"),
                      ("signal_confidence", "category_accuracy"),
                      ("options_delta_exposure", "delta"),
                      ("options_iv_percentile", "iv_percentile"),
                      ("options_gamma_risk", "gamma")):
        assert PROVIDER_REGISTRY[name].provide({key: bad}) == 0.5


def test_risk_reward_uses_recorded_execution_prices():
    context = {"entryPrice": 100, "exitPrice": 120, "stopLoss": 90, "rrRatio": 2}
    assert PROVIDER_REGISTRY["risk_reward_actual"].provide(context) == 0.75


def test_domain_record_file_is_used(tmp_path, monkeypatch):
    import app.evidence_providers as module
    (tmp_path / "trade_metadata.json").write_text('{"entity-1": {"gamma": 0.02, "provenance": "sample"}}')
    monkeypatch.setattr(module, "DATA_DIR", tmp_path)
    result = PROVIDER_REGISTRY["options_gamma_risk"].read_payload("entity-1")
    assert result["value"] == 0.2 and result["evidence_tier"] == "SYNTHETIC"
