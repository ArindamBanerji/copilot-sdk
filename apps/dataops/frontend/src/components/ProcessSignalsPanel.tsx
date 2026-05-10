import type { ProcessSignalsResponse } from "../types";

interface ProcessSignalsPanelProps {
  signals: ProcessSignalsResponse | null;
  loading: boolean;
}

export default function ProcessSignalsPanel({ signals, loading }: ProcessSignalsPanelProps) {
  if (loading) {
    return (
      <section className="copilot-card p-4 text-sm dataops-muted">
        Loading process context...
      </section>
    );
  }

  const metrics = signals?.metrics || [];
  const flatSignals = Object.entries(signals?.signals || {});

  if (!signals || (metrics.length === 0 && flatSignals.length === 0)) {
    return null;
  }

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="dataops-section-title">Process Signals</h2>
          <p className="text-sm dataops-muted">{signals.system || "unknown system"}</p>
        </div>
        <span
          className="rounded-full px-2 py-1 text-xs font-semibold"
          style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}
        >
          ⚡ Celonis EMS
        </span>
      </div>

      <div className="grid gap-2">
        {metrics.length > 0
          ? metrics.map((metric, index) => (
              <div
                key={`${metric.name || "metric"}-${index}`}
                className="rounded-md border p-3 text-sm"
                style={{ borderColor: "var(--copilot-border)" }}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold" style={{ color: "var(--copilot-text)" }}>
                    {metric.name || metric.label || "Process metric"}
                  </span>
                  <span style={{ color: "var(--copilot-primary)" }}>
                    {formatMetricValue(metric.value, metric.unit)}
                    {typeof metric.deltaPct === "number" ? ` (${metric.deltaPct >= 0 ? "↑" : "↓"}${Math.abs(metric.deltaPct)}% vs baseline)` : ""}
                  </span>
                </div>
                {metric.baseline !== undefined ? (
                  <div className="mt-1 text-xs dataops-muted">Baseline: {formatMetricValue(metric.baseline, metric.unit)}</div>
                ) : null}
              </div>
            ))
          : flatSignals.map(([key, value]) => (
              <div key={key} className="flex justify-between gap-3 rounded-md px-3 py-2 text-sm" style={{ background: "var(--copilot-surface-muted)" }}>
                <span className="dataops-muted">{humanize(key)}</span>
                <span className="font-semibold" style={{ color: "var(--copilot-text)" }}>{String(value)}</span>
              </div>
            ))}
      </div>

      {signals.variant?.id || signals.variant?.description ? (
        <div className="mt-4 rounded-md p-3 text-sm" style={{ background: "var(--copilot-surface-muted)" }}>
          <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>
            Variant {signals.variant.id || "matched"}
          </div>
          {signals.variant.description ? <div className="mt-1 dataops-muted">{signals.variant.description}</div> : null}
        </div>
      ) : null}

      {signals.correlation?.narrative || typeof signals.correlation?.confidence === "number" ? (
        <div className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-primary)" }}>
          {signals.correlation?.narrative ? <div style={{ color: "var(--copilot-text)" }}>{signals.correlation.narrative}</div> : null}
          {typeof signals.correlation?.confidence === "number" ? (
            <div className="mt-1 text-xs dataops-muted">
              Confidence: {Math.round(signals.correlation.confidence * 100)}%
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function formatMetricValue(value: unknown, unit?: string): string {
  const number = Number(value);
  const display = Number.isFinite(number) ? String(number) : String(value ?? "--");
  return unit ? `${display} ${unit}` : display;
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
