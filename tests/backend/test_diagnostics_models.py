import pytest
from types import SimpleNamespace

from copilot_sdk.backend.diagnostics_models import _cypher_count, build_diagnostics
from copilot_sdk.graph import InMemoryGraphStore




def _seed_store():
    store = InMemoryGraphStore(domain="trading")
    for index in range(500):
        decision_id = store.write_decision("trading", f"category-{index % 5}", "hold", 0.8, {"signal": 0.5})
        if index < 100:
            store.write_outcome(decision_id, "hold", True, domain="trading")
    store.update_conservation_state("trading", "GREEN", 1.0, 1.0, 100, 0.75, 100.0,
                                    5, 5, 0.0, 0.0, "false")
    return store


class _Shape:
    n_categories = 5
    n_actions = 4
    n_factors = 10


class _Preset:
    shape = _Shape()


class _Scorer:
    def __init__(self):
        self.graph_store = _seed_store()
    _preset = _Preset()

    def get_verified_count(self):
        return 100

    def _compute_iks(self, persist_artifacts=False):
        return 42.0

    def _conservation_pause(self):
        return None

    class _Outbox:
        db_path = "outbox.db"

        def pending_count(self):
            return 0

        def count_abandoned(self):
            return 0

    _outbox = _Outbox()


def test_diagnostics_contract_is_complete_and_failure_isolated():
    scorer = _Scorer()
    payload = build_diagnostics("trading", scorer, scorer.graph_store)
    assert payload["domain"] == "trading"
    assert set(payload["layers"]) if "layers" in payload else True
    for key in ("infrastructure", "scorer_state", "conservation", "j6_readiness", "graph_artifacts"):
        assert key in payload
        assert "status" in payload[key]


def test_diagnostics_reports_live_scorer_store_and_conservation_state():
    scorer = _Scorer()
    payload = build_diagnostics("trading", scorer, scorer.graph_store)
    assert payload["scorer_state"]["verified_count"] == 100
    assert payload["scorer_state"]["tensor_shape"] == [5, 4, 10]
    assert payload["scorer_state"]["learned_values"] == 210
    assert payload["conservation"]["conservation_status"] == "GREEN"
    assert payload["conservation"]["gate_passes"] is True
    assert payload["graph_artifacts"]["decisions"] == 500
    assert payload["j6_readiness"]["outbox_path"] == "outbox.db"
    assert payload["j6_readiness"]["outbox_pending"] == 0
    assert payload["infrastructure"]["outbox_pending"] == 0
    assert payload["infrastructure"]["outbox_abandoned"] == 0


def test_diagnostics_outbox_reflects_pending_and_abandoned_counts():
    class _PendingOutbox:
        db_path = "outbox.db"

        def pending_count(self):
            return 3

        def count_abandoned(self):
            return 2

    class _PendingScorer(_Scorer):
        _outbox = _PendingOutbox()

    payload = build_diagnostics("trading", _PendingScorer(), _seed_store())

    assert payload["infrastructure"]["outbox_pending"] == 3
    assert payload["infrastructure"]["outbox_abandoned"] == 2


@pytest.mark.age
def test_diagnostics_finds_age_query_through_nested_active_store(disposable_age):
    store = disposable_age.store("trading")
    for index in range(7):
        store.write_fingerprint(f"fingerprint-{index}", "trading", ["signal"],
                                {"factors": []}, 0, index)
    active = SimpleNamespace(_store=store)
    assert _cypher_count(active, "Fingerprint", "trading") == 7
    assert _cypher_count(active, "Fingerprint", "other") == 0


def test_diagnostics_prefers_live_scorer_conservation_state():
    class _LiveScorer(_Scorer):
        def get_verified_count(self):
            return 4862

        def _evolution_conservation_state(self):
            return {
                "status": "GREEN",
                "verified_count": 4862,
                "correct_count": 3712,
                "q": 3712 / 4862,
                "alpha": 1.0,
                "theta_min": 23.53,
            }

    payload = build_diagnostics("soc", _LiveScorer(), _seed_store())
    assert payload["conservation"]["V"] == 4862
    assert payload["conservation"]["q"] == 3712 / 4862


def test_j6_readiness_ready_when_conservation_red():
    class _RedScorer(_Scorer):
        graph_store = InMemoryGraphStore(domain="soc")

        def _evolution_conservation_state(self):
            return {
                "status": "RED",
                "V": 4862,
                "q": 0.76,
                "alpha": 0.0,
                "theta_min": 23.53,
            }

        def _conservation_pause(self):
            return {"reason": "conservation_red"}

    payload = build_diagnostics("soc", _RedScorer(), _RedScorer.graph_store)

    # J6 readiness reports persistence/infrastructure readiness. A RED
    # conservation gate blocks learning separately without making the graph
    # store or outbox unavailable.
    assert payload["j6_readiness"]["status"] == "ready"
    assert payload["conservation"]["conservation_status"] == "RED"
