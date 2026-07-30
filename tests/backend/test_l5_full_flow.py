import math
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.scoring_router import create_scoring_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.dk_persistence import DKWelfordTracker
from copilot_sdk.scoring.scorer import CompoundingScorer


DOMAIN = "dataops"
CATEGORY = "pipeline_failure"
FACTORS = (
    "impact_scope",
    "source_reliability",
    "recurrence_frequency",
    "downstream_urgency",
    "data_freshness",
    "business_criticality",
)
ACTIONS = (
    "auto_approve",
    "investigate",
    "escalate_to_owner",
    "pause_downstream",
    "refer_to_specialist",
)


class FullFlowGraphStore(InMemoryGraphStore):
    def count_categories_with_n(self, domain: str, n: int) -> int:
        counts: dict[str, int] = {}
        for decision in self.get_all_decisions(domain):
            category = decision.get("category")
            if category is not None:
                counts[str(category)] = counts.get(str(category), 0) + 1
        return sum(1 for count in counts.values() if count >= int(n))


def _factor_payload(i: int) -> dict[str, float]:
    if i % 2 == 0:
        values = [0.95, 0.88, 0.5, 0.5, 0.5, 0.5]
    else:
        values = [0.05, 0.12, 0.5, 0.5, 0.5, 0.5]
    return dict(zip(FACTORS, values))


def _expected_action(i: int) -> str:
    return ACTIONS[1] if i % 2 == 0 else ACTIONS[0]


def _assert_finite_vector(vector: list[float], expected_len: int) -> None:
    assert isinstance(vector, list)
    assert len(vector) == expected_len
    assert all(math.isfinite(float(value)) for value in vector)


def _score_and_learn(
    client: TestClient,
    *,
    i: int,
    actual_action: str | None = None,
) -> tuple[dict, dict]:
    score_response = client.post(
        "/score",
        json={"category": CATEGORY, "factors": _factor_payload(i)},
    )
    assert score_response.status_code == 200, score_response.text
    score_payload = score_response.json()

    observed_action = actual_action or _expected_action(i)
    learn_response = client.post(
        "/learn",
        json={
            "decision_id": score_payload["decision_id"],
            "actual_action": observed_action,
            "outcome": "confirmed" if observed_action == score_payload["action"] else "override",
        },
    )
    assert learn_response.status_code == 200, learn_response.text
    return score_payload, learn_response.json()


def _run_sdk_full_flow() -> SimpleNamespace:
    store = FullFlowGraphStore(domain=DOMAIN)
    scorer = CompoundingScorer.from_preset(
        DOMAIN,
        graph_store=store,
        enable_rl=False,
        profile="test",
    )
    setattr(scorer, "_conservation_pause", lambda: None)
    tracker = DKWelfordTracker()
    app = FastAPI()
    app.include_router(
        create_scoring_router(
            DOMAIN,
            scorer_factory=lambda: scorer,
            learning_store=store,
            dk_welford_tracker=tracker,
        )
    )
    client = TestClient(app)

    first_score, first_learn = _score_and_learn(client, i=0)
    assert scorer.get_category_phase(CATEGORY) == "MEAN_CONVERGENCE"

    last_mean_score = first_score
    last_mean_learn = first_learn
    for i in range(1, 200):
        last_mean_score, last_mean_learn = _score_and_learn(client, i=i)

    assert scorer.get_category_phase(CATEGORY) == "VARIANCE_LEARNING"
    centroids_before_variance = store.get_centroids(DOMAIN)
    assert centroids_before_variance

    dk_row = None
    final_score = last_mean_score
    final_learn = last_mean_learn
    for i in range(200, 280):
        score_response = client.post(
            "/score",
            json={"category": CATEGORY, "factors": _factor_payload(i)},
        )
        assert score_response.status_code == 200, score_response.text
        final_score = score_response.json()
        actual_action = _expected_action(i)
        learn_response = client.post(
            "/learn",
            json={
                "decision_id": final_score["decision_id"],
                "actual_action": actual_action,
                "outcome": "confirmed" if actual_action == final_score["action"] else "override",
            },
        )
        assert learn_response.status_code == 200, learn_response.text
        final_learn = learn_response.json()

        dk_row = store.get_dk_weights(DOMAIN)
        if dk_row:
            break

    assert dk_row is not None
    conservation_state = store.get_conservation_state(DOMAIN)
    assert conservation_state is not None

    return SimpleNamespace(
        store=store,
        scorer=scorer,
        first_score=first_score,
        first_learn=first_learn,
        last_mean_score=last_mean_score,
        last_mean_learn=last_mean_learn,
        last_mean_actual_action=_expected_action(199),
        final_score=final_score,
        final_learn=final_learn,
        centroids_before_variance=centroids_before_variance,
        centroids_after_variance=store.get_centroids(DOMAIN),
        dk_row=dk_row,
        conservation_state=conservation_state,
    )


