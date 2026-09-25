from __future__ import annotations

from typing import cast

import numpy as np

from copilot_sdk.scoring.investigation import EvidenceProvider, InvestigationTrace, VLDInvestigator
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.situation_classifier import SituationClassifier

from app.evidence_provider import PurchasingEvidenceProvider
from app.vld_preseed import seed_vld_purchasing_showcase


PRESET = PurchasingPreset()
FACTOR_NAMES = list(PRESET.shape.factor_names)
ACTION_NAMES = list(PRESET.shape.action_names)


def test_evidence_provider_protocol() -> None:
    provider = PurchasingEvidenceProvider(seed_vld_purchasing_showcase(), "VLD-PUR-DEMAND-SPIKE")
    assert isinstance(provider, EvidenceProvider)


def test_evidence_vendor_reliability() -> None:
    provider = PurchasingEvidenceProvider(seed_vld_purchasing_showcase(), "VLD-PUR-VENDOR-CASCADE")
    evidence = provider.read_evidence("VLD-PUR-VENDOR-CASCADE", 4, "historical_waste")
    assert evidence is not None
    assert evidence["source"] == "vendor_tracker"
    assert evidence["value"] > 0.70
    assert evidence["reliability_score"] < 0.30
    assert evidence["quality_incidents_30d"] == 2


def test_evidence_substitution() -> None:
    provider = PurchasingEvidenceProvider(seed_vld_purchasing_showcase(), "VLD-PUR-DEMAND-SPIKE")
    evidence = provider.read_evidence("VLD-PUR-DEMAND-SPIKE", 6, "price_memory_index")
    assert evidence is not None
    assert evidence["source"] == "vendor_catalog"
    assert evidence["value"] > 0.80
    assert evidence["alternate_lead_days"] == 2
    assert evidence["premium_pct"] == 0.08


def test_evidence_empty_branch() -> None:
    provider = PurchasingEvidenceProvider(seed_vld_purchasing_showcase(), "missing")
    assert provider.read_evidence("missing", 0, "expected_demand") is None


def test_evidence_all_seven_factors() -> None:
    provider = PurchasingEvidenceProvider(seed_vld_purchasing_showcase(), "VLD-PUR-DEMAND-SPIKE")
    seen = {
        name: provider.read_evidence("VLD-PUR-DEMAND-SPIKE", index, name)
        for index, name in enumerate(FACTOR_NAMES)
    }
    assert set(seen) == set(FACTOR_NAMES)
    assert all(evidence is not None for evidence in seen.values())


def test_preseed_creates_three_orders() -> None:
    seeded = seed_vld_purchasing_showcase({})
    assert set(seeded["orders"]) == {
        "VLD-PUR-DEMAND-SPIKE",
        "VLD-PUR-VENDOR-CASCADE",
        "VLD-PUR-S1-STANDARD",
    }


def test_preseed_idempotent() -> None:
    seeded: dict = {}
    seed_vld_purchasing_showcase(seeded)
    seed_vld_purchasing_showcase(seeded)
    assert len(seeded["orders"]) == 3
    assert len(seeded["suppliers"]) == 3


def test_demand_spike() -> None:
    data = seed_vld_purchasing_showcase()
    trace = _run_demand_spike(data)
    assert ACTION_NAMES[trace.surface_action] == "order_more"
    assert ACTION_NAMES[trace.final_action] == "order_less"
    assert [step.factor_name for step in trace.steps[:2]] == ["supplier_lead_time", "price_memory_index"]
    assert {step.evidence_source for step in trace.steps} >= {"lead_time_tracker", "vendor_catalog"}


def test_vendor_cascade() -> None:
    data = seed_vld_purchasing_showcase()
    order = data["orders"]["VLD-PUR-VENDOR-CASCADE"]
    investigator = VLDInvestigator(_vendor_cascade_mu(), np.full(7, 0.16), FACTOR_NAMES, tau=0.05)
    trace = investigator.investigate(
        "VLD-PUR-VENDOR-CASCADE",
        order["category"],
        _vector(order),
        PurchasingEvidenceProvider(data, "VLD-PUR-VENDOR-CASCADE"),
        budget=2,
        K_weights=np.array([0.1, 0.1, 0.1, 0.1, 100.0, 1.0, 0.1]),
        gated_sources={"vendor_tracker", "lead_time_tracker"},
    )
    assert ACTION_NAMES[trace.surface_action] == "order_as_planned"
    assert ACTION_NAMES[trace.final_action] == "skip"
    assert [step.factor_name for step in trace.steps[:2]] == ["historical_waste", "supplier_lead_time"]
    assert {step.evidence_source for step in trace.steps} >= {"vendor_tracker", "lead_time_tracker"}


