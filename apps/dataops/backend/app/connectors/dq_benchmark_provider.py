"""K4 data-quality benchmark provider for DataOps."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from copilot_sdk.evidence.provenance import Provenanced

QUALITY_DIMENSIONS = (
    {
        "name": "completeness",
        "label": "Completeness",
        "description": "Required values are present and usable.",
        "standard": "ISO 8000 / DAMA DMBOK",
        "provenance": "scraped_external",
    },
    {
        "name": "accuracy",
        "label": "Accuracy",
        "description": "Values match the real-world entity they describe.",
        "standard": "ISO 8000 / DAMA DMBOK",
        "provenance": "scraped_external",
    },
    {
        "name": "timeliness",
        "label": "Timeliness",
        "description": "Values are current enough for operational use.",
        "standard": "ISO 8000 / DAMA DMBOK",
        "provenance": "scraped_external",
    },
    {
        "name": "consistency",
        "label": "Consistency",
        "description": "Values do not conflict across systems or records.",
        "standard": "ISO 8000 / DAMA DMBOK",
        "provenance": "scraped_external",
    },
    {
        "name": "uniqueness",
        "label": "Uniqueness",
        "description": "Entities are represented once without duplicate records.",
        "standard": "ISO 8000 / DAMA DMBOK",
        "provenance": "scraped_external",
    },
    {
        "name": "validity",
        "label": "Validity",
        "description": "Values conform to expected formats, ranges, and schemas.",
        "standard": "ISO 8000 / DAMA DMBOK",
        "provenance": "scraped_external",
    },
)

SCHEMA_FIXTURES = {
    "Person": {
        "@context": "https://schema.org",
        "@type": "Class",
        "name": "Person",
        "properties": ["name", "email", "telephone", "address"],
        "provenance": "sample",
    },
    "Organization": {
        "@context": "https://schema.org",
        "@type": "Class",
        "name": "Organization",
        "properties": ["name", "legalName", "taxID", "address"],
        "provenance": "sample",
    },
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


@dataclass
class DiskCacheEntry:
    value: dict[str, Any]
    as_of: str


class SchemaOrgSource:
    """Live Schema.org source for entity schemas."""

    provenance_tier = "scraped_external"

    def __init__(self, timeout: float = 3.0) -> None:
        self._timeout = timeout

    def fetch_schema(self, entity_type: str) -> dict[str, Any] | None:
        url = f"https://schema.org/{entity_type}.jsonld"
        with urllib.request.urlopen(url, timeout=self._timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            return None
        graph = payload.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict) and item.get("rdfs:label") == entity_type:
                    return _normalize_schema_org_payload(entity_type, item)
        return _normalize_schema_org_payload(entity_type, payload)


class DQBenchmarkProvider:
    """K4 data quality benchmark intelligence.

    Static ISO 8000 and DAMA DMBOK references are bundled published standards.
    Schema.org schemas use a cache cascade: cached -> live -> stale cached ->
    fixture(sample). Every public method returns Provenanced[T].
    """

    provenance_tier = "scraped_external"

    def __init__(
        self,
        *,
        cache_dir: Path | None = None,
        cache_ttl_hours: int = 24,
        source: Any | None = None,
    ) -> None:
        self._cache_dir = Path(cache_dir) if cache_dir is not None else Path.cwd() / ".dq_cache"
        self._cache_ttl = timedelta(hours=cache_ttl_hours)
        self._source = source if source is not None else SchemaOrgSource()

    def quality_dimensions(self) -> Provenanced[list[dict]]:
        """ISO 8000 + DAMA DMBOK quality dimensions."""
        return Provenanced(
            value=[dict(row) for row in QUALITY_DIMENSIONS],
            source=self.provenance_tier,
            label="ISO 8000 / DAMA DMBOK",
            as_of=now_iso(),
        )

    def schema_for_entity(self, entity_type: str) -> Provenanced[dict]:
        """Schema.org type definition for validation."""
        clean_type = _clean_entity_type(entity_type)
        cached = self._read_cache(clean_type)
        if cached is not None and self._is_fresh(cached.as_of):
            return Provenanced(value=cached.value, source="cached", as_of=cached.as_of)

        try:
            live = self._source.fetch_schema(clean_type)
            if live:
                live = dict(live)
                live.setdefault("provenance", self._source_provenance_tier())
                as_of = now_iso()
                self._write_cache(clean_type, live, as_of)
                return Provenanced(
                    value=live,
                    source=self._source_provenance_tier(),
                    as_of=as_of,
                )
        except Exception:
            pass

        if cached is not None:
            return Provenanced(value=cached.value, source="cached", as_of=cached.as_of)

        fixture = _schema_fixture(clean_type)
        return Provenanced(
            value=fixture,
            source="sample",
            label="sample schema fallback",
            as_of=now_iso(),
        )

    def benchmark_scores(self, metrics: dict) -> Provenanced[dict]:
        """Score metrics against ISO 8000 and DAMA DMBOK dimensions."""
        dimension_scores = {
            row["name"]: _score_metric(metrics.get(row["name"]))
            for row in QUALITY_DIMENSIONS
        }
        overall = round(sum(dimension_scores.values()) / len(dimension_scores), 3)
        status = "strong" if overall >= 0.9 else "watch" if overall >= 0.7 else "weak"
        return Provenanced(
            value={
                "overall_score": overall,
                "status": status,
                "dimension_scores": dimension_scores,
                "provenance": self.provenance_tier,
            },
            source=self.provenance_tier,
            label="ISO 8000 / DAMA DMBOK benchmark",
            as_of=now_iso(),
        )

    def _source_provenance_tier(self) -> str:
        return str(getattr(self._source, "provenance_tier", "scraped_external"))

    def _cache_path(self, entity_type: str) -> Path:
        return self._cache_dir / f"{entity_type.lower()}.json"

    def _read_cache(self, entity_type: str) -> DiskCacheEntry | None:
        path = self._cache_path(entity_type)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        value = payload.get("value")
        as_of = payload.get("as_of")
        if not isinstance(value, dict) or not isinstance(as_of, str):
            return None
        return DiskCacheEntry(value=value, as_of=as_of)

    def _write_cache(self, entity_type: str, value: dict[str, Any], as_of: str) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_path(entity_type).write_text(
            json.dumps({"as_of": as_of, "value": value}, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _is_fresh(self, as_of: str) -> bool:
        try:
            timestamp = datetime.fromisoformat(as_of)
        except ValueError:
            return False
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return now_utc() - timestamp <= self._cache_ttl


class MockDQBenchmarkProvider:
    """Sample fallback provider for DQ benchmark UI/tests."""

    provenance_tier = "sample"

    def quality_dimensions(self) -> Provenanced[list[dict]]:
        rows = [dict(row, provenance="sample") for row in QUALITY_DIMENSIONS]
        return Provenanced(value=rows, source="sample", label="sample dimensions")

    def schema_for_entity(self, entity_type: str) -> Provenanced[dict]:
        return Provenanced(
            value=_schema_fixture(_clean_entity_type(entity_type)),
            source="sample",
            label="sample schema",
        )

    def benchmark_scores(self, metrics: dict) -> Provenanced[dict]:
        real = DQBenchmarkProvider(source=_NullSource()).benchmark_scores(metrics)
        return Provenanced(
            value={**real.value, "provenance": "sample"},
            source="sample",
            label="sample benchmark",
        )


class _NullSource:
    provenance_tier = "sample"

    def fetch_schema(self, entity_type: str) -> None:
        return None


def _clean_entity_type(entity_type: str) -> str:
    text = "".join(char for char in str(entity_type or "") if char.isalnum() or char in "_-")
    return text or "Thing"


def _schema_fixture(entity_type: str) -> dict[str, Any]:
    if entity_type in SCHEMA_FIXTURES:
        return dict(SCHEMA_FIXTURES[entity_type])
    return {
        "@context": "https://schema.org",
        "@type": "Class",
        "name": entity_type,
        "properties": [],
        "provenance": "sample",
    }


def _score_metric(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number > 1.0:
        number = number / 100.0
    return round(max(0.0, min(number, 1.0)), 3)


def _normalize_schema_org_payload(entity_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    raw_properties = payload.get("properties") or payload.get("schema:domainIncludes") or []
    properties: list[str] = []
    if isinstance(raw_properties, list):
        for item in raw_properties:
            if isinstance(item, str):
                properties.append(item)
            elif isinstance(item, dict):
                name = item.get("@id") or item.get("name") or item.get("rdfs:label")
                if isinstance(name, str):
                    properties.append(name.rsplit("/", 1)[-1])
    return {
        "@context": "https://schema.org",
        "@type": "Class",
        "name": entity_type,
        "properties": sorted(set(properties)),
    }
