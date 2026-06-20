import { useEffect, useMemo, useState } from "react";
import { getIKSSummary } from "../api";
import type { IKSSummary } from "../types";

const CATEGORY_ORDER = ["protein", "produce", "dairy", "dry_goods", "beverages"];

function categoryLabel(category: string) {
  return category.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function boundedScore(value?: number) {
  const score = Number(value ?? 0);
  if (!Number.isFinite(score)) return 0;
  return Math.max(0, Math.min(score, 100));
}

export default function IKSTrackerPanel() {
  const [summary, setSummary] = useState<IKSSummary>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const nextSummary = await getIKSSummary();
        if (active) {
          setSummary(nextSummary);
        }
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load IKS");
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

  const score = boundedScore(summary?.iksScore);
  const categories = useMemo(() => {
    const values = summary?.perCategory ?? {};
    return CATEGORY_ORDER.filter((category) => Object.prototype.hasOwnProperty.call(values, category));
  }, [summary]);

  if (loading) {
    return (
      <section className="purchase-card" data-testid="iks-tracker-panel">
        Loading IKS...
      </section>
    );
  }

  if (error) {
    return (
      <section className="purchase-card" data-testid="iks-tracker-panel">
        <p className="purchase-kicker">IKS</p>
        <h2 className="purchase-title">IKS unavailable</h2>
        <p className="purchase-muted">{error}</p>
      </section>
    );
  }

  return (
    <section className="purchase-card" data-testid="iks-tracker-panel">
      <div className="purchase-card-header" style={{ alignItems: "flex-start", gap: 16 }}>
        <div>
          <p className="purchase-kicker">Institutional knowledge</p>
          <h2 className="purchase-title">Your system knows {score.toFixed(0)}% of patterns</h2>
          <p className="purchase-muted">
            IKS is computed from verified decisions and updates as chefs confirm or override orders.
          </p>
        </div>
        <div
          data-testid="iks-gauge"
          style={{
            alignItems: "center",
            border: "8px solid #dbeafe",
            borderRadius: "50%",
            display: "flex",
            height: 104,
            justifyContent: "center",
            minWidth: 104,
            width: 104,
          }}
        >
          <strong style={{ color: "#1d4ed8", fontSize: 24 }}>{score.toFixed(0)}%</strong>
        </div>
      </div>

      <div style={{ display: "grid", gap: 10, marginTop: 16 }}>
        {categories.map((category) => {
          const value = boundedScore(summary?.perCategory?.[category]);
          return (
            <div key={category}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <span style={{ color: "#475569", fontWeight: 700 }}>{categoryLabel(category)}</span>
                <span style={{ color: "#1e293b", fontWeight: 800 }}>{value.toFixed(0)}%</span>
              </div>
              <div style={{ background: "#e2e8f0", borderRadius: 999, height: 8, marginTop: 5 }}>
                <div
                  style={{
                    background: "#2563eb",
                    borderRadius: 999,
                    height: "100%",
                    width: `${value}%`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
