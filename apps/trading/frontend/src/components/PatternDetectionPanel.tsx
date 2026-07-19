import { useEffect, useState } from "react";
import { getPatterns } from "../api";
import type { DetectedPattern, PatternDetectionResponse } from "../types";

function labelForPattern(name: string): string {
  return name
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function severityTone(severity: number): {
  label: string;
  badge: string;
  bar: string;
} {
  if (severity >= 0.7) {
    return {
      label: "High",
      badge: "border-red-400/40 bg-red-400/10 text-red-100",
      bar: "bg-red-400",
    };
  }
  if (severity >= 0.4) {
    return {
      label: "Medium",
      badge: "border-amber-400/40 bg-amber-400/10 text-amber-100",
      bar: "bg-amber-400",
    };
  }
  return {
    label: "Low",
    badge: "border-emerald-400/40 bg-emerald-400/10 text-emerald-100",
    bar: "bg-emerald-400",
  };
}

function formatPercent(value: number): string {
  return `${Math.round(Math.max(0, value) * 100)}%`;
}

function PatternCard({ pattern }: { pattern: DetectedPattern }) {
  const severity = Math.max(0, Math.min(1, Number(pattern.severity) || 0));
  const tone = severityTone(severity);
  const affectedTrades = pattern.affectedTrades ?? [];

  return (
    <article className="rounded-md border border-white/10 bg-white/[0.03] p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-white">
            {pattern.displayName || labelForPattern(pattern.name)}
          </h3>
          <p className="mt-1 text-sm trading-muted">{pattern.description}</p>
        </div>
        <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${tone.badge}`}>
          {tone.label} severity
        </span>
      </div>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
        <div className={`h-full rounded-full ${tone.bar}`} style={{ width: formatPercent(severity) }} />
      </div>

      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <p className="text-xs uppercase tracking-wide trading-muted">Frequency</p>
          <p className="font-semibold text-white">{formatPercent(pattern.frequency)}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide trading-muted">Affected trades</p>
          <p className="font-semibold text-white">{pattern.affectedTradeCount}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide trading-muted">Severity</p>
          <p className="font-semibold text-white">{severity.toFixed(2)}</p>
        </div>
      </div>

      {affectedTrades.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {affectedTrades.map((tradeId) => (
            <span key={tradeId} className="rounded-md border border-white/10 px-2 py-1 font-mono text-xs trading-muted">
              {tradeId}
            </span>
          ))}
        </div>
      ) : null}

      <p className="mt-4 text-sm text-white">{pattern.recommendation}</p>
    </article>
  );
}

export default function PatternDetectionPanel() {
  const [data, setData] = useState<PatternDetectionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const unavailable = Boolean(error) || !data;

  useEffect(() => {
    let cancelled = false;
    getPatterns()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((loadError) => {
        console.debug("pattern detection unavailable", loadError);
        if (!cancelled) setError("Pattern detection unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <section className="copilot-card p-5">
        <p className="text-sm uppercase tracking-wide trading-muted">Behavioral Pattern Detection</p>
        <h2 className="mt-1 text-xl font-semibold text-white">Scanning imported trades...</h2>
      </section>
    );
  }

  if (unavailable || !data) {
    return (
      <section className="copilot-card p-5">
        <p className="text-sm uppercase tracking-wide trading-muted">Behavioral Pattern Detection</p>
        <h2 className="mt-1 text-xl font-semibold text-white">Pattern detection unavailable</h2>
        <p className="mt-2 text-sm trading-muted">Trading behavior patterns are not available right now.</p>
      </section>
    );
  }

  const patterns = data.patterns ?? [];
  const totalTrades = data.totalTradesAnalyzed ?? data.totalTrades ?? 0;
  const totalPatterns = data.totalPatternsDetected ?? patterns.length;

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">Behavioral Pattern Detection</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Repeat behaviors across imported trades</h2>
          <p className="mt-2 text-sm trading-muted">
            Looks for recurring trading patterns such as rapid re-entry, clustered trades, and drawdown sizing.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2 text-right text-sm">
          <div className="rounded-md border border-white/10 px-3 py-2">
            <p className="text-2xl font-semibold text-white">{totalPatterns}</p>
            <p className="text-xs uppercase tracking-wide trading-muted">patterns</p>
          </div>
          <div className="rounded-md border border-white/10 px-3 py-2">
            <p className="text-2xl font-semibold text-white">{totalTrades}</p>
            <p className="text-xs uppercase tracking-wide trading-muted">trades</p>
          </div>
        </div>
      </div>

      {data.mostSevere ? (
        <div className="mt-4 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-sm">
          <span className="trading-muted">Most severe: </span>
          <span className="font-semibold text-white">{labelForPattern(data.mostSevere)}</span>
        </div>
      ) : null}

      {!patterns.length ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          {data.message || "Import trades to detect patterns."}
        </div>
      ) : (
        <div className="mt-5 grid gap-3">
          {patterns.map((pattern) => (
            <PatternCard key={pattern.name} pattern={pattern} />
          ))}
        </div>
      )}
    </section>
  );
}
