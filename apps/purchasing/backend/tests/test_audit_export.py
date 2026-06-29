import json

from app.services.audit_export import AuditExportService


def test_pack_has_all_sections():
    sections = AuditExportService().generate_pack()["sections"]

    assert {"decision_trail", "conservation_proof", "override_history", "auto_approve_log", "hash_chain_verification"} <= set(sections)


def test_decision_trail_not_empty():
    assert AuditExportService().generate_pack()["sections"]["decision_trail"]


def test_conservation_proof_present():
    assert AuditExportService().generate_pack()["sections"]["conservation_proof"]["status"] == "GREEN"


def test_override_count():
    pack = AuditExportService().generate_pack()

    assert pack["total_overrides"] >= len(pack["sections"]["override_history"])


def test_hash_chain_present():
    hash_chain = AuditExportService().generate_pack()["sections"]["hash_chain_verification"]

    assert hash_chain["verified"] is True
    assert hash_chain["hash"]


def test_json_export_valid():
    payload = json.loads(AuditExportService().export_json())

    assert payload["provenance"] == "demo"


def test_csv_export_valid():
    exported = AuditExportService().export_csv_summary()

    assert exported.startswith("decision_id,timestamp,action,override,reason")
    assert "PUR-001" in exported


def test_provenance_demo():
    assert AuditExportService().generate_pack()["provenance"] == "demo"
