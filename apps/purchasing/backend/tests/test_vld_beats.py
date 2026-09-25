"""Demo beat wiring only: canonical factors, actual traces, explicit missing data.

v2.9 contains legacy dimension indices and unbuilt historical entity traversals.
These tests do not claim the paper's expanded action-flip narratives are live.
"""
from dataclasses import asdict
import numpy as np
import pytest

from copilot_sdk.scoring.investigation import VLDInvestigator
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from app.investigation_config import INVESTIGATION_CONFIG as CONFIG, create_evidence_provider, build_trace_links
from app.vld_preseed import seed_vld_purchasing_showcase

def test_vld_pur_1_supplier_lead_time_provider_exists():
    assert CONFIG["provider_registry"]["supplier_lead_time"].dimension_index == 5
    assert CONFIG["provider_registry"]["event_flag"].dimension_index == 3


def test_vld_pur_2_delivery_history_provider_exists():
    assert CONFIG["provider_registry"]["historical_waste"].dimension_index == 4
    provider = CONFIG["provider_registry"]["supplier_lead_time"]
    assert provider.provide({}) == 0.5


@pytest.mark.parametrize("decision_id", ["VLD-PUR-DEMAND-SPIKE", "VLD-PUR-VENDOR-CASCADE"],
                         ids=["vld_pur_1_trace_path_valid", "vld_pur_2_trace_path_valid"])
def test_vld_trace_path_valid(decision_id):
    source = seed_vld_purchasing_showcase()
    beat = source["orders"][decision_id]
    provider = create_evidence_provider(None, decision_id, fixture_data=source)
    vector = [beat["factors"][name] for name in CONFIG["factor_names"]]
    category = beat["category"]
    # Real exported geometry; no forced factor order or action.
    import json
    from pathlib import Path
    data = json.loads((Path(__file__).resolve().parents[4] / "real_centroids_v1.json").read_text())
    mu = np.asarray(data["copilots"]["purchasing"]["all_category_mu"][category])
    investigator = VLDInvestigator(mu, np.ones(len(vector)), CONFIG["factor_names"])
    trace = investigator.investigate(decision_id, category, vector, provider, budget=2,
                                     gated_sources=CONFIG["gated_sources"])
    links = build_trace_links(provider.attachment, "episode-2", [asdict(s) for s in trace.steps],
                              previous_episode={"entity_id": provider.attachment["entity_id"], "episode_id": "episode-1"})
    assert len(trace.steps) == 2
    reads = [link for link in links if link["edge"] == "DECIDED_ON"]
    assert [link["dimension"] for link in reads] == [s.dimension for s in trace.steps]
    assert [link["factor_name"] for link in reads] == [s.factor_name for s in trace.steps]
    assert len([link for link in links if link["edge"] == "MEMBER_OF"]) == len(reads)
    assert links[-1] == {"edge": "CONTINUES", "from": "episode-1", "to": "episode-2"}
