"""Cached weather factors for purchasing decisions."""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WeatherForecast:
    temperature_f: float
    precipitation_prob: float
    wind_mph: float
    weather_factor: float
    source: str


_WEATHER_CACHE: dict[str, WeatherForecast] = {
    "clear_warm": WeatherForecast(72.0, 0.05, 5.0, 0.15, "cached"),
    "overcast": WeatherForecast(61.0, 0.25, 8.0, 0.35, "cached"),
    "rainy": WeatherForecast(55.0, 0.70, 12.0, 0.68, "cached"),
    "stormy": WeatherForecast(49.0, 0.90, 24.0, 0.88, "cached"),
    "hot": WeatherForecast(91.0, 0.10, 7.0, 0.58, "cached"),
    "cold": WeatherForecast(28.0, 0.20, 11.0, 0.62, "cached"),
}


def get_weather_factor(
    zip_code: str = "10001",
    date=None,
    use_live: bool = False,
) -> WeatherForecast:
    del date
    frozen = _frozen_weather()
    if frozen is not None:
        return frozen
    if not use_live:
        return _WEATHER_CACHE.get(zip_code, _WEATHER_CACHE["overcast"])
    return _fetch_live_weather(zip_code)


def _frozen_weather() -> WeatherForecast | None:
    freeze_path = os.environ.get("OPENMETEO_FREEZE", "").strip()
    if not freeze_path:
        return None
    try:
        payload = json.loads(Path(freeze_path).read_text(encoding="utf-8"))
        return WeatherForecast(
            temperature_f=float(payload["temperature_f"]),
            precipitation_prob=float(payload["precipitation_prob"]),
            wind_mph=float(payload["wind_mph"]),
            weather_factor=float(payload["weather_factor"]),
            source=str(payload.get("source") or "live"),
        )
    except Exception:
        return None


def _fetch_live_weather(zip_code: str) -> WeatherForecast:
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=40.7128&longitude=-74.0060"
            "&current=temperature_2m,precipitation,wind_speed_10m"
        )
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        current = payload["current"]
        temperature_c = float(current.get("temperature_2m", 16.0))
        temperature_f = temperature_c * 9.0 / 5.0 + 32.0
        precipitation = float(current.get("precipitation", 0.0))
        wind_kph = float(current.get("wind_speed_10m", 0.0))
        wind_mph = wind_kph * 0.621371
        factor = min(max(precipitation / 5.0 + wind_mph / 60.0, 0.0), 1.0)
        return WeatherForecast(
            temperature_f=round(temperature_f, 1),
            precipitation_prob=round(min(precipitation / 5.0, 1.0), 3),
            wind_mph=round(wind_mph, 1),
            weather_factor=round(factor, 3),
            source="live",
        )
    except Exception:
        return _WEATHER_CACHE.get(zip_code, _WEATHER_CACHE["overcast"])
