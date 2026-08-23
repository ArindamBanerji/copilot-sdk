"""DataOps graph enrichment service."""

from __future__ import annotations

import hashlib
import asyncio
import inspect
import json
from datetime import datetime, timezone
from typing import Any


DATAOPS_DOMAIN = "dataops"


class DataOpsGraphEnricher:
    """Write idempotent enrichment records through a graph-store abstraction."""

    def write_enrichment(
        self,
        graph_store: Any,
        source_ids: list[str],
        enrichment_type: str,
        payload: dict[str, Any],
    ) -> str:
        normalized_sources = _normalize_sources(source_ids)
        normalized_type = str(enrichment_type or "").strip()
        if not normalized_sources:
            raise ValueError("source_ids is required")
        if not normalized_type:
            raise ValueError("enrichment_type is required")
        enrichment_id = _enrichment_id(normalized_sources, normalized_type)
        record = {
            "enrichment_id": enrichment_id,
            "source_ids": normalized_sources,
        "enrichment_type": normalized_type,
        "payload": dict(payload or {}),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "domain": DATAOPS_DOMAIN,
        }

        writer = getattr(graph_store, "write_enrichment", None)
        if callable(writer):
            written_id = writer(record)
            self._link_sources(graph_store, enrichment_id, normalized_sources)
            return str(written_id or enrichment_id)

        upsert = getattr(graph_store, "upsert_enrichment_node", None)
        if callable(upsert):
            written_id = upsert(**record)
            self._link_sources(graph_store, enrichment_id, normalized_sources)
            return str(written_id or enrichment_id)

        run_query = getattr(graph_store, "run_query", None)
        if callable(run_query):
            result = _run_graph_query(
                run_query,
                _age_find_query(),
                {"enrichment_id": enrichment_id, "domain": DATAOPS_DOMAIN},
            )
            query = _age_update_query() if result else _age_create_query()
            result = _run_graph_query(run_query, query, record)
            self._link_sources(graph_store, enrichment_id, normalized_sources)
            if isinstance(result, list) and result:
                return str(result[0].get("enrichment_id") or enrichment_id)
            return enrichment_id

        raise TypeError("graph_store does not support enrichment writes")

    def _link_sources(self, graph_store: Any, enrichment_id: str, source_ids: list[str]) -> None:
        linker = getattr(graph_store, "link_enrichment_source", None)
        if callable(linker):
            for source_id in source_ids:
                linker(enrichment_id, source_id)


def _normalize_sources(source_ids: list[str]) -> list[str]:
    return sorted({str(source_id).strip() for source_id in source_ids if str(source_id).strip()})


def _enrichment_id(source_ids: list[str], enrichment_type: str) -> str:
    digest = hashlib.sha256(
        json.dumps(
            {"source_ids": source_ids, "enrichment_type": enrichment_type},
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"enrichment-{digest}"


def _run_graph_query(run_query: Any, query: str, parameters: dict[str, Any]) -> Any:
    result = run_query(query, parameters)
    if inspect.isawaitable(result):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(result)
        raise RuntimeError("async graph query must be awaited by the caller")
    return result


def _age_find_query() -> str:
    return """
    MATCH (existing:EnrichmentNode {enrichment_id: $enrichment_id})
    WHERE existing.domain = $domain
    RETURN existing.enrichment_id AS enrichment_id
    """


def _age_update_query() -> str:
    return """
    MATCH (existing:EnrichmentNode {enrichment_id: $enrichment_id})
    WHERE existing.domain = $domain
    SET existing.domain = $domain,
        existing.source_ids = $source_ids,
        existing.enrichment_type = $enrichment_type,
        existing.payload = $payload,
        existing.timestamp = $timestamp
    RETURN existing.enrichment_id AS enrichment_id
    """


def _age_create_query() -> str:
    return """
    CREATE (node:EnrichmentNode {
        domain: $domain,
        enrichment_id: $enrichment_id,
        source_ids: $source_ids,
        enrichment_type: $enrichment_type,
        payload: $payload,
        timestamp: $timestamp
    })
    RETURN node.enrichment_id AS enrichment_id
    """
