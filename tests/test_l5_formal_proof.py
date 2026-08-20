from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "verify_l5_completion.py"
spec = importlib.util.spec_from_file_location("verify_l5_completion_formal", SCRIPT_PATH)
assert spec and spec.loader
l5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(l5)


def complete_raw_result() -> dict[str, Any]:
    return {
        "total_expected": 15,
        "l5_centroids": {"count": 8, "valid_range": True, "invalid": [], "missing": []},
        "l5_dk_weights": {"count": 3, "valid_range": True, "invalid": [], "missing": []},
        "l5_conservation": {"count": 1, "valid_range": True, "invalid": [], "missing": []},
        "l5_edges": {"SHAPED_BY": 1, "TRIGGERED_BY": 1, "all_linked": True},
        "l5_welford": {"all_valid": True, "missing_welford": []},
        "l5_timestamps": {"sequential": True, "total_timestamps": 12},
        "total_found": 12,
        "complete": True,
        "missing_cells": [],
        "invalid_cells": [],
        "proof_status": "COMPLETE",
    }


def test_formal_proof_has_all_code_defined_conditions() -> None:
    proof = l5.formalize_proof(complete_raw_result(), graph_name="soc_graph_c9b", test_count=9)
    assert len(l5.C9_CONDITIONS) == 9
    assert len(proof["conditions"]) == 9
    assert {item["check_function"] for item in proof["conditions"]} == {
        check.__name__ for _, check, _ in l5.C9_CONDITIONS
    }


def test_formal_proof_all_conditions_pass() -> None:
    proof = l5.formalize_proof(complete_raw_result(), graph_name="soc_graph_c9b")
    assert proof["all_pass"] is True
    assert all(item["result"] == "PASS" for item in proof["conditions"])


def test_formal_proof_has_self_verifiable_sha256() -> None:
    proof = l5.formalize_proof(complete_raw_result(), graph_name="soc_graph_c9b")
    assert proof["artifact_sha256"] == l5.proof_sha256(proof)
    assert len(proof["artifact_sha256"]) == 64


def test_formal_proof_records_uncommitted_identity_and_schema() -> None:
    proof = l5.formalize_proof(complete_raw_result(), graph_name="soc_graph_c9b", test_count=42)
    assert proof["git_hash"] == "uncommitted"
    assert proof["schema_version"] == "c9-formal-proof-v1"
    assert proof["timestamp"].endswith("Z")
    assert proof["test_count"] == 42


def test_formal_proof_json_round_trip(tmp_path: Path) -> None:
    proof = l5.formalize_proof(complete_raw_result(), graph_name="soc_graph_c9b")
    output = tmp_path / "l5_proof.json"
    l5.write_proof_artifact(proof, output)
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded["all_pass"] is True
    assert loaded["artifact_sha256"] == l5.proof_sha256(loaded)


def test_cli_writes_formal_proof_file(tmp_path: Path) -> None:
    output = tmp_path / "l5_proof.json"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--json", "--output", str(output)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert output.exists(), completed.stderr
    proof = json.loads(output.read_text(encoding="utf-8"))
    assert len(proof["conditions"]) == 9
    assert proof["artifact_sha256"] == l5.proof_sha256(proof)
