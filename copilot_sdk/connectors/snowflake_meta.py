"""Snowflake metadata connector.

The connector exposes metadata only. It does not read table rows.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class SnowflakeMetaConnector:
    """Metadata connector for Snowflake INFORMATION_SCHEMA."""

    source_name = "snowflake"
    entity_type = "warehouse_metadata"
    trust_tier = 1

    def __init__(
        self,
        account: str = "",
        user: str = "",
        password: str = "",
        database: str = "",
        warehouse: str = "",
        schema: str = "PUBLIC",
    ) -> None:
        self._account = account
        self._user = user
        self._password = password
        self._database = database
        self._warehouse = warehouse
        self._schema = schema

    @property
    def _connected(self) -> bool:
        return bool(self._account and self._user)

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RuntimeError(
                f"{self.source_name} connector not configured. "
                f"Use Mock{self.__class__.__name__} for demo mode."
            )

    def _connect(self) -> Any:
        self._ensure_connected()
        try:
            import snowflake.connector  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("snowflake connector dependency is not installed") from exc
        return snowflake.connector.connect(
            account=self._account,
            user=self._user,
            password=self._password,
            database=self._database or None,
            warehouse=self._warehouse or None,
            schema=self._schema or None,
        )

    def fetch(self, entity_id: str = "all") -> list[dict[str, Any]]:
        """Return table metadata records from Snowflake INFORMATION_SCHEMA."""
        self._ensure_connected()
        query = """
            SELECT table_name, row_count, bytes, created, last_altered
            FROM information_schema.tables
            WHERE table_schema = %s
        """
        params: list[Any] = [self._schema]
        if entity_id != "all":
            query += " AND table_name = %s"
            params.append(entity_id)
        rows: list[dict[str, Any]] = []
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                for table_name, row_count, bytes_used, created, last_altered in cursor.fetchall():
                    rows.append(
                        {
                            "table_name": table_name,
                            "row_count": row_count or 0,
                            "bytes": bytes_used or 0,
                            "created": created.isoformat() if hasattr(created, "isoformat") else created,
                            "created_at": created.isoformat() if hasattr(created, "isoformat") else created,
                            "last_altered": last_altered.isoformat()
                            if hasattr(last_altered, "isoformat")
                            else last_altered,
                            "provenance": "live",
                        }
                    )
        return rows

    def fetch_columns(self, table_name: str) -> list[dict[str, Any]]:
        """Return column metadata for a table."""
        if not table_name:
            raise ValueError("table_name is required")
        self._ensure_connected()
        query = """
            SELECT table_name, column_name, data_type, is_nullable, comment, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """
        rows: list[dict[str, Any]] = []
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, [self._schema, table_name])
                for row in cursor.fetchall():
                    rows.append(
                        {
                            "table_name": row[0],
                            "column_name": row[1],
                            "data_type": row[2],
                            "is_nullable": row[3],
                            "comment": row[4],
                            "ordinal_position": row[5],
                            "provenance": "live",
                        }
                    )
        return rows

    def fetch_query_history(self, days: int = 7) -> list[dict[str, Any]]:
        """Return query history metadata."""
        if days < 1:
            raise ValueError("days must be positive")
        self._ensure_connected()
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = """
            SELECT query_id, query_text, user_name, execution_time, rows_produced,
                   warehouse_name, start_time
            FROM table(information_schema.query_history(end_time_range_start => %s))
            ORDER BY start_time DESC
        """
        rows: list[dict[str, Any]] = []
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, [since])
                for row in cursor.fetchall():
                    started_at = row[6]
                    rows.append(
                        {
                            "query_id": row[0],
                            "query_text": row[1],
                            "user_name": row[2],
                            "execution_time_ms": row[3],
                            "rows_produced": row[4],
                            "warehouse_name": row[5],
                            "started_at": started_at.isoformat()
                            if hasattr(started_at, "isoformat")
                            else started_at,
                            "provenance": "live",
                        }
                    )
        return rows

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate table metadata shape."""
        try:
            return bool(record.get("table_name")) and int(record.get("row_count", -1)) >= 0
        except (TypeError, ValueError):
            return False

    def to_map_nodes(self) -> list[dict[str, Any]]:
        """Return Intelligence Map source dicts for table metadata."""
        nodes: list[dict[str, Any]] = []
        for table in self.fetch():
            row_count = int(table.get("row_count", 0) or 0)
            table_name = str(table.get("table_name", ""))
            nodes.append(
                {
                    "id": f"snowflake_{table_name}".lower(),
                    "node_id": f"snowflake_{table_name}".lower(),
                    "name": table_name,
                    "source_name": table_name,
                    "domain": "data_engineering",
                    "entity_type": self.entity_type,
                    "trust_tier": self.trust_tier,
                    "source_reliability": 0.95,
                    "record_count": row_count,
                    "size": row_count,
                    "quality_score": 0.95,
                    "provenance": table.get("provenance", "live"),
                }
            )
        return nodes

    def __str__(self) -> str:
        return f"SnowflakeMetaConnector(account={self._account})"

    __repr__ = __str__
