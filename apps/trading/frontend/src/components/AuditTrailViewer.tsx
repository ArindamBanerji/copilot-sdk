import { useEffect, useState } from "react";
import { fetchAuditTrail } from "../api";
import type { AuditTrailEntry, SelfAuditTrailResponse } from "../types";

export default function AuditTrailViewer() {
  const [data, setData] = useState<SelfAuditTrailResponse | null>(null);
  const [expanded, setExpanded] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchAuditTrail().then((payload) => {
      if (!cancelled) setData(payload);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const trails = data?.trails || [];
  return (
    <section className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase" style={{ color: "var(--copilot-primary)" }}>SC-16</p>
      <h2 className="mt-1 text-xl font-semibold">Audit Trail</h2>
      <p className="mt-1 text-sm trading-muted">Decision {"->"} factors {"->"} recommendation {"->"} outcome.</p>
      {trails.length === 0 ? <p className="mt-4 text-sm trading-muted">No audit trail available yet.</p> : null}
      <div className="mt-4 grid gap-3">
        {trails.map((entry) => <AuditEntry key={decisionId(entry)} entry={entry} expanded={expanded === decisionId(entry)} onToggle={() => setExpanded(expanded === decisionId(entry) ? "" : decisionId(entry))} />)}
      </div>
    </section>
  );
}

function AuditEntry({ entry, expanded, onToggle }: { entry: AuditTrailEntry; expanded: boolean; onToggle: () => void }) {
  return (
    <article className="rounded-md border p-3" style={{ borderColor: entry.isCorrect === false ? "var(--copilot-danger)" : "var(--copilot-border)" }}>
      <button className="font-mono text-xs" type="button" onClick={onToggle}>{decisionId(entry)}</button>
      <p className="mt-1 text-sm trading-muted">
        {humanize(entry.category || "uncategorized")} {"->"}{" "}
        {humanize(String(entry.actualAction || entry.actual_action || entry.recommendedAction || entry.recommended_action || "outcome"))}
      </p>
      {expanded ? <pre className="mt-3 max-h-36 overflow-auto rounded-md p-3 text-xs trading-muted">{JSON.stringify({ factors: entry.factors, metadata: entry.metadata, outcome: entry.outcomeMetadata }, null, 2)}</pre> : null}
    </article>
  );
}

function decisionId(entry: AuditTrailEntry) {
  return String(entry.decisionId || entry.decision_id || "unknown");
}

function humanize(value: string) {
  return value.replace(/_/g, " ");
}
