from app.services.regime_monitor import RegimeMonitor
from app.services.regime_scoring import build_regime_context
from scripts.preseed_demo_fixtures import regime_metadata, trading_seed_sequence


def test_seed_inputs_trigger_real_monitor_before_stabilization() -> None:
    sequence = trading_seed_sequence()
    assert len(sequence) == 55
    assert sum(correct for _, correct, _ in sequence[:40]) == 34
    assert sum(correct for _, correct, _ in sequence[40:]) == 8
    monitor = RegimeMonitor()
    for index, _, volatile in sequence:
        context = build_regime_context(metadata=regime_metadata(volatile))
        monitor.record(context["regime"])
        if index == 39:
            assert monitor.current_regime == "trending"
            assert not monitor.is_regime_break
    assert monitor.current_regime == "volatile"
    assert monitor.is_regime_break
    assert monitor.decisions_in_new_regime == 15 < monitor.decisions_to_stabilize
