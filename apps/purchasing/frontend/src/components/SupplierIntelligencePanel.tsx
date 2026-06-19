import { useEffect, useMemo, useState } from "react";
import {
  getQBOBills,
  getQBOLeadTimes,
  getQBOPriceHistory,
  getQBOStatus,
  getQBOVendors,
} from "../api";
import type { QBOInvoice, QBOLeadTimes, QBOPricePoint, QBOStatus, QBOSupplier } from "../types";

interface SupplierDetail {
  itemName?: string;
  priceHistory?: QBOPricePoint[];
  leadTimes?: QBOLeadTimes;
  loading?: boolean;
  error?: string;
}

function formatName(value?: string) {
  return String(value ?? "standard").replace(/_/g, " ");
}

function invoicesForSupplier(invoices: QBOInvoice[], supplierId: string) {
  return invoices.filter((invoice) => String(invoice.supplierId ?? "") === supplierId);
}

function firstItemName(invoices: QBOInvoice[]) {
  for (const invoice of invoices) {
    const item = invoice.lineItems?.find((line) => line.itemName);
    if (item?.itemName) {
      return item.itemName;
    }
  }
  return "salmon filet";
}

function reliabilityLabel(archetype?: string) {
  const key = String(archetype ?? "");
  if (key.includes("gold")) return "High";
  if (key.includes("seasonal")) return "Seasonal";
  if (key.includes("price_memory")) return "Watch price";
  if (key.includes("trust_trap") || key.includes("volatile") || key.includes("declining")) return "Monitor";
  if (key.includes("new")) return "Emerging";
  return "Standard";
}

function priceTrend(archetype?: string, history?: QBOPricePoint[]) {
  if (String(archetype ?? "").includes("seasonal")) {
    return { label: "seasonal", color: "#2563eb" };
  }
  const prices = (history ?? [])
    .map((point) => Number(point.unitPrice))
    .filter((price) => Number.isFinite(price) && price > 0);
  if (prices.length < 2) {
    return { label: "stable", color: "#15803d" };
  }
  const first = prices[0];
  const last = prices[prices.length - 1];
  const change = first ? (last - first) / first : 0;
  if (change > 0.05) {
    return { label: "rising", color: "#b45309" };
  }
  return { label: "stable", color: "#15803d" };
}

function statusLabel(status?: QBOStatus) {
  if (String(status?.sourceName ?? "").includes("mock")) {
    return { text: "Mock Data", color: "#6b7280" };
  }
  if (status?.connected) {
    return { text: "QuickBooks Connected", color: "#15803d" };
  }
  return { text: "Accounting unavailable", color: "#6b7280" };
}

