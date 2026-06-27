"""dbt metadata connector."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


class DBTConnector:
    """dbt Cloud API or local artifact connector."""

    source_name = "dbt"
    entity_type = "transformation"
    trust_tier = 2

    _VALID_STATUSES = {"pass", "warn", "error", "skipped"}

    def __init__(self, api_token: str = "", account_id: str = "", artifacts_path: str | None = None) -> None:
        self._api_token = api_token
        self._account_id = account_id
        self._artifacts_path = artifacts_path

    @property
    def _connected(self) -> bool:
        return bool(self._api_token or self._artifacts_path)

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RuntimeError(
                f"{self.source_name} connector not configured. "
                f"Use Mock{self.__class__.__name__} for demo mode."
            )

    def _artifact_file(self, filename: str) -> Path:
        self._ensure_connected()
        if not self._artifacts_path:
            raise RuntimeError("dbt artifacts_path is required for local artifact reads")
        return Path(self._artifacts_path) / filename

    def _read_artifact(self, filename: str) -> dict[str, Any]:
        path = self._artifact_file(filename)
        with path.open(encoding="utf-8") as handle:
            return cast(dict[str, Any], json.load(handle))

    def fetch(self, entity_id: str = "latest") -> list[dict[str, Any]]:
        self._ensure_connected()
        if self._artifacts_path:
            manifest = self._read_artifact("manifest.json")
            run_results_path = self._artifact_file("run_results.json")
            run_results = {}
            if run_results_path.exists():
                run_results = self._read_artifact("run_results.json")
            result_by_id = {item.get("unique_id"): item for item in run_results.get("results", [])}
            rows: list[dict[str, Any]] = []
            for unique_id, node in manifest.get("nodes", {}).items():
                if node.get("resource_type") != "model":
                    continue
                name = str(node.get("name", ""))
                if entity_id not in ("latest", "all", name, unique_id):
                    continue
                result = result_by_id.get(unique_id, {})
                rows.append(
                    {
                        "model_name": name,
                        "status": result.get("status", "pass"),
                        "execution_time_s": result.get("execution_time", 0),
                        "rows_affected": result.get("adapter_response", {}).get("rows_affected", 0),
                        "run_started_at": run_results.get("metadata", {}).get("generated_at"),
                        "created_at": run_results.get("metadata", {}).get("generated_at"),
                        "provenance": "live",
                    }
                )
            return rows
        if not self._account_id:
            raise RuntimeError("dbt account_id is required for dbt Cloud API reads")
        raise RuntimeError("dbt Cloud API fetch is not implemented without an HTTP client")

    def fetch_tests(self) -> list[dict[str, Any]]:
        self._ensure_connected()
        if self._artifacts_path:
            run_results = self._read_artifact("run_results.json")
            manifest_path = self._artifact_file("manifest.json")
            manifest = self._read_artifact("manifest.json") if manifest_path.exists() else {}
            rows: list[dict[str, Any]] = []
            for result in run_results.get("results", []):
                unique_id = str(result.get("unique_id", ""))
                node = manifest.get("nodes", {}).get(unique_id, {})
                if node.get("resource_type") != "test" and not unique_id.startswith("test."):
                    continue
                depends_on = node.get("depends_on", {}).get("nodes", [])
                model_name = ""
                for dependency in depends_on:
                    model = manifest.get("nodes", {}).get(dependency, {})
                    if model.get("resource_type") == "model":
                        model_name = str(model.get("name", ""))
                        break
                rows.append(
                    {
                        "test_name": node.get("name") or unique_id,
                        "model_name": model_name,
                        "status": result.get("status", "pass"),
                        "failures": result.get("failures", 0),
                        "provenance": "live",
                    }
                )
            return rows
        if not self._account_id:
            raise RuntimeError("dbt account_id is required for dbt Cloud API reads")
        raise RuntimeError("dbt Cloud API test fetch is not implemented without an HTTP client")

    def fetch_freshness(self) -> list[dict[str, Any]]:
        self._ensure_connected()
        if self._artifacts_path:
            sources_path = self._artifact_file("sources.json")
            if not sources_path.exists():
                return []
            sources = self._read_artifact("sources.json")
            rows: list[dict[str, Any]] = []
            for result in sources.get("results", []):
                unique_id = str(result.get("unique_id", ""))
                max_loaded_at = result.get("max_loaded_at")
                status = str(result.get("status", "pass"))
                rows.append(
                    {
                        "model_name": unique_id.rsplit(".", 1)[-1],
                        "last_run": max_loaded_at,
                        "hours_since_run": result.get("snapshotted_at_age", 0),
                        "is_stale": status in {"warn", "error"},
                        "provenance": "live",
                    }
                )
            return rows
        if not self._account_id:
            raise RuntimeError("dbt account_id is required for dbt Cloud API reads")
        raise RuntimeError("dbt Cloud API freshness fetch is not implemented without an HTTP client")

    def validate(self, record: dict[str, Any]) -> bool:
        try:
            status = str(record.get("status", ""))
            runtime = float(record.get("execution_time_s", -1))
        except (TypeError, ValueError):
            return False
        return bool(record.get("model_name")) and status in self._VALID_STATUSES and runtime >= 0

    def to_map_nodes(self) -> list[dict[str, Any]]:
        tests = self.fetch_tests()
        failing_models = {str(item.get("model_name")) for item in tests if item.get("status") == "error"}
        stale = {str(item.get("model_name")) for item in self.fetch_freshness() if item.get("is_stale")}
        nodes: list[dict[str, Any]] = []
        for model in self.fetch():
            name = str(model.get("model_name", ""))
            color = "green"
            quality = 0.95
            if name in failing_models or model.get("status") == "error":
                color = "red"
                quality = 0.45
            elif name in stale or model.get("status") == "warn":
                color = "amber"
                quality = 0.7
            nodes.append(
                {
                    "id": f"dbt_{name}".lower(),
                    "node_id": f"dbt_{name}".lower(),
                    "name": name,
                    "source_name": name,
                    "domain": "data_engineering",
                    "entity_type": self.entity_type,
                    "trust_tier": self.trust_tier,
                    "source_reliability": quality,
                    "record_count": int(model.get("rows_affected", 0) or 0),
                    "status_color": color,
                    "quality_score": quality,
                    "provenance": model.get("provenance", "live"),
                }
            )
        return nodes

    def __str__(self) -> str:
        return f"DBTConnector(account={self._account_id})"

    __repr__ = __str__
