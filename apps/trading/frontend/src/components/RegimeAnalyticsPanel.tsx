import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

type RegimeName = "trending" | "volatile" | "ranging" | string;

interface RegimeStat {
  regime: RegimeName;
  decisionCount: number;
  verifiedCount: number;
  accuracy: number | null;
  iksProxy: number | null;
  conservationCount?: number;
  conservationSafeCount?: number;
  conservationRate?: number | null;
  measurementState: "measured" | "accumulating" | string;
  provenance: string;
}

interface RegimeAnalyticsResponse {
  regimes: Record<string, RegimeStat>;
  totalDecisions: number;
  regimeCount: number;
}

const DISPLAY_ORDER = ["trending", "volatile", "ranging"];

function label(value: string): string {
  return value.replace(/_/g, " ").replace(/^\w/, (letter) => letter.toUpperCase());
}

function percent(value: number | null): string {
  return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "-";
}

function iks(value: number | null): string {
  return typeof value === "number" ? (value * 100).toFixed(1) : "-";
}

function conservation(stat: RegimeStat): string {
  if (!stat.conservationCount || typeof stat.conservationRate !== "number") return "-";
  return `${(stat.conservationRate * 100).toFixed(1)}% safe`;
}

function measurementText(stat: RegimeStat): string {
  if (stat.decisionCount === 0) return "No decisions in this regime yet";
  if (stat.verifiedCount < 30) {
    return `${stat.verifiedCount} verified - need ${30 - stat.verifiedCount} more for measured stats`;
  }
  return "Measured from verified outcomes";
}

function stateMarker(state: string): string {
  return state === "measured" ? "measured" : "accumulating";
}

export default function RegimeAnalyticsPanel() {
  const [payload, setPayload] = useState<RegimeAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const regimes = useMemo(() => {
    const rows = payload?.regimes ?? {};
    return Object.values(rows).sort((left, right) => {
      const leftIndex = DISPLAY_ORDER.indexOf(left.regime);
      const rightIndex = DISPLAY_ORDER.indexOf(right.regime);
      return (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex);
    });
  }, [payload]);

  useEffect(() => {
    let cancelled = false;
    apiGet<RegimeAnalyticsResponse>("/api/trading/regime-analytics")
      .then((data) => {
        if (!cancelled) setPayload(data);
      })
      .catch((loadError) => {
        console.debug("regime analytics unavailable", loadError);
        if (!cancelled) setError("Regime analytics unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <div className="h-24 animate-pulse rounded-md bg-white/10" />;
  if (error) return <div className="text-sm text-red-500">{error}</div>;
  if (!payload) return null;

  return (
    <section data-testid="regime-analytics-panel" className="copilot-card p-5">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-base font-semibold">Per-Regime Decision Quality</h2>
          <p className="mt-1 text-sm trading-muted">
            Read-only stats from regime-tagged decisions.
          </p>
        </div>
        <div className="rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Total decisions</div>
          <div className="mt-1 font-semibold">{payload.totalDecisions}</div>
        </div>
      </div>

      <div className="mt-4 grid gap-3">
        {regimes.map((stat) => (
          <article
            key={stat.regime}
            data-testid={`regime-analytics-${stat.regime}`}
            className="rounded-md border p-4"
            style={{ borderColor: "var(--copilot-border)" }}
          >
            <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
              <div>
                <h3 className="font-semibold">
                  {label(stat.regime)} ({stat.decisionCount} decisions)
                </h3>
                <div className="mt-2 flex flex-wrap gap-3 text-sm">
                  <span data-testid={`regime-accuracy-${stat.regime}`}>Accuracy: {percent(stat.accuracy)}</span>
                  <span data-testid={`regime-iks-${stat.regime}`}>IKS: {iks(stat.iksProxy)}</span>
                  <span>Conservation: {conservation(stat)}</span>
                  <span className="trading-muted">[{stateMarker(stat.measurementState)}]</span>
                </div>
                <p className="mt-2 text-sm trading-muted">{measurementText(stat)}</p>
              </div>
              <ProvenanceBadge source={stat.provenance} />
            </div>
          </article>
        ))}
      </div>

      <p className="mt-4 text-sm trading-muted">
        Your edge is real where measured. In accumulating regimes, you do not have enough verified data to know yet.
      </p>
    </section>
  );
}
