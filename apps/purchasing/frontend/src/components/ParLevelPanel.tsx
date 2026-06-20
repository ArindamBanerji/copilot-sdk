import { useEffect, useMemo, useState } from "react";
import { getParRecommendations, getParStatus } from "../api";
import type { ParRecommendation, ParStatus } from "../types";

function formatCurrency(value?: number) {
  return new Intl.NumberFormat("en-US", {
    currency: "USD",
    maximumFractionDigits: 0,
    style: "currency",
  }).format(Number(value ?? 0));
}

function formatNumber(value?: number) {
  return Number(value ?? 0).toLocaleString(undefined, { maximumFractionDigits: 1 });
}

function categoryLabel(category?: string) {
  return (category ?? "unknown").replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function confidenceStyle(confidence?: string) {
  const normalized = (confidence ?? "").toLowerCase();
  if (normalized === "high") return { background: "#dcfce7", color: "#166534" };
  if (normalized === "moderate") return { background: "#fef3c7", color: "#92400e" };
  return { background: "#f1f5f9", color: "#475569" };
}

export default function ParLevelPanel() {
  const [recommendations, setRecommendations] = useState<ParRecommendation[]>([]);
  const [status, setStatus] = useState<ParStatus>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const [nextRecommendations, nextStatus] = await Promise.all([
          getParRecommendations(),
          getParStatus(),
        ]);
        if (active) {
          setRecommendations(nextRecommendations);
          setStatus(nextStatus);
        }
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load par intelligence");
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

  const topRecommendations = useMemo(
    () => recommendations.slice(0, 5),
    [recommendations],
  );
  const adjustmentCount = recommendations.filter(
    (rec) => Math.abs(Number(rec.recommendedPar ?? 0) - Number(rec.currentPar ?? 0)) >= 1,
  ).length;
  const weeklySavings = recommendations.reduce(
    (sum, rec) => sum + Number(rec.weeklySavingsEstimate ?? 0),
    0,
  );

  if (loading) {
    return (
      <section className="purchase-card" data-testid="par-level-panel">
        Loading par intelligence...
      </section>
    );
  }

  if (error) {
    return (
      <section className="purchase-card" data-testid="par-level-panel">
        <p className="purchase-kicker">Par intelligence</p>
        <h2 className="purchase-title">Par recommendations unavailable</h2>
        <p className="purchase-muted">{error}</p>
      </section>
    );
  }

  return (
    <section className="purchase-card" data-testid="par-level-panel">
      <div className="purchase-card-header" style={{ alignItems: "flex-start", gap: 16 }}>
        <div>
          <p className="purchase-kicker">Par intelligence</p>
          <h2 className="purchase-title">Recommended par levels</h2>
          <p className="purchase-muted">
            QBO order history tuned for service level and waste exposure.
          </p>
        </div>
        <span className="status-pill">{status?.provenanceTier ?? "scraped_external"}</span>
      </div>

      <div className="mini-metric-grid" data-testid="par-level-summary" style={{ marginTop: 14 }}>
        <div>
          <span>Items analyzed</span>
          <strong>{status?.totalItems ?? recommendations.length}</strong>
          <small>{status?.dataSource ?? "quickbooks_online"}</small>
        </div>
        <div>
          <span>Adjustments recommended</span>
          <strong>{adjustmentCount}</strong>
          <small>par level changes</small>
        </div>
        <div>
          <span>Weekly savings estimate</span>
          <strong>{formatCurrency(weeklySavings)}</strong>
          <small>estimate, not measured outcome</small>
        </div>
      </div>

      {topRecommendations.length === 0 ? (
        <p className="purchase-muted" style={{ marginTop: 16 }}>
          No par level recommendations are available from QBO order history yet.
        </p>
      ) : (
        <div className="purchase-grid two" style={{ marginTop: 16 }}>
          {topRecommendations.map((rec) => (
            <article
              key={`${rec.category}-${rec.itemName}`}
              data-testid="par-recommendation-card"
              style={{
                border: "1px solid #e2e8f0",
                borderRadius: 8,
                padding: 16,
                background: "#fff",
              }}
            >
              <div className="purchase-card-header" style={{ alignItems: "flex-start", gap: 12 }}>
                <div>
                  <p className="purchase-kicker">{categoryLabel(rec.category)}</p>
                  <h3 className="purchase-title" style={{ fontSize: 18 }}>
                    {rec.itemName}
                  </h3>
                </div>
                <span
                  style={{
                    borderRadius: 999,
                    fontSize: 12,
                    fontWeight: 800,
                    padding: "4px 9px",
                    ...confidenceStyle(rec.confidence),
                  }}
                >
                  {rec.confidence} confidence
                </span>
              </div>

              <div className="mini-metric-grid" style={{ marginTop: 12 }}>
                <div>
                  <span>Current par</span>
                  <strong>{formatNumber(rec.currentPar)}</strong>
                </div>
                <div>
                  <span>Recommended par</span>
                  <strong>{formatNumber(rec.recommendedPar)}</strong>
                </div>
                <div>
                  <span>Service level</span>
                  <strong>{Math.round(Number(rec.serviceLevel ?? 0) * 100)}%</strong>
                </div>
              </div>

              <p className="purchase-muted" style={{ marginTop: 12 }}>
                Weekly savings estimate: <strong>{formatCurrency(rec.weeklySavingsEstimate)}</strong>
              </p>

              {rec.seasonalAdjustment ? (
                <p
                  className="purchase-muted"
                  data-testid="par-seasonal-note"
                  style={{ marginTop: 8 }}
                >
                  Seasonal adjustment: +{Math.round((rec.seasonalAdjustment - 1) * 100)}% for{" "}
                  {categoryLabel(rec.category).toLowerCase()}.
                </p>
              ) : null}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
