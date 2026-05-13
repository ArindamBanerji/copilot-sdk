import { useEffect, useState } from "react";

import { fetchAuditTrail } from "../api";
import type { SelfDecisionEntry } from "../types";

function idOf(decision: SelfDecisionEntry): string {
  return decision.decision_id ?? decision.decisionId ?? "decision";
}

function actionOf(decision: SelfDecisionEntry): string {
  return decision.recommended_action ?? decision.recommendedAction ?? decision.action ?? "pending";
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

export function AuditTrailViewer() {
  const [trails, setTrails] = useState<SelfDecisionEntry[] | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchAuditTrail().then((response) => {
      if (active) setTrails(response?.trails ?? []);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="purchase-card">
      <p className="purchase-kicker">SC-16 Audit Trail</p>
      <h3 className="purchase-title">Decision to outcome chain</h3>
      {!trails ? (
        <p className="purchase-muted mt-4">Loading...</p>
      ) : trails.length === 0 ? (
        <p className="purchase-muted mt-4">No audit trails yet.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {trails.map((trail) => {
            const id = idOf(trail);
            const correct = trail.is_correct ?? trail.isCorrect;
            return (
              <article
                key={id}
                className={`rounded-lg border p-3 ${correct === false ? "border-rose-200 bg-rose-50" : "border-emerald-200 bg-emerald-50"}`}
              >
                <button className="flex w-full items-center justify-between text-left" onClick={() => setExpanded(expanded === id ? null : id)}>
                  <span className="font-mono text-xs text-slate-700">{id}</span>
                  <span className="text-xs uppercase tracking-[0.16em] text-slate-500">decision {"->"} factors {"->"} outcome</span>
                </button>
                <p className="mt-2 text-sm text-slate-700">
                  {label(trail.category ?? "category")} / {label(actionOf(trail))} / {Math.round((trail.confidence ?? 0) * 100)}%
                </p>
                {expanded === id ? (
                  <pre className="mt-3 overflow-x-auto rounded-md bg-white/80 p-2 text-xs text-slate-700">
                    {JSON.stringify(trail, null, 2)}
                  </pre>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
