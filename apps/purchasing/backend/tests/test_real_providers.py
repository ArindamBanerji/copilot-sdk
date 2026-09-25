"""Tier 5D domain computations and their investigation adapters."""
from copy import deepcopy
import math
import pytest

from app.evidence_providers import PROVIDER_REGISTRY
from app.investigation_config import create_evidence_provider

CASES = [["historical_waste",{"waste_pct":0.08},0.4,{"waste_pct":1e+300}],["supplier_lead_time",{"lead_time_days":2},0.7142857142857143,{"lead_time_days":-1e+300}],["price_memory_index",{"price_change_count":3,"months_tracked":12},0.75,{"price_change_count":1e+300,"months_tracked":1e-300}]]


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
    source = {"orders": {"entity-1": context}}
    result = PROVIDER_REGISTRY[name].read_payload("entity-1", fixture_data=source)
    assert result["value"] == pytest.approx(expected)
    assert result["source"].startswith("SYNTHETIC:fixture:")
    assert result["evidence_tier"] == "SYNTHETIC"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), "invalid", [], {}])
def test_invalid_numeric_input_is_neutral(bad):
    for name, key in (("historical_waste", "waste_pct"),
                      ("supplier_lead_time", "lead_time_days"),
                      ("price_memory_index", "price_change_count")):
        assert PROVIDER_REGISTRY[name].provide({key: bad}) == 0.5


def test_history_derives_price_change_rate():
    assert PROVIDER_REGISTRY["price_memory_index"].provide(
        {"monthly_unit_prices": [10, 10, 12, 12]}) == pytest.approx(2 / 3)


def test_zero_denominators_are_neutral():
    assert PROVIDER_REGISTRY["price_memory_index"].provide(
        {"price_change_count": 1, "months_tracked": 0}) == 0.5
    assert PROVIDER_REGISTRY["historical_waste"].provide(
        {"waste_units": 1, "received_units": 0}) == 0.5


def test_supplier_record_provides_lead_time():
    data = {"orders": {"O1": {"supplier_id": "S1"}},
            "suppliers": {"S1": {"lead_time_days": 3}}}
    value = PROVIDER_REGISTRY["supplier_lead_time"].read_payload("O1", fixture_data=data)
    assert value["value"] == pytest.approx(4 / 7)
