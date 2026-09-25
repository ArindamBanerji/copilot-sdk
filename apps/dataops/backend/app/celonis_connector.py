"""Celonis Knowledge Model API with captured-response and sample fallbacks.

API contract: https://developer.celonis.com/process-intelligence-apis/knowledge-model-api/api-reference/try-it/
The public Remockly service is a developer demo, not a customer tenant.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from apps.dataops.backend.app.connector_cache import ConnectorCache

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_CELONIS_URL = "https://16abf815-424c-413e-b92d-6c6f8fc633cd.remockly.com/intelligence/api"
DEMO_KM_ID = "open-purchase-requisition.purchase-requisition-km"
SAMPLE_KM_ID = "km-p2p-dataops"


class CelonisConnector:
    provenance_tier = "sample"

    def __init__(self, base_url: str | None = None, token: str | None = None,
                 cache_dir: str | Path | None = None, timeout: float = 10.0) -> None:
        env_url, env_token = os.getenv("CELONIS_URL"), os.getenv("CELONIS_TOKEN")
        self.base_url = (base_url or env_url or DEFAULT_CELONIS_URL).rstrip("/")
        self.is_demo = urlparse(self.base_url).hostname == urlparse(DEFAULT_CELONIS_URL).hostname
        self.token = token if token is not None else env_token or ("demo-token" if self.is_demo else "")
        self.cache_dir = Path(cache_dir) if cache_dir is not None else DATA_DIR
        self.timeout = timeout
        self.last_source = "celonis_cache"
        self._live_enabled = bool(base_url or env_url or token or env_token or
                                  os.getenv("CELONIS_LIVE", "").lower() == "true")
        self._cache = ConnectorCache(self.cache_dir, f"celonis:{self.base_url}:{self.token}")

    async def _collection(self, endpoint: str, key: str, filename: str,
                          allow_sample: bool = True) -> dict[str, Any]:
        try:
            payload, live = await self._cache.fetch(endpoint, None, self._request_json,
                                                   lambda value: _list_from_payload(value, key))
            rows = _list_from_payload(payload, key)
            provenance = "sandbox" if self.is_demo else "external"
        except (RuntimeError, ValueError):
            rows = self._load_cache_list(filename) if allow_sample else []
            live, provenance = False, "sample"
        self.last_source = "celonis_live" if live else "celonis_cache"
        return {"source": self.last_source, "provenance": provenance, key: rows}

    async def get_knowledge_models(self) -> dict[str, Any]:
        return await self._collection("/knowledge-models", "knowledge_models", "celonis_knowledge_models.json")

    async def get_kpis(self, km_id: str) -> dict[str, Any]:
        return await self._collection(f"/knowledge-models/{quote(km_id, safe='')}/kpis", "kpis",
                                      "celonis_kpis.json", allow_sample=km_id == SAMPLE_KM_ID)

    async def get_process_data(self, km_id: str, fields: list[str] | None = None,
                               kpis: list[str] | None = None) -> dict[str, Any]:
        params: dict[str, str] = {}
        if self.is_demo and km_id == DEMO_KM_ID and fields is None and kpis is None:
            fields, kpis = ["MATERIALS.ACTIVITY"], ["AVG_EVENTS_PER_CASE", "FILTERED_COUNT"]
        if fields:
            params["fields"] = ",".join(fields)
        if kpis:
            params["kpis"] = ",".join(kpis)
        try:
            payload, live = await self._cache.fetch(
                f"/knowledge-models/{quote(km_id, safe='')}/data", params,
                self._request_json, _process_payload)
            process = _process_payload(payload)
            provenance = "sandbox" if self.is_demo else "external"
        except (RuntimeError, ValueError):
            # The checked-in P2P scenario is not data for an arbitrary customer KM.
            process = self._load_cache_dict("celonis_process_data.json") if km_id == SAMPLE_KM_ID and not params else {}
            live, provenance = False, "sample"
        self.last_source = "celonis_live" if live else "celonis_cache"
        return {"source": self.last_source, "provenance": provenance,
                "process_data": {**process, "source": self.last_source, "provenance": provenance} if process else {}}

    async def health(self) -> dict[str, Any]:
        payload = await self.get_knowledge_models()
        live = payload["source"] == "celonis_live"
        count = len(payload["knowledge_models"])
        return {"status": "ok" if live else "cache" if count else "unavailable",
                "live": live, "connected": live, "cached": not live and bool(count),
                "source": payload["source"], "km_count": count,
                "cached_models": 0 if live else count, "provenance": payload["provenance"]}

    async def _request_json(self, endpoint: str, params: dict[str, str] | None = None) -> Any:
        if not self._live_enabled or not self.token:
            raise RuntimeError("Celonis live connection is not configured")
        import httpx
        # Keep certificate verification enabled. TLS errors follow the cache path.
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}{endpoint}", params=params,
                                        headers={"Accept": "application/json", "Authorization": f"Bearer {self.token}"})
            response.raise_for_status()
            return response.json()

    def _load_cache_list(self, filename: str) -> list[dict[str, Any]]:
        payload = self._load_cache_dict(filename)
        key = "knowledge_models" if filename == "celonis_knowledge_models.json" else "kpis"
        try:
            return _list_from_payload(payload, key)
        except ValueError:
            return []

    def _load_cache_dict(self, filename: str) -> dict[str, Any]:
        try:
            payload = json.loads((self.cache_dir / filename).read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (OSError, ValueError):
            return {}


def _list_from_payload(payload: Any, key: str) -> list[dict[str, Any]]:
    raw = payload
    if isinstance(payload, dict):
        raw = next((payload[name] for name in (key, "content", "items", "data") if name in payload), None)
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise ValueError("Expected a Celonis collection")
    return raw


def _process_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Expected Celonis KM data object")
    process = payload.get("process_data", payload)
    if not isinstance(process, dict) or not any(key in process for key in ("content", "activities", "process_model")):
        raise ValueError("Expected Celonis data content")
    # /data contains selected record fields and KPIs, not automatically durations.
    # Preserve the raw result; do not invent timing metrics from event counts.
    return process