@pytest.fixture(scope="module")
def sdk_full_flow() -> SimpleNamespace:
    return _run_sdk_full_flow()


def test_full_learn_flow_writes_all_three_l5_node_types(sdk_full_flow: SimpleNamespace) -> None:
    centroids = sdk_full_flow.store.get_centroids(DOMAIN)
    assert centroids
    centroid = next(
        row for row in centroids if row["category"] == CATEGORY and row["action"] == sdk_full_flow.last_mean_actual_action
    )
    _assert_finite_vector(centroid["vector_json"], len(FACTORS))
    assert isinstance(centroid["caused_by_decision_id"], str)
    assert centroid["caused_by_decision_id"]

    assert sdk_full_flow.centroids_after_variance == sdk_full_flow.centroids_before_variance

    dk_row = sdk_full_flow.dk_row
    assert dk_row["domain"] == DOMAIN
    assert dk_row["entity_group"] is None
    assert dk_row["welford_state"] is not None
    assert dk_row["weight_json"] == sdk_full_flow.scorer.get_dk_weights()

    conservation = sdk_full_flow.conservation_state
    assert conservation["domain"] == DOMAIN
    assert math.isfinite(float(conservation["alpha"]))
    assert "status" in conservation

    for payload in (sdk_full_flow.first_learn, sdk_full_flow.final_learn):
        assert "decision_id" in payload
        assert "action" in payload
        assert "centroid_updated" in payload
        assert "centroid_vector" not in payload
        assert "weight_tensor" not in payload
        assert "welford_state" not in payload


def test_dk_welford_storage_roundtrip_full_flow(sdk_full_flow: SimpleNamespace) -> None:
    row = sdk_full_flow.dk_row
    welford_state = row["welford_state"]
    assert isinstance(welford_state, dict)

    expected_vectors = (
        "confirmed_mean",
        "confirmed_m2",
        "overridden_mean",
        "overridden_m2",
        "all_mean",
        "all_m2",
    )
    for key in expected_vectors:
        _assert_finite_vector(welford_state[key], len(FACTORS))

    assert welford_state["n_all"] > 0
    assert row["n_confirmed"] >= 0
    assert row["n_overridden"] >= 0
    assert row["weight_json"] == sdk_full_flow.scorer.get_dk_weights()


def test_full_learn_flow_writes_all_three(sdk_full_flow: SimpleNamespace) -> None:
    assert sdk_full_flow.centroids_after_variance
    assert sdk_full_flow.dk_row["welford_state"] is not None
    assert sdk_full_flow.conservation_state is not None

    centroid_keys = {
        (row["category"], row["action"])
        for row in sdk_full_flow.centroids_after_variance
    }
    assert (CATEGORY, sdk_full_flow.last_mean_actual_action) in centroid_keys
    assert sdk_full_flow.scorer.get_category_phase(CATEGORY) == "VARIANCE_LEARNING"
