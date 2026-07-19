from __future__ import annotations

from pathlib import Path

from scripts.generate_tab_state_types import render_shared, render_trading


ROOT = Path(__file__).resolve().parents[1]


def test_generated_ts_is_current():
    expected = {
        ROOT / "copilot_sdk" / "frontend" / "providers" / "schemas" / "shared.ts": render_shared(),
        ROOT / "apps" / "trading" / "frontend" / "src" / "state" / "schemas" / "trading.ts": render_trading(),
    }
    stale = []
    for path, content in expected.items():
        committed = path.read_text(encoding="utf-8")
        if committed != content:
            stale.append(str(path.relative_to(ROOT)))
    assert stale == [], f"Generated TS types are stale. Run scripts/generate_tab_state_types.py: {stale}"
