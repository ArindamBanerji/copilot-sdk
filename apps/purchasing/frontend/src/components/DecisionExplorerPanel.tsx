import { useEffect, useMemo, useState } from "react";

import { fetchDecisions } from "../api";
import type { SelfDecisionEntry } from "../types";

function actionOf(decision: SelfDecisionEntry): string {
  return decision.recommended_action ?? decision.recommendedAction ?? decision.action ?? "pending";
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

export function DecisionExplorerPanel() {
  const [decisions, setDecisions] = useState<SelfDecisionEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchDecisions({ category: category || undefined, verifiedOnly }).then((response) => {
      if (!active) return;
      setDecisions(response?.decisions ?? []);
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [category, verifiedOnly]);

  const categories = useMemo(
    () =>
      Array.from(new Set(decisions.map((decision) => decision.category).filter((value): value is string => Boolean(value)))).sort(),
    [decisions],
  );

  return (
    <section className="purchase-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="purchase-kicker">SC-14 Decision Explorer</p>
          <h3 className="purchase-title">Purchasing decision history</h3>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <select
            className="rounded-md border border-slate-300 bg-white px-3 py-2"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="">All categories</option>
            {categories.map((item) => (
              <option key={item} value={item}>
                {label(item)}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-slate-600">
            <input type="checkbox" checked={verifiedOnly} onChange={(event) => setVerifiedOnly(event.target.checked)} />
            verified only
          </label>
        </div>
      </div>
      {loading ? (
        <p className="purchase-muted mt-4">Loading...</p>
      ) : decisions.length === 0 ? (
        <p className="purchase-muted mt-4">No decisions match these filters.</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-[0.16em] text-slate-500">
              <tr>
                <th className="py-2 pr-4">Decision</th>
                <th className="py-2 pr-4">Category</th>
                <th className="py-2 pr-4">Action</th>
                <th className="py-2 pr-4">Confidence</th>
                <th className="py-2">Verified</th>
              </tr>
            </thead>
            <tbody>
              {decisions.map((decision) => {
                const id = decision.decision_id ?? decision.decisionId ?? "decision";
                return (
                  <tr key={id} className="border-t border-slate-200">
                    <td className="py-2 pr-4">
                      <button className="font-mono text-xs text-emerald-700" onClick={() => setExpanded(expanded === id ? null : id)}>
                        {id}
                      </button>
                      {expanded === id ? (
                        <pre className="mt-2 max-w-md overflow-x-auto rounded-md bg-slate-100 p-2 text-xs text-slate-700">
                          {JSON.stringify(decision.factors ?? {}, null, 2)}
                        </pre>
                      ) : null}
                    </td>
                    <td className="py-2 pr-4 capitalize">{label(decision.category ?? "uncategorized")}</td>
                    <td className="py-2 pr-4 capitalize">{label(actionOf(decision))}</td>
                    <td className="py-2 pr-4">{Math.round((decision.confidence ?? 0) * 100)}%</td>
                    <td className="py-2">{decision.is_correct ?? decision.isCorrect ? "correct" : "pending"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

