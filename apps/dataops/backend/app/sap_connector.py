"""SAP connector with deterministic cache fallback for DataOps demos."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, cast
from apps.dataops.backend.app.connector_cache import ConnectorCache

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_SAP_BASE_URL = "https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap"


class SAPConnector:
    provenance_tier = "sample"  # cache-backed fixture, not live SAP
    # When real SAP API wired: change to "scraped_external"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        cache_dir: str | Path | None = None,
        timeout: float = 10.0,
    ) -> None:
        env_base_url = os.getenv("SAP_BASE_URL")
        env_api_key = os.getenv("SAP_API_KEY")
        self.base_url = (base_url or env_base_url or DEFAULT_SAP_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else env_api_key
        self.cache_dir = Path(cache_dir) if cache_dir is not None else DATA_DIR
        self.timeout = timeout
        self.last_source = "sap_cache"
        self._live_enabled = bool(self.api_key)
        self._cache = ConnectorCache(self.cache_dir, f"sap:{self.base_url}:{self.api_key or ''}")

    async def get_purchase_orders(self, top: int = 20, skip: int = 0) -> dict[str, Any]:
        return await self._get_collection(
            endpoint="/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder",
            cache_name="sap_purchase_orders.json",
            result_key="purchase_orders",
            top=top,
            skip=skip,
        )

    async def get_supplier_invoices(self, top: int = 20, skip: int = 0) -> dict[str, Any]:
        return await self._get_collection(
            endpoint="/API_SUPPLIERINVOICE_PROCESS_SRV/A_SupplierInvoice",
            cache_name="sap_supplier_invoices.json",
            result_key="supplier_invoices",
            top=top,
            skip=skip,
        )

    async def get_suppliers(self, top: int = 20, skip: int = 0) -> dict[str, Any]:
        return await self._get_collection(
            endpoint="/API_BUSINESS_PARTNER/A_BusinessPartner",
            cache_name="sap_suppliers.json",
            result_key="suppliers",
            top=top,
            skip=skip,
        )

    async def health(self) -> dict[str, Any]:
        payload = await self.get_purchase_orders()
        live = payload["source"] == "sap_live"
        count = payload["total"]
        return {"status": "ok" if live else "cache" if count else "unavailable",
                "live": live, "connected": live, "cached": not live and bool(count),
                "source": payload["source"], "record_count": count,
                "cached_records": 0 if live else count, "provenance": payload["provenance"]}

    async def _get_collection(
        self,
        *,
        endpoint: str,
        cache_name: str,
        result_key: str,
        top: int,
        skip: int = 0,
    ) -> dict[str, Any]:
        safe_top = max(1, min(int(top), 100))
        safe_skip = max(0, int(skip))
        try:
            payload, live = await self._cache.fetch(
                endpoint, {"$top": str(safe_top), "$skip": str(safe_skip), "$format": "json"},
                self._request_json, _parse_odata_results)
            records = _parse_odata_results(payload)[:safe_top]
            self.last_source = "sap_live" if live else "sap_cache"
            return {"source": self.last_source, "provenance": "sandbox" if "sandbox.api.sap.com" in self.base_url else "external",
                    "total": len(records), result_key: records}
        except (RuntimeError, ValueError):
            records = self._load_cache_list(cache_name)[safe_skip:safe_skip + safe_top]
            self.last_source = "sap_cache"
            return {"source": "sap_cache", "provenance": "sample", "total": len(records), result_key: records}

    async def _request_json(self, endpoint: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        if not self._live_enabled:
            raise RuntimeError("SAP live connection is not configured")
        import httpx

        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["APIKey"] = self.api_key
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    def _load_cache_list(self, filename: str) -> list[dict[str, Any]]:
        path = self.cache_dir / filename
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("SAP cache file %s could not be loaded: %s", filename, exc)
            return []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for value in payload.values():
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        logger.warning("SAP cache file %s did not contain a list payload", filename)
        return []


def _parse_odata_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("d", {}) if isinstance(payload, dict) else {}
    results = data.get("results") if isinstance(data, dict) else None
    if not isinstance(results, list) or not all(isinstance(item, dict) for item in results):
        raise ValueError("Expected SAP OData V2 d.results collection")
    return results
