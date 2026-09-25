"""Provider contracts, including explicit neutral fallback provenance."""
import math
import pytest

from app.evidence_providers import FACTOR_NAMES, PROVIDER_REGISTRY
from app.investigation_config import create_evidence_provider


def source():
    return {"orders": {"entity-1": {"order_id": "entity-1",
            "factors": {name: i / 7 for i, name in enumerate(FACTOR_NAMES)}}}}


@pytest.mark.parametrize("name", FACTOR_NAMES)
def test_provider_returns_float_or_none(name):
    value = PROVIDER_REGISTRY[name].read("entity-1", source())
    assert isinstance(value, float)


@pytest.mark.parametrize("name", FACTOR_NAMES)
def test_provider_output_range_0_1(name):
    value = PROVIDER_REGISTRY[name].read("entity-1", source())
    assert math.isfinite(value) and 0 <= value <= 1


@pytest.mark.parametrize("name", FACTOR_NAMES)
def test_provider_deterministic(name):
    provider = PROVIDER_REGISTRY[name]
    assert provider.read("entity-1", source()) == provider.read("entity-1", source())


def test_provider_registry_complete():
    assert list(PROVIDER_REGISTRY) == FACTOR_NAMES
    assert [p.dimension_index for p in PROVIDER_REGISTRY.values()] == list(range(7))


@pytest.mark.parametrize("name", FACTOR_NAMES[4:])
def test_missing_domain_data_is_marked(name):
    provider = PROVIDER_REGISTRY[name]
    payload = provider.read_payload("unseen-entity")
    assert payload["missing_data"] and payload["evidence_tier"] == "MISSING_DATA"
    assert payload["value"] == 0.5
    assert payload["source"].startswith("MISSING_DATA:neutral:")
    assert payload == provider.read_payload("unseen-entity")
    assert payload["value"] == provider.read_payload("different-entity")["value"]


def test_missing_supported_evidence_is_empty():
    assert PROVIDER_REGISTRY[FACTOR_NAMES[0]].read("unknown-entity") is None


def test_graph_evidence_zero_is_not_missing():
    class Graph:
        def get_vld_evidence(self, *args):
            return {"value": 0.0, "confidence": 0.9, "source": "graph"}
    payload = PROVIDER_REGISTRY[FACTOR_NAMES[0]].read_payload("entity-1", Graph())
    assert payload["value"] == 0.0
    assert payload["source"] == "graph"


def test_provider_rejects_dimension_name_mismatch():
    provider = create_evidence_provider(None, "entity-1")
    with pytest.raises(ValueError, match="canonical registry"):
        provider.read_evidence("entity-1", 1, FACTOR_NAMES[0])
    with pytest.raises(ValueError, match="different decision"):
        provider.read_evidence("other", 0, FACTOR_NAMES[0])


@pytest.mark.parametrize("value", [None, float("nan"), float("inf")])
def test_empty_or_invalid_graph_evidence_is_not_retried(value):
    class Graph:
        calls = 0
        def get_vld_evidence(self, *args):
            self.calls += 1
            return {"value": value, "confidence": 0.9, "source": "graph"}
    graph = Graph()
    assert PROVIDER_REGISTRY[FACTOR_NAMES[0]].read("unseen-entity", graph) is None
    assert graph.calls == 1


def test_neutral_fallback_is_independent_of_decision_id():
    class Graph:
        def get_decision(self, decision_id, domain):
            return {"decision_id": decision_id, "entity_id": "shared-entity"}
    a = create_evidence_provider(Graph(), "decision-a")
    b = create_evidence_provider(Graph(), "decision-b")
    name = FACTOR_NAMES[-1]
    assert a.read_evidence("decision-a", 6, name)["value"] == b.read_evidence("decision-b", 6, name)["value"]
