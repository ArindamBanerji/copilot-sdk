"""Trading factory/provider tests using explicit injected dependencies."""

import pytest

from apps.trading.backend.app.services.trading_evolver import (
    create_default_trading_evolver,
)


def _provider() -> dict[str, object]:
    return {
        "status": "GREEN",
        "overallSafe": True,
        "domain": "trading",
        "source": "test_provider",
        "observed_at": "2026-01-01T00:00:00+00:00",
    }


def test_trading_factory_requires_provider() -> None:
    with pytest.raises(TypeError):
        create_default_trading_evolver()  # type: ignore[call-arg]


def test_trading_factory_with_provider_creates_evolver() -> None:
    evolver = create_default_trading_evolver(conservation_provider=_provider)
    assert evolver.conservation_provider is _provider


def test_trading_factory_provider_is_used_at_promotion_time() -> None:
    evolver = create_default_trading_evolver(conservation_provider=_provider)
    assert evolver.conservation_provider()["source"] == "test_provider"


def test_trading_main_wiring_has_live_provider() -> None:
    from apps.trading.backend.app.main import app

    provider = app.state.evolver.conservation_provider
    state = provider.get_state()
    assert state["domain"] == "trading"
    assert state["source"] == "scorer"
    assert state["status"] in {"GREEN", "AMBER", "RED", "CALIBRATING", "UNKNOWN"}
    assert state["overallSafe"] is (state["status"] == "GREEN")
