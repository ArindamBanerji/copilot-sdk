import type { CSSProperties } from "react";
import type { AccuracyByCategoryResponse, CategoryAccuracy } from "../types";

interface AccuracyAlertsProps {
  data: AccuracyByCategoryResponse | null;
  loading?: boolean;
}

export default function AccuracyAlerts({ data, loading = false }: AccuracyAlertsProps) {
  if (loading) {
    return <section className="copilot-card p-4 text-sm dataops-muted">Loading accuracy by category...</section>;
  }

  const entries = Object.entries(data?.categories || {});
  if (!data || entries.length === 0) {
    return <section className="copilot-card p-4 text-sm dataops-muted">Accuracy by category unavailable.</section>;
  }

  const sorted = entries.sort((left, right) => {
    const leftAccuracy = numeric(left[1].accuracy, 1);
    const rightAccuracy = numeric(right[1].accuracy, 1);
    return leftAccuracy - rightAccuracy || left[0].localeCompare(right[0]);
  });

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="dataops-section-title">Accuracy by Category</h2>
          <p className="mt-1 text-xs dataops-muted">
            {formatPercent(data.overallAccuracy)} overall accuracy across {data.totalDecisions ?? 0} verified decisions.
          </p>
        </div>
        <TrendSummary declining={data.categoriesDeclining || []} improving={data.categoriesImproving || []} />
      </div>

      <div className="mt-4 grid gap-2">
        {sorted.map(([category, accuracy]) => (
          <CategoryRow key={category} category={category} accuracy={accuracy} />
        ))}
      </div>
    </section>
  );
}

function CategoryRow({ category, accuracy }: { category: string; accuracy: CategoryAccuracy }) {
  const value = numeric(accuracy.accuracy, 0);
  const level = accuracy.alertLevel || "warning";
  return (
    <div className="grid gap-2 rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
            {humanize(category)}
          </div>
          <div className="mt-1 text-xs dataops-muted">
            {accuracy.correct ?? 0}/{accuracy.total ?? 0} correct · {accuracy.trend || "stable"}
            {accuracy.recentAccuracy != null ? ` · recent ${formatPercent(accuracy.recentAccuracy)}` : ""}
          </div>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={levelStyle(level)}>
          {levelIcon(level)} {level}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full" style={{ background: "rgba(148, 163, 184, 0.22)" }}>
        <div className="h-full rounded-full" style={{ width: `${Math.min(value * 100, 100)}%`, ...barStyle(level) }} />
      </div>
      <div className="text-right text-xs font-semibold" style={{ color: "var(--copilot-text)" }}>
        {formatPercent(accuracy.accuracy)}
      </div>
    </div>
  );
}

function TrendSummary({ declining, improving }: { declining: string[]; improving: string[] }) {
  if (declining.length === 0 && improving.length === 0) {
    return <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">stable</span>;
  }
  return (
    <div className="text-right text-xs dataops-muted">
      {declining.length > 0 ? <div>Declining: {declining.map(humanize).join(", ")}</div> : null}
      {improving.length > 0 ? <div>Improving: {improving.map(humanize).join(", ")}</div> : null}
    </div>
  );
}

function numeric(value: unknown, fallback: number): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function formatPercent(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "n/a";
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}

function levelIcon(level: string): string {
  if (level === "critical") {
    return "!";
  }
  if (level === "warning") {
    return "!";
  }
  return "OK";
}

function levelStyle(level: string): CSSProperties {
  if (level === "critical") {
    return { background: "#fee2e2", color: "#b91c1c" };
  }
  if (level === "warning") {
    return { background: "#fef3c7", color: "#92400e" };
  }
  return { background: "#dcfce7", color: "#166534" };
}

function barStyle(level: string): CSSProperties {
  if (level === "critical") {
    return { background: "#dc2626" };
  }
  if (level === "warning") {
    return { background: "#d97706" };
  }
  return { background: "#16a34a" };
}
