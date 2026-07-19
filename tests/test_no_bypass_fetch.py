from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT_ROOT = ROOT / "apps" / "trading" / "frontend" / "src"
ENDPOINT_MAP = ROOT / "copilot_sdk" / "frontend" / "providers" / "tradingEndpointMap.ts"


def _static_urls() -> set[str]:
    source = ENDPOINT_MAP.read_text(encoding="utf-8")
    return set(re.findall(r': "([^"]+)"', source))


def test_no_static_fetch_inside_provider():
    static_urls = _static_urls()
    offenders: list[str] = []
    for path in COMPONENT_ROOT.rglob("*.tsx"):
        if "node_modules" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        if "useTabData" not in source and "TabDataProvider" not in source:
            continue
        for url in static_urls:
            if url in source and re.search(r"\b(fetch|apiGet|apiPost|safeApiGet|safeApiPost)\b", source):
                offenders.append(f"{path.relative_to(ROOT)} -> {url}")
    assert offenders == []
