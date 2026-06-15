"""Toast POS SourceConnector implementation for Purchasing."""

from __future__ import annotations


class ToastConnector:
    """SourceConnector for Toast POS system.

    Implements the 5-member SourceConnector protocol:
      source_name, entity_type, trust_tier, fetch, validate

    Fetches daily restaurant sales data from Toast API:
    - Order summaries (total_orders, total_revenue, covers)
    - Item-level sales (item_name, quantity_sold, revenue, category)
    - Cover counts by daypart (lunch, dinner, late_night)

    Records include a 'timestamp' field for BaseSourceProfiler
    freshness computation.

    Auth: API key header (X-Toast-API-Key).
    Base URL: configurable (default https://api.toasttab.com/v2).

    NOTE: Connector implementations are app-local and wired explicitly
    to BaseSourceProfiler. If a connector registry is added, migrate to
    copilot_sdk/connectors/ in one batch.
    """

    source_name = "toast_pos"
    entity_type = "restaurant_sales"
    trust_tier = 2

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.toasttab.com/v2",
        location_id: str = "",
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._location_id = location_id

    def fetch(self, entity_id: str) -> list[dict]:
        """Fetch records for entity_id, expected as date string YYYY-MM-DD."""
        import requests

        url = f"{self._base_url}/orders/summary"
        headers = {"X-Toast-API-Key": self._api_key}
        params = {"date": entity_id, "locationId": self._location_id}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, list):
            data = [data] if data else []
        return data

    def validate(self, record: dict) -> bool:
        """Validate a Toast POS record."""
        required = ("timestamp", "total_orders", "covers", "total_revenue")
        if not all(key in record for key in required):
            return False

        if not isinstance(record.get("total_orders"), int) or record["total_orders"] < 0:
            return False
        if not isinstance(record.get("covers"), int) or record["covers"] < 0:
            return False

        try:
            revenue = float(record["total_revenue"])
        except (TypeError, ValueError):
            return False
        if revenue < 0:
            return False

        items = record.get("items", [])
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    return False
                if "item_name" not in item or "quantity_sold" not in item:
                    return False
                if not isinstance(item["quantity_sold"], int):
                    return False
        return True
