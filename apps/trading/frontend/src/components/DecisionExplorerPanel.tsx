import { useEffect, useMemo, useState } from "react";
import { fetchDecisions } from "../api";
import type { SelfDecisionEntry, SelfDecisionExplorerResponse } from "../types";

export default function DecisionExplorerPanel() {
  const [data, setData] = useState<SelfDecisionExplorerResponse | null>(null);
  const [category, setCategory] = useState("");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [expanded, setExpanded] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchDecisions({ category: category || undefined, verifiedOnly, limit: 50 }).then((payload) => {
      if (!cancelled) setData(payload);
    });
    return () => {
      cancelled = true;
    };
  }, [category, verifiedOnly]);

  const decisions = data?.decisions || [];
  const categories = useMemo(() => Array.from(new Set(decisions.map((d) => d.category).filter(Boolean))).sort(), [decisions]);

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase" style={{ color: "var(--copilot-primary)" }}>SC-14</p>
          <h2 className="mt-1 text-xl font-semibold">Decision Explorer</h2>
          <p className="mt-1 text-sm trading-muted">{data?.total ?? 0} GraphStore decisions</p>
        </div>
        <div className="flex flex-wrap gap-3 text-sm">
          <select className="rounded-md border px-2 py-2" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All categories</option>
            {categories.map((item) => <option key={item} value={item}>{item?.replace(/_/g, " ")}</option>)}
          </select>
          <label className="flex items-center gap-2 trading-muted">
            <input type="checkbox" checked={verifiedOnly} onChange={(event) => setVerifiedOnly(event.target.checked)} />
            Verified only
          </label>
        </div>
      </div>
      {decisions.length === 0 ? <p className="mt-4 text-sm trading-muted">No decisions match these filters.</p> : null}
      <div className="mt-4 grid gap-2">
        {decisions.map((decision) => {
          const id = decisionId(decision);
          return (
            <article key={id} className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <button className="font-mono text-xs" type="button" onClick={() => setExpanded(expanded === id ? "" : id)}>{id}</button>
              <div className="mt-2 grid gap-2 text-sm md:grid-cols-4">
                <span>{humanize(decision.category || "uncategorized")}</span>
                <span>{humanize(actionName(decision))}</span>
                <span>{formatPercent(decision.confidence)}</span>
                <span>{decision.isCorrect === true ? "correct" : decision.isCorrect === false ? "incorrect" : "pending"}</span>
              </div>
              {expanded === id ? <pre className="mt-3 max-h-36 overflow-auto rounded-md p-3 text-xs trading-muted">{JSON.stringify(decision.factors || {}, null, 2)}</pre> : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}

function decisionId(decision: SelfDecisionEntry) {
  return String(decision.decisionId || decision.decision_id || "unknown");
}

function actionName(decision: SelfDecisionEntry) {
  return String(decision.recommendedAction || decision.recommended_action || decision.action || "unknown");
}

function formatPercent(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "n/a";
}

function humanize(value: string) {
  return value.replace(/_/g, " ");
}
