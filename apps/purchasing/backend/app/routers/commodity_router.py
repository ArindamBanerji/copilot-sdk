"""Commodity price endpoints for Purchasing."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from app.connectors.commodity_provider import (
    COMMODITY_CATEGORIES,
    CommodityDataProvider,
)


def create_commodity_router(provider: CommodityDataProvider | None = None) -> APIRouter:
    if provider is None:
        provider = CommodityDataProvider()
    router = APIRouter(prefix="/api/purchasing/commodity", tags=["commodity"])

    @router.get("/prices/{category}")
    def get_prices(category: str) -> dict[str, Any]:
        if category not in COMMODITY_CATEGORIES:
            raise HTTPException(status_code=404, detail=f"Unknown commodity category: {category}")
        return jsonable_encoder(provider.get_category_prices(category))

    @router.get("/index/{category}")
    def get_index(category: str) -> dict[str, Any]:
        if category not in COMMODITY_CATEGORIES:
            raise HTTPException(status_code=404, detail=f"Unknown commodity category: {category}")
        return jsonable_encoder(provider.get_price_index(category))

    @router.get("/indices")
    def get_all_indices() -> dict[str, Any]:
        return jsonable_encoder(provider.get_all_indices())

    @router.get("/status")
    def get_status() -> dict[str, Any]:
        source_name = type(provider._source).__name__
        return {
            "source": source_name,
            "provenance_tier": provider._source.provenance_tier,
            "fred_active": source_name == "FREDCommoditySource",
            "categories": list(COMMODITY_CATEGORIES),
        }

    return router
