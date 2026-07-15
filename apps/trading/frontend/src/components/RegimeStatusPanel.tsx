import { useEffect, useMemo, useState } from "react";
import { getRegimeStatus } from "../api";
import type { RegimeStatusResponse } from "../types";

function label(value: string | null | undefined): string {
  return value ? value.replace(/_/g, " ") : "unknown";
}

export default function RegimeStatusPanel() {
  const [status, setStatus] = useState<RegimeStatusResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    getRegimeStatus()
      .then((payload) => {
        if (!cancelled) {
          setStatus(payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStatus(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const active = status?.regimeBreakActive === true;
  const progress = useMemo(() => {
    const current = Math.max(0, Number(status?.decisionsInNewRegime || 0));
    const total = Math.max(1, Number(status?.decisionsToStabilize || 20));
    return Math.min(100, Math.round((current / total) * 100));
  }, [status]);

  if (!status) {
    return null;
  }

  return (
    <section
      data-testid="regime-status-panel"
      className={`copilot-card p-5 ${active ? "border-amber-300/60 bg-amber-500/10" : ""}`}
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">
            {active ? "Regime Break Detected" : "Regime Stability"}
          </p>
          <h2 data-testid="regime-status-current" className="mt-1 text-xl font-semibold capitalize">
            {active
              ? `${label(status.previousRegime)} -> ${label(status.currentRegime)}`
              : label(status.currentRegime)}
          </h2>
          <p className="mt-2 text-sm trading-muted">
            {status.decisionsInNewRegime} / {status.decisionsToStabilize} decisions in new regime
          </p>
        </div>
        <div className="rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Autonomy</div>
          <div data-testid="regime-status-autonomy" className="mt-1 font-semibold uppercase">
            {status.autonomyLevel}
          </div>
        </div>
      </div>

      {status.restrictions.length ? (
        <ul data-testid="regime-status-restrictions" className="mt-4 space-y-1 text-sm">
          {status.restrictions.map((restriction) => (
            <li key={restriction}>{restriction}</li>
          ))}
        </ul>
      ) : null}

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full bg-emerald-400" style={{ width: `${progress}%` }} />
      </div>
    </section>
  );
}
