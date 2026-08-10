"""Static external data provider catalog for acquisition planning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).parent / "data" / "external_catalog.json"


@dataclass(frozen=True)
class CatalogEntry:
    provider_id: str
    provider_name: str
    description: str
    data_type: str
    cost_tier: str
    cost_detail: str
    integration: str
    api_url: str
    domains: list[str]
    expected_improvement_pp: dict[str, float]
    use_cases: list[str]
    freshness: str = ""
    coverage: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "description": self.description,
            "data_type": self.data_type,
            "cost_tier": self.cost_tier,
            "cost_detail": self.cost_detail,
            "integration": self.integration,
            "api_url": self.api_url,
            "domains": list(self.domains),
            "expected_improvement_pp": dict(self.expected_improvement_pp),
            "use_cases": list(self.use_cases),
            "freshness": self.freshness,
            "coverage": self.coverage,
        }


class ExternalDataCatalog:
    """Load and query the versioned external provider reference data."""

    def __init__(self, catalog_path: Path | None = None) -> None:
        self._entries = self._load(catalog_path or DEFAULT_PATH)

    def list_all(self) -> list[CatalogEntry]:
        return list(self._entries)

    def search(
        self,
        query: str = "",
        domain: str | None = None,
        cost_tier: str | None = None,
        data_type: str | None = None,
    ) -> list[CatalogEntry]:
        terms = [term for term in query.casefold().split() if term]
        normalized_domain = domain.casefold() if domain else None
        normalized_cost = cost_tier.casefold() if cost_tier else None
        normalized_type = data_type.casefold() if data_type else None
        result = []
        for entry in self._entries:
            searchable = " ".join(
                [entry.provider_id, entry.provider_name, entry.description, entry.data_type, *entry.domains, *entry.use_cases]
            ).casefold()
            if terms and not all(term in searchable for term in terms):
                continue
            if normalized_domain and normalized_domain not in {item.casefold() for item in entry.domains}:
                continue
            if normalized_cost and entry.cost_tier.casefold() != normalized_cost:
                continue
            if normalized_type and entry.data_type.casefold() != normalized_type:
                continue
            result.append(entry)
        return result

    def get_by_id(self, provider_id: str) -> CatalogEntry | None:
        target = provider_id.casefold()
        return next((entry for entry in self._entries if entry.provider_id.casefold() == target), None)

    def for_domain(self, domain: str) -> list[CatalogEntry]:
        return self.search(domain=domain)

    def estimated_value(self, provider_id: str, domain: str) -> float:
        entry = self.get_by_id(provider_id)
        if entry is None:
            return 0.0
        return float(entry.expected_improvement_pp.get(domain, 0.0))

    @staticmethod
    def _load(path: Path) -> list[CatalogEntry]:
        with path.open(encoding="utf-8") as handle:
            raw: object = json.load(handle)
        if not isinstance(raw, list):
            raise ValueError("external catalog must contain a JSON list")
        entries: list[CatalogEntry] = []
        for item in raw:
            if not isinstance(item, dict):
                raise ValueError("external catalog entries must be objects")
            entries.append(CatalogEntry(
                provider_id=str(item["provider_id"]),
                provider_name=str(item["provider_name"]),
                description=str(item["description"]),
                data_type=str(item["data_type"]),
                cost_tier=str(item["cost_tier"]),
                cost_detail=str(item.get("cost_detail", "")),
                integration=str(item["integration"]),
                api_url=str(item["api_url"]),
                domains=[str(value) for value in item.get("domains", [])],
                expected_improvement_pp={str(key): float(value) for key, value in dict(item.get("expected_improvement_pp", {})).items()},
                use_cases=[str(value) for value in item.get("use_cases", [])],
                freshness=str(item.get("freshness", "")),
                coverage=str(item.get("coverage", "")),
            ))
        return entries
