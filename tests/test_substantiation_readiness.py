from __future__ import annotations

from copilot_sdk.substantiation.readiness import DayZeroReadiness


def test_readiness_has_6_fields() -> None:
    readiness = _readiness(renders_day_zero_state=True)

    assert hasattr(readiness, "renders_day_zero_state")


def test_gate_fails_without_day_zero_state() -> None:
    readiness = _readiness(renders_day_zero_state=False)

    assert readiness.gate() == (False, ["renders_day_zero_state"])


def test_gate_passes_with_all_6() -> None:
    readiness = _readiness(renders_day_zero_state=True)

    assert readiness.gate() == (True, [])


def _readiness(*, renders_day_zero_state: bool) -> DayZeroReadiness:
    return DayZeroReadiness(
        feature="feature",
        copilot="test",
        populated=True,
        proven=True,
        instrumented=True,
        real_path_committed=True,
        labels_honest=True,
        renders_day_zero_state=renders_day_zero_state,
    )
