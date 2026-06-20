import { useEffect, useMemo, useState } from "react";
import { getCommodityIndices } from "../api";
import type { CommodityIndicesResponse } from "../types";

const CATEGORY_ORDER = ["protein", "produce", "dairy", "dry_goods", "beverages"];

function categoryLabel(category: string) {
  return category.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function indexTone(value?: number) {
  if (value == null || !Number.isFinite(value)) return "#64748b";
  if (value > 1.05) return "#b91c1c";
  if (value >= 0.98) return "#b45309";
  return "#15803d";
}

function trendLabel(value?: number) {
  if (value == null || !Number.isFinite(value)) return "No index";
  if (value > 1.05) return "above average";
  if (value >= 0.98) return "near average";
  return "below average";
}

function trendArrow(value?: number) {
  if (value == null || !Number.isFinite(value)) return "-";
  if (value > 1.05) return "↑";
  if (value >= 0.98) return "→";
  return "↓";
}

function cachedAge(asOf?: string | null): string {
  if (!asOf) return "";
  const timestamp = Date.parse(asOf);
  if (Number.isNaN(timestamp)) return "";
  const hours = Math.max(0, Math.round((Date.now() - timestamp) / (1000 * 60 * 60)));
  if (hours < 1) return " (<1h ago)";
  return ` (${hours}h ago)`;
}

function CommodityProvenanceBadge({ source, asOf }: { source: string; asOf?: string | null }) {
  const normalized = source.toLowerCase();
  const label =
    normalized === "live"
      ? "Commodity data: live"
      : normalized === "cached"
        ? `Commodity data: cached${cachedAge(asOf)}`
        : "Commodity data: sample";
  const color =
    normalized === "live"
      ? "#10b981"
      : normalized === "cached"
        ? "#f59e0b"
        : "#94a3b8";

  return (
    <div
      data-testid="commodity-provenance"
      style={{ alignItems: "center", display: "inline-flex", fontSize: 12, gap: 8, color: "#475569" }}
    >
      <span style={{ background: color, borderRadius: 999, height: 8, width: 8 }} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export default function CommodityPricePanel() {
  const [payload, setPayload] = useState<CommodityIndicesResponse>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const nextPayload = await getCommodityIndices();
        if (active) {
          setPayload(nextPayload);
        }
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load commodity prices");
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

  const indices = payload?.value ?? {};
  const categories = useMemo(
    () => CATEGORY_ORDER.filter((category) => Object.prototype.hasOwnProperty.call(indices, category)),
    [indices],
  );

  if (loading) {
    return (
      <section className="purchase-card" data-testid="commodity-price-panel">
        Loading commodity prices...
      </section>
    );
  }

  if (error) {
    return (
      <section className="purchase-card" data-testid="commodity-price-panel">
        <p className="purchase-kicker">Commodity prices</p>
        <h2 className="purchase-title">Commodity prices unavailable</h2>
        <p className="purchase-muted">{error}</p>
      </section>
    );
  }

  return (
    <section className="purchase-card" data-testid="commodity-price-panel">
      <div className="purchase-card-header" style={{ alignItems: "flex-start", gap: 16 }}>
        <div>
          <p className="purchase-kicker">Commodity prices</p>
          <h2 className="purchase-title">Category price indices</h2>
          <p className="purchase-muted">Index compares current commodity price to its 12-month average.</p>
        </div>
        <CommodityProvenanceBadge source={payload?.source ?? "fixture"} asOf={payload?.asOf} />
      </div>

      <div className="mini-metric-grid" style={{ marginTop: 14 }}>
        {categories.map((category) => {
          const value = Number(indices[category]);
          const tone = indexTone(value);
          return (
            <div key={category} data-testid="commodity-index-card">
              <span>{categoryLabel(category)}</span>
              <strong style={{ color: tone }}>
                {trendArrow(value)} {Number.isFinite(value) ? value.toFixed(3) : "n/a"}
              </strong>
              <small style={{ color: tone, fontWeight: 700 }}>{trendLabel(value)}</small>
            </div>
          );
        })}
      </div>
    </section>
  );
}
