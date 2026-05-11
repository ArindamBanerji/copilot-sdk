import { useEffect, useState } from "react";
import { getRuleLifecycle } from "../api";
import type { LifecycleEvent, RuleLifecycleResponse, RuleWithLifecycle } from "../types";

export default function RuleLifecycle() {
  const [data, setData] = useState<RuleLifecycleResponse | null>(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    getRuleLifecycle({ status: status || undefined })
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load rule lifecycle.");
          setData(null);
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
  }, [status]);

  const summary = data?.summary || {};
  const rules = data?.rules || [];

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-15
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Rule Lifecycle
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            {loading ? "Loading lifecycle evidence..." : `${data?.total ?? 0} rules · ${summary.promoted ?? 0} promoted · ${summary.rejected ?? 0} rejected`}
          </p>
        </div>
        <label className="grid gap-1 text-xs font-semibold dataops-muted">
          Status
          <select
            className="rounded-md border px-2 py-2 text-sm"
            style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)", color: "var(--copilot-text)" }}
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All</option>
            <option value="promoted">Promoted</option>
            <option value="rejected">Rejected</option>
            <option value="shadow">Shadow</option>
            <option value="proposed">Proposed</option>
          </select>
        </label>
      </div>

      {error ? <p className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p> : null}
      {!loading && !error && rules.length === 0 ? <p className="mt-4 text-sm dataops-muted">No lifecycle rules match this filter.</p> : null}

      {!error && rules.length > 0 ? (
        <div className="mt-5 grid gap-3">
          {rules.map((rule) => (
            <RuleCard key={rule.variantId || rule.id || rule.name || "rule"} rule={rule} />
          ))}
        </div>
      ) : null}
    </section>
  );
}

function RuleCard({ rule }: { rule: RuleWithLifecycle }) {
  const status = rule.status || "proposed";
  const rejected = status === "rejected";
  return (
    <article className="rounded-md border p-4" style={{ borderColor: rejected ? "var(--copilot-danger)" : "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
            {rule.variantId || rule.name || rule.id || "Lifecycle rule"}
          </h3>
          <p className="mt-1 text-sm dataops-muted">{rule.description || "No rule description available."}</p>
        </div>
        <span
          className="rounded-full px-2 py-1 text-xs font-semibold"
          style={{
            background: rejected ? "rgba(239, 68, 68, 0.12)" : "var(--copilot-primary-light)",
            color: rejected ? "var(--copilot-danger)" : "var(--copilot-primary)",
          }}
        >
          {humanize(status)}
        </span>
      </div>

      <div className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
        <Metric label="Win rate" value={formatPercent(rule.winRate)} />
        <Metric label="Decisions evaluated" value={formatNumber(rule.decisionsEvaluated)} />
        <Metric label="Source" value={rule.sourceRule || rule.sourceCopilot || "local"} />
      </div>

      {rule.rejectedReason ? (
        <p className="mt-3 rounded-md p-3 text-sm" style={{ background: "rgba(239, 68, 68, 0.08)", color: "var(--copilot-danger)" }}>
          Rejected reason: {rule.rejectedReason}
        </p>
      ) : null}

      <div className="mt-4">
        <h4 className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>Lifecycle Events</h4>
        <div className="mt-3 grid gap-2">
          {(rule.lifecycleEvents || []).length ? (
            rule.lifecycleEvents?.map((event, index) => <EventRow key={`${event.type || "event"}-${index}`} event={event} />)
          ) : (
            <p className="text-sm dataops-muted">No lifecycle events available.</p>
          )}
        </div>
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs dataops-muted">{label}</div>
      <div className="mt-1 font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</div>
    </div>
  );
}

function EventRow({ event }: { event: LifecycleEvent }) {
  const type = event.type || "event";
  const terminalRejected = type === "rejected";
  return (
    <div className="grid gap-1 rounded-md border p-3 sm:grid-cols-[10rem_minmax(0,1fr)]" style={{ borderColor: terminalRejected ? "var(--copilot-danger)" : "var(--copilot-border)" }}>
      <div>
        <div className="text-sm font-semibold" style={{ color: terminalRejected ? "var(--copilot-danger)" : "var(--copilot-primary)" }}>
          {humanize(type)}
        </div>
        <div className="text-xs dataops-muted">{event.date || "date unavailable"}</div>
      </div>
      <p className="text-sm dataops-muted">{event.detail || "No detail available."}</p>
    </div>
  );
}

function formatPercent(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "n/a";
}

function formatNumber(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? String(Math.round(number)) : "n/a";
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
