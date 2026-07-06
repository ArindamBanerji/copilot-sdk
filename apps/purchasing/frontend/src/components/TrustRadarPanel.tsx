import { useEffect, useMemo, useState } from "react";
import { getExpectedTrustWeights, getTrustInsights, getTrustWeights } from "../api";
import { factorDisplayName } from "../factorDisplay";
import type { TrustExpectedWeightsResponse, TrustInsight, TrustWeightsResponse } from "../types";

const FACTORS = [
  "expectedDemand",
  "dayOfWeek",
  "weatherForecast",
  "eventFlag",
  "historicalWaste",
  "supplierLeadTime",
  "priceMemoryIndex",
];
const CATEGORIES = ["protein", "produce", "dairy", "dryGoods", "beverages"];

const FALLBACK_LABELS: Record<string, string> = {
  expectedDemand: factorDisplayName("expectedDemand"),
  dayOfWeek: factorDisplayName("dayOfWeek"),
  weatherForecast: factorDisplayName("weatherForecast"),
  eventFlag: factorDisplayName("eventFlag"),
  historicalWaste: factorDisplayName("historicalWaste"),
  supplierLeadTime: factorDisplayName("supplierLeadTime"),
  priceMemoryIndex: factorDisplayName("priceMemoryIndex"),
};

function categoryLabel(category: string) {
  return category.replace(/([A-Z])/g, " $1").replace(/\b\w/g, (char) => char.toUpperCase());
}

function bounded(value?: number) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) return 0;
  return Math.max(0, Math.min(numeric, 1));
}

function pointsFor(values: Record<string, number> | undefined, radius: number, center: number) {
  return FACTORS.map((factor, index) => {
    const angle = -Math.PI / 2 + (index * Math.PI * 2) / FACTORS.length;
    const value = bounded(values?.[factor]);
    const r = radius * value;
    return `${center + Math.cos(angle) * r},${center + Math.sin(angle) * r}`;
  }).join(" ");
}

function axisPoint(index: number, radius: number, center: number) {
  const angle = -Math.PI / 2 + (index * Math.PI * 2) / FACTORS.length;
  return {
    x: center + Math.cos(angle) * radius,
    y: center + Math.sin(angle) * radius,
  };
}

