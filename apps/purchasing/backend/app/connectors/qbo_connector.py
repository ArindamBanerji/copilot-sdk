"""QuickBooks Online SourceConnector implementation for Purchasing."""

from __future__ import annotations

from datetime import date, timedelta
from statistics import mean, median, pstdev
from typing import Any


class QBOConnector:
    """QuickBooks Online API connector.

    Implements the 5-member SourceConnector protocol:
      source_name, entity_type, trust_tier, fetch, validate

    Auth: OAuth 2.0 via intuitlib / python-quickbooks optional
    dependencies. Secrets are stored only on the instance and are never
    logged or returned by normalized records.
    """

    source_name = "quickbooks_online"
    entity_type = "accounting"
    trust_tier = 1

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        refresh_token: str = "",
        realm_id: str = "",
        sandbox: bool = True,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._realm_id = realm_id
        self._sandbox = sandbox
        self._base_url = (
            "https://sandbox-quickbooks.api.intuit.com/v3"
            if sandbox
            else "https://quickbooks.api.intuit.com/v3"
        )

    def fetch(self, entity_id: str) -> list[dict]:
        """Fetch normalized QBO records for a protocol entity id."""
        if entity_id == "vendors":
            return self.fetch_vendors()
        if entity_id == "bills":
            return self.fetch_bills()
        if entity_id == "purchase_orders":
            return self.fetch_purchase_orders()
        if entity_id == "payments":
            return self.fetch_payments()
        if entity_id.startswith("price_history:"):
            _, supplier_id, item_name = entity_id.split(":", maxsplit=2)
            return self.compute_price_history(supplier_id, item_name)
        if entity_id.startswith("lead_times:"):
            _, supplier_id = entity_id.split(":", maxsplit=1)
            return [self.compute_lead_times(supplier_id)]
        return []

    def validate(self, record: dict) -> bool:
        """Validate normalized supplier or invoice records."""
        if not isinstance(record, dict):
            return False
        record_type = str(record.get("record_type") or "")
        if record_type == "supplier":
            return bool(record.get("supplier_id") and record.get("supplier_name"))
        if record_type == "invoice":
            if not (record.get("supplier_id") and record.get("amount") is not None and record.get("invoice_date")):
                return False
            try:
                return float(record["amount"]) >= 0.0
            except (TypeError, ValueError):
                return False
        return bool(record.get("supplier_id") and record.get("supplier_name"))

    def fetch_vendors(self, max_results: int = 100) -> list[dict]:
        """Fetch QBO Vendor rows as normalized supplier profiles."""
        rows = self._query(f"SELECT * FROM Vendor MAXRESULTS {int(max_results)}", "Vendor")
        return [self._normalize_supplier(row) for row in rows]

    def fetch_bills(self, since_days: int = 365) -> list[dict]:
        """Fetch QBO Bill rows as normalized invoice records."""
        since = (date.today() - timedelta(days=int(since_days))).isoformat()
        rows = self._query(f"SELECT * FROM Bill WHERE TxnDate > '{since}'", "Bill")
        return [self._normalize_invoice(row) for row in rows]

    def fetch_purchase_orders(self, since_days: int = 365) -> list[dict]:
        """Fetch QBO PurchaseOrder rows as normalized order records."""
        since = (date.today() - timedelta(days=int(since_days))).isoformat()
        rows = self._query(f"SELECT * FROM PurchaseOrder WHERE TxnDate > '{since}'", "PurchaseOrder")
        return [self._normalize_order(row) for row in rows]

    def fetch_payments(self, since_days: int = 365) -> list[dict]:
        """Fetch QBO BillPayment rows as normalized payment records."""
        since = (date.today() - timedelta(days=int(since_days))).isoformat()
        rows = self._query(f"SELECT * FROM BillPayment WHERE TxnDate > '{since}'", "BillPayment")
        return [self._normalize_payment(row) for row in rows]

    def compute_price_history(self, vendor_id: str, item_name: str) -> list[dict]:
        """Return price history for supplier x item from invoice line items."""
        history: list[dict] = []
        for invoice in self.fetch_bills():
            if str(invoice.get("supplier_id")) != str(vendor_id):
                continue
            for item in invoice.get("line_items", []):
                if str(item.get("item_name", "")).lower() != str(item_name).lower():
                    continue
                history.append(
                    {
                        "date": invoice.get("invoice_date"),
                        "unit_price": item.get("unit_price"),
                        "quantity": item.get("quantity"),
                        "invoice_id": invoice.get("invoice_id"),
                    }
                )
        return sorted(history, key=lambda row: str(row.get("date") or ""))

    def compute_lead_times(self, vendor_id: str) -> dict:
        """Compute supplier lead time from matched order/invoice pairs."""
        invoices = {
            str(row.get("order_id")): row
            for row in self.fetch_bills()
            if str(row.get("supplier_id")) == str(vendor_id) and row.get("order_id")
        }
        lead_days: list[int] = []
        by_quarter: dict[str, list[int]] = {}
        for order in self.fetch_purchase_orders():
            if str(order.get("supplier_id")) != str(vendor_id):
                continue
            invoice = invoices.get(str(order.get("order_id")))
            if not invoice:
                continue
            days = _days_between(order.get("order_date"), invoice.get("invoice_date"))
            if days is None:
                continue
            lead_days.append(days)
            quarter = _quarter(invoice.get("invoice_date"))
            by_quarter.setdefault(quarter, []).append(days)
        return _lead_time_payload(lead_days, by_quarter)

    def test_connection(self) -> dict:
        """Verify OAuth credentials by fetching company info."""
        self._ensure_live_dependencies()
        if not self._realm_id:
            return {"connected": False, "company_name": None, "realm_id": self._realm_id}
        response = self._request("companyinfo/1", params={})
        company = response.get("CompanyInfo", {}) if isinstance(response, dict) else {}
        return {
            "connected": bool(company),
            "company_name": company.get("CompanyName"),
            "realm_id": self._realm_id,
        }

    def _query(self, query: str, result_key: str) -> list[dict]:
        payload = self._request("query", params={"query": query, "minorversion": "75"})
        response = payload.get("QueryResponse", {}) if isinstance(payload, dict) else {}
        rows = response.get(result_key, [])
        return rows if isinstance(rows, list) else []

    def _request(self, path: str, params: dict[str, Any]) -> dict:
        self._ensure_live_dependencies()
        if not all((self._client_id, self._client_secret, self._refresh_token, self._realm_id)):
            raise ValueError("QuickBooks credentials are required for live API access")

        import requests
        from intuitlib.client import AuthClient

        auth_client = AuthClient(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri="",
            environment="sandbox" if self._sandbox else "production",
        )
        auth_client.refresh(refresh_token=self._refresh_token)
        url = f"{self._base_url}/company/{self._realm_id}/{path.lstrip('/')}"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {auth_client.access_token}", "Accept": "application/json"},
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _ensure_live_dependencies() -> None:
        try:
            import intuitlib.client  # noqa: F401
            import quickbooks  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "QuickBooks integration requires: pip install python-quickbooks intuitlib"
            ) from exc

    @staticmethod
    def _normalize_supplier(row: dict[str, Any]) -> dict:
        metadata = row.get("MetaData") if isinstance(row.get("MetaData"), dict) else {}
        return {
            "record_type": "supplier",
            "supplier_id": str(row.get("Id") or ""),
            "supplier_name": str(row.get("DisplayName") or row.get("CompanyName") or ""),
            "active": bool(row.get("Active", True)),
            "balance": _float(row.get("Balance"), 0.0),
            "currency": _currency(row),
            "updated_at": metadata.get("LastUpdatedTime"),
            "timestamp": metadata.get("LastUpdatedTime"),
        }

    @staticmethod
    def _normalize_invoice(row: dict[str, Any]) -> dict:
        supplier = row.get("VendorRef") if isinstance(row.get("VendorRef"), dict) else {}
        invoice_id = str(row.get("Id") or "")
        return {
            "record_type": "invoice",
            "invoice_id": invoice_id,
            "supplier_id": str(supplier.get("value") or ""),
            "supplier_name": str(supplier.get("name") or ""),
            "invoice_date": row.get("TxnDate"),
            "amount": _float(row.get("TotalAmt"), 0.0),
            "currency": _currency(row),
            "order_id": _linked_order_id(row),
            "line_items": _line_items(row),
            "timestamp": row.get("TxnDate"),
        }

    @staticmethod
    def _normalize_order(row: dict[str, Any]) -> dict:
        supplier = row.get("VendorRef") if isinstance(row.get("VendorRef"), dict) else {}
        return {
            "record_type": "order",
            "order_id": str(row.get("Id") or ""),
            "supplier_id": str(supplier.get("value") or ""),
            "supplier_name": str(supplier.get("name") or ""),
            "order_date": row.get("TxnDate"),
            "amount": _float(row.get("TotalAmt"), 0.0),
            "line_items": _line_items(row),
            "timestamp": row.get("TxnDate"),
        }

    @staticmethod
    def _normalize_payment(row: dict[str, Any]) -> dict:
        supplier = row.get("VendorRef") if isinstance(row.get("VendorRef"), dict) else {}
        return {
            "record_type": "payment",
            "payment_id": str(row.get("Id") or ""),
            "supplier_id": str(supplier.get("value") or ""),
            "supplier_name": str(supplier.get("name") or ""),
            "payment_date": row.get("TxnDate"),
            "amount": _float(row.get("TotalAmt"), 0.0),
            "timestamp": row.get("TxnDate"),
        }


