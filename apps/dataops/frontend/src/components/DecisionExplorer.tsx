import { useEffect, useMemo, useState } from "react";
import { getDecisions } from "../api";
import type { ActionBreakdown, DecisionEntry, DecisionExplorerResponse } from "../types";

type CorrectFilter = "all" | "true" | "false";

interface DecisionFilters {
  system: string;
  category: string;
  action: string;
  correct: CorrectFilter;
}

const initialFilters: DecisionFilters = {
  system: "",
  category: "",
  action: "",
  correct: "all",
};

export default function DecisionExplorer() {
  const [data, setData] = useState<DecisionExplorerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DecisionFilters>(initialFilters);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    getDecisions({
      limit: 20,
      system: filters.system || undefined,
      category: filters.category || undefined,
      action: filters.action || undefined,
      correct: filters.correct === "all" ? undefined : filters.correct === "true",
    })
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load decision history.");
          setData(null);
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
  }, [filters]);

  const decisions = data?.decisions || [];
  const summary = data?.summary || {};
  const byAction = summary.byAction || {};
  const byCategory = summary.byCategory || {};
  const systemOptions = useMemo(() => uniqueOptions(decisions.map((decision) => decision.system)), [decisions]);
  const actionOptions = useMemo(() => uniqueOptions(Object.keys(byAction)), [byAction]);
  const categoryOptions = useMemo(() => uniqueOptions(Object.keys(byCategory)), [byCategory]);

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-14
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Decision Explorer
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            {loading ? "Loading decision history..." : `${data?.total ?? 0} decisions · ${formatPercent(summary.accuracy)} accuracy`}
          </p>
        </div>
        <div className="grid gap-2 sm:grid-cols-4">
          <FilterSelect label="System" value={filters.system} options={systemOptions} onChange={(system) => setFilters((current) => ({ ...current, system }))} />
          <FilterSelect label="Category" value={filters.category} options={categoryOptions} onChange={(category) => setFilters((current) => ({ ...current, category }))} />
          <FilterSelect label="Action" value={filters.action} options={actionOptions} onChange={(action) => setFilters((current) => ({ ...current, action }))} />
          <label className="grid gap-1 text-xs font-semibold dataops-muted">
            Correct
            <select
              className="rounded-md border px-2 py-2 text-sm"
              style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)", color: "var(--copilot-text)" }}
              value={filters.correct}
              onChange={(event) => setFilters((current) => ({ ...current, correct: event.target.value as CorrectFilter }))}
            >
              <option value="all">All</option>
              <option value="true">Correct</option>
              <option value="false">Incorrect</option>
            </select>
          </label>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p> : null}
      {!loading && !error && decisions.length === 0 ? <p className="mt-4 text-sm dataops-muted">No decisions match these filters.</p> : null}

      {!error && decisions.length > 0 ? (
        <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <Breakdown title="By Action" rows={byAction} />
          <Breakdown title="By Category" rows={byCategory} />
          <div className="xl:col-span-2">
            <h3 className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>Recent Decisions</h3>
            <div className="mt-3 grid gap-2">
              {decisions.map((decision, index) => (
                <DecisionRow key={`${decision.decisionId || decision.alertId || "decision"}-${index}`} decision={decision} />
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function FilterSelect({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-1 text-xs font-semibold dataops-muted">
      {label}
      <select
        className="rounded-md border px-2 py-2 text-sm"
        style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)", color: "var(--copilot-text)" }}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {humanize(option)}
          </option>
        ))}
      </select>
    </label>
  );
}

function Breakdown({ title, rows }: { title: string; rows: Record<string, ActionBreakdown> }) {
  const entries = Object.entries(rows).sort((left, right) => (right[1].count || 0) - (left[1].count || 0));
  return (
    <div>
      <h3 className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{title}</h3>
      <div className="mt-3 grid gap-2">
        {entries.length ? entries.map(([name, row]) => <BreakdownRow key={name} name={name} row={row} />) : <p className="text-sm dataops-muted">No breakdown available.</p>}
      </div>
    </div>
  );
}

function BreakdownRow({ name, row }: { name: string; row: ActionBreakdown }) {
  const winRate = numeric(row.winRate);
  return (
    <div>
      <div className="flex items-center justify-between gap-3 text-sm">
        <span style={{ color: "var(--copilot-text)" }}>{humanize(name)}</span>
        <span className="dataops-muted">{row.count ?? 0} · {formatPercent(winRate)}</span>
      </div>
      <div className="mt-1 h-2 overflow-hidden rounded-full" style={{ background: "var(--copilot-primary-light)" }}>
        <div className="h-full rounded-full" style={{ width: `${Math.max(0, Math.min(winRate ?? 0, 1)) * 100}%`, background: "var(--copilot-primary)" }} />
      </div>
    </div>
  );
}

function DecisionRow({ decision }: { decision: DecisionEntry }) {
  const correctness = decision.isCorrect === true ? "correct" : decision.isCorrect === false ? "incorrect" : "unknown";
  const color = correctness === "correct" ? "var(--copilot-success)" : correctness === "incorrect" ? "var(--copilot-danger)" : "var(--copilot-text-muted)";
  const icon = correctness === "correct" ? "✓" : correctness === "incorrect" ? "✗" : "?";
  return (
    <article className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
            {decision.alertId || decision.eventId || "Unknown alert"} · {humanize(decision.actionTaken || "unknown action")}
          </div>
          <p className="mt-1 text-xs dataops-muted">
            {decision.system || "unknown system"} · {humanize(decision.category || "uncategorized")} · {decision.source || "history"}
          </p>
        </div>
        <div className="text-right text-xs font-semibold" style={{ color }}>
          {icon} {humanize(correctness)}
          {typeof decision.scoreConfidence === "number" ? <div className="mt-1 dataops-muted">Score confidence {formatPercent(decision.scoreConfidence)}</div> : null}
        </div>
      </div>
    </article>
  );
}

function uniqueOptions(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort();
}

function numeric(value: unknown): number | null {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function formatPercent(value: unknown): string {
  const number = numeric(value);
  return number === null ? "n/a" : `${Math.round(number * 100)}%`;
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
