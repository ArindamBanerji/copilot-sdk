import { useEffect, useState } from "react";

import { getEarlyWarnings } from "../api";
import type { EarlyWarning, EarlyWarningResponse, TrendSignal } from "../types";

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDelta(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

function label(value: string): string {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}

function riskTone(riskScore: number): string {
  if (riskScore >= 0.7) {
    return "border-red-200 bg-red-50";
  }
  if (riskScore >= 0.4) {
    return "border-amber-200 bg-amber-50";
  }
  return "border-slate-200 bg-white";
}

function severityTone(severity: TrendSignal["severity"]): string {
  if (severity === "critical") {
    return "bg-red-100 text-red-800";
  }
  if (severity === "warning") {
    return "bg-amber-100 text-amber-800";
  }
  if (severity === "watch") {
    return "bg-sky-100 text-sky-800";
  }
  return "bg-slate-100 text-slate-700";
}

function directionMark(signal: TrendSignal): string {
  if (signal.direction === "stable") {
    return "-";
  }
  const isExceptionSignal = signal.signal_name.toLowerCase().includes("exception");
  if (signal.direction === "declining") {
    return isExceptionSignal && signal.delta_pct > 0 ? "^" : "v";
  }
  return isExceptionSignal ? "v" : "^";
}

export function EarlyWarningPanel() {
  const [data, setData] = useState<EarlyWarningResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError(false);

    getEarlyWarnings()
      .then((response) => {
        if (cancelled) {
          return;
        }
        if (response) {
          setData(response);
        } else {
          setData(null);
          setError(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
          setError(true);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const warnings = data?.warnings ?? [];

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Supplier trend risk</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Early Warning Signals</h2>
          <p className="mt-1 text-sm text-slate-500">
            Watch suppliers whose exception, delivery, or financial signals are moving out of tolerance.
          </p>
        </div>
        {!loading && !error ? (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
            {data?.active_warnings ?? 0} active
          </span>
        ) : null}
      </div>

      {loading ? (
        <div className="mt-4 rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-600">
          Loading early warning signals...
        </div>
      ) : error ? (
        <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          Unable to load early warning signals.
        </div>
      ) : warnings.length === 0 ? (
        <div className="mt-4 rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-600">
          No active warnings.
        </div>
      ) : (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <SummaryMetric label="Active warnings" value={String(data?.active_warnings ?? warnings.length)} />
            <SummaryMetric label="Monitored suppliers" value={String(data?.monitored_suppliers ?? 0)} />
            <SummaryMetric label="Patterns detected" value={String(data?.patterns_detected ?? 0)} />
          </div>

          <div className="mt-4 space-y-4">
            {warnings.map((warning) => (
              <WarningCard key={warning.supplier_id} warning={warning} />
            ))}
          </div>
        </>
      )}
    </article>
  );
}

function SummaryMetric({ label: metricLabel, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{metricLabel}</p>
      <p className="mt-1 text-xl font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function WarningCard({ warning }: { warning: EarlyWarning }) {
  return (
    <section className={`rounded-lg border p-4 ${riskTone(warning.risk_score)}`}>
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-950">{warning.supplier_name}</h3>
          <p className="mt-1 text-sm text-slate-600">{label(warning.pattern)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">
            Risk {formatPercent(warning.risk_score)}
          </span>
          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">
            Confidence {formatPercent(warning.confidence)}
          </span>
          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">
            {warning.lead_time_weeks}w lead time
          </span>
        </div>
      </div>

      <p className="mt-3 text-sm text-slate-700">{warning.recommendation}</p>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {warning.signals.map((signal) => (
          <div key={signal.signal_name} className="rounded-md border border-white/70 bg-white/80 p-3">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-semibold text-slate-950">{label(signal.signal_name)}</p>
              <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${severityTone(signal.severity)}`}>
                {label(signal.severity)}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-600">
              {directionMark(signal)} {label(signal.direction)} {formatDelta(signal.delta_pct)}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Current {signal.current_value.toFixed(2)} vs baseline {signal.baseline_value.toFixed(2)}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
