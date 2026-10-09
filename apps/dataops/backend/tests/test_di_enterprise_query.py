from __future__ import annotations

from pathlib import Path
from copilot_sdk.graph.memory_store import InMemoryGraphStore

from copilot_sdk.di import DataOpsEnterpriseProvider, DIQueryService




def _seed_store():
    store = InMemoryGraphStore(domain="dataops")
    decision_id = store.write_decision("dataops", "pipeline_failure", "investigate", 0.8,
        {"impact_scope": 0.5}, metadata={"decision_id": "DOPS-1", "invoice_id": "510990003"})
    store.write_outcome(decision_id, "investigate", True, domain="dataops")
    return store


def _service() -> DIQueryService:
    backend_root = Path(__file__).resolve().parents[1]
    provider = DataOpsEnterpriseProvider(
        _seed_store(),
        invoice_path=backend_root / "data" / "sap_supplier_invoices.json",
        source_profiles={
            "sap_s4hana": {"source_name": "SAP S/4HANA", "trust": 0.99, "freshness_hours": 2.0},
            "celonis_p2p": {"source_name": "Celonis P2P", "trust": 0.87, "freshness_hours": 2.0},
        },
    )
    return DIQueryService(provider, allowed_domains={"dataops"})


def test_revenue_query_uses_governed_sap_amounts_and_cross_source_attribution() -> None:
    response = _service().execute(
        {"question": "What was revenue last month?", "context": {"domain": "dataops"}}
    )

    assert response.answer == "$3,385,700"
    assert response.confidence_label == "moderate"
    assert {item.source for item in response.source_attribution} == {"SAP S/4HANA", "Celonis P2P"}
    assert "10 governed records contributed, 3 unmatched." == response.evidence
    assert any("SAP S/4HANA" in step for step in response.computation_path)


def test_unmatched_invoice_query_reports_count_and_gap() -> None:
    response = _service().execute(
        {"question": "How many unmatched invoices?", "context": {"domain": "dataops"}}
    )

    assert response.answer == "3"
    assert "3 unmatched" in response.evidence
    assert response.confidence_label == "moderate"


def test_each_query_executes_fresh() -> None:
    service = _service()
    request = {"question": "What was revenue last month?", "context": {"domain": "dataops"}}

    first = service.execute(request)
    second = service.execute(request)
    assert first.metadata.cache == "miss"
    assert second.metadata.cache == "miss"
    assert second.answer == first.answer
    assert second.metadata.query_id != first.metadata.query_id