export default function SupplierIntelligencePanel() {
  const [suppliers, setSuppliers] = useState<QBOSupplier[]>([]);
  const [invoices, setInvoices] = useState<QBOInvoice[]>([]);
  const [status, setStatus] = useState<QBOStatus>();
  const [selectedSupplierId, setSelectedSupplierId] = useState<string>();
  const [details, setDetails] = useState<Record<string, SupplierDetail>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const [nextStatus, nextSuppliers, nextInvoices] = await Promise.all([
          getQBOStatus(),
          getQBOVendors(),
          getQBOBills(),
        ]);
        if (!active) return;
        setStatus(nextStatus);
        setSuppliers(nextSuppliers.slice(0, 30));
        setInvoices(nextInvoices);
        setSelectedSupplierId((current) => current ?? nextSuppliers[0]?.supplierId);
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load supplier intelligence");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  const invoicesBySupplier = useMemo(() => {
    const grouped = new Map<string, QBOInvoice[]>();
    invoices.forEach((invoice) => {
      const supplierId = String(invoice.supplierId ?? "");
      if (!supplierId) return;
      grouped.set(supplierId, [...(grouped.get(supplierId) ?? []), invoice]);
    });
    return grouped;
  }, [invoices]);

  const selectedSupplier = suppliers.find((supplier) => supplier.supplierId === selectedSupplierId);

  useEffect(() => {
    if (!selectedSupplierId || details[selectedSupplierId]?.priceHistory || details[selectedSupplierId]?.loading) {
      return;
    }
    const supplierId = selectedSupplierId;
    const selectedInvoices = invoicesBySupplier.get(supplierId) ?? [];
    const itemName = firstItemName(selectedInvoices);
    let active = true;
    async function loadDetails() {
      setDetails((current) => ({
        ...current,
        [supplierId]: { ...current[supplierId], itemName, loading: true, error: undefined },
      }));
      try {
        const [priceHistory, leadTimes] = await Promise.all([
          getQBOPriceHistory(supplierId, itemName),
          getQBOLeadTimes(supplierId),
        ]);
        if (!active) return;
        setDetails((current) => ({
          ...current,
          [supplierId]: { itemName, priceHistory, leadTimes, loading: false },
        }));
      } catch (caught) {
        if (!active) return;
        setDetails((current) => ({
          ...current,
          [supplierId]: {
            ...current[supplierId],
            itemName,
            loading: false,
            error: caught instanceof Error ? caught.message : "Unable to load supplier detail",
          },
        }));
      }
    }
    loadDetails();
    return () => {
      active = false;
    };
  }, [details, invoicesBySupplier, selectedSupplierId]);

  if (loading) {
    return (
      <section className="purchase-card" data-testid="supplier-loading">
        Loading supplier intelligence...
      </section>
    );
  }

  if (error || suppliers.length === 0) {
    return (
      <section className="purchase-card" data-testid="supplier-empty">
        <p className="purchase-kicker">Supplier intelligence</p>
        <p>{error ?? "No supplier data available."}</p>
      </section>
    );
  }

  const badge = statusLabel(status);
  const selectedInvoices = selectedSupplierId ? invoicesForSupplier(invoices, selectedSupplierId) : [];
  const selectedDetail = selectedSupplierId ? details[selectedSupplierId] : undefined;
  const trend = priceTrend(selectedSupplier?.archetype, selectedDetail?.priceHistory);

  return (
    <section className="purchase-card supplier-intelligence-panel" data-testid="supplier-intelligence-panel">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Supplier intelligence</p>
          <h2 className="purchase-title">QuickBooks supplier signals</h2>
        </div>
        <span
          data-testid="qbo-status-badge"
          style={{
            alignItems: "center",
            border: "1px solid #d1d5db",
            borderRadius: 999,
            display: "inline-flex",
            gap: 8,
            padding: "6px 10px",
            whiteSpace: "nowrap",
          }}
        >
          <span
            aria-hidden="true"
            style={{ background: badge.color, borderRadius: 999, display: "inline-block", height: 8, width: 8 }}
          />
          {badge.text}
        </span>
      </div>

      <div className="summary-table" data-testid="supplier-table">
        <div className="summary-row header">
          <span>Name</span>
          <span>Archetype</span>
          <span>Reliability</span>
          <span>Avg Lead Time</span>
          <span>Invoice Count</span>
        </div>
        {suppliers.map((supplier) => {
          const isSelected = supplier.supplierId === selectedSupplierId;
          const supplierDetail = details[supplier.supplierId];
          const supplierInvoices = invoicesBySupplier.get(supplier.supplierId) ?? [];
          return (
            <div
              aria-expanded={isSelected}
              className="summary-row"
              data-testid="supplier-row"
              key={supplier.supplierId}
              onClick={() => setSelectedSupplierId(supplier.supplierId)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setSelectedSupplierId(supplier.supplierId);
                }
              }}
              role="button"
              style={{
                cursor: "pointer",
                outline: isSelected ? "2px solid #2563eb" : undefined,
                outlineOffset: isSelected ? 2 : undefined,
              }}
              tabIndex={0}
            >
              <span>{supplier.supplierName}</span>
              <span>{formatName(supplier.archetype)}</span>
              <span>{reliabilityLabel(supplier.archetype)}</span>
              <span>
                {supplierDetail?.leadTimes?.meanDays != null
                  ? `${Number(supplierDetail.leadTimes.meanDays).toFixed(1)} days`
                  : isSelected && supplierDetail?.loading
                    ? "Loading..."
                    : "Open"}
              </span>
              <span>{supplierInvoices.length}</span>
            </div>
          );
        })}
      </div>

      {selectedSupplier && (
        <div
          className="supplier-detail-panel"
          data-testid="supplier-detail"
          style={{ background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: 8, marginTop: 16, padding: 16 }}
        >
          <div className="purchase-card-header">
            <div>
              <p className="purchase-kicker">Supplier detail</p>
              <h3 className="purchase-title">{selectedSupplier.supplierName}</h3>
            </div>
            <span>{selectedInvoices.length} invoices</span>
          </div>

          {selectedDetail?.error ? (
            <p className="purchase-muted">{selectedDetail.error}</p>
          ) : (
            <div className="summary-table">
              <div className="summary-row">
                <span>Item</span>
                <span>{selectedDetail?.itemName ?? firstItemName(selectedInvoices)}</span>
              </div>
              <div className="summary-row" data-testid="price-trend">
                <span>Price trend</span>
                <span style={{ color: trend.color, fontWeight: 700 }}>{trend.label}</span>
              </div>
              <div className="summary-row" data-testid="lead-time-stats">
                <span>Lead time</span>
                <span>
                  {selectedDetail?.leadTimes?.meanDays != null
                    ? `${Number(selectedDetail.leadTimes.meanDays).toFixed(1)} days average`
                    : selectedDetail?.loading
                      ? "Loading..."
                      : "No matched orders"}
                  {selectedDetail?.leadTimes?.sampleCount != null
                    ? ` (${selectedDetail.leadTimes.sampleCount} samples)`
                    : ""}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
