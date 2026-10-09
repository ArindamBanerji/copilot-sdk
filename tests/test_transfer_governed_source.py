"""Governed-source enforcement for cross-copilot transfer execution."""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend import transfer_router
from copilot_sdk.backend.transfer_router import (
    _patterns_for_execute,
    create_self_transfer_router,
    create_transfer_router,
)
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.transfer import SharedPatternRegistry, TransferPattern
from copilot_sdk.transfer.category_mappings import get_mapping

SOURCE = "dataops"
TARGET = "trading"
ARTIFACT = "artifact:dataops:verified-1"


class _Scorer:
    _domain = TARGET

    def __init__(self) -> None:
        self.graph_store = InMemoryGraphStore(domain=TARGET)
        self.gae_scorer = SimpleNamespace(centroids=[[0.5]])

    def warm_start(self, patterns: list[TransferPattern]) -> dict[str, Any]:
        return {
            "applied": len(patterns),
            "score": 0.8 if patterns else 0.0,
            "source_copilots": sorted({pattern.source_copilot for pattern in patterns}),
        }


def _conservation(
    store: InMemoryGraphStore,
    domain: str,
    *,
    status: str = "GREEN",
    alpha: float = 0.9,
    q: float = 0.9,
    verified: int = 20,
    theta_min: float = 0.1,
) -> None:
    store.update_conservation_state(
        domain=domain,
        status=status,
        alpha=alpha,
        q=q,
        V=verified,
        theta_min=theta_min,
        product=alpha * q * verified,
        categories_total=3,
        categories_with_data=3,
        baseline_product=0.6,
        relative_threshold=0.1,
        complacency_flag="false",
    )


def _pattern(*, artifact_id: str = ARTIFACT) -> TransferPattern:
    mapping = get_mapping(SOURCE, TARGET)
    assert mapping
    return TransferPattern(
        pattern_id="governed-dataops-pattern",
        source_copilot=SOURCE,
        source_domain=SOURCE,
        target_domain=TARGET,
        pattern_type="centroid_delta",
        category=next(iter(mapping)),
        action="strong_execution",
        win_rate=0.8,
        centroid_delta=[0.02],
        confidence=0.9,
        metadata={"source_artifact_id": artifact_id},
    )


def _seed(
    scorer: _Scorer,
    *,
    artifact_ids: tuple[str, ...] = (ARTIFACT,),
    pattern: bool = True,
) -> None:
    store = scorer.graph_store
    _conservation(store, SOURCE)
    _conservation(store, TARGET)
    for artifact_id in artifact_ids:
        store.save_governance(SOURCE, artifact_id, {"kind": "judgment_artifact"})
    if pattern:
        SharedPatternRegistry(store, SOURCE).register(_pattern())


def _client(scorer: _Scorer, *, self_router: bool = False) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_self_transfer_router(scorer)
        if self_router
        else create_transfer_router(scorer)
    )
    return TestClient(app)


def _payload(*, artifacts: list[str] | None = None, dry_run: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source_domain": SOURCE,
        "target_domain": TARGET,
        "source_artifact_ids": artifacts if artifacts is not None else [ARTIFACT],
        "dry_run": dry_run,
    }
    return payload


@pytest.mark.parametrize("self_router", [False, True])
def test_execute_without_governed_patterns_returns_422(self_router: bool) -> None:
    scorer = _Scorer()
    path = "/api/self/transfer" if self_router else "/api/transfer/execute"

    response = _client(scorer, self_router=self_router).post(path, json=_payload())

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "No governed transfer patterns available. Register source artifacts first."
    )


def test_synthetic_pattern_helper_is_removed() -> None:
    assert not hasattr(transfer_router, "_demo_patterns_for_mapping")


def test_patterns_for_execute_returns_empty_without_governance() -> None:
    scorer = _Scorer()
    mapping = get_mapping(SOURCE, TARGET)
    assert mapping
    patterns, provenance = _patterns_for_execute(scorer, SOURCE, TARGET, mapping, None)
    assert patterns == []
    assert provenance == "governed"


def test_missing_source_artifact_returns_422() -> None:
    scorer = _Scorer()
    _seed(scorer)
    response = _client(scorer).post(
        "/api/transfer/execute",
        json=_payload(artifacts=["artifact:missing"]),
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Source artifact artifact:missing not found in governance store"
    )


def test_all_source_artifacts_present_permits_execution() -> None:
    scorer = _Scorer()
    artifacts = (ARTIFACT, "artifact:dataops:verified-2")
    _seed(scorer, artifact_ids=artifacts)
    response = _client(scorer).post(
        "/api/transfer/execute",
        json=_payload(artifacts=list(artifacts)),
    )
    assert response.status_code == 200
    assert response.json()["executed"] is True


