from __future__ import annotations

import importlib
import importlib.util
import sys
from types import ModuleType
from pathlib import Path
from typing import Any

import pytest
from scripts import generate_tab_state_types


ROOT = Path(__file__).resolve().parents[1]


def test_generated_ts_is_current(monkeypatch: pytest.MonkeyPatch) -> None:
    original_app_modules = {
        name: module for name, module in sys.modules.items()
        if name == "app" or name.startswith("app.")
    }

    def load_schema_modules_without_app_initializer() -> tuple[Any, dict[Any, type[Any]]]:
        backend_app = generate_tab_state_types.TRADING_BACKEND / "app"
        fake_app = ModuleType("app")
        fake_app.__path__ = [str(backend_app)]  # type: ignore[attr-defined]
        fake_app.__package__ = "app"
        fake_state = ModuleType("app.state")
        fake_state.__path__ = [str(backend_app / "state")]  # type: ignore[attr-defined]
        fake_state.__package__ = "app.state"
        fake_schemas = ModuleType("app.state.schemas")
        fake_schemas.__path__ = [str(backend_app / "state" / "schemas")]  # type: ignore[attr-defined]
        fake_schemas.__package__ = "app.state.schemas"
        sys.modules.update({
            "app": fake_app,
            "app.state": fake_state,
            "app.state.schemas": fake_schemas,
        })
        try:
            key_manifest = importlib.import_module("app.state.key_manifest")
            schema_module = importlib.import_module("app.state.schemas.trading")
            return key_manifest.TradingKey, dict(schema_module.TRADING_SCHEMA_BY_KEY)
        finally:
            for name in list(sys.modules):
                if name == "app" or name.startswith("app."):
                    sys.modules.pop(name, None)
            sys.modules.update(original_app_modules)

    monkeypatch.setattr(
        generate_tab_state_types,
        "_load_trading_schema_models",
        load_schema_modules_without_app_initializer,
    )
    expected = {
        ROOT / "copilot_sdk" / "frontend" / "providers" / "schemas" / "shared.ts": generate_tab_state_types.render_shared(),
        ROOT / "apps" / "trading" / "frontend" / "src" / "state" / "schemas" / "trading.ts": generate_tab_state_types.render_trading(),
    }
    stale = []
    for path, content in expected.items():
        committed = path.read_text(encoding="utf-8")
        if committed != content:
            stale.append(str(path.relative_to(ROOT)))
    assert stale == [], f"Generated TS types are stale. Run scripts/generate_tab_state_types.py: {stale}"