export default function TrustRadarPanel() {
  const [weights, setWeights] = useState<TrustWeightsResponse>();
  const [expected, setExpected] = useState<TrustExpectedWeightsResponse>();
  const [insights, setInsights] = useState<TrustInsight[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("protein");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const [nextWeights, nextExpected, nextInsights] = await Promise.all([
          getTrustWeights(),
          getExpectedTrustWeights(),
          getTrustInsights(),
        ]);
        if (active) {
          setWeights(nextWeights);
          setExpected(nextExpected);
          setInsights(nextInsights);
          const firstCategory = Object.keys(nextWeights.weights ?? {})[0] ?? "protein";
          setSelectedCategory(firstCategory);
        }
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load trust analysis");
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

  const factorLabels = expected?.factorLabels ?? FALLBACK_LABELS;
  const visibleCategories = useMemo(
    () => CATEGORIES.filter((category) => expected?.weights?.[category] || weights?.weights?.[category]),
    [expected, weights],
  );
  const actualValues = weights?.weights?.[selectedCategory];
  const expectedValues = expected?.weights?.[selectedCategory];
  const active = weights?.phase === "active" && actualValues;
  const progress = Math.min(100, Math.round(((weights?.decisionsTotal ?? 0) / 200) * 100));

  if (loading) {
    return (
      <section className="purchase-card" data-testid="trust-radar-panel">
        Loading trust analysis...
      </section>
    );
  }

  if (error) {
    return (
      <section className="purchase-card" data-testid="trust-radar-panel">
        <p className="purchase-kicker">Trust radar</p>
        <h2 className="purchase-title">Trust analysis unavailable</h2>
        <p className="purchase-muted">{error}</p>
      </section>
    );
  }

  return (
    <section className="purchase-card" data-testid="trust-radar-panel">
      <div className="purchase-card-header" style={{ alignItems: "flex-start", gap: 16 }}>
        <div>
          <p className="purchase-kicker">Trust radar</p>
          <h1 className="purchase-title">The system learns which kitchen signals deserve trust</h1>
          <p className="purchase-muted">
            DK trust weights come from verified decisions. Expected weights are preset defaults.
          </p>
        </div>
        <span className="status-pill">{weights?.provenance ?? "real_measured"}</span>
      </div>

      {active ? (
        <>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14 }}>
            {visibleCategories.map((category) => (
              <button
                key={category}
                type="button"
                onClick={() => setSelectedCategory(category)}
                className={category === selectedCategory ? "tab-button active" : "tab-button"}
              >
                {categoryLabel(category)}
              </button>
            ))}
          </div>

          <div style={{ display: "grid", gap: 18, gridTemplateColumns: "minmax(280px, 360px) 1fr", marginTop: 18 }}>
            <svg
              data-testid="trust-radar-chart"
              viewBox="0 0 320 320"
              role="img"
              aria-label="Trust radar chart"
              style={{ maxWidth: 360, width: "100%" }}
            >
              {[0.25, 0.5, 0.75, 1].map((scale) => (
                <polygon
                  key={scale}
                  points={pointsFor(Object.fromEntries(FACTORS.map((factor) => [factor, scale])), 112, 160)}
                  fill="none"
                  stroke="#e2e8f0"
                  strokeWidth="1"
                />
              ))}
              {FACTORS.map((factor, index) => {
                const end = axisPoint(index, 116, 160);
                const label = axisPoint(index, 142, 160);
                return (
                  <g key={factor}>
                    <line x1="160" y1="160" x2={end.x} y2={end.y} stroke="#cbd5e1" />
                    <text
                      x={label.x}
                      y={label.y}
                      textAnchor={label.x < 145 ? "end" : label.x > 175 ? "start" : "middle"}
                      dominantBaseline="middle"
                      fill="#475569"
                      fontSize="11"
                      fontWeight="700"
                    >
                      {factorLabels[factor] ?? FALLBACK_LABELS[factor]}
                    </text>
                  </g>
                );
              })}
              <polygon
                points={pointsFor(expectedValues, 112, 160)}
                fill="none"
                stroke="#64748b"
                strokeDasharray="6 4"
                strokeWidth="2"
              />
              <polygon
                points={pointsFor(actualValues, 112, 160)}
                fill="rgba(34, 197, 94, 0.28)"
                stroke="#16a34a"
                strokeWidth="3"
              />
            </svg>

            <div>
              <div style={{ display: "flex", gap: 14, marginBottom: 12 }}>
                <span className="purchase-muted">Green: actual DK trust</span>
                <span className="purchase-muted">Gray dashed: expected</span>
              </div>
              <div style={{ display: "grid", gap: 8 }}>
                {FACTORS.map((factor) => (
                  <div key={factor} style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                    <span style={{ color: "#475569", fontWeight: 700 }}>
                      {factorLabels[factor] ?? FALLBACK_LABELS[factor]}
                    </span>
                    <strong>{bounded(actualValues?.[factor]).toFixed(2)}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      ) : (
        <div data-testid="trust-learning-state" style={{ marginTop: 18 }}>
          <h2 className="purchase-title" style={{ fontSize: 20 }}>
            Learning your patterns - {weights?.decisionsTotal ?? 0}/200 decisions
          </h2>
          <div style={{ background: "#e2e8f0", borderRadius: 999, height: 10, marginTop: 10 }}>
            <div
              style={{
                background: "#16a34a",
                borderRadius: 999,
                height: "100%",
                width: `${progress}%`,
              }}
            />
          </div>
          <p className="purchase-muted" style={{ marginTop: 10 }}>
            DK trust weights appear after enough verified chef actions. Factors include{" "}
            {FACTORS.map((factor) => factorLabels[factor] ?? FALLBACK_LABELS[factor]).join(", ")}.
          </p>
        </div>
      )}

      {insights.length > 0 ? (
        <div className="purchase-grid two" style={{ marginTop: 18 }}>
          {insights.map((insight) => (
            <article
              key={`${insight.category}-${insight.trapFactor}-${insight.trustedFactor}`}
              data-testid="trust-insight-card"
              style={{
                background: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: 8,
                padding: 14,
              }}
            >
              <p className="purchase-kicker">{categoryLabel(insight.category)}</p>
              <p style={{ color: "#1e293b", fontWeight: 800, margin: 0 }}>{insight.insight}</p>
              <p className="purchase-muted" style={{ margin: "8px 0 0" }}>
                Gap {(Number(insight.gap) * 100).toFixed(0)} percentage points.
              </p>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
