from copilot_sdk.backend.diagnostics_models import _cypher_count, build_diagnostics
from copilot_sdk.graph import InMemoryGraphStore


class _Store:
    domain = "trading"
    backend = "age"
    graph_name = "soc_graph"

    def get_decisions(self, domain, limit=1):
        return [{"category": "a"}] * 500

    def count_decisions(self, domain):
        return 500

    def count_verified_decisions(self, domain):
        return 100

    def count_correct(self, domain):
        return 100

    def count_categories_with_n(self, domain, n=1):
        return 5

    def count_outcomes(self, domain):
        return 0

    def has_domain_anchor(self, domain):
        return True

    def get_conservation_state(self, domain):
        return {"status": "GREEN", "V": 100, "q": 1.0, "alpha": 1.0, "theta_min": 0.75}

    def write_conservation_status(self, *args, **kwargs):
        pass

    def write_centroid_checkpoint(self, *args, **kwargs):
        pass


class _Shape:
    n_categories = 5
    n_actions = 4
    n_factors = 10


class _Preset:
    shape = _Shape()


class _Scorer:
    graph_store = _Store()
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


def test_diagnostics_finds_age_query_through_nested_active_store():
    class _RawAGEStore:
        def _run_query(self, query):
            assert "RETURN count(n) AS cnt" in query
            return [{"cnt": 7}]

    class _SDKAdapter:
        def __init__(self):
            self._store = _RawAGEStore()

    class _ActiveStore:
        def __init__(self):
            self._store = _SDKAdapter()

    assert _cypher_count(_ActiveStore(), "Fingerprint", "trading") == 7


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

    payload = build_diagnostics("soc", _LiveScorer(), _Store())
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

    assert payload["j6_readiness"]["status"] == "ready"
    assert payload["conservation"]["conservation_status"] == "RED"
