"""Purchasing POS data endpoints."""

from __future__ import annotations

import os
import warnings
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException

from app.connectors.mock_toast import MockToastConnector
from copilot_sdk.di.profiler import BaseSourceProfiler

ConnectorFactory = Callable[[], Any]


def _demo_mode() -> bool:
    configured = os.environ.get("DEMO_MODE", os.environ.get("PURCHASING_DEMO_MODE"))
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes", "on"}
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


def _is_mock_connector(connector: Any) -> bool:
    source = str(getattr(connector, "source_name", "") or type(connector).__name__).lower()
    return "mock" in source or "fixture" in source


def _default_toast_connector() -> Any:
    if os.environ.get("TOAST_CLIENT_ID"):
        try:
            import requests  # noqa: F401
            from app.connectors.toast import ToastConnector

            if not os.environ.get("TOAST_CLIENT_ID"):
                raise ValueError("Incomplete Toast credentials")
            return ToastConnector(
                api_key=os.environ["TOAST_CLIENT_ID"],
                base_url=os.environ.get("TOAST_BASE_URL", "https://api.toasttab.com/v2"),
                location_id=os.environ.get("TOAST_LOCATION_ID", ""),
            )
        except ImportError:
            if not _demo_mode():
                raise RuntimeError("Toast provider is unavailable")
            warnings.warn("TOAST_CLIENT_ID set but client library not installed. Using mock.")
        except Exception as exc:
            if not _demo_mode():
                raise RuntimeError("Toast provider failed to initialize") from exc
            warnings.warn(f"Toast connector failed to initialize: {exc}. Using mock.")
    if not _demo_mode():
        raise RuntimeError("Toast provider is not configured")
    return MockToastConnector()


def create_pos_router(
    connector_factory: ConnectorFactory | None = None,
) -> APIRouter:
    """Create read-only Toast POS endpoints for Purchasing."""
    factory = connector_factory or _default_toast_connector
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-pos"])

    @router.get("/pos/today")
    def pos_today() -> dict[str, Any]:
        try:
            connector = factory()
            if not _demo_mode() and _is_mock_connector(connector):
                raise RuntimeError("Toast provider is unavailable")
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Toast POS provider unavailable") from exc
        requested_date = date.today().isoformat()
        records = _fetch_records(connector, requested_date)
        effective_date = requested_date
        source_status = "today"

        if not records:
            fallback_date = _latest_fixture_date(connector)
            if _demo_mode() and fallback_date is not None and fallback_date != requested_date:
                fallback_records = _fetch_records(connector, fallback_date)
                if fallback_records:
                    records = fallback_records
                    effective_date = fallback_date
                    source_status = "fixture_fallback"

        summary = _empty_summary(requested_date, effective_date, connector, source_status)
        if records:
            summary.update(_record_summary(records[0]))
            summary["records"] = records
        if _demo_mode():
            summary["source"] = "demo_fixture"
            summary["provenance"] = "demo_fixture"
        return summary

    @router.get("/pos/profile")
    def pos_profile() -> dict[str, Any]:
        try:
            connector = factory()
            if not _demo_mode() and _is_mock_connector(connector):
                raise RuntimeError("Toast provider is unavailable")
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Toast POS provider unavailable") from exc
        entity_ids = _last_7_dates()
        date_source = "last_7_dates"

        if not any(_fetch_records(connector, entity_id) for entity_id in entity_ids):
            fixture_dates = _fixture_dates(connector)
            if _demo_mode() and fixture_dates:
                entity_ids = fixture_dates[-7:]
                date_source = "fixture_fallback"

        profile = BaseSourceProfiler(connector).profile(entity_ids)
        payload = profile.to_dict()
        payload["entity_ids"] = entity_ids
        payload["date_source"] = date_source
        if _demo_mode():
            payload["source"] = "demo_fixture"
            payload["provenance"] = "demo_fixture"
        return payload

    return router


def _fetch_records(connector: Any, entity_id: str) -> list[dict]:
    records = connector.fetch(entity_id)
    return [record for record in records if isinstance(record, dict)]


def _empty_summary(
    requested_date: str,
    effective_date: str,
    connector: Any,
    source_status: str,
) -> dict[str, Any]:
    return {
        "source_name": str(getattr(connector, "source_name", "toast_pos_mock")),
        "entity_type": str(getattr(connector, "entity_type", "restaurant_sales")),
        "requested_date": requested_date,
        "date": effective_date,
        "source_status": source_status,
        "covers": 0,
        "total_revenue": 0.0,
        "total_orders": 0,
        "items": [],
        "dayparts": {"lunch": 0, "dinner": 0, "late_night": 0},
        "prep_categories": [],
        "records": [],
    }


def _record_summary(record: dict[str, Any]) -> dict[str, Any]:
    items = record.get("items") if isinstance(record.get("items"), list) else []
    prep_categories = sorted(
        {
            str(item.get("category"))
            for item in items
            if isinstance(item, dict) and item.get("category")
        }
    )
    dayparts = record.get("dayparts") if isinstance(record.get("dayparts"), dict) else {}
    return {
        "covers": int(record.get("covers", 0) or 0),
        "total_revenue": float(record.get("total_revenue", 0.0) or 0.0),
        "total_orders": int(record.get("total_orders", 0) or 0),
        "items": items,
        "dayparts": {
            "lunch": int(dayparts.get("lunch", 0) or 0),
            "dinner": int(dayparts.get("dinner", 0) or 0),
            "late_night": int(dayparts.get("late_night", 0) or 0),
        },
        "prep_categories": prep_categories,
    }


def _last_7_dates() -> list[str]:
    today = date.today()
    start = today - timedelta(days=6)
    return [(start + timedelta(days=offset)).isoformat() for offset in range(7)]


def _fixture_dates(connector: Any) -> list[str]:
    data = getattr(connector, "_data", None)
    if not isinstance(data, dict):
        return []
    return sorted(str(key) for key in data)


def _latest_fixture_date(connector: Any) -> str | None:
    fixture_dates = _fixture_dates(connector)
    return fixture_dates[-1] if fixture_dates else None
