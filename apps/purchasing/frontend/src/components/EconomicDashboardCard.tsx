import { useEffect, useMemo, useState } from "react";
import { fetchEconomicModel, type EconomicModelResponse } from "../api";

function money(value?: number) {
  return `$${Math.round(Number(value ?? 0)).toLocaleString()}`;
}

function label(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function EconomicDashboardCard() {
  const [model, setModel] = useState<EconomicModelResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchEconomicModel()
      .then((data) => {
        if (mounted) setModel(data);
      })
      .catch((caught) => {
        if (mounted) setError(caught instanceof Error ? caught.message : "ROI unavailable");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const sourceRows = useMemo(() => Object.entries(model?.sources ?? {}), [model]);
  const unlockRows = (model?.unlocks ?? []).slice(0, 6);

  if (loading) {
    return <section className="purchase-card">Loading ROI...</section>;
  }

  if (error) {
    return (
      <section className="purchase-card error-card">
        <p className="purchase-kicker">ROI unavailable</p>
        <p>{error}</p>
      </section>
    );
  }

  if (!model) {
    return <section className="purchase-card">Not enough decisions for ROI calculation</section>;
  }

  return (
    <section className="purchase-card" data-testid="economic-dashboard-card">
      <div className="panel-header">
        <div>
          <p className="purchase-kicker">ROI Dashboard</p>
          <h2 className="purchase-title">Year 1: {money(model.annualProjection)} savings at current pace</h2>
        </div>
        <span className="badge">{model.provenance === "demo" ? "Sample data" : model.tier}</span>
      </div>

      <div className="stats-row">
        <div>
          <span>Month target</span>
          <strong>{money(model.projectedSavings)}</strong>
        </div>
        <div>
          <span>Saved so far</span>
          <strong>{money(model.actualSavings)}</strong>
        </div>
        <div>
          <span>Attainment</span>
          <strong>{Number(model.attainmentPct ?? 0).toFixed(0)}%</strong>
        </div>
        <div>
          <span>At $499/month</span>
          <strong>{Number(model.roiMultiple ?? 0).toFixed(1)}x ROI</strong>
        </div>
      </div>

      <div className="purchase-grid two">
        <div>
          <h3>Where savings came from</h3>
          <ul className="compact-list">
            {sourceRows.map(([name, value]) => (
              <li key={name}>
                <span>{label(name)}</span>
                <strong>{money(value)}</strong>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3>This week</h3>
          <p>{model.weeklyReport?.summary ?? "No weekly savings yet."}</p>
          <p className="trading-muted">Net recovered this month: {money(model.weeklyReport?.netRecoveredMonth)}</p>
        </div>
      </div>

      <div>
        <h3>Bank proof</h3>
        <ul className="compact-list">
          {unlockRows.map((row) => (
            <li key={row.name}>
              <span>{row.name}</span>
              <strong>{money(row.savings)}</strong>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
