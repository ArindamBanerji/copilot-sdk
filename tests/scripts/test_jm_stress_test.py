"""Ensure the live verifier cannot pass unexercised or mismatched contracts."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

import pytest


@pytest.fixture
def stress() -> Any:
    path = Path(__file__).resolve().parents[2] / "scripts" / "jm_stress_test.py"
    spec = importlib.util.spec_from_file_location("jm_stress_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_concurrent_validation_failures_cannot_pass(stress: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stress, "http_post", lambda *args, **kwargs: (422, {"detail": "invalid"}))
    result = stress.phase_8(SimpleNamespace())
    assert not result.passed
    assert any("Scored 0/40" in check for check in result.checks)


def test_concurrent_scores_require_exact_domain_persistence(stress: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    def post(port: int, path: str, payload: dict[str, Any], **kwargs: Any) -> tuple[int, dict[str, Any]]:
        tag = payload.get("event_id") or payload["metadata"]["entity_id"]
        return 200, {"decision_id": tag}

    monkeypatch.setattr(stress, "http_post", post)
    age = SimpleNamespace(find_decision=lambda did, domain: None if domain == "s2p" else {"domain": domain})
    result = stress.phase_8(age)
    assert not result.passed
    assert any("s2p: expected 10 persisted scores" in failure for failure in result.failures)


@pytest.mark.parametrize("identity", [None, "", "MISSING", "unavailable"])
def test_matching_missing_health_identities_fail(stress: Any, monkeypatch: pytest.MonkeyPatch, identity: Any) -> None:
    payload = {"ready": True, "graph_connected": True, "graph_backend": "age",
               "graph_name": "soc_graph", "graph_status": {"storage_identity": identity}}
    monkeypatch.setattr(stress, "http_get", lambda *args, **kwargs: (200, payload))
    assert not stress.phase_9(None).passed


def test_traversal_http_error_cannot_be_hidden_by_other_witnesses(stress: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    pattern = {"source_domain": "trading", "target_domain": "purchasing", "pattern_id": "tp-1"}
    age = SimpleNamespace(transfer_patterns=lambda: [pattern], movement_decision=lambda domain: "real-id")

    def get(port: int, path: str, **kwargs: Any) -> tuple[int, Any]:
        if "target_domain=s2p" in path:
            return 500, {"detail": "failed"}
        if "decision_movement" in path:
            return 200, [{"decision_id": "real-id"}]
        return 200, [{"transfer_pattern": pattern}]

    monkeypatch.setattr(stress, "http_get", get)
    result = stress.phase_7(age)
    assert not result.passed
    assert any("HTTP 500" in failure for failure in result.failures)


def test_inventory_comparison_excludes_archives(stress: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    counts = {"active": 880, "archived": 2531, "total": 3411, "verified": 416}
    age = SimpleNamespace(decision_counts=lambda domain: counts,
                          find_decision=lambda did, domain: {"decision_id": did, "domain": domain})

    def get(port: int, path: str, **kwargs: Any) -> tuple[int, Any]:
        if "analytics" in path:
            return 200, {"total_trades": 880}
        if "conservation" in path:
            return 200, {"verified_count": 416}
        return 200, {"source": "graph", "invoices": [{"decision_id": "s2p-1"}]}

    monkeypatch.setattr(stress, "http_get", get)
    assert stress.phase_10(age).passed


def test_decision_counts_distinguish_archive_pending_and_verified(stress: Any) -> None:
    class Client:
        async def run_query(self, *args: Any) -> list[dict[str, Any]]:
            return [
                {"archived": True, "status": "confirmed", "cnt": 2531, "ids": 2531},
                {"archived": None, "status": "pending", "cnt": 370, "ids": 370},
                {"archived": False, "status": "confirmed", "cnt": 510, "ids": 510},
            ]

    verifier = stress.AGEVerifier.__new__(stress.AGEVerifier)
    verifier._client = Client()
    assert verifier.decision_counts("trading") == {
        "active": 880, "archived": 2531, "total": 3411, "verified": 510,
    }
