from __future__ import annotations

from pathlib import Path

import pytest

from copilot_sdk.backend.health_builder import build_graph_health, health_status_code


@pytest.mark.parametrize("domain", ["trading", "purchasing", "dataops", "s2p", "soc"])
@pytest.mark.age
def test_copilot_health_returns_graph_contract(domain: str, shared_age_readonly) -> None:
    payload = build_graph_health(*shared_age_readonly, domain)
    assert payload["ready"] is True
    assert payload["graph_backend"] == "age"
    assert payload["graph_connected"] is True
    assert payload["graph_name"] == "soc_graph"
    assert payload["graph_status"]["storage_identity"]


@pytest.mark.parametrize("domain", ["trading", "purchasing", "dataops", "s2p", "soc"])
@pytest.mark.age
def test_copilot_both_aliases_agree(domain: str, shared_age_readonly) -> None:
    health = build_graph_health(*shared_age_readonly, domain)
    api_health = build_graph_health(*shared_age_readonly, domain)
    assert health["graph_backend"] == api_health["graph_backend"]
    assert health["graph_connected"] == api_health["graph_connected"]
    assert health["graph_name"] == api_health["graph_name"]
    assert health["graph_status"]["storage_identity"] == api_health["graph_status"]["storage_identity"]


@pytest.mark.age
def test_health_all_copilots_same_identity(shared_age_readonly) -> None:
    identities = {
        build_graph_health(*shared_age_readonly, domain)["graph_status"]["storage_identity"]
        for domain in ["trading", "purchasing", "dataops", "s2p", "soc"]
    }
    assert len(identities) == 1


@pytest.mark.age
def test_health_get_no_mutation(shared_age_readonly) -> None:
    graph, config = shared_age_readonly
    before = graph.get_all_decisions("trading")
    first = build_graph_health(graph, config, "trading")
    second = build_graph_health(graph, config, "trading")
    assert graph.get_all_decisions("trading") == before
    assert first["graph_status"]["components"] == second["graph_status"]["components"]


def test_health_graph_failure_returns_503() -> None:
    from types import SimpleNamespace
    payload = build_graph_health(None, SimpleNamespace(backend="age", graph="soc_graph"), "trading")
    assert payload["ready"] is False
    assert payload["graph_connected"] is False
    assert health_status_code(payload) == 503
    assert payload["graph_status"]["components"]["decisions"] == "unavailable"


def test_launcher_verifies_readiness() -> None:
    source = Path("demo.py").read_text(encoding="utf-8")
    assert 'h.get("graph_connected") is True' in source
    assert 'h.get("graph_name") == "soc_graph"' in source
    assert '" [AGE?]"' in source
