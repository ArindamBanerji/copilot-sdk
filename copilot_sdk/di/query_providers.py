"""Governed data-provider contracts for DI-3."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from copilot_sdk.di.query_models import QueryPlan, RawQueryResult, SourceUsage


class ProviderUnavailableError(RuntimeError):
    """Raised when governed data cannot be read without substitution."""


class DataProvider(Protocol):
    def execute(self, plan: QueryPlan) -> RawQueryResult:
        ...

    def get_source_profiles(self, source_ids: list[str]) -> list[Any]:
        ...

    def get_source_health(self, source_ids: list[str]) -> list[Any]:
        ...

    def get_active_alerts(self, source_ids: list[str]) -> list[Any]:
        ...

    def get_conservation_state(self, source_ids: list[str]) -> Any:
        ...


class GraphStoreProvider:
    """Read query evidence through an already-authorized GraphStore."""

    def __init__(
        self,
        graph_store: Any,
        *,
        domain: str = "dataops",
        source_profiles: Mapping[str, Any] | None = None,
    ) -> None:
        self.graph_store = graph_store
        self.domain = domain
        self.source_profiles = dict(source_profiles or {})

    def execute(self, plan: QueryPlan) -> RawQueryResult:
        if plan.domain != self.domain:
            raise ProviderUnavailableError("GraphStore provider domain is not authorized")
        rows = self._decisions()
        usages = _source_usage(rows)
        return RawQueryResult(
            rows=rows,
            source_usage=usages,
            data_as_of=_latest_timestamp(rows),
            records_scanned=len(rows),
            query_path=["AGE GraphStore", f"domain={plan.domain}"],
            unmatched_records=_count_unmatched(rows),
        )

    def get_source_profiles(self, source_ids: list[str]) -> list[Any]:
        return [
            _with_source_id(self.source_profiles[source_id], source_id)
            for source_id in source_ids
            if source_id in self.source_profiles
        ]

    def get_all_source_profiles(self) -> list[Any]:
        return [_with_source_id(profile, source_id) for source_id, profile in self.source_profiles.items()]

    def get_source_health(self, source_ids: list[str]) -> list[Any]:
        del source_ids
        return []

    def get_active_alerts(self, source_ids: list[str]) -> list[Any]:
        del source_ids
        return []

    def get_conservation_state(self, source_ids: list[str]) -> Any:
        del source_ids
        return None

    def _decisions(self) -> list[dict[str, Any]]:
        try:
            reader = getattr(self.graph_store, "get_verified_decisions", None)
            if callable(reader):
                try:
                    rows = reader(self.domain)
                except TypeError:
                    rows = reader()
                if rows:
                    return _dict_rows(rows)
            reader = getattr(self.graph_store, "get_all_decisions", None)
            if callable(reader):
                try:
                    return _dict_rows(reader(self.domain))
                except TypeError:
                    return _dict_rows(reader())
            raise ProviderUnavailableError("GraphStore has no governed decision reader")
        except ProviderUnavailableError:
            raise
        except Exception as exc:
            raise ProviderUnavailableError("Governed GraphStore read failed") from exc


class DataOpsEnterpriseProvider:
    """Combine governed SAP invoice evidence with graph reconciliation data."""

    uses_snapshot_time_windows = True

    def __init__(
        self,
        graph_store: Any,
        *,
        invoice_path: str | Path,
        source_profiles: Mapping[str, Any] | None = None,
    ) -> None:
        self.graph_provider = GraphStoreProvider(
            graph_store,
            domain="dataops",
            source_profiles=source_profiles,
        )
        self.invoice_path = Path(invoice_path)
        self.source_profiles = dict(source_profiles or {})

    def execute(self, plan: QueryPlan) -> RawQueryResult:
        if plan.domain != "dataops":
            raise ProviderUnavailableError("DataOps enterprise provider domain is not authorized")
        if plan.metric in {"revenue", "invoice_total", "unmatched_invoice_count", "unmatched_invoice_rate"}:
            return self._invoice_result(plan)
        return self.graph_provider.execute(plan)

    def get_source_profiles(self, source_ids: list[str]) -> list[Any]:
        return [
            _with_source_id(self.source_profiles[source_id], source_id)
            for source_id in source_ids
            if source_id in self.source_profiles
        ]

    def get_all_source_profiles(self) -> list[Any]:
        return [_with_source_id(profile, source_id) for source_id, profile in self.source_profiles.items()]

    def get_source_health(self, source_ids: list[str]) -> list[Any]:
        del source_ids
        return []

    def get_active_alerts(self, source_ids: list[str]) -> list[Any]:
        del source_ids
        return []

    def get_conservation_state(self, source_ids: list[str]) -> Any:
        del source_ids
        return None

    def _invoice_result(self, plan: QueryPlan) -> RawQueryResult:
        records = _load_json_records(self.invoice_path)
        decision_ids = self._decision_invoice_ids()
        rows = [_normalize_invoice(record, decision_ids) for record in records]
        data_as_of = max((_parse_date(row["timestamp"]) for row in rows), default=None)
        return RawQueryResult(
            rows=rows,
            source_usage=_source_usage(rows, requested_sources=plan.requested_sources),
            data_as_of=data_as_of,
            records_scanned=len(rows),
            query_path=[
                "SAP S/4HANA invoices → governed amount/status",
                "Celonis P2P → match-process corroboration",
                f"AGE GraphStore → {len(decision_ids)} invoice decision links",
            ],
            unmatched_records=_count_unmatched(rows),
        )

    def _decision_invoice_ids(self) -> set[str]:
        try:
            decisions = self.graph_provider._decisions()
        except ProviderUnavailableError:
            return set()
        invoice_ids: set[str] = set()
        for decision in decisions:
            for key in ("invoice_id", "SupplierInvoice", "supplier_invoice"):
                value = decision.get(key)
                if value:
                    invoice_ids.add(str(value))
            metadata = decision.get("metadata")
            if isinstance(metadata, Mapping):
                for key in ("invoice_id", "SupplierInvoice", "supplier_invoice"):
                    value = metadata.get(key)
                    if value:
                        invoice_ids.add(str(value))
        return invoice_ids


class FixtureProvider:
    """Explicit test-only provider; never used as production outage fallback."""

    def __init__(
        self,
        rows: Iterable[Mapping[str, Any]] | None = None,
        *,
        profiles: Mapping[str, Any] | None = None,
        health: Mapping[str, Any] | None = None,
        alerts: Mapping[str, Any] | None = None,
        conservation: Any = None,
        data_as_of: datetime | None = None,
        unavailable: bool = False,
    ) -> None:
        self.rows = [dict(row) for row in (rows or [])]
        self.profiles = dict(profiles or {})
        self.health = dict(health or {})
        self.alerts = dict(alerts or {})
        self.conservation = conservation
        self.data_as_of = data_as_of
        self.unavailable = unavailable

    def execute(self, plan: QueryPlan) -> RawQueryResult:
        if self.unavailable:
            raise ProviderUnavailableError("Fixture provider unavailable")
        rows = list(self.rows)
        return RawQueryResult(
            rows=rows,
            source_usage=_source_usage(rows),
            data_as_of=self.data_as_of or _latest_timestamp(rows),
            records_scanned=len(rows),
            query_path=["FixtureProvider", f"domain={plan.domain}"],
            unmatched_records=_count_unmatched(rows),
        )

    def get_source_profiles(self, source_ids: list[str]) -> list[Any]:
        return [_with_source_id(self.profiles[source_id], source_id) for source_id in source_ids if source_id in self.profiles]

    def get_all_source_profiles(self) -> list[Any]:
        return [_with_source_id(profile, source_id) for source_id, profile in self.profiles.items()]

    def get_source_health(self, source_ids: list[str]) -> list[Any]:
        return [self.health[source_id] for source_id in source_ids if source_id in self.health]

    def get_active_alerts(self, source_ids: list[str]) -> list[Any]:
        return [self.alerts[source_id] for source_id in source_ids if source_id in self.alerts]

    def get_conservation_state(self, source_ids: list[str]) -> Any:
        del source_ids
        return self.conservation


def _dict_rows(rows: Iterable[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _with_source_id(profile: Any, source_id: str) -> Any:
    if isinstance(profile, Mapping):
        return {**dict(profile), "source_id": source_id}
    return profile


def _source_ids(row: Mapping[str, Any]) -> list[str]:
    raw = row.get("source_ids")
    if isinstance(raw, list):
        return [str(value) for value in raw if value]
    source = row.get("source_id") or row.get("source") or row.get("system")
    metadata = row.get("metadata")
    if not source and isinstance(metadata, Mapping):
        source = metadata.get("source_id") or metadata.get("source")
    return [str(source)] if source else ["graph"]


def _source_usage(
    rows: list[dict[str, Any]],
    requested_sources: list[str] | None = None,
) -> list[SourceUsage]:
    counts: dict[str, int] = {}
    for row in rows:
        source_ids = _source_ids(row)
        if requested_sources:
            source_ids = [source_id for source_id in source_ids if source_id in requested_sources]
        for source_id in source_ids or (requested_sources or ["graph"]):
            counts[source_id] = counts.get(source_id, 0) + 1
    total = sum(counts.values()) or 1
    return [
        SourceUsage(source_id=source_id, records_used=count, contribution=count / total)
        for source_id, count in sorted(counts.items())
    ]


def _latest_timestamp(rows: list[dict[str, Any]]) -> datetime | None:
    values: list[datetime] = []
    for row in rows:
        value = row.get("created_at") or row.get("timestamp")
        if isinstance(value, datetime):
            values.append(value if value.tzinfo else value.replace(tzinfo=timezone.utc))
    return max(values) if values else None


def _count_unmatched(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if str(row.get("match_status", "")).lower() in {"unmatched", "mismatch"})


def _load_json_records(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProviderUnavailableError("SAP invoice fixture is unavailable") from exc
    if not isinstance(payload, list):
        raise ProviderUnavailableError("SAP invoice fixture must contain a list")
    return [dict(item) for item in payload if isinstance(item, Mapping)]


def _normalize_invoice(record: Mapping[str, Any], decision_ids: set[str]) -> dict[str, Any]:
    invoice_id = str(record.get("SupplierInvoice") or record.get("invoice_id") or "")
    status = str(record.get("Status") or record.get("status") or "").lower()
    matched_by_graph = invoice_id in decision_ids
    match_status = "matched" if matched_by_graph or status == "matched" else "unmatched"
    timestamp = str(record.get("PostingDate") or record.get("DocumentDate") or "")
    return {
        "invoice_id": invoice_id,
        "amount": float(record.get("InvoiceGrossAmount") or record.get("amount") or 0.0),
        "timestamp": timestamp,
        "status": status,
        "match_status": match_status,
        "supplier_id": str(record.get("Supplier") or ""),
        "supplier_name": str(record.get("SupplierName") or ""),
        "source_ids": ["sap_s4hana", "celonis_p2p"],
        "provenance": str(record.get("provenance") or "sample"),
    }


def _parse_date(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
