import { useEffect, useState } from "react";
import { fetchAccuracyByCategory } from "../api";
import type { SelfAccuracyByCategoryResponse, SelfCategoryAccuracy } from "../types";

type AccuracyLevel = "green" | "amber" | "red";

export default function AccuracyAlertsPanel() {
  const [data, setData] = useState<SelfAccuracyByCategoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchAccuracyByCategory()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <section data-testid="accuracy-alerts" className="copilot-card p-5 text-sm dataops-muted">Loading accuracy alerts...</section>;
  }
  if (error) {
    return <section data-testid="accuracy-alerts" className="copilot-card p-5 text-sm dataops-muted">Accuracy alerts unavailable.</section>;
  }

  const categories = data?.categories || [];
  const threshold = data?.threshold ?? 0.7;
  const alertCount = categories.filter((category) => category.alert || numeric(category.accuracy) < threshold).length;

  return (
    <section data-testid="accuracy-alerts" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-12 · SELF-COMPUTATION
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Accuracy Alerts
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            Per-category accuracy across {data?.overallVerified ?? 0} verified decisions.
          </p>
        </div>
        <div data-testid="accuracy-alert-summary" className="rounded-md px-3 py-2" style={{ background: alertCount ? "rgba(220, 38, 38, 0.1)" : "rgba(22, 163, 74, 0.1)" }}>
          <p className="text-xs font-semibold uppercase tracking-wide dataops-muted">Below threshold</p>
          <p className="mt-1 text-lg font-semibold" style={{ color: alertCount ? "var(--copilot-danger)" : "var(--copilot-success)" }}>
            {alertCount} categor{alertCount === 1 ? "y" : "ies"}
          </p>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-xs dataops-muted">
        <span>Threshold: {formatPercent(threshold)}</span>
        <span>Green &gt;80% · Amber 60–80% · Red &lt;60%</span>
      </div>
      <div className="mt-3 grid gap-3" data-testid="accuracy-category-list">
        {categories.length === 0 ? <p className="text-sm dataops-muted">No verified category history yet.</p> : null}
        {categories.map((category) => <CategoryRow key={category.category || "uncategorized"} category={category} threshold={threshold} />)}
      </div>
    </section>
  );
}

function CategoryRow({ category, threshold }: { category: SelfCategoryAccuracy; threshold: number }) {
  const accuracy = numeric(category.accuracy);
  const level = accuracy > 0.8 ? "green" : accuracy >= 0.6 ? "amber" : "red";
  const belowThreshold = Boolean(category.alert) || accuracy < threshold;
  const trend = trendValue(category);
  return (
    <div data-testid="accuracy-category" data-accuracy-level={level} data-alert={belowThreshold ? "true" : "false"} className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{humanize(category.category || "uncategorized")}</div>
          <div className="mt-1 text-xs dataops-muted">
            {category.correct ?? 0}/{category.total ?? 0} correct · {trend}
          </div>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={badgeStyle(level)}>
          {belowThreshold ? "Alert" : level}
        </span>
      </div>
      <div className="relative mt-3 h-3 overflow-hidden rounded-full" style={{ background: "rgba(148, 163, 184, 0.22)" }}>
        <div className="absolute inset-y-0 z-10 border-l-2 border-dashed" style={{ left: `${Math.min(threshold * 100, 100)}%`, borderColor: "var(--copilot-text-muted)" }} />
        <div className="h-full rounded-full" style={{ width: `${Math.min(Math.max(accuracy * 100, 0), 100)}%`, background: levelColor(level) }} />
      </div>
      <div className="mt-1 flex justify-between text-xs font-semibold" style={{ color: "var(--copilot-text)" }}>
        <span>{formatPercent(accuracy)}</span>
        <span>{belowThreshold ? "Needs attention" : "Stable"}</span>
      </div>
    </div>
  );
}

function numeric(value: unknown): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function trendValue(category: SelfCategoryAccuracy): string {
  const trend = (category as SelfCategoryAccuracy & { trend?: unknown }).trend;
  return typeof trend === "string" && trend ? trend : "stable";
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function humanize(value: string): string {
  return value.replace(/[_-]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function levelColor(level: AccuracyLevel): string {
  return level === "green" ? "#16a34a" : level === "amber" ? "#d97706" : "#dc2626";
}

function badgeStyle(level: AccuracyLevel) {
  return { background: `${levelColor(level)}1f`, color: levelColor(level) };
}
