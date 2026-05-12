import { useEffect, useState } from "react";
import { fetchAuditTrail } from "../api";
import type { AuditTrailEntry, SelfAuditTrailResponse } from "../types";

export default function AuditTrailViewer() {
  const [trail, setTrail] = useState<SelfAuditTrailResponse | null>(null);
  const [expanded, setExpanded] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchAuditTrail()
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setTrail(payload);
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const entries = trail?.trails || [];

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-16
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Audit Trail
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            Decision, factors, recommendation, and outcome events from GraphStore.
          </p>
        </div>
        <span
          className="rounded-full px-2 py-1 text-xs font-semibold"
          style={{
            background: entries.length ? "rgba(34, 197, 94, 0.12)" : "var(--copilot-surface-muted)",
            color: entries.length ? "var(--copilot-success)" : "var(--copilot-text-muted)",
          }}
        >
          {entries.length ? `${entries.length} trails` : "No trails"}
        </span>
      </div>

      {loading ? <p className="mt-4 text-sm dataops-muted">Loading audit trail...</p> : null}
      {!loading && entries.length === 0 ? <p className="mt-4 text-sm dataops-muted">No audit trail available yet.</p> : null}

      {!loading && entries.length > 0 ? (
        <div className="mt-5 grid gap-3">
          {entries.map((entry) => (
            <AuditEntryCard
              key={decisionId(entry)}
              entry={entry}
              expanded={expanded === decisionId(entry)}
              onToggle={() => setExpanded(expanded === decisionId(entry) ? "" : decisionId(entry))}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

function AuditEntryCard({ entry, expanded, onToggle }: { entry: AuditTrailEntry; expanded: boolean; onToggle: () => void }) {
  const correct = entry.isCorrect;
  const border = correct === true ? "var(--copilot-success)" : correct === false ? "var(--copilot-danger)" : "var(--copilot-border)";
  return (
    <article className="rounded-md border p-4" style={{ borderColor: border }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <button type="button" className="font-mono text-sm font-semibold" style={{ color: "var(--copilot-primary)" }} onClick={onToggle}>
            {decisionId(entry)}
          </button>
          <p className="mt-1 text-sm dataops-muted">
            {humanize(entry.category || "uncategorized")} · {humanize(entry.recommendedAction || entry.actualAction || "unknown")}
          </p>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
          {correct === true ? "correct" : correct === false ? "incorrect" : "pending"}
        </span>
      </div>
      <div className="mt-3 grid gap-2 text-xs dataops-muted sm:grid-cols-4">
        <span>decision</span>
        <span>factors</span>
        <span>recommendation</span>
        <span>outcome</span>
      </div>
      {expanded ? (
        <div className="mt-3 grid gap-3">
          <pre className="mt-3 max-h-32 overflow-auto rounded-md p-3 text-xs" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
            {JSON.stringify({ factors: entry.factors, metadata: entry.metadata, outcome: entry.outcomeMetadata }, null, 2)}
          </pre>
        </div>
      ) : null}
    </article>
  );
}

function decisionId(entry: AuditTrailEntry): string {
  return String(entry.decisionId || entry.decision_id || "unknown");
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
