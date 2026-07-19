import { useEffect, useState } from "react";
import { fetchAuditTrail } from "../api";
import type { AuditTrailEntry, SelfAuditTrailResponse } from "../types";

export default function AuditTrail() {
  const [expanded, setExpanded] = useState("");
  const [data, setData] = useState<SelfAuditTrailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchAuditTrail(undefined, 20)
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((loadError) => {
        console.debug("audit trail unavailable", loadError);
        if (!cancelled) setError("Audit trail unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <section className="copilot-card p-4 text-sm trading-muted">Audit trail unavailable.</section>;
  }

  const trails = Array.isArray(data?.trails) ? data.trails : [];
  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-16
          </p>
          <h2 className="mt-1 text-xl font-semibold">Audit Trail</h2>
          <p className="mt-1 text-sm trading-muted">Decision, factors, recommendation, and outcome evidence from GraphStore.</p>
        </div>
        <span
          className="rounded-full px-2 py-1 text-xs font-semibold"
          style={{ background: trails.length ? "rgba(21, 128, 61, 0.12)" : "var(--copilot-surface-muted)", color: trails.length ? "var(--trading-positive)" : "var(--copilot-text-muted)" }}
        >
          {trails.length ? `${trails.length} trails` : "No trails"}
        </span>
      </div>

      {loading ? <p className="mt-4 text-sm trading-muted">Loading audit trail...</p> : null}
      {!loading && trails.length === 0 ? <p className="mt-4 text-sm trading-muted">No audit trail yet. Confirm trades to build an evidence chain.</p> : null}
      {!loading && trails.length > 0 ? (
        <div className="mt-5 grid gap-3">
          {trails.map((entry, index) => {
            const id = decisionId(entry, index);
            return <AuditEntry key={id} entry={entry} expanded={expanded === id} onToggle={() => setExpanded(expanded === id ? "" : id)} />;
          })}
        </div>
      ) : null}
    </section>
  );
}

function AuditEntry({ entry, expanded, onToggle }: { entry: AuditTrailEntry; expanded: boolean; onToggle: () => void }) {
  const correct = entry.isCorrect;
  return (
    <article className="rounded-md border p-4" style={{ borderColor: correct === false ? "var(--copilot-danger)" : "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <button className="font-mono text-xs font-semibold" style={{ color: "var(--copilot-primary)" }} type="button" onClick={onToggle}>
            {decisionId(entry)}
          </button>
          <p className="mt-1 text-sm trading-muted">
            {humanize(entry.category || "uncategorized")} · {humanize(actionName(entry))}
          </p>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
          {correct === true ? "correct" : correct === false ? "incorrect" : "pending"}
        </span>
      </div>
      <div className="mt-3 grid gap-2 text-xs trading-muted sm:grid-cols-4">
        <span>decision</span>
        <span>factors</span>
        <span>recommendation</span>
        <span>outcome</span>
      </div>
      {expanded ? (
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          <Fact label="Confidence" value={formatPercent(entry.confidence)} />
          <Fact label="Actual" value={humanize(String(entry.actualAction || entry.actual_action || "pending"))} />
          <Fact label="Verified" value={formatTimestamp(entry.verifiedAt)} />
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

function decisionId(entry: AuditTrailEntry, fallbackIndex = 0): string {
  return String(entry.decisionId || entry.decision_id || `trail-${fallbackIndex}`);
}

function actionName(entry: AuditTrailEntry): string {
  return String(entry.actualAction || entry.actual_action || entry.recommendedAction || entry.recommended_action || entry.action || "outcome");
}

function formatPercent(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "n/a";
}

function formatTimestamp(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) return new Date(value * 1000).toLocaleString();
  return value ? String(value) : "n/a";
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}
