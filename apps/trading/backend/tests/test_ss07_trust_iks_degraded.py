from __future__ import annotations

from types import SimpleNamespace

from app.services.trust_analysis import TrustAnalyzer
from app.state.compute_helpers import safe_call
from app.state.trading_registry import _iks_state


def test_trust_analysis_marks_dk_readiness_unavailable() -> None:
    class BrokenStore:
        def get_decisions(self, _domain: str, *, limit: int):
            raise RuntimeError("offline")

    scorer = SimpleNamespace(
        phase="A",
        graph_store=BrokenStore(),
        _preset=SimpleNamespace(shape=SimpleNamespace(category_names=(), factor_names=())),
        get_phase=lambda: "A",
        get_dk_weights=lambda: None,
    )

    payload = TrustAnalyzer().analyze(scorer, [])

    assert payload["decisions_until_dk"] is None
    assert payload["dk_readiness_available"] is False


def test_safe_call_and_iks_state_preserve_failure_status() -> None:
    value, available = safe_call(lambda: (_ for _ in ()).throw(RuntimeError("offline")), 0.0, with_status=True)
    state = _iks_state(lambda: SimpleNamespace(_compute_iks=lambda: (_ for _ in ()).throw(RuntimeError("offline"))))

    assert value == 0.0
    assert available is False
    assert state == {"iks": 0.0, "iks_available": False}


def test_safe_call_happy_path_marks_value_available() -> None:
    value, available = safe_call(lambda: 2.5, 0.0, with_status=True)

    assert value == 2.5
    assert available is True
