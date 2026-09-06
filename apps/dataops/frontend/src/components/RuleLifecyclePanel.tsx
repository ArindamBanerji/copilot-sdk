import { useEffect, useState } from "react";
import { getRuleLifecycle } from "../api";
import type { RuleLifecycleResponse, RuleWithLifecycle } from "../types";

const stages = ["proposed", "shadow", "promoted", "rejected"] as const;
type LoadState = "loading" | "ready" | "error";

export default function RuleLifecyclePanel() {
  const [status, setStatus] = useState<LoadState>("loading");
  const [data, setData] = useState<RuleLifecycleResponse>({ rules: [], summary: {} });

  useEffect(() => {
    let cancelled = false;
    getRuleLifecycle()
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData({ rules: [], summary: {} });
          setStatus("error");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const rules = data.rules || [];
  const summary = data.summary || {};
  const promoted = summary.promoted ?? countStatus(rules, "promoted");
  const rejected = summary.rejected ?? countStatus(rules, "rejected");
  const shadow = summary.shadow ?? countStatus(rules, "shadow");
  const active = promoted + (summary.proposed ?? countStatus(rules, "proposed"));

  return (
    <section data-testid="rule-lifecycle" className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
        SC-15
      </p>
      <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
        Rule Lifecycle
      </h2>
      <p className="mt-1 text-sm dataops-muted">Proposals move through shadow testing before promotion or rejection.</p>
      <div data-testid="rule-lifecycle-summary" className="mt-4 grid gap-2 text-sm sm:grid-cols-4">
        <Summary label="Active" value={active} />
        <Summary label="Shadow-testing" value={shadow} />
        <Summary label="Rejected" value={rejected} />
        <Summary label="Promoted" value={promoted} />
      </div>

      {status === "loading" ? <p className="mt-5 text-sm dataops-muted">Loading lifecycle data...</p> : null}
      {status === "error" ? <p className="mt-5 text-sm dataops-muted">Rule lifecycle is unavailable right now.</p> : null}
      {status === "ready" && rules.length === 0 ? <p className="mt-5 text-sm dataops-muted">No rules have entered the lifecycle yet.</p> : null}
      {rules.length > 0 ? (
        <div data-testid="rule-lifecycle-track" className="mt-5 grid gap-4">
          {rules.map((rule, index) => <LifecycleTrack key={`${rule.id || rule.variantId || rule.name || "rule"}-${index}`} rule={rule} />)}
        </div>
      ) : null}
    </section>
  );
}

function LifecycleTrack({ rule }: { rule: RuleWithLifecycle }) {
  const current = normalizeStatus(rule.status);
  const eventTypes = new Set((rule.lifecycleEvents || []).map((event) => normalizeStatus(event.type)));
  return (
    <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>{rule.name || rule.variantId || rule.id || "Evolution rule"}</div>
          <p className="mt-1 text-sm dataops-muted">{rule.description || rule.sourceRule || "No description available."}</p>
        </div>
        <span data-testid="rule-status" className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: statusColors(current).background, color: statusColors(current).color }}>
          {humanize(current)}
        </span>
      </div>
      <div data-testid="rule-lifecycle-stage-track" className="mt-5 grid grid-cols-4 gap-2">
        {stages.map((stage, index) => {
          const reached = eventTypes.has(stage) || stage === current || (current === "promoted" && index < 3) || (current === "rejected" && index < 2);
          return (
            <div key={stage} className="relative text-center text-xs">
              <div className="mx-auto h-4 w-4 rounded-full border-2" style={{ borderColor: reached ? statusColors(stage).color : "var(--copilot-border)", background: reached ? statusColors(stage).color : "transparent" }} />
              {index < stages.length - 1 ? <div className="absolute left-1/2 top-2 h-px w-full" style={{ background: reached ? "var(--copilot-primary-light)" : "var(--copilot-border)" }} /> : null}
              <div className="relative mt-2 dataops-muted">{humanize(stage)}</div>
            </div>
          );
        })}
      </div>
      {rule.winRate != null ? <p className="mt-3 text-xs dataops-muted">Shadow accuracy {Math.round(rule.winRate * 100)}% across {rule.decisionsEvaluated ?? 0} decisions.</p> : null}
      {rule.rejectedReason ? <p className="mt-2 text-xs text-red-700">Rejected: {rule.rejectedReason}</p> : null}
    </article>
  );
}

function Summary({ label, value }: { label: string; value: number }) {
  return <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}><div className="text-xs dataops-muted">{label}</div><div className="mt-1 font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</div></div>;
}

function countStatus(rules: RuleWithLifecycle[], status: string): number {
  return rules.filter((rule) => normalizeStatus(rule.status) === status).length;
}

function normalizeStatus(status: string | null | undefined): string {
  const value = String(status || "proposed").toLowerCase();
  if (value.includes("promot")) return "promoted";
  if (value.includes("reject")) return "rejected";
  if (value.includes("shadow")) return "shadow";
  return "proposed";
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}

function statusColors(status: string) {
  if (status === "promoted") return { background: "rgba(34, 197, 94, 0.12)", color: "var(--copilot-success)" };
  if (status === "rejected") return { background: "rgba(239, 68, 68, 0.12)", color: "var(--copilot-danger)" };
  if (status === "shadow") return { background: "rgba(245, 158, 11, 0.16)", color: "#b45309" };
  return { background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" };
}
