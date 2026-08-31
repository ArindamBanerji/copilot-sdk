"""Mock dbt connector for demos and tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from copilot_sdk.connectors.dbt_connector import DBTConnector


class DemoDBTConnector(DBTConnector):
    """Fifteen models and eight test results. No network."""

    source_name = "dbt"

    _MODELS = [
        "stg_orders",
        "stg_customers",
        "stg_products",
        "stg_suppliers",
        "stg_invoices",
        "int_order_items",
        "int_customer_orders",
        "fct_orders",
        "fct_revenue",
        "fct_supplier_performance",
        "dim_customers",
        "dim_products",
        "dim_suppliers",
        "dim_dates",
        "rpt_executive_summary",
    ]

    def fetch(self, entity_id: str = "latest") -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        rows = []
        for index, model_name in enumerate(self._MODELS):
            if entity_id not in ("latest", "all", model_name):
                continue
            status = "warn" if model_name in {"stg_customers", "fct_orders"} else "pass"
            if model_name == "fct_orders":
                status = "error"
            started = now - timedelta(hours=index + 1)
            rows.append(
                {
                    "model_name": model_name,
                    "status": status,
                    "execution_time_s": 12.5 + index * 3.2,
                    "rows_affected": 1_000 + index * 750,
                    "run_started_at": started.isoformat(),
                    "created_at": started.isoformat(),
                    "provenance": "demo",
                }
            )
        return rows

    def fetch_tests(self) -> list[dict[str, Any]]:
        rows = [
            ("not_null_stg_orders_order_id", "stg_orders", "pass", 0),
            ("unique_stg_orders_order_id", "stg_orders", "pass", 0),
            ("not_null_stg_customers_customer_id", "stg_customers", "warn", 12),
            ("accepted_values_dim_products_status", "dim_products", "pass", 0),
            ("relationships_fct_orders_customer_id", "fct_orders", "error", 41),
            ("not_null_fct_revenue_amount", "fct_revenue", "pass", 0),
            ("freshness_stg_invoices", "stg_invoices", "warn", 3),
            ("unique_dim_suppliers_supplier_id", "dim_suppliers", "pass", 0),
        ]
        return [
            {
                "test_name": test_name,
                "model_name": model_name,
                "status": status,
                "failures": failures,
                "provenance": "demo",
            }
            for test_name, model_name, status, failures in rows
        ]

    def fetch_freshness(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        stale_models = {"stg_customers": 30.0, "fct_orders": 49.0}
        rows = []
        for index, model_name in enumerate(self._MODELS):
            hours = stale_models.get(model_name, float(index + 1))
            rows.append(
                {
                    "model_name": model_name,
                    "last_run": (now - timedelta(hours=hours)).isoformat(),
                    "hours_since_run": hours,
                    "is_stale": hours > 24,
                    "provenance": "demo",
                }
            )
        return rows


MockDBTConnector = DemoDBTConnector
