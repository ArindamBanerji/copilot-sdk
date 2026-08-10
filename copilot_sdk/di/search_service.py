"""Quality-aware search over registered data connectors."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from copilot_sdk.di.models import SourceProfile
from copilot_sdk.di.search_models import AssetResult, SearchResult


class DISearchService:
    """Search connector assets and apply deterministic quality filters."""

    def __init__(self, connectors: list[Any], profiler: Any) -> None:
        self.connectors = connectors
        self.profiler = profiler

    def search(self, query: str, filters: dict[str, object] | None = None) -> SearchResult:
        parsed = self._parse_filters(query)
        if filters:
            parsed.update({key: value for key, value in filters.items() if value is not None})
        text = re.sub(r"freshness\s*(?:above|over|below|under|>=|<=|>|<)\s*\d+(?:\.\d+)?\s*(?:hours?|h|%)?", " ", query, flags=re.I)
        text = re.sub(r"trust\s*tier\s*(?:=|is)?\s*\d+", " ", text, flags=re.I)
        text = re.sub(r"iks\s*(?:above|over|>=|>)\s*\d+(?:\.\d+)?", " ", text, flags=re.I)
        text = re.sub(r"quality\s*(?:status\s*)?(?:healthy|degraded|stale)", " ", text, flags=re.I)
        candidates = self._search_connectors(text, parsed)
        filtered = self._apply_quality_filters(candidates, parsed)
        ranked = self._rank_by_quality(filtered)
        limit = int(str(parsed.get("limit", 20)))
        results = ranked[: max(1, min(limit, 100))]
        return SearchResult(
            results=results,
            total=len(ranked),
            filters_applied=parsed,
            quality_summary=f"{len(ranked)} of {len(candidates)} assets match your quality criteria",
        )

    def _parse_filters(self, query: str) -> dict[str, object]:
        filters: dict[str, object] = {}
        text = query.lower()
        match = re.search(r"freshness\s*(?:above|over|>=|>)\s*(\d+(?:\.\d+)?)\s*%", text)
        if match:
            filters["freshness_min"] = float(match.group(1)) / 100.0
        match = re.search(r"freshness\s*(?:below|under|<=|<)\s*(\d+(?:\.\d+)?)\s*(hours?|h|%)", text)
        if match:
            value = float(match.group(1))
            filters["freshness_max"] = value / 100.0 if match.group(2).startswith("%") else value
        match = re.search(r"trust\s*tier\s*(?:=|is)?\s*(\d+)", text)
        if match:
            filters["trust_tier"] = int(match.group(1))
        match = re.search(r"iks\s*(?:above|over|>=|>)\s*(\d+(?:\.\d+)?)", text)
        if match:
            filters["iks_min"] = float(match.group(1))
        match = re.search(r"quality\s*(?:status\s*)?(healthy|degraded|stale)", text)
        if match:
            filters["quality_status"] = match.group(1)
        return filters

    def _search_connectors(self, text: str, filters: dict[str, object]) -> list[AssetResult]:
        lowered = text.lower()
        requested_types = {
            {"tables": "table", "models": "model", "dags": "dag"}[term]
            for term in ("tables", "models", "dags")
            if term in lowered
        }
        terms = [term for term in re.findall(r"[\w-]+", lowered) if term not in {"show", "me", "find", "which", "sources", "assets", "tables", "models", "dags", "where", "with", "have", "that", "and", "or"}]
        assets: list[AssetResult] = []
        for connector in self.connectors:
            mapper = getattr(connector, "to_map_nodes", None)
            nodes = mapper() if callable(mapper) else []
            for node in nodes:
                name = str(node.get("name") or node.get("source_name") or node.get("id", ""))
                asset_type = self._asset_type(connector, node)
                if requested_types and asset_type not in requested_types:
                    continue
                haystack = f"{name} {asset_type} {getattr(connector, 'source_name', '')}".lower()
                if terms and not all(term in haystack for term in terms):
                    continue
                trust_tier = int(node.get("trust_tier", getattr(connector, "trust_tier", 3)))
                trust_score = float(node.get("source_reliability", node.get("quality_score", self._tier_score(trust_tier))))
                freshness = self._freshness_hours(node, connector)
                status, issues = self._quality(trust_score, freshness, str(node.get("status_color", "")))
                iks = float(node.get("iks", node.get("quality_score", trust_score * 100.0) if node.get("quality_score", 0) > 1 else trust_score * 100.0))
                assets.append(AssetResult(
                    asset_id=str(node.get("id") or node.get("node_id") or name),
                    asset_name=name,
                    asset_type=asset_type,
                    source_connector=str(getattr(connector, "source_name", "unknown")),
                    trust_tier=trust_tier,
                    trust_score=max(0.0, min(1.0, trust_score)),
                    freshness_hours=freshness,
                    quality_status=status,
                    quality_issues=issues,
                    match_reason="Matched asset name, type, or connector" if terms else "All registered assets",
                    iks=iks,
                ))
        return assets

    def _apply_quality_filters(self, assets: list[AssetResult], filters: dict[str, object]) -> list[AssetResult]:
        result = assets
        if "trust_tier" in filters:
            result = [asset for asset in result if asset.trust_tier == int(str(filters["trust_tier"]))]
        if "freshness_max" in filters:
            result = [asset for asset in result if asset.freshness_hours is not None and asset.freshness_hours <= float(str(filters["freshness_max"]))]
        if "freshness_min" in filters:
            result = [asset for asset in result if asset.freshness_hours is not None and asset.freshness_hours <= 24 * (1 - float(str(filters["freshness_min"]))) ]
        if "quality_status" in filters:
            result = [asset for asset in result if asset.quality_status == str(filters["quality_status"])]
        if "iks_min" in filters:
            result = [asset for asset in result if asset.iks >= float(str(filters["iks_min"]))]
        return result

    def _rank_by_quality(self, assets: list[AssetResult]) -> list[AssetResult]:
        return sorted(assets, key=lambda asset: (asset.trust_score * self._freshness_score(asset.freshness_hours), asset.trust_score), reverse=True)

    def _freshness_hours(self, node: dict[str, Any], connector: Any) -> float | None:
        if node.get("freshness_hours") is not None:
            return float(node["freshness_hours"])
        name = str(node.get("name", ""))
        try:
            rows = connector.fetch(name if getattr(connector, "source_name", "") == "dbt" else "all")
            timestamps = [row.get("last_altered") or row.get("run_started_at") or row.get("timestamp") or row.get("execution_date") for row in rows if str(row.get("table_name") or row.get("model_name") or row.get("dag_id")) == name]
            valid = [self._hours_since(value) for value in timestamps if value]
            return min(valid) if valid else None
        except Exception:
            return None

    @staticmethod
    def _hours_since(value: Any) -> float:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 3600.0)

    @staticmethod
    def _asset_type(connector: Any, node: dict[str, Any]) -> str:
        source = str(getattr(connector, "source_name", ""))
        return {"snowflake": "table", "dbt": "model", "airflow": "dag"}.get(source, str(node.get("entity_type", "source")))

    @staticmethod
    def _tier_score(tier: int) -> float:
        return {1: 0.95, 2: 0.8, 3: 0.6}.get(tier, 0.5)

    @staticmethod
    def _quality(trust: float, freshness: float | None, status_color: str) -> tuple[str, list[str]]:
        issues: list[str] = []
        if status_color == "red" or trust < 0.6:
            issues.append("low source reliability")
        if status_color == "amber":
            issues.append("connector reports a warning")
        if freshness is None or freshness > 24:
            issues.append("stale or unavailable freshness metadata")
        if status_color == "red" or trust < 0.6 or (freshness is not None and freshness > 48):
            return "stale", issues
        if status_color == "amber" or (freshness is not None and freshness > 24):
            return "degraded", issues
        return "healthy", issues

    @staticmethod
    def _freshness_score(hours: float | None) -> float:
        return 0.5 if hours is None else max(0.0, min(1.0, 1.0 - hours / 168.0))
