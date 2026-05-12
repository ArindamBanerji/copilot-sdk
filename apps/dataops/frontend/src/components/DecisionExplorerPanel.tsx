import { useEffect, useMemo, useState } from "react";
import { fetchDecisions } from "../api";
import type { SelfDecisionEntry, SelfDecisionExplorerResponse } from "../types";

export default function DecisionExplorerPanel() {
  const [data, setData] = useState<SelfDecisionExplorerResponse | null>(null);
  const [category, setCategory] = useState("");
  const [action, setAction] = useState("");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [expanded, setExpanded] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    fetchDecisions({
      limit: 50,
      category: category || undefined,
      action: action || undefined,
      verifiedOnly,
    })
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
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
  }, [category, action, verifiedOnly]);

  const decisions = data?.decisions || [];
  const categories = useMemo(() => unique(decisions.map((decision) => decision.category)), [decisions]);
  const actions = useMemo(
    () => unique(decisions.map((decision) => actionName(decision))),
    [decisions],
  );

  if (error) {
    return null;
  }

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
            {loading ? "Loading decisions..." : `${data?.total ?? 0} GraphStore decisions`}
          </p>
        </div>
        <div className="grid gap-2 sm:grid-cols-[10rem_10rem_auto]">
          <Filter label="Category" value={category} options={categories} onChange={setCategory} />
          <Filter label="Action" value={action} options={actions} onChange={setAction} />
          <label className="flex items-end gap-2 pb-2 text-xs font-semibold dataops-muted">
            <input type="checkbox" checked={verifiedOnly} onChange={(event) => setVerifiedOnly(event.target.checked)} />
            Verified only
          </label>
        </div>
      </div>

      {!loading && decisions.length === 0 ? <p className="mt-4 text-sm dataops-muted">No decisions match these filters.</p> : null}
      {decisions.length > 0 ? (
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="dataops-muted">
              <tr>
                <th className="py-2 pr-4">Decision</th>
                <th className="py-2 pr-4">Category</th>
                <th className="py-2 pr-4">Action</th>
                <th className="py-2 pr-4">Confidence</th>
                <th className="py-2 pr-4">Timestamp</th>
                <th className="py-2">Verified</th>
              </tr>
            </thead>
            <tbody>
              {decisions.map((decision) => {
                const id = decisionId(decision);
                const isExpanded = expanded === id;
                return (
                  <tr key={id} className="border-t align-top" style={{ borderColor: "var(--copilot-border)" }}>
                    <td className="py-3 pr-4">
                      <button
                        type="button"
                        className="font-mono text-xs"
                        style={{ color: "var(--copilot-primary)" }}
                        onClick={() => setExpanded(isExpanded ? "" : id)}
                      >
                        {id}
                      </button>
                      {isExpanded ? (
                        <pre className="mt-2 max-h-40 overflow-auto rounded-md p-3 text-xs" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
                          {JSON.stringify(decision.factors || {}, null, 2)}
                        </pre>
                      ) : null}
                    </td>
                    <td className="py-3 pr-4">{humanize(decision.category || "uncategorized")}</td>
                    <td className="py-3 pr-4">{humanize(actionName(decision))}</td>
                    <td className="py-3 pr-4">{formatPercent(decision.confidence)}</td>
                    <td className="py-3 pr-4">{formatTimestamp(decision.createdAt)}</td>
                    <td className="py-3">{verifiedBadge(decision)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function Filter({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
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

function unique(values: Array<string | undefined>): string[] {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort();
}

function decisionId(decision: SelfDecisionEntry): string {
  return String(decision.decisionId || decision.decision_id || "unknown");
}

function actionName(decision: SelfDecisionEntry): string {
  return String(decision.recommendedAction || decision.recommended_action || decision.action || "unknown");
}

function verifiedBadge(decision: SelfDecisionEntry) {
  if (decision.isCorrect === true) {
    return <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">correct</span>;
  }
  if (decision.isCorrect === false) {
    return <span className="rounded-full bg-red-50 px-2 py-1 text-xs font-semibold text-red-700">incorrect</span>;
  }
  return <span className="rounded-full px-2 py-1 text-xs font-semibold dataops-muted">pending</span>;
}

function formatPercent(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "n/a";
}

function formatTimestamp(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return new Date(value * 1000).toLocaleString();
  }
  return value ? String(value) : "n/a";
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}
