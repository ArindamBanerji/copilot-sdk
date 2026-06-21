"""SAP connector with deterministic cache fallback for DataOps demos."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

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
        timeout: float = 5.0,
    ) -> None:
        env_base_url = os.getenv("SAP_BASE_URL")
        env_api_key = os.getenv("SAP_API_KEY")
        self.base_url = (base_url or env_base_url or DEFAULT_SAP_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else env_api_key
        self.cache_dir = Path(cache_dir) if cache_dir is not None else DATA_DIR
        self.timeout = timeout
        self.last_source = "sap_cache"
        self._live_enabled = bool(base_url or env_base_url or api_key or env_api_key)

    async def get_purchase_orders(self, top: int = 20) -> dict[str, Any]:
        return await self._get_collection(
            endpoint="/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder",
            cache_name="sap_purchase_orders.json",
            result_key="purchase_orders",
            top=top,
        )

    async def get_supplier_invoices(self, top: int = 20) -> dict[str, Any]:
        return await self._get_collection(
            endpoint="/API_SUPPLIERINVOICE_PROCESS_SRV/A_SupplierInvoice",
            cache_name="sap_supplier_invoices.json",
            result_key="supplier_invoices",
            top=top,
        )

    async def get_suppliers(self, top: int = 20) -> dict[str, Any]:
        return await self._get_collection(
            endpoint="/API_BUSINESS_PARTNER/A_BusinessPartner",
            cache_name="sap_suppliers.json",
            result_key="suppliers",
            top=top,
        )

    async def health(self) -> dict[str, Any]:
        try:
            await self._request_json(
                "/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder",
                params={"$top": "1", "$format": "json"},
            )
            return {"status": "ok", "live": True, "source": "sap_live"}
        except Exception as exc:
            logger.warning("SAP health check failed; using cache fallback: %s", exc)
            orders = self._load_cache_list("sap_purchase_orders.json")
            return {
                "status": "cache",
                "live": False,
                "source": "sap_cache",
                "cached_records": len(orders),
            }

    async def _get_collection(
        self,
        *,
        endpoint: str,
        cache_name: str,
        result_key: str,
        top: int,
    ) -> dict[str, Any]:
        safe_top = max(1, min(int(top), 100))
        try:
            payload = await self._request_json(endpoint, params={"$top": str(safe_top), "$format": "json"})
            records = _parse_odata_results(payload)[:safe_top]
            self.last_source = "sap_live"
            return {"source": "sap_live", "total": len(records), result_key: records}
        except Exception as exc:
            logger.warning("SAP live fetch failed for %s; using %s: %s", endpoint, cache_name, exc)
            records = self._load_cache_list(cache_name)[:safe_top]
            self.last_source = "sap_cache"
            return {"source": "sap_cache", "total": len(records), result_key: records}

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
            return response.json()

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
    results = data.get("results", []) if isinstance(data, dict) else []
    return [item for item in results if isinstance(item, dict)]
