import { useEffect, useState } from "react";
import { getPromotedEvolutionRules } from "../api";
import type { PromotedEvolutionVariant } from "../api";

const order = ["proposed", "shadow", "promoted", "rejected"];
type LoadState = "loading" | "ready" | "error";

export default function RuleLifecyclePanel() {
  const [status, setStatus] = useState<LoadState>("loading");
  const [rules, setRules] = useState<PromotedEvolutionVariant[]>([]);

  useEffect(() => {
    let cancelled = false;
    getPromotedEvolutionRules()
      .then((payload) => {
        if (!cancelled) {
          setRules(Array.isArray(payload) ? payload : []);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRules([]);
          setStatus("error");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
        SC-15
      </p>
      <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
        Rule Lifecycle
      </h2>
      <div className="mt-5 grid gap-3">
        {status === "loading" ? <LifecycleRow rule={{ name: "Loading lifecycle", status: "created", description: "Reading promoted DataOps variants." }} /> : null}
        {status === "error" ? <LifecycleRow rule={{ name: "No promoted variants yet", status: "created", description: "Rule lifecycle is unavailable right now." }} /> : null}
        {status === "ready" && rules.length === 0 ? (
          <LifecycleRow rule={{ name: "No promoted variants yet", status: "created", description: "Promoted DataOps variants will appear after evolution runs." }} />
        ) : null}
        {status === "ready"
          ? rules.map((rule, index) => <LifecycleRow key={`${rule.variantId || rule.variant_id || rule.id || rule.name || "rule"}-${index}`} rule={rule} />)
          : null}
      </div>
      <p className="mt-4 text-xs dataops-muted">Lifecycle state is backed by SDK evolution endpoints.</p>
    </section>
  );
}

function LifecycleRow({ rule }: { rule: PromotedEvolutionVariant }) {
  const status = String(rule.status || "proposed");
  const title = String(rule.variantId || rule.variant_id || rule.ruleName || rule.rule_name || rule.name || rule.id || "Evolution variant");
  const description = String(rule.description || rule.category || rule.timestamp || rule.promotedAt || rule.promoted_at || "No description available.");
  const colors = statusColors(status);
  return (
    <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>{title}</div>
          <p className="mt-1 text-sm dataops-muted">{description}</p>
          {typeof rule.accuracy === "number" ? <p className="mt-2 text-xs dataops-muted">Accuracy {Math.round(rule.accuracy * 100)}%</p> : null}
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: colors.background, color: colors.color }}>
          {humanize(status)}
        </span>
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-4">
        {order.map((state) => (
          <div key={state} className="rounded-md border p-2 text-xs" style={{ borderColor: state === status ? "var(--copilot-primary)" : "var(--copilot-border)", color: state === status ? "var(--copilot-primary)" : "var(--copilot-text-muted)" }}>
            {humanize(state)}
          </div>
        ))}
      </div>
    </article>
  );
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}

function statusColors(status: string) {
  const normalized = status.toLowerCase();
  if (normalized.includes("promot") || normalized.includes("approved")) {
    return { background: "rgba(34, 197, 94, 0.12)", color: "var(--copilot-success)" };
  }
  if (normalized.includes("reject")) {
    return { background: "rgba(239, 68, 68, 0.12)", color: "var(--copilot-danger)" };
  }
  return { background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" };
}
