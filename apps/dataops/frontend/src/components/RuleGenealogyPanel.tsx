import { useEffect, useState } from "react";
import { getRuleLifecycle } from "../api";
import type { RuleLifecycleResponse, RuleWithLifecycle } from "../types";

export default function RuleGenealogyPanel() {
  const [data, setData] = useState<RuleLifecycleResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getRuleLifecycle()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const rules = data?.rules || [];
  return (
    <section data-testid="rule-genealogy" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-13 · OPERATIONAL EVOLUTION
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Rule Genealogy
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            How AgentEvolver proposed, tested, promoted, and rejected operational rules.
          </p>
        </div>
        <div data-testid="rule-genealogy-summary" className="rounded-md px-3 py-2" style={{ background: "var(--copilot-primary-light)" }}>
          <p className="text-xs font-semibold uppercase tracking-wide dataops-muted">Rules tracked</p>
          <p className="mt-1 text-lg font-semibold" style={{ color: "var(--copilot-primary)" }}>{data?.total ?? rules.length}</p>
        </div>
      </div>

      {loading ? <p className="mt-5 text-sm dataops-muted">Loading rule genealogy...</p> : null}
      {error ? <p className="mt-5 text-sm dataops-muted">Rule genealogy unavailable.</p> : null}
      {!loading && !error && rules.length === 0 ? <p className="mt-5 text-sm dataops-muted">No lifecycle rules recorded yet.</p> : null}

      {!loading && !error && rules.length > 0 ? (
        <div className="mt-5 grid gap-3" data-testid="rule-genealogy-list">
          {rules.map((rule, index) => <GenealogyRule key={`${rule.variantId || rule.id || rule.name || "rule"}-${index}`} rule={rule} />)}
        </div>
      ) : null}

      <div data-testid="rule-genealogy-narrative" className="mt-5 rounded-md p-3 text-sm" style={{ background: "rgba(124, 58, 237, 0.08)", color: "var(--copilot-primary)" }}>
        The system that admits failure: rejected rules remain visible as evidence of learning, not hidden exceptions.
      </div>
    </section>
  );
}

function GenealogyRule({ rule }: { rule: RuleWithLifecycle }) {
  const status = String(rule.status || "proposed").toLowerCase();
  const title = rule.variantId || rule.name || rule.id || "Evolution rule";
  const source = rule.sourceRule || rule.sourceCopilot || "AgentEvolver";
  const style = statusStyle(status);
  return (
    <article data-testid="rule-genealogy-rule" className="rounded-md border p-4" style={{ borderColor: status === "rejected" ? "var(--copilot-danger)" : "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>{title}</h3>
          <p className="mt-1 text-sm dataops-muted">{rule.description || "No rule description available."}</p>
        </div>
        <span data-testid="rule-genealogy-status" className="rounded-full px-2 py-1 text-xs font-semibold" style={style}>{humanize(status)}</span>
      </div>
      <div className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
        <Metric label="Accuracy" value={formatPercent(rule.winRate)} />
        <Metric label="Decisions" value={formatNumber(rule.decisionsEvaluated)} />
        <Metric label="Source" value={source} />
      </div>
      {status === "rejected" ? <p className="mt-3 rounded-md p-3 text-sm" style={{ background: "rgba(239, 68, 68, 0.08)", color: "var(--copilot-danger)" }}>Rejected reason: {rule.rejectedReason || "Accuracy did not meet the promotion bar."}</p> : null}
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

function formatPercent(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "n/a";
}

function formatNumber(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? String(Math.round(number)) : "n/a";
}

function humanize(value: string): string {
  return value.replace(/[_-]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusStyle(status: string) {
  if (status.includes("promot") || status.includes("approved")) {
    return { background: "rgba(22, 163, 74, 0.12)", color: "var(--copilot-success)" };
  }
  if (status.includes("reject")) {
    return { background: "rgba(220, 38, 38, 0.12)", color: "var(--copilot-danger)" };
  }
  if (status.includes("shadow")) {
    return { background: "rgba(217, 119, 6, 0.12)", color: "#b45309" };
  }
  return { background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" };
}
