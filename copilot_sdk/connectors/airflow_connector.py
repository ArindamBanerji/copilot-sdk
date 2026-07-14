"""Airflow REST metadata connector."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AirflowConnector:
    """Airflow REST API client. No apache-airflow dependency."""

    source_name = "airflow"
    entity_type = "orchestration"
    trust_tier = 2

    _VALID_STATES = {"success", "failed", "running", "queued"}

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080/api/v1",
        username: str = "",
        password: str = "",
        token: str = "",
    ) -> None:
        self._base_url = base_url
        self._username = username
        self._password = password
        self._token = token

    @property
    def _connected(self) -> bool:
        return bool(self._base_url and (self._username or self._token))

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RuntimeError(
                f"{self.source_name} connector not configured. "
                f"Use Mock{self.__class__.__name__} for demo mode."
            )

    def _request_json(self, path: str) -> dict[str, Any]:
        self._ensure_connected()
        url = f"{self._base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=5) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            raise RuntimeError(f"airflow API request failed with status {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError("airflow API request failed") from exc
        return cast(dict[str, Any], json.loads(payload))

    def fetch(self, entity_id: str = "all") -> list[dict[str, Any]]:
        self._ensure_connected()
        path = "dags/~/dagRuns?limit=100"
        if entity_id != "all":
            path = f"dags/{entity_id}/dagRuns?limit=100"
        payload = self._request_json(path)
        rows: list[dict[str, Any]] = []
        for run in payload.get("dag_runs", []):
            dag_id = run.get("dag_id") or entity_id
            rows.append(
                {
                    "dag_id": dag_id,
                    "run_id": run.get("dag_run_id") or run.get("run_id"),
                    "state": run.get("state"),
                    "execution_date": run.get("execution_date") or run.get("logical_date"),
                    "start_date": run.get("start_date"),
                    "end_date": run.get("end_date"),
                    "duration_seconds": run.get("duration_seconds", 0),
                    "timestamp": run.get("start_date") or run.get("execution_date"),
                    "provenance": "live",
                }
            )
        return rows

    def fetch_tasks(self, dag_id: str, run_id: str) -> list[dict[str, Any]]:
        if not dag_id or not run_id:
            raise ValueError("dag_id and run_id are required")
        self._ensure_connected()
        payload = self._request_json(f"dags/{dag_id}/dagRuns/{run_id}/taskInstances")
        rows: list[dict[str, Any]] = []
        for task in payload.get("task_instances", []):
            rows.append(
                {
                    "dag_id": dag_id,
                    "run_id": run_id,
                    "task_id": task.get("task_id"),
                    "state": task.get("state"),
                    "duration_seconds": task.get("duration") or task.get("duration_seconds") or 0,
                    "try_number": task.get("try_number", 0),
                    "operator": task.get("operator"),
                    "provenance": "live",
                }
            )
        return rows

    def fetch_dag_stats(self, dag_id: str, days: int = 30) -> dict[str, Any]:
        if not dag_id:
            raise ValueError("dag_id is required")
        if days < 1:
            raise ValueError("days must be positive")
        self._ensure_connected()
        since = datetime.now(timezone.utc) - timedelta(days=days)
        runs = [
            run
            for run in self.fetch(dag_id)
            if not run.get("execution_date") or str(run.get("execution_date")) >= since.isoformat()
        ]
        completed = [run for run in runs if run.get("state") in {"success", "failed"}]
        success = sum(1 for run in completed if run.get("state") == "success")
        failed = sum(1 for run in completed if run.get("state") == "failed")
        durations = [float(run.get("duration_seconds", 0) or 0) for run in completed]
        run_count = len(completed)
        return {
            "success_rate": success / run_count if run_count else 0.0,
            "avg_duration_s": sum(durations) / len(durations) if durations else 0.0,
            "failure_rate": failed / run_count if run_count else 0.0,
            "avg_retry_count": 0.0,
            "run_count": run_count,
            "failure_pattern": None,
            "provenance": "live",
        }

    def validate(self, record: dict[str, Any]) -> bool:
        try:
            state = str(record.get("state", ""))
            duration = float(record.get("duration_seconds", -1))
        except (TypeError, ValueError):
            return False
        return bool(record.get("dag_id")) and state in self._VALID_STATES and duration >= 0

    def to_map_nodes(self) -> list[dict[str, Any]]:
        dag_ids = sorted({str(run.get("dag_id")) for run in self.fetch() if run.get("dag_id")})
        nodes = []
        for dag_id in dag_ids:
            stats = self.fetch_dag_stats(dag_id)
            success_rate = float(stats.get("success_rate", 0.0) or 0.0)
            color = "green" if success_rate > 0.9 else "amber" if success_rate >= 0.7 else "red"
            nodes.append(
                {
                    "id": f"airflow_{dag_id}".lower(),
                    "node_id": f"airflow_{dag_id}".lower(),
                    "name": dag_id,
                    "source_name": dag_id,
                    "domain": "data_engineering",
                    "entity_type": self.entity_type,
                    "trust_tier": self.trust_tier,
                    "source_reliability": success_rate,
                    "record_count": int(stats.get("run_count", 0) or 0),
                    "success_rate": success_rate,
                    "status_color": color,
                    "quality_score": success_rate,
                    "provenance": "live",
                }
            )
        return nodes

    def __str__(self) -> str:
        return f"AirflowConnector(url={self._base_url})"

    __repr__ = __str__
