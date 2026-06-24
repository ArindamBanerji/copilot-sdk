import { useEffect, useState } from "react";
import { getCrossSystemInsights, type CrossSystemAlert } from "../api";

function label(value?: string): string {
  return String(value || "unknown").replace(/_/g, " ");
}

function pct(value?: number): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

export default function CrossSystemPanel() {
  const [alerts, setAlerts] = useState<CrossSystemAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getCrossSystemInsights()
      .then((payload) => {
        if (cancelled) return;
        setAlerts(payload?.alerts || []);
      })
      .catch(() => {
        if (!cancelled) setError("Cross-system insights are unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--copilot-primary)" }}>
            Cross-system insights
          </p>
          <h2 className="mt-1 text-xl font-semibold">Cross-System Insights</h2>
          <p className="mt-2 text-sm" style={{ color: "var(--copilot-text-muted)" }}>
            Advisory only -- no automated action taken.
          </p>
        </div>
        {loading ? <span className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>Loading...</span> : null}
      </div>

      {error ? <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      {!loading && !error && alerts.length === 0 ? (
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm" style={{ color: "var(--copilot-text-muted)" }}>
          No cross-system correlations detected.
        </p>
      ) : null}

      <div className="mt-4 grid gap-3">
        {alerts.map((alert) => {
          const entityId = alert.entityId || alert.entity_id || "entity";
          const sourceSignal = alert.sourceSignal || alert.source_signal;
          const relatedSignal = alert.relatedSignal || alert.related_signal;
          return (
            <article key={alert.alertId || alert.alert_id || entityId} className="rounded-md border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-slate-950">{label(entityId)}</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    {label(sourceSignal)} correlated with {label(relatedSignal)}
                  </p>
                </div>
                <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                  Correlation {pct(alert.correlation)}
                </span>
              </div>
              {alert.timeline?.length ? (
                <ol className="mt-3 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
                  {alert.timeline.map((item, index) => (
                    <li key={`${entityId}-${index}`} className="rounded-md bg-slate-50 p-2">
                      {String(item.domain || "copilot")}: {label(String(item.signal || "signal"))}
                    </li>
                  ))}
                </ol>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
