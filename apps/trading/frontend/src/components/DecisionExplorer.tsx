import { useEffect, useMemo, useState } from "react";
import { fetchDecisions } from "../api";
import type { SelfDecisionEntry, SelfDecisionExplorerResponse } from "../types";

export default function DecisionExplorer() {
  const [data, setData] = useState<SelfDecisionExplorerResponse | null>(null);
  const [category, setCategory] = useState("");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [expanded, setExpanded] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    fetchDecisions({ category: category || undefined, verifiedOnly, limit: 50 })
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
  }, [category, verifiedOnly]);

  const decisions = Array.isArray(data?.decisions) ? data.decisions : [];
  const categories = useMemo(
    () => Array.from(new Set(decisions.map((decision) => decision.category).filter((value): value is string => Boolean(value)))).sort(),
    [decisions],
  );

  if (error) {
    return <section className="copilot-card p-4 text-sm trading-muted">Decision Explorer unavailable.</section>;
  }

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-14
          </p>
          <h2 className="mt-1 text-xl font-semibold">Decision Explorer</h2>
          <p className="mt-1 text-sm trading-muted">
            {loading ? "Loading trading decisions..." : `${data?.total ?? 0} GraphStore decisions`}
          </p>
        </div>
        <div className="flex flex-wrap gap-3 text-sm">
          <label className="grid gap-1 text-xs font-semibold trading-muted">
            Category
            <select className="rounded-md border px-2 py-2 text-sm" value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="">All categories</option>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {humanize(item)}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-end gap-2 pb-2 text-xs font-semibold trading-muted">
            <input type="checkbox" checked={verifiedOnly} onChange={(event) => setVerifiedOnly(event.target.checked)} />
            Verified only
          </label>
        </div>
      </div>

      {!loading && decisions.length === 0 ? <p className="mt-4 text-sm trading-muted">No decisions yet.</p> : null}
      {decisions.length > 0 ? (
        <div className="mt-5 grid gap-3">
          {decisions.map((decision, index) => {
            const id = decisionId(decision, index);
            return (
              <DecisionCard key={id} decision={decision} expanded={expanded === id} onToggle={() => setExpanded(expanded === id ? "" : id)} />
            );
          })}
        </div>
      ) : null}
    </section>
  );
}

function DecisionCard({ decision, expanded, onToggle }: { decision: SelfDecisionEntry; expanded: boolean; onToggle: () => void }) {
  const factorEntries = Object.entries(decision.factors || {}).slice(0, 6);
  return (
    <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <button className="font-mono text-xs font-semibold" style={{ color: "var(--copilot-primary)" }} type="button" onClick={onToggle}>
            {decisionId(decision)}
          </button>
          <p className="mt-1 text-sm trading-muted">
            {humanize(decision.category || "uncategorized")} · {humanize(actionName(decision))}
          </p>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
          {decision.isCorrect === true ? "correct" : decision.isCorrect === false ? "incorrect" : "pending"}
        </span>
      </div>
      <div className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
        <Fact label="Confidence" value={formatPercent(decision.confidence)} />
        <Fact label="Recommended" value={humanize(actionName(decision))} />
        <Fact label="Created" value={formatTimestamp(decision.createdAt)} />
      </div>
      {expanded ? (
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {factorEntries.length ? factorEntries.map(([key, value]) => <Fact key={key} label={humanize(key)} value={formatValue(value)} />) : <p className="text-sm trading-muted">No factor breakdown available.</p>}
        </div>
      ) : null}
    </article>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-sm font-semibold">{value}</div>
    </div>
  );
}

function decisionId(decision: SelfDecisionEntry, fallbackIndex = 0): string {
  return String(decision.decisionId || decision.decision_id || `decision-${fallbackIndex}`);
}

function actionName(decision: SelfDecisionEntry): string {
  return String(decision.recommendedAction || decision.recommended_action || decision.actualAction || decision.actual_action || decision.action || "unknown");
}

function formatPercent(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "n/a";
}

function formatTimestamp(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) return new Date(value * 1000).toLocaleString();
  return value ? String(value) : "n/a";
}

function formatValue(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : String(value ?? "n/a");
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}
