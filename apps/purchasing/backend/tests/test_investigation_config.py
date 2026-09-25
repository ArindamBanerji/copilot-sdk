"""Canonical schema and read-only decision attachment contracts."""
import ast
import json
from pathlib import Path
import pytest

from app.investigation_config import INVESTIGATION_CONFIG as CONFIG, decision_attachment, create_evidence_provider, build_trace_links

EXPORT = json.loads((Path(__file__).resolve().parents[4] / "real_centroids_v1.json").read_text())["copilots"]["purchasing"]


def test_config_has_all_fields():
    assert {"copilot_name", "factor_names", "category_names", "action_names",
            "provider_registry", "campaign_topology", "decision_attachment"} <= CONFIG.keys()
    assert CONFIG["copilot_name"] == "purchasing"


def test_factor_names_match_centroids():
    assert CONFIG["factor_names"] == EXPORT["factor_names"]


def test_category_names_match_centroids():
    assert CONFIG["category_names"] == list(EXPORT["all_category_mu"])


def test_action_names_match_centroids():
    assert CONFIG["action_names"] == EXPORT["action_names"]


def test_campaign_topology_has_required_edges():
    assert set(CONFIG["campaign_topology"]) == {"DECIDED_ON", "MEMBER_OF", "CONTINUES"}


def test_mount_gates_match_config_and_are_sweep_readable():
    path = Path(__file__).resolve().parents[1] / "app/main.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "create_investigation_router"]
    assert len(calls) == 1
    gates = next(item.value for item in calls[0].keywords if item.arg == "gated_sources")
    assert ast.literal_eval(gates) == CONFIG["gated_sources"]


def test_decision_attachment_returns_entity():
    attached = decision_attachment({"decision_id": "D1", "metadata": {
        "order_id": "E1", "supplier_id": "P1"}})
    assert attached["lookup_id"] == "E1"
    assert attached["entity_id"] == "E1"
    assert attached["resolved"]


def test_factory_uses_domain_scoped_graph_attachment():
    class Graph:
        def get_decision(self, decision_id, domain):
            assert (decision_id, domain) == ("D1", "purchasing")
            return {"decision_id": "D1", "metadata": {"order_id": "E1"}}
    provider = create_evidence_provider(Graph(), "D1")
    assert provider.attachment["lookup_id"] == "E1"


def test_unresolved_decision_is_not_claimed_as_linked_entity():
    attachment = create_evidence_provider(None, "unknown").attachment
    assert attachment["entity_id"] == "unknown"
    assert attachment["resolved"] is False
    with pytest.raises(ValueError):
        decision_attachment({})


def test_continues_rejects_other_entity():
    attached = decision_attachment({"decision_id": "D1", "entity_id": "E1"})
    with pytest.raises(ValueError, match="same entity"):
        build_trace_links(attached, "episode-2", [],
                          previous_episode={"entity_id": "E2", "episode_id": "episode-1"})


def test_trace_links_reject_legacy_dimension_mismatch():
    attached = decision_attachment({"decision_id": "D1"})
    with pytest.raises(ValueError, match="mismatch"):
        build_trace_links(attached, "episode-1", [{"dimension": 0, "factor_name": CONFIG["factor_names"][1]}])