def _line_items(row: dict[str, Any]) -> list[dict]:
    items: list[dict] = []
    lines = row.get("Line") if isinstance(row.get("Line"), list) else []
    for line in lines:
        detail = line.get("ItemBasedExpenseLineDetail") if isinstance(line, dict) else {}
        item_ref = detail.get("ItemRef") if isinstance(detail, dict) else {}
        quantity = _float(detail.get("Qty"), 0.0) if isinstance(detail, dict) else 0.0
        amount = _float(line.get("Amount"), 0.0) if isinstance(line, dict) else 0.0
        unit_price = round(amount / quantity, 2) if quantity else 0.0
        items.append(
            {
                "item_name": str(item_ref.get("name") or line.get("Description") or ""),
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
            }
        )
    return items


def _linked_order_id(row: dict[str, Any]) -> str | None:
    linked = row.get("LinkedTxn") if isinstance(row.get("LinkedTxn"), list) else []
    for item in linked:
        if isinstance(item, dict) and item.get("TxnType") == "PurchaseOrder":
            return str(item.get("TxnId") or "")
    return None


def _currency(row: dict[str, Any]) -> str:
    currency = row.get("CurrencyRef") if isinstance(row.get("CurrencyRef"), dict) else {}
    return str(currency.get("value") or "USD")


def _float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _days_between(start: Any, end: Any) -> int | None:
    try:
        start_date = date.fromisoformat(str(start))
        end_date = date.fromisoformat(str(end))
    except ValueError:
        return None
    return (end_date - start_date).days


def _quarter(value: Any) -> str:
    try:
        parsed = date.fromisoformat(str(value))
    except ValueError:
        return "unknown"
    return f"Q{((parsed.month - 1) // 3) + 1}"


def _lead_time_payload(lead_days: list[int], by_quarter: dict[str, list[int]]) -> dict:
    if not lead_days:
        return {
            "mean_days": None,
            "median_days": None,
            "std_days": None,
            "sample_count": 0,
            "by_quarter": {},
        }
    return {
        "mean_days": round(mean(lead_days), 2),
        "median_days": round(median(lead_days), 2),
        "std_days": round(pstdev(lead_days), 2) if len(lead_days) > 1 else 0.0,
        "sample_count": len(lead_days),
        "by_quarter": {key: round(mean(values), 2) for key, values in sorted(by_quarter.items())},
    }
