import { useEffect, useMemo, useState } from "react";

const BASE = "http://localhost:8020";

type CostImpact = {
  dollars_found?: number;
  food_cost_saved?: number;
  waste_prevented?: number;
  prep_waste_avoided?: number;
  price_variance_flagged?: number;
  price_flags_surfaced?: number;
  net_found_period?: number;
};

type SupplierChange = {
  supplier?: string;
  supplier_id?: string;
  issue?: string;
  metric?: string;
  pct?: number;
};

type TopItem = {
  item?: string;
  name?: string;
  issue?: string;
  amount?: number;
  value?: number;
};

type WeeklyReport = {
  cost_impact?: CostImpact;
  supplier_changes?: SupplierChange[];
  top_items?: TopItem[];
  total_decisions?: number;
  total_verified?: number;
};

function money(value?: number) {
  return `$${Math.round(Number(value ?? 0)).toLocaleString()}`;
}

function label(value?: string) {
  return String(value || "price flag").replace(/_/g, " ");
}

export default function WeeklyReportPanel() {
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let mounted = true;
    fetch(`${BASE}/api/purchasing/report/weekly`)
      .then((response) => {
        if (!response.ok) throw new Error(`Weekly report failed with ${response.status}`);
        return response.json() as Promise<WeeklyReport>;
      })
      .then((data) => {
        if (mounted) setReport(data);
      })
      .catch(() => {
        if (mounted) setError(true);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const impact = report?.cost_impact ?? {};
  const found = Number(impact.dollars_found ?? impact.food_cost_saved ?? 0);
  const prevented = Number(impact.waste_prevented ?? impact.prep_waste_avoided ?? 0);
  const flagged = Number(impact.price_variance_flagged ?? impact.price_flags_surfaced ?? 0);
  const net = Number(impact.net_found_period ?? found + prevented + flagged);
  const topItems = useMemo(() => (report?.top_items ?? []).slice(0, 4), [report]);
  const supplierChanges = useMemo(() => (report?.supplier_changes ?? []).slice(0, 4), [report]);

  if (loading) {
    return <section className="purchase-card">Loading weekly report...</section>;
  }

  if (error || !report) {
    return (
      <section className="purchase-card" data-testid="weekly-report-panel">
        <p className="purchase-kicker">Weekly Report</p>
        <h2 className="purchase-title">No report data</h2>
        <p className="purchase-muted">The weekly report appears after order decisions are available.</p>
      </section>
    );
  }

  return (
    <section className="purchase-card" data-testid="weekly-report-panel">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Weekly Report</p>
          <h2 className="purchase-title">What the kitchen found this week</h2>
          <p className="purchase-muted">
            {report.total_verified ?? 0} verified decisions from {report.total_decisions ?? 0} orders.
          </p>
        </div>
      </div>

      <div className="stats-row">
        <div>
          <span>Found</span>
          <strong>{money(found)}</strong>
        </div>
        <div>
          <span>Prevented</span>
          <strong>{money(prevented)}</strong>
        </div>
        <div>
          <span>Flagged</span>
          <strong>{money(flagged)}</strong>
        </div>
      </div>

      <p className="purchase-muted mt-3">Net this month: {money(net)}</p>

      <div className="purchase-grid two mt-4">
        <div>
          <h3>Top Items</h3>
          {topItems.length > 0 ? (
            <ul className="compact-list">
              {topItems.map((item, index) => (
                <li key={`${item.item ?? item.name ?? "item"}-${index}`}>
                  <span>{item.item ?? item.name ?? "Item"} - {label(item.issue)}</span>
                  <strong>{money(item.amount ?? item.value)}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <p className="purchase-muted">No top items yet.</p>
          )}
        </div>
        <div>
          <h3>Supplier Flags</h3>
          {supplierChanges.length > 0 ? (
            <ul className="compact-list">
              {supplierChanges.map((change, index) => (
                <li key={`${change.supplier_id ?? change.supplier ?? "supplier"}-${index}`}>
                  <span>{change.supplier ?? change.supplier_id ?? "Supplier"} - {label(change.issue ?? change.metric)}</span>
                  <strong>{Number(change.pct ?? 0).toFixed(1)}%</strong>
                </li>
              ))}
            </ul>
          ) : (
            <p className="purchase-muted">No supplier flags yet.</p>
          )}
        </div>
      </div>
    </section>
  );
}