def test_partial_source_artifacts_refuse_missing_third() -> None:
    scorer = _Scorer()
    present = (ARTIFACT, "artifact:dataops:verified-2")
    _seed(scorer, artifact_ids=present)
    response = _client(scorer).post(
        "/api/transfer/execute",
        json=_payload(artifacts=[*present, "artifact:dataops:missing-3"]),
    )
    assert response.status_code == 422
    assert "artifact:dataops:missing-3" in response.json()["detail"]


@pytest.mark.parametrize(
    ("domain", "missing_state"),
    [(SOURCE, False), (TARGET, True)],
)
def test_transfer_refuses_invalid_conservation_state(
    domain: str,
    missing_state: bool,
) -> None:
    scorer = _Scorer()
    if missing_state:
        _conservation(scorer.graph_store, SOURCE)
        scorer.graph_store.save_governance(
            SOURCE,
            ARTIFACT,
            {"kind": "judgment_artifact"},
        )
        SharedPatternRegistry(scorer.graph_store, SOURCE).register(_pattern())
    else:
        _seed(scorer)
        _conservation(
            scorer.graph_store,
            domain,
            alpha=0.1,
            q=0.1,
            verified=1,
            theta_min=1.0,
        )
    response = _client(scorer).post("/api/transfer/execute", json=_payload())
    assert response.status_code == 409
    assert response.json()["detail"] == f"Conservation threshold not met for {domain}"


def test_both_domains_above_threshold_permit_transfer() -> None:
    scorer = _Scorer()
    _seed(scorer)
    response = _client(scorer).post("/api/transfer/execute", json=_payload())
    assert response.status_code == 200
    assert response.json()["patterns_applied"] == 1
    assert response.json()["provenance"] == "governed"


def test_governance_event_includes_source_conservation() -> None:
    scorer = _Scorer()
    _seed(scorer)
    response = _client(scorer).post("/api/transfer/execute", json=_payload())
    assert response.status_code == 200
    records = [
        row
        for row in scorer.graph_store.list_governance(TARGET)
        if row.get("kind") == "transfer_checkpoint"
    ]
    assert len(records) == 1
    record = records[0]
    assert record["source_conservation_state"] == {
        "verified_count": 20,
        "correct_count": 18,
        "q": 0.9,
    }


def test_governance_event_includes_target_conservation() -> None:
    scorer = _Scorer()
    _seed(scorer)
    response = _client(scorer).post("/api/transfer/execute", json=_payload())
    assert response.status_code == 200
    records = [
        row
        for row in scorer.graph_store.list_governance(TARGET)
        if row.get("kind") == "transfer_checkpoint"
    ]
    assert len(records) == 1
    record = records[0]
    assert record["target_conservation_state"] == {
        "verified_count": 20,
        "correct_count": 18,
        "q": 0.9,
    }


def test_governance_event_includes_artifact_ids_and_mapping() -> None:
    scorer = _Scorer()
    _seed(scorer)
    response = _client(scorer).post("/api/transfer/execute", json=_payload())
    assert response.status_code == 200
    records = [
        row
        for row in scorer.graph_store.list_governance(TARGET)
        if row.get("kind") == "transfer_checkpoint"
    ]
    assert len(records) == 1
    record = records[0]
    assert record["source_artifact_ids"] == [ARTIFACT]
    assert record["mapping_details"] == get_mapping(SOURCE, TARGET)


def test_governance_event_has_timestamp_and_provenance() -> None:
    scorer = _Scorer()
    _seed(scorer)
    response = _client(scorer).post("/api/transfer/execute", json=_payload())
    assert response.status_code == 200
    records = [
        row
        for row in scorer.graph_store.list_governance(TARGET)
        if row.get("kind") == "transfer_checkpoint"
    ]
    assert len(records) == 1
    record = records[0]
    assert record["transfer_provenance"] == "governed"
    assert datetime.fromisoformat(record["validation_timestamp"]).tzinfo is not None


def test_registry_validation_accepts_registered_source_artifact() -> None:
    store = InMemoryGraphStore()
    store.save_governance(SOURCE, ARTIFACT, {"kind": "judgment_artifact"})
    registry = SharedPatternRegistry(store, SOURCE)
    assert registry.register(_pattern(), graph_store=store).pattern_id


def test_register_with_missing_artifact_raises_valueerror() -> None:
    store = InMemoryGraphStore()
    registry = SharedPatternRegistry(store, SOURCE)
    for artifact_id in ("artifact:missing", ""):
        with pytest.raises(ValueError, match="Source artifact not registered"):
            registry.register(_pattern(artifact_id=artifact_id), graph_store=store)


def test_registry_without_validation_store_remains_backward_compatible() -> None:
    store = InMemoryGraphStore()
    registry = SharedPatternRegistry(store, SOURCE)
    assert registry.register(_pattern(artifact_id="")).pattern_id
