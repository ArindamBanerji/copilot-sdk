import { useEffect, useState } from "react";
import { fetchS2PAuditTrail } from "../api";
import type { AuditTrailResponse } from "../types";

function action(decision: { recommended_action?: string; recommendedAction?: string; action?: string }) {
  return (decision.recommended_action ?? decision.recommendedAction ?? decision.action ?? "n/a").replace(/_/g, " ");
}

export function AuditTrailPanel({ invoiceId }: { invoiceId?: string }) {
  const [data, setData] = useState<AuditTrailResponse | null>(null);

  useEffect(() => {
    if (!invoiceId) {
      setData(null);
      return;
    }
    let cancelled = false;
    fetchS2PAuditTrail(invoiceId).then((response) => {
      if (!cancelled) setData(response);
    });
    return () => {
      cancelled = true;
    };
  }, [invoiceId]);

  const decisions = data?.decisions ?? [];

  return (
    <article className="copilot-card p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Invoice audit trail</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">Decision to outcome chain</h2>
      {decisions.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No recorded decisions for this invoice yet.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {decisions.map((decision) => (
            <div key={decision.decision_id ?? decision.decisionId} className="rounded-md border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <span className="font-mono text-xs font-semibold text-slate-700">
                  {decision.decision_id ?? decision.decisionId}
                </span>
                <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                  {decision.category ?? "uncategorized"}
                </span>
              </div>
              <p className="mt-3 text-sm text-slate-700">
                recommendation <span className="font-semibold capitalize">{action(decision)}</span>
                {decision.actual_action || decision.actualAction ? (
                  <> · outcome {(decision.actual_action ?? decision.actualAction)?.replace(/_/g, " ")}</>
                ) : null}
              </p>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
