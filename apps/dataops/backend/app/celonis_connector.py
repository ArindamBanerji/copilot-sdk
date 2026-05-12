"""Celonis connector with deterministic cache fallback for DataOps demos."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_CELONIS_URL = "https://developer.celonis.com/demo"


class CelonisConnector:
    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        cache_dir: str | Path | None = None,
        timeout: float = 5.0,
    ) -> None:
        env_base_url = os.getenv("CELONIS_URL")
        env_token = os.getenv("CELONIS_TOKEN")
        self.base_url = (base_url or env_base_url or DEFAULT_CELONIS_URL).rstrip("/")
        self.token = token if token is not None else env_token or "demo-token"
        self.cache_dir = Path(cache_dir) if cache_dir is not None else DATA_DIR
        self.timeout = timeout
        self.last_source = "celonis_cache"
        self._live_enabled = bool(base_url or env_base_url or token or env_token)

    async def get_knowledge_models(self) -> dict[str, Any]:
        try:
            payload = await self._request_json("/knowledge-models")
            models = _list_from_payload(payload, "knowledge_models")
            self.last_source = "celonis_live"
            return {"source": "celonis_live", "knowledge_models": models}
        except Exception as exc:
            logger.warning("Celonis knowledge model fetch failed; using cache: %s", exc)
            models = self._load_cache_list("celonis_knowledge_models.json")
            self.last_source = "celonis_cache"
            return {"source": "celonis_cache", "knowledge_models": models}

    async def get_kpis(self, km_id: str) -> dict[str, Any]:
        try:
            payload = await self._request_json(f"/knowledge-models/{km_id}/kpis")
            kpis = _list_from_payload(payload, "kpis")
            self.last_source = "celonis_live"
            return {"source": "celonis_live", "kpis": kpis}
        except Exception as exc:
            logger.warning("Celonis KPI fetch failed for %s; using cache: %s", km_id, exc)
            kpis = self._load_cache_list("celonis_kpis.json")
            self.last_source = "celonis_cache"
            return {"source": "celonis_cache", "kpis": kpis}

    async def get_process_data(
        self,
        km_id: str,
        fields: list[str] | None = None,
        kpis: list[str] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {}
        if fields:
            params["fields"] = ",".join(fields)
        if kpis:
            params["kpis"] = ",".join(kpis)
        try:
            payload = await self._request_json(f"/knowledge-models/{km_id}/process-data", params=params)
            process_data = payload.get("process_data", payload) if isinstance(payload, dict) else {}
            self.last_source = "celonis_live"
            return {"source": "celonis_live", "process_data": process_data if isinstance(process_data, dict) else {}}
        except Exception as exc:
            logger.warning("Celonis process data fetch failed for %s; using cache: %s", km_id, exc)
            process_data = self._load_cache_dict("celonis_process_data.json")
            self.last_source = "celonis_cache"
            return {"source": "celonis_cache", "process_data": process_data}

    async def health(self) -> dict[str, Any]:
        try:
            await self._request_json("/knowledge-models")
            return {"status": "ok", "live": True, "source": "celonis_live"}
        except Exception as exc:
            logger.warning("Celonis health check failed; using cache fallback: %s", exc)
            models = self._load_cache_list("celonis_knowledge_models.json")
            return {
                "status": "cache",
                "live": False,
                "source": "celonis_cache",
                "cached_models": len(models),
            }

    async def _request_json(self, endpoint: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        if not self._live_enabled:
            raise RuntimeError("Celonis live connection is not configured")
        import httpx

        headers = {"Accept": "application/json", "Authorization": f"Bearer {self.token}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    def _load_cache_list(self, filename: str) -> list[dict[str, Any]]:
        payload = self._load_cache_dict(filename)
        for value in payload.values():
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        logger.warning("Celonis cache file %s did not contain a list payload", filename)
        return []

    def _load_cache_dict(self, filename: str) -> dict[str, Any]:
        path = self.cache_dir / filename
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Celonis cache file %s could not be loaded: %s", filename, exc)
            return {}
        if isinstance(payload, dict):
            return payload
        logger.warning("Celonis cache file %s did not contain a dict payload", filename)
        return {}


def _list_from_payload(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    raw = payload.get(key) or payload.get("items") or payload.get("data") or []
    return [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []
