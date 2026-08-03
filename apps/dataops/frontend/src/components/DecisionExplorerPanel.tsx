import { useEffect, useMemo, useState } from "react";
import { fetchDecisions } from "../api";
import type { SelfDecisionEntry, SelfDecisionExplorerResponse } from "../types";

export default function DecisionExplorerPanel() {
  const [data, setData] = useState<SelfDecisionExplorerResponse | null>(null);
  const [category, setCategory] = useState("");
  const [action, setAction] = useState("");
  const [outcome, setOutcome] = useState("");
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

  const allDecisions = data?.decisions || [];
  const decisions = useMemo(
    () => allDecisions.filter((decision) => !outcome || outcomeName(decision) === outcome),
    [allDecisions, outcome],
  );
  const categories = useMemo(() => unique(allDecisions.map((decision) => decision.category)), [allDecisions]);
  const actions = useMemo(
    () => unique(allDecisions.map((decision) => actionName(decision))),
    [allDecisions],
  );
  const correctCount = decisions.filter((decision) => outcomeName(decision) === "correct").length;
  const commonAction = mostCommon(decisions.map((decision) => actionName(decision)));

  if (error) {
    return null;
  }

  return (
    <section data-testid="decision-explorer" className="copilot-card p-5">
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
        <div className="grid gap-2 sm:grid-cols-[10rem_10rem_10rem_auto]">
          <Filter label="Category" value={category} options={categories} onChange={setCategory} />
          <Filter label="Action" value={action} options={actions} onChange={setAction} />
          <Filter label="Outcome" value={outcome} options={["correct", "incorrect", "pending"]} onChange={setOutcome} />
          <label className="flex items-end gap-2 pb-2 text-xs font-semibold dataops-muted">
            <input type="checkbox" checked={verifiedOnly} onChange={(event) => setVerifiedOnly(event.target.checked)} />
            Verified only
          </label>
        </div>
      </div>

      {!loading ? (
        <div data-testid="decision-summary" className="mt-4 grid gap-2 text-sm sm:grid-cols-4">
          <Summary label="Decisions" value={String(decisions.length)} />
          <Summary label="Accuracy" value={decisions.length ? `${Math.round((correctCount / decisions.length) * 100)}%` : "n/a"} />
          <Summary label="Common action" value={humanize(commonAction || "n/a")} />
          <Summary label="Outcome filter" value={humanize(outcome || "all")} />
        </div>
      ) : null}
      {!loading && decisions.length === 0 ? <p className="mt-4 text-sm dataops-muted">No decisions match these filters.</p> : null}
      {decisions.length > 0 ? (
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="dataops-muted">
              <tr>
                <th className="py-2 pr-4">Decision</th>
                <th className="py-2 pr-4">Category</th>
                <th className="py-2 pr-4">Action</th>
                <th className="py-2 pr-4">Outcome</th>
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
                    <td className="py-3 pr-4">{outcomeBadge(outcomeName(decision))}</td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        <span>{formatPercent(decision.confidence)}</span>
                        <span className="h-1.5 w-16 overflow-hidden rounded-full" style={{ background: "var(--copilot-surface-muted)" }}>
                          <span className="block h-full rounded-full" style={{ width: `${confidencePercent(decision.confidence)}%`, background: "var(--copilot-primary)" }} />
                        </span>
                      </div>
                    </td>
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

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs dataops-muted">{label}</div>
      <div className="mt-1 font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</div>
    </div>
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
  return outcomeBadge(outcomeName(decision));
}

function outcomeBadge(outcome: string) {
  if (outcome === "correct") {
    return <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">correct</span>;
  }
  if (outcome === "incorrect") {
    return <span className="rounded-full bg-red-50 px-2 py-1 text-xs font-semibold text-red-700">incorrect</span>;
  }
  return <span className="rounded-full px-2 py-1 text-xs font-semibold dataops-muted">pending</span>;
}

function outcomeName(decision: SelfDecisionEntry): "correct" | "incorrect" | "pending" {
  const raw = decision as SelfDecisionEntry & { correct?: boolean };
  const value = decision.isCorrect ?? decision.is_correct ?? raw.correct;
  return value === true ? "correct" : value === false ? "incorrect" : "pending";
}

function mostCommon(values: string[]): string | undefined {
  const counts = new Map<string, number>();
  values.forEach((value) => counts.set(value, (counts.get(value) || 0) + 1));
  return [...counts.entries()].sort((left, right) => right[1] - left[1])[0]?.[0];
}

function formatPercent(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "n/a";
}

function confidencePercent(value: unknown): number {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.min(100, Math.round(number * 100))) : 0;
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
