import { useEffect, useMemo, useState } from "react";
import { fetchRegimeVrp } from "../api";
import type { RegimeVrpResponse } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

function value(value: number | null | undefined, digits = 1): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "-";
}

export default function RegimeVRPCard() {
  const [payload, setPayload] = useState<RegimeVrpResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const regimes = useMemo(() => Object.values(payload?.regimes || {}), [payload]);

  useEffect(() => {
    let cancelled = false;
    fetchRegimeVrp()
      .then((data) => {
        if (!cancelled) setPayload(data);
      })
      .catch((loadError) => {
        console.debug("regime vrp unavailable", loadError);
        if (!cancelled) setError("Regime VRP unavailable.");
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
    <section className="copilot-card p-5" data-testid="regime-vrp-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">V5 volatility diagnostic</p>
          <h2 className="mt-1 text-xl font-semibold">Regime-Conditioned Rich/Cheap</h2>
        </div>
        <ProvenanceBadge source={payload?.provenance || "accumulating"} />
      </div>
      <div className="mt-4 grid gap-2">
        {regimes.length ? regimes.map((row) => (
          <div key={row.regime} className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-white/5 px-3 py-2 text-sm">
            <span className="font-semibold">{row.regime}</span>
            <span>{value(payload?.dayZero ? null : row.percentile)}th percentile</span>
            <span className="uppercase trading-muted">{row.band || "unknown"}</span>
          </div>
        )) : <p className="text-sm trading-muted">Awaiting regime-tagged VRP decisions.</p>}
      </div>
      {payload?.dayZero ? (
        <p className="mt-3 text-sm trading-muted">Awaiting {payload.decisionsUntilMeasured ?? 0} more decisions before measured magnitude.</p>
      ) : null}
      <p className="mt-3 text-xs trading-muted">Diagnostic only. Substantiation: {payload?.substantiation || "T-O"}.</p>
    </section>
  );
}
