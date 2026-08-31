"""Mock Snowflake metadata connector for demos and tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from copilot_sdk.connectors.snowflake_meta import SnowflakeMetaConnector


class DemoSnowflakeConnector(SnowflakeMetaConnector):
    """Ten tables, fifty columns, and twenty query history records. No network."""

    source_name = "snowflake"

    _TABLES = [
        ("orders", 12_000_000, 2_400_000_000, 6),
        ("customers", 2_100_000, 420_000_000, 5),
        ("products", 45_000, 18_000_000, 5),
        ("suppliers", 8_200, 3_300_000, 5),
        ("invoices", 3_400_000, 900_000_000, 5),
        ("payments", 2_800_000, 720_000_000, 5),
        ("shipments", 1_100_000, 280_000_000, 5),
        ("returns", 340_000, 80_000_000, 5),
        ("inventory", 890_000, 130_000_000, 5),
        ("metrics", 15_000_000, 1_200_000_000, 4),
    ]

    _COLUMN_TYPES = ["VARCHAR", "INTEGER", "NUMBER", "TIMESTAMP_NTZ", "DATE", "BOOLEAN", "FLOAT"]

    def fetch(self, entity_id: str = "all") -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        rows = []
        for index, (table_name, row_count, bytes_used, column_count) in enumerate(self._TABLES):
            if entity_id not in ("all", table_name):
                continue
            created = now - timedelta(days=240 + index)
            rows.append(
                {
                    "table_name": table_name,
                    "row_count": row_count,
                    "bytes": bytes_used,
                    "column_count": column_count,
                    "created": created.isoformat(),
                    "created_at": created.isoformat(),
                    "last_altered": (now - timedelta(hours=index + 1)).isoformat(),
                    "provenance": "demo",
                }
            )
        return rows

    def fetch_columns(self, table_name: str) -> list[dict[str, Any]]:
        table_names = [table[0] for table in self._TABLES]
        if table_name not in table_names:
            return []
        columns: list[dict[str, Any]] = []
        for table, _, _, count in self._TABLES:
            for position in range(1, count + 1):
                if table != table_name:
                    continue
                columns.append(
                    {
                        "table_name": table,
                        "column_name": f"{table}_field_{position}",
                        "data_type": self._COLUMN_TYPES[(position - 1) % len(self._COLUMN_TYPES)],
                        "is_nullable": "YES" if position % 3 else "NO",
                        "comment": f"Metadata column {position} for {table}",
                        "ordinal_position": position,
                        "provenance": "demo",
                    }
                )
        return columns

    def fetch_all_columns(self) -> list[dict[str, Any]]:
        columns: list[dict[str, Any]] = []
        for table_name, _, _, _ in self._TABLES:
            columns.extend(self.fetch_columns(table_name))
        return columns

    def fetch_query_history(self, days: int = 7) -> list[dict[str, Any]]:
        if days < 1:
            raise ValueError("days must be positive")
        base = datetime.now(timezone.utc)
        tables = [table[0] for table in self._TABLES]
        return [
            {
                "query_id": f"QID-{index + 1:04d}",
                "query_text": f"SELECT COUNT(*) FROM ANALYTICS.{tables[index % len(tables)].upper()} WHERE UPDATED_AT >= CURRENT_DATE - 7",
                "user_name": "DATA_ENGINEERING",
                "execution_time_ms": 250 + index * 37,
                "rows_produced": 1 if index % 4 else 500,
                "warehouse_name": "TRANSFORMING_WH",
                "started_at": (base - timedelta(hours=index)).isoformat(),
                "provenance": "demo",
            }
            for index in range(20)
        ]


MockSnowflakeConnector = DemoSnowflakeConnector