def test_s1_conservation() -> None:
    data = seed_vld_purchasing_showcase()
    order = data["orders"]["VLD-PUR-S1-STANDARD"]
    mu = _s1_mu()
    investigator = VLDInvestigator(mu, np.full(7, 0.12), FACTOR_NAMES, tau=0.05)
    vector = _vector(order)
    _, probabilities = investigator.score(vector)
    q_surface = investigator.compute_Q(vector, probabilities)
    assessment = SituationClassifier().classify(vector, mu, np.full(7, 0.12), probabilities, q_surface)
    assert assessment.situation == "S1"
    assert assessment.recommended_budget == 0
    trace = investigator.investigate(
        "VLD-PUR-S1-STANDARD",
        order["category"],
        vector,
        PurchasingEvidenceProvider(data, "VLD-PUR-S1-STANDARD"),
        budget=assessment.recommended_budget,
    )
    assert trace.steps == []


def test_demand_spike_trace_order() -> None:
    trace = _run_demand_spike(seed_vld_purchasing_showcase())
    assert len(trace.steps) >= 2
    assert trace.steps[0].factor_name == "supplier_lead_time"
    assert trace.steps[1].factor_name == "price_memory_index"


def test_investigation_health(client) -> None:
    response = client.get("/api/investigation/health")
    assert response.status_code == 200
    assert response.json()["investigation_available"] is True


def test_investigation_endpoint(client) -> None:
    response = client.post(
        "/api/investigation/investigate",
        json={
            "decision_id": "VLD-PUR-DEMAND-SPIKE",
            "category": "dry_goods",
            "factor_vector": list(seed_vld_purchasing_showcase()["orders"]["VLD-PUR-DEMAND-SPIKE"]["factors"].values()),
            "budget": 2,
            "use_K": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision_id"] == "VLD-PUR-DEMAND-SPIKE"
    assert isinstance(payload["steps"], list)
    assert "contrast" in payload


def _run_demand_spike(data: dict) -> InvestigationTrace:
    order = data["orders"]["VLD-PUR-DEMAND-SPIKE"]
    investigator = VLDInvestigator(_demand_spike_mu(), np.full(7, 0.16), FACTOR_NAMES, tau=0.05)
    return investigator.investigate(
        "VLD-PUR-DEMAND-SPIKE",
        order["category"],
        _vector(order),
        PurchasingEvidenceProvider(data, "VLD-PUR-DEMAND-SPIKE"),
        budget=2,
        K_weights=np.array([0.1, 0.1, 0.1, 0.1, 0.1, 100.0, 1.0]),
        gated_sources={"vendor_tracker", "lead_time_tracker"},
    )


def _vector(order: dict) -> np.ndarray:
    return cast(
        np.ndarray,
        np.asarray([float(order["factors"][name]) for name in FACTOR_NAMES], dtype=np.float64),
    )


def _demand_spike_mu() -> np.ndarray:
    return cast(np.ndarray, np.asarray(
        [
            [0.55, 0.50, 0.50, 0.50, 0.20, 0.20, 0.80],
            [0.80, 0.50, 0.50, 0.50, 0.50, 0.35, 0.30],
            [0.80, 0.50, 0.50, 0.50, 0.50, 0.25, 0.82],
            [0.20, 0.50, 0.50, 0.50, 0.80, 0.80, 0.20],
        ],
        dtype=np.float64,
    ))


def _vendor_cascade_mu() -> np.ndarray:
    return cast(np.ndarray, np.asarray(
        [
            [0.40, 0.50, 0.50, 0.50, 0.50, 0.40, 0.55],
            [0.85, 0.50, 0.50, 0.50, 0.20, 0.20, 0.75],
            [0.25, 0.50, 0.50, 0.50, 0.30, 0.25, 0.85],
            [0.40, 0.50, 0.50, 0.50, 0.72, 0.72, 0.55],
        ],
        dtype=np.float64,
    ))


def _s1_mu() -> np.ndarray:
    return cast(np.ndarray, np.asarray(
        [
            [0.58, 0.50, 0.50, 0.50, 0.20, 0.20, 0.84],
            [0.92, 0.20, 0.20, 0.80, 0.70, 0.70, 0.30],
            [0.20, 0.80, 0.80, 0.20, 0.70, 0.70, 0.90],
            [0.10, 0.50, 0.50, 0.50, 0.90, 0.90, 0.10],
        ],
        dtype=np.float64,
    ))
