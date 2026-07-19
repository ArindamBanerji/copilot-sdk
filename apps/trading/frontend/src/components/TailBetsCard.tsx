import { useEffect, useState } from "react";
import { fetchCorrelation } from "../api";
import type { CorrelationResponse } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

function num(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "-";
}

export default function TailBetsCard() {
  const [payload, setPayload] = useState<CorrelationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCorrelation()
      .then((data) => {
        if (!cancelled) setPayload(data);
      })
      .catch((loadError) => {
        console.debug("tail bets unavailable", loadError);
        if (!cancelled) setError("Tail bets unavailable.");
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

  const dayZero = payload?.dayZero === true;
  const source = payload?.provenance || (payload?.source === "yfinance" && !dayZero ? "scraped_external" : "accumulating");

  if (dayZero) {
    return (
      <section className="copilot-card p-5" data-testid="tail-bets-card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm uppercase tracking-wide trading-muted">V7 volatility diagnostic</p>
            <h2 className="mt-1 text-xl font-semibold">Effective Bets in a Tail</h2>
          </div>
          <ProvenanceBadge source="accumulating" />
        </div>
        <p className="mt-3 text-sm trading-muted">
          Awaiting {payload?.decisionsUntilMeasured ?? 0} more decisions before measured magnitude.
        </p>
      </section>
    );
  }

  return (
    <section className="copilot-card p-5" data-testid="tail-bets-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">V7 volatility diagnostic</p>
          <h2 className="mt-1 text-xl font-semibold">Effective Bets in a Tail</h2>
        </div>
        <ProvenanceBadge source={source} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Effective multiplier</div>
          <div className="text-2xl font-semibold">{num(payload?.effectiveMultiplier)}x</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Effective bets</div>
          <div className="text-2xl font-semibold">{num(payload?.nEffectiveBets)}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Tail gap</div>
          <div className="text-2xl font-semibold">{num(payload?.tailGap)}</div>
        </div>
      </div>
      {payload?.source === "insufficient_data" ? (
        <p className="mt-3 text-sm trading-muted">{payload.reason || "Awaiting enough positions for tail-bet diagnostics."}</p>
      ) : null}
      <p className="mt-3 text-xs trading-muted">Diagnostic only. Substantiation: T-R when return history is available.</p>
    </section>
  );
}
