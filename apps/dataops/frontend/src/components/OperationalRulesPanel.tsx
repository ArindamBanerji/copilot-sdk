import { useEffect, useState } from "react";
import { getOperationalRules } from "../api";
import type { OperationalRule, OperationalRulesResponse } from "../types";

const STATUS_STYLES: Record<string, { background: string; color: string }> = {
  promoted: { background: "rgba(34, 197, 94, 0.12)", color: "var(--copilot-success)" },
  rejected: { background: "rgba(239, 68, 68, 0.12)", color: "var(--copilot-danger)" },
  shadow: { background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" },
  proposed: { background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" },
};

export default function OperationalRulesPanel() {
  const [data, setData] = useState<OperationalRulesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getOperationalRules()
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load operational rules.");
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
  }, []);

  const rules = data?.rules || [];

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            OE-4
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Operational Rules
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            {loading ? "Loading operational AgentEvolver rules..." : `${data?.total ?? 0} rules generated from operational patterns`}
          </p>
        </div>
        <Summary summary={data?.summary} />
      </div>

      {error ? <p className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p> : null}
      {!loading && !error && rules.length === 0 ? <p className="mt-4 text-sm dataops-muted">No operational rules available.</p> : null}

      {!error && rules.length > 0 ? (
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {rules.map((rule, index) => (
            <RuleCard key={ruleCardKey(rule, index)} rule={rule} />
          ))}
        </div>
      ) : null}
    </section>
  );
}

function ruleCardKey(rule: OperationalRule, index: number): string {
  return `${rule.id || "rule"}-${rule.name || "unnamed"}-${rule.status || "proposed"}-${rule.recommendation || "none"}-${index}`;
}

function Summary({ summary }: { summary?: OperationalRulesResponse["summary"] }) {
  const statuses = ["proposed", "shadow", "promoted", "rejected"];
  return (
    <div className="flex flex-wrap gap-2">
      {statuses.map((status) => {
        const style = STATUS_STYLES[status] || STATUS_STYLES.proposed;
        return (
          <span key={status} className="rounded-full px-2 py-1 text-xs font-semibold" style={style}>
            {summary?.[status] ?? 0} {humanize(status)}
          </span>
        );
      })}
    </div>
  );
}

function RuleCard({ rule }: { rule: OperationalRule }) {
  const status = rule.status || "proposed";
  const style = STATUS_STYLES[status] || STATUS_STYLES.proposed;
  return (
    <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>{rule.id || rule.name || "Operational rule"}</h3>
          <p className="mt-1 text-sm dataops-muted">{rule.name || rule.description || "Rule template"}</p>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={style}>
          {humanize(status)}
        </span>
      </div>
      <div className="mt-3 grid gap-2 text-sm">
        <Fact label="Type" value={humanize(rule.type || rule.category || "rule")} />
        <Fact label="System" value={humanize(rule.system || "dataops")} />
        <Fact label="Impact" value={rule.estimatedImpact || rule.expectedImpact || "Impact pending"} />
      </div>
      <p className="mt-3 text-sm dataops-muted">{rule.recommendation || rule.description || "No recommendation detail available."}</p>
    </article>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <span className="text-xs dataops-muted">{label}</span>
      <span className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</span>
    </div>
  );
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
