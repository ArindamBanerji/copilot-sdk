from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from freezegun import freeze_time

from copilot_sdk.scoring.verification import weather


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    state: dict[str, Any] = {"calls": 0, "fail": False, "temperature": 20.0}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            state["calls"] += 1
            if state["fail"]:
                self.send_error(503)
                return
            body = json.dumps({"current": {"temperature_2m": state["temperature"]}}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.delenv("OPENMETEO_FREEZE", raising=False)
    monkeypatch.setattr(weather, "_FORECAST_URL", f"http://127.0.0.1:{server.server_port}/")
    weather._LIVE_CACHE.clear()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
        weather._LIVE_CACHE.clear()


def test_forecast_reused_then_refreshed_after_ttl(provider: dict[str, Any]) -> None:
    with freeze_time("2026-09-05") as clock:
        first = weather.get_weather_factor(use_live=True)
        provider["temperature"] = 30.0
        assert weather.get_weather_factor(use_live=True) == first
        assert provider["calls"] == 1
        clock.tick(301)
        assert weather.get_weather_factor(use_live=True).temperature_f == 86.0
        assert provider["calls"] == 2


def test_overlapping_requests_make_one_external_request(provider: dict[str, Any]) -> None:
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: weather.get_weather_factor(use_live=True), range(8)))
    assert all(result.source == "live" for result in results)
    assert provider["calls"] == 1


def test_failure_fallback_retries_soon_without_live_label(provider: dict[str, Any]) -> None:
    with freeze_time("2026-09-05") as clock:
        provider["fail"] = True
        assert weather.get_weather_factor(use_live=True).source == "cached"
        provider["fail"] = False
        assert weather.get_weather_factor(use_live=True).source == "cached"
        assert provider["calls"] == 1
        clock.tick(16)
        assert weather.get_weather_factor(use_live=True).source == "live"
        assert provider["calls"] == 2


def test_freeze_file_takes_priority_over_live_cache(
    provider: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    weather.get_weather_factor(use_live=True)
    path = tmp_path / "weather.json"
    path.write_text(json.dumps({"temperature_f": 42, "precipitation_prob": 0.2,
                               "wind_mph": 7, "weather_factor": 0.1, "source": "frozen"}))
    monkeypatch.setenv("OPENMETEO_FREEZE", str(path))
    assert weather.get_weather_factor(use_live=True).temperature_f == 42
    assert provider["calls"] == 1
