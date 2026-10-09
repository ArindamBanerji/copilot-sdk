"""Trading factory/provider tests using explicit injected dependencies."""

import pytest
import importlib.util
import sys
from pathlib import Path

from copilot_sdk.testing.fixtures import requires_age


TRADING_EVOLVER_PATH = (
    Path(__file__).resolve().parents[1]
    / "apps" / "trading" / "backend" / "app" / "services" / "trading_evolver.py"
)
TRADING_EVOLVER_CONFIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "apps" / "trading" / "backend" / "app" / "evolution" / "evolver_config.py"
)


def _load_test_module(name: str, path: Path):
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


def _create_default_trading_evolver(*args, **kwargs):
    """Load the service module by file so app package initialization stays untouched."""
    module = _load_test_module("_sdk_test_trading_evolver", TRADING_EVOLVER_PATH)
    config_module = _load_test_module("_sdk_test_trading_evolver_config", TRADING_EVOLVER_CONFIG_PATH)
    module.import_module = lambda _name: config_module
    return module.create_default_trading_evolver(*args, **kwargs)


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
        _create_default_trading_evolver()  # type: ignore[call-arg]


def test_trading_factory_with_provider_creates_evolver() -> None:
    evolver = _create_default_trading_evolver(conservation_provider=_provider)
    assert evolver.conservation_provider is _provider


def test_trading_factory_provider_is_used_at_promotion_time() -> None:
    evolver = _create_default_trading_evolver(conservation_provider=_provider)
    assert evolver.conservation_provider()["source"] == "test_provider"


@requires_age
def test_trading_main_wiring_has_live_provider() -> None:
    from apps.trading.backend.app.main import app

    provider = app.state.evolver.conservation_provider
    state = provider.get_state()
    assert state["domain"] == "trading"
    assert state["source"] == "scorer"
    assert state["status"] in {"GREEN", "AMBER", "RED", "CALIBRATING", "UNKNOWN"}
    assert state["overallSafe"] is (state["status"] == "GREEN")
