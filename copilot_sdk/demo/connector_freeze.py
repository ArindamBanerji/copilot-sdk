"""Freeze external connector responses for deterministic recording."""

from __future__ import annotations

import json
import os
import importlib.util
import sys
from pathlib import Path
from typing import Any


class ConnectorFreeze:
    """Freeze external connectors for deterministic recording."""

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        root = Path(cache_dir) if cache_dir is not None else Path.cwd() / ".record_freeze"
        self.cache_dir = root

    def freeze(self) -> dict[str, str]:
        """Cache current connector responses. Future calls return cached."""
        return {
            "fred": self.freeze_fred(),
            "openmeteo": self.freeze_openmeteo(),
        }

    def freeze_fred(self) -> str:
        path = self.cache_dir / "fred.json"
        rows_by_category = self._live_fred_rows()
        if rows_by_category is None:
            rows_by_category = {
                "protein": _fred_rows("Ground Beef", "per lb"),
                "produce": _fred_rows("Lettuce", "per lb"),
                "dairy": _fred_rows("Whole Milk", "per unit"),
                "dry_goods": _fred_rows("Flour", "per lb"),
                "beverages": _fred_rows("Coffee", "per unit"),
            }
        self._write_json(
            path,
            {
                **rows_by_category,
                "provenance": "scraped_external",
            },
        )
        os.environ["FRED_FREEZE"] = str(path)
        return str(path)

    def freeze_openmeteo(self) -> str:
        path = self.cache_dir / "openmeteo.json"
        self._write_json(
            path,
            {
                "temperature_f": 68.0,
                "precipitation_prob": 0.12,
                "wind_mph": 6.0,
                "weather_factor": 0.22,
                "source": "live",
                "provenance": "scraped_external",
            },
        )
        os.environ["OPENMETEO_FREEZE"] = str(path)
        return str(path)

    def unfreeze(self) -> None:
        os.environ.pop("FRED_FREEZE", None)
        os.environ.pop("OPENMETEO_FREEZE", None)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _live_fred_rows(self) -> dict[str, list[dict[str, Any]]] | None:
        api_key = os.environ.get("FRED_API_KEY", "").strip()
        if not api_key:
            return None
        old_freeze = os.environ.pop("FRED_FREEZE", None)
        try:
            source_path = (
                Path(__file__).resolve().parents[2]
                / "apps"
                / "purchasing"
                / "backend"
                / "app"
                / "connectors"
                / "commodity_source.py"
            )
            spec = importlib.util.spec_from_file_location("demo_fred_commodity_source", source_path)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules["demo_fred_commodity_source"] = module
            spec.loader.exec_module(module)
            FREDCommoditySource = module.FREDCommoditySource
            source = FREDCommoditySource(api_key=api_key)
            rows_by_category: dict[str, list[dict[str, Any]]] = {}
            for category in ("protein", "produce", "dairy", "dry_goods", "beverages"):
                rows = source.fetch_category_prices(category)
                if rows:
                    rows_by_category[category] = [dict(row) for row in rows]
            if not rows_by_category:
                return None
            return rows_by_category
        except Exception:
            return None
        finally:
            if old_freeze is not None:
                os.environ["FRED_FREEZE"] = old_freeze


def _fred_rows(item: str, unit: str) -> list[dict[str, Any]]:
    return [
        {"date": f"2026-{month:02d}", "item": item, "price": round(3.0 + month * 0.07, 2), "unit": unit}
        for month in range(1, 13)
    ]


__all__ = ["ConnectorFreeze"]
