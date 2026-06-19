import { useEffect, useMemo, useState } from "react";
import {
  getSpendAlerts,
  getSpendByCategory,
  getSpendBySupplier,
  getSpendCostPerCover,
  getSpendSummary,
} from "../api";
import type {
  CategorySpend,
  CostPerCoverPoint,
  SpendAlert,
  SpendSummary,
  SupplierSpend,
} from "../types";

const PERIOD_OPTIONS = [7, 14, 30, 90];

function money(value?: number | null, digits = 0) {
  if (!Number.isFinite(Number(value))) {
    return "n/a";
  }
  return `$${Number(value).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })}`;
}

function categoryLabel(category: string) {
  return category.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function alertColor(variance: number) {
  if (variance > 15) return "#b91c1c";
  if (variance > 10) return "#b45309";
  return "#15803d";
}

function sparklinePath(values: number[], width = 260, height = 54) {
  if (values.length < 2) return "";
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(1, max - min);
  return values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

export default function SpendSummaryPanel() {
  const [period, setPeriod] = useState(30);
  const [summary, setSummary] = useState<SpendSummary>();
  const [categories, setCategories] = useState<CategorySpend[]>([]);
  const [alerts, setAlerts] = useState<SpendAlert[]>([]);
  const [suppliers, setSuppliers] = useState<SupplierSpend[]>([]);
  const [coverTrend, setCoverTrend] = useState<CostPerCoverPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const [nextSummary, nextCategories, nextAlerts, nextSuppliers, nextCoverTrend] =
          await Promise.all([
            getSpendSummary(period),
            getSpendByCategory(period),
            getSpendAlerts(10),
            getSpendBySupplier(period, 10),
            getSpendCostPerCover(period),
          ]);
        if (!active) return;
        setSummary(nextSummary);
        setCategories(nextCategories);
        setAlerts(nextAlerts);
        setSuppliers(nextSuppliers);
        setCoverTrend(nextCoverTrend);
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load spend dashboard");
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
  }, [period]);

  const alertTone = alerts.length > 0 ? "#b91c1c" : "#15803d";
  const maxCategoryPct = useMemo(
    () => Math.max(1, ...categories.map((category) => Number(category.pctOfTotal || 0))),
    [categories],
  );
  const maxSupplierSpend = useMemo(
    () => Math.max(1, ...suppliers.map((supplier) => Number(supplier.totalAmount || 0))),
    [suppliers],
  );
  const coverPoints = useMemo(
    () => coverTrend.filter((point) => point.costPerCover != null && Number.isFinite(Number(point.costPerCover))),
    [coverTrend],
  );
  const currentCoverPoint = coverPoints.length > 0 ? coverPoints[coverPoints.length - 1] : undefined;
  const path = sparklinePath(coverPoints.map((point) => Number(point.costPerCover)));

  if (loading) {
    return (
      <section className="purchase-card" data-testid="spend-loading">
        Loading food cost dashboard...
      </section>
    );
  }

  if (error) {
    return (
      <section className="purchase-card" data-testid="spend-summary-panel">
        <p className="purchase-kicker">Food cost</p>
        <h2 className="purchase-title">Spend dashboard unavailable</h2>
        <p className="purchase-muted">{error}</p>
      </section>
    );
  }

  return (
    <section className="purchase-card spend-summary-panel" data-testid="spend-summary-panel">
      <div className="purchase-card-header" style={{ alignItems: "flex-start", gap: 16 }}>
        <div>
          <p className="purchase-kicker">Food cost</p>
          <h2 className="purchase-title">Spend dashboard</h2>
        </div>
        <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
          <label style={{ display: "grid", gap: 4, fontSize: 12, fontWeight: 700 }}>
            Period
            <select
              data-testid="spend-period-selector"
              value={period}
              onChange={(event) => setPeriod(Number(event.target.value))}
              style={{
                border: "1px solid #cbd5e1",
                borderRadius: 6,
                color: "#0f172a",
                padding: "6px 8px",
              }}
            >
              {PERIOD_OPTIONS.map((days) => (
                <option key={days} value={days}>
                  {days} days
                </option>
              ))}
            </select>
          </label>
          <span
            data-testid="price-alerts-badge"
            style={{
              border: `1px solid ${alertTone}`,
              borderRadius: 999,
              color: alertTone,
              fontWeight: 700,
              padding: "6px 10px",
            }}
          >
            {alerts.length > 0 ? `${alerts.length} price alerts` : "No price alerts"}
          </span>
        </div>
      </div>

      <div className="mini-metric-grid" data-testid="spend-overview">
        <div>
          <span>Total spend</span>
          <strong>{money(summary?.totalSpend)}</strong>
        </div>
        <div>
          <span>Orders</span>
          <strong>{summary?.orderCount ?? 0}</strong>
        </div>
        <div>
          <span>Avg order</span>
          <strong>{money(summary?.avgOrderAmount)}</strong>
        </div>
        <div>
          <span>Cost per cover</span>
          <strong>{summary?.costPerCover != null ? money(summary.costPerCover, 2) : "No cover data"}</strong>
        </div>
      </div>

      <div data-testid="spend-categories" style={{ display: "grid", gap: 10, marginTop: 16 }}>
        {categories.map((category) => {
          const pct = Number(category.pctOfTotal || 0);
          const width = `${Math.max(4, (pct / maxCategoryPct) * 100)}%`;
          return (
            <div key={category.category}>
              <div className="purchase-card-header" style={{ marginBottom: 4 }}>
                <span>{categoryLabel(category.category)}</span>
                <strong>
                  {money(category.totalAmount)} ({pct.toFixed(1)}%)
                </strong>
              </div>
              <div style={{ background: "#e5e7eb", borderRadius: 999, height: 8, overflow: "hidden" }}>
                <div
                  aria-label={`${categoryLabel(category.category)} spend share`}
                  style={{ background: "#2563eb", borderRadius: 999, height: "100%", width }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <details open={alerts.length > 0} data-testid="price-alerts-list" style={{ marginTop: 18 }}>
        <summary style={{ cursor: "pointer", fontWeight: 800 }}>Price alert details</summary>
        <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
          {alerts.length === 0 ? (
            <p className="purchase-muted">Invoice prices are within rolling ranges.</p>
          ) : (
            alerts.slice(0, 8).map((alert) => {
              const tone = alertColor(Number(alert.variancePct || 0));
              return (
                <div
                  key={`${alert.itemName}-${alert.supplierName}-${alert.currentPrice}`}
                  data-testid="price-alert-item"
                  style={{
                    borderLeft: `4px solid ${tone}`,
                    display: "grid",
                    gap: 2,
                    padding: "4px 0 4px 10px",
                  }}
                >
                  <strong>{alert.itemName}</strong>
                  <span style={{ color: tone, fontWeight: 700 }}>
                    Invoice price {money(alert.currentPrice, 2)} vs rolling avg {money(alert.avgPrice, 2)} (+
                    {Number(alert.variancePct || 0).toFixed(1)}%)
                  </span>
                  <span className="purchase-muted">
                    {alert.supplierName || "Unknown supplier"}
                    {alert.category ? ` · ${categoryLabel(alert.category)}` : ""}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </details>

      <div data-testid="supplier-spend-breakdown" style={{ display: "grid", gap: 10, marginTop: 18 }}>
        <div className="purchase-card-header">
          <h3 style={{ fontSize: 16, margin: 0 }}>Supplier spend</h3>
          <span className="purchase-muted">Top {Math.min(10, suppliers.length)} suppliers</span>
        </div>
        {suppliers.map((supplier, index) => {
          const width = `${Math.max(4, (Number(supplier.totalAmount || 0) / maxSupplierSpend) * 100)}%`;
          return (
            <div key={supplier.supplierId || supplier.supplierName} data-testid="supplier-spend-row">
              <div className="purchase-card-header" style={{ marginBottom: 4 }}>
                <span>
                  {index + 1}. {supplier.supplierName}
                </span>
                <strong>
                  {money(supplier.totalAmount)} · {supplier.orderCount} orders
                </strong>
              </div>
              <div style={{ background: "#e5e7eb", borderRadius: 999, height: 8, overflow: "hidden" }}>
                <div
                  aria-label={`${supplier.supplierName} spend`}
                  style={{ background: "#0f766e", borderRadius: 999, height: "100%", width }}
                />
              </div>
              {supplier.categories?.length ? (
                <small className="purchase-muted">{supplier.categories.map(categoryLabel).join(", ")}</small>
              ) : null}
            </div>
          );
        })}
      </div>

      <div data-testid="cost-per-cover-trend" style={{ display: "grid", gap: 10, marginTop: 18 }}>
        <div className="purchase-card-header">
          <h3 style={{ fontSize: 16, margin: 0 }}>Cost per cover trend</h3>
          <strong>{currentCoverPoint ? money(currentCoverPoint.costPerCover, 2) : "No cover data"}</strong>
        </div>
        {coverPoints.length === 0 ? (
          <p className="purchase-muted" data-testid="cost-per-cover-empty">
            No cover data available
          </p>
        ) : (
          <svg aria-label="Cost per cover trend" role="img" viewBox="0 0 260 54" style={{ width: "100%", height: 64 }}>
            <path d={path} fill="none" stroke="#7c3aed" strokeLinecap="round" strokeWidth="3" />
          </svg>
        )}
      </div>
    </section>
  );
}
