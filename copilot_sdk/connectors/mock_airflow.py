"""Mock Airflow connector for demos and tests."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from copilot_sdk.connectors.airflow_connector import AirflowConnector


class MockAirflowConnector(AirflowConnector):
    """Eight DAGs, thirty runs, and deterministic task metadata. No network."""

    source_name = "airflow"

    _DAGS = [
        "etl_orders",
        "etl_customers",
        "etl_products",
        "sync_inventory",
        "report_daily",
        "ml_training",
        "data_quality",
        "backup_nightly",
    ]

    def fetch(self, entity_id: str = "all") -> list[dict[str, Any]]:
        base = datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc)
        failed_indices = {0, 7, 14, 21}
        running_indices = {28, 29}
        rows = []
        for index in range(30):
            state = "failed" if index in failed_indices else "running" if index in running_indices else "success"
            dag_id = self._DAGS[index % len(self._DAGS)]
            if index in failed_indices:
                dag_id = "etl_orders"
            if entity_id not in ("all", dag_id):
                continue
            start = base + timedelta(days=index)
            duration = 180 if dag_id == "data_quality" else 2700 if dag_id == "ml_training" else 900 + index * 10
            rows.append(
                {
                    "dag_id": dag_id,
                    "run_id": f"scheduled__{index + 1:03d}",
                    "state": state,
                    "execution_date": start.isoformat(),
                    "start_date": start.isoformat(),
                    "end_date": (start + timedelta(seconds=duration)).isoformat() if state != "running" else None,
                    "duration_seconds": duration,
                    "timestamp": start.isoformat(),
                    "provenance": "demo",
                }
            )
        return rows

    def fetch_tasks(self, dag_id: str, run_id: str) -> list[dict[str, Any]]:
        if dag_id not in self._DAGS:
            return []
        operators = ["SnowflakeOperator", "DbtRunOperator", "PythonOperator", "SQLCheckOperator", "EmailOperator"]
        return [
            {
                "dag_id": dag_id,
                "run_id": run_id,
                "task_id": f"{dag_id}_task_{index}",
                "state": "success" if index % 5 else "failed",
                "duration_seconds": 60 + index * 45,
                "try_number": 1 if index % 5 else 2,
                "operator": operators[index % len(operators)],
                "provenance": "demo",
            }
            for index in range(1, 7)
        ]

    def fetch_dag_stats(self, dag_id: str, days: int = 30) -> dict[str, Any]:
        runs = self.fetch(dag_id)
        if days < 1:
            raise ValueError("days must be positive")
        if not runs:
            return super().fetch_dag_stats(dag_id, days)
        completed = [run for run in runs if run["state"] in {"success", "failed"}]
        success = sum(1 for run in completed if run["state"] == "success")
        failed = sum(1 for run in completed if run["state"] == "failed")
        run_count = len(completed)
        failure_days = Counter(
            datetime.fromisoformat(str(run["execution_date"])).strftime("%A")
            for run in completed
            if run["state"] == "failed"
        )
        failure_pattern = failure_days.most_common(1)[0][0] if failure_days else None
        durations = [float(run["duration_seconds"]) for run in completed]
        return {
            "success_rate": success / run_count if run_count else 0.0,
            "avg_duration_s": sum(durations) / len(durations) if durations else 0.0,
            "failure_rate": failed / run_count if run_count else 0.0,
            "avg_retry_count": 0.3 if failed else 0.0,
            "run_count": run_count,
            "failure_pattern": failure_pattern,
            "provenance": "demo",
        }

    def to_map_nodes(self) -> list[dict[str, Any]]:
        nodes = super().to_map_nodes()
        for node in nodes:
            node["provenance"] = "demo"
            if node["name"] == "etl_orders":
                node["status_color"] = "red"
                node["success_rate"] = 0.8
                node["source_reliability"] = 0.8
            elif node["name"] == "ml_training":
                node["status_color"] = "amber"
                node["success_rate"] = 0.85
                node["source_reliability"] = 0.85
            elif node["name"] == "data_quality":
                node["status_color"] = "green"
                node["success_rate"] = 1.0
                node["source_reliability"] = 1.0
        return nodes
