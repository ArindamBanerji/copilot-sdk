import { useEffect, useState } from "react";
import { getSupplierScorecards } from "../api";
import type { SupplierScorecard } from "../types";

function formatPct(value?: number) {
  return `${Number(value ?? 0).toFixed(1)}%`;
}

function tierStyle(tier?: string) {
  if (tier === "A") return { background: "#dcfce7", color: "#166534" };
  if (tier === "B") return { background: "#fef3c7", color: "#92400e" };
  return { background: "#fee2e2", color: "#991b1b" };
}

export default function SupplierScorecardPanel() {
  const [scorecards, setScorecards] = useState<SupplierScorecard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const nextScorecards = await getSupplierScorecards();
        if (active) {
          setScorecards(nextScorecards);
        }
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load supplier scorecards");
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

  if (loading) {
    return (
      <section className="purchase-card" data-testid="supplier-scorecard-panel">
        Loading supplier scorecards...
      </section>
    );
  }

  if (error) {
    return (
      <section className="purchase-card" data-testid="supplier-scorecard-panel">
        <p className="purchase-kicker">Supplier scorecards</p>
        <h2 className="purchase-title">Supplier scorecards unavailable</h2>
        <p className="purchase-muted">{error}</p>
      </section>
    );
  }

  return (
    <section className="purchase-card" data-testid="supplier-scorecard-panel">
      <div className="purchase-card-header" style={{ alignItems: "flex-start", gap: 16 }}>
        <div>
          <p className="purchase-kicker">Supplier scorecards</p>
          <h2 className="purchase-title">Supplier reliability and price trend</h2>
          <p className="purchase-muted">
            QBO order history plus verified exceptions, ranked for purchasing decisions.
          </p>
        </div>
        <span className="status-pill">scraped_external</span>
      </div>

      <div style={{ overflowX: "auto", marginTop: 14 }}>
        <table style={{ borderCollapse: "collapse", minWidth: 720, width: "100%" }}>
          <thead>
            <tr style={{ color: "#64748b", fontSize: 12, textAlign: "left", textTransform: "uppercase" }}>
              <th style={{ padding: "8px 6px" }}>Supplier</th>
              <th style={{ padding: "8px 6px" }}>Tier</th>
              <th style={{ padding: "8px 6px" }}>On-time</th>
              <th style={{ padding: "8px 6px" }}>Price trend</th>
              <th style={{ padding: "8px 6px" }}>Exceptions</th>
              <th style={{ padding: "8px 6px" }}>Summary</th>
            </tr>
          </thead>
          <tbody>
            {scorecards.map((card) => (
              <tr key={card.supplierId} style={{ borderTop: "1px solid #e2e8f0" }}>
                <td style={{ padding: "10px 6px", fontWeight: 800 }}>{card.supplierName}</td>
                <td style={{ padding: "10px 6px" }}>
                  <span
                    data-testid="supplier-tier-badge"
                    style={{
                      borderRadius: 999,
                      display: "inline-flex",
                      fontSize: 12,
                      fontWeight: 900,
                      minWidth: 28,
                      justifyContent: "center",
                      padding: "4px 9px",
                      ...tierStyle(card.tier),
                    }}
                  >
                    {card.tier}
                  </span>
                </td>
                <td style={{ padding: "10px 6px" }}>{formatPct(card.reliabilityPct)}</td>
                <td style={{ padding: "10px 6px" }}>{formatPct(card.priceTrendPct)}</td>
                <td style={{ padding: "10px 6px" }}>{formatPct(card.exceptionRate)}</td>
                <td style={{ padding: "10px 6px" }}>
                  <details>
                    <summary style={{ cursor: "pointer", fontWeight: 700 }}>{card.trend}</summary>
                    <p className="purchase-muted" style={{ margin: "6px 0 0" }}>
                      {card.summary}
                    </p>
                  </details>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
