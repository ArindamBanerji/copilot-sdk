import { useEffect, useState } from "react";
import { getRuleLifecycle } from "../api";
import type { RuleLifecycleResponse, RuleWithLifecycle } from "../types";

const order = ["proposed", "shadow", "promoted", "rejected"];

export default function RuleLifecyclePanel() {
  const [data, setData] = useState<RuleLifecycleResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    getRuleLifecycle()
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const rules = data?.rules || [];
  if (rules.length === 0) {
    return <section className="copilot-card p-4 text-sm dataops-muted">No lifecycle rules available.</section>;
  }

  return (
    <section className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
        SC-15
      </p>
      <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
        Rule Lifecycle
      </h2>
      <div className="mt-5 grid gap-3">
        {rules.map((rule) => <LifecycleRow key={rule.variantId || rule.id || rule.name || "rule"} rule={rule} />)}
      </div>
      <p className="mt-4 text-xs dataops-muted">Based on seeded evolution data.</p>
    </section>
  );
}

function LifecycleRow({ rule }: { rule: RuleWithLifecycle }) {
  const status = String(rule.status || "proposed");
  return (
    <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>{rule.variantId || rule.name || rule.id || "rule"}</div>
          <p className="mt-1 text-sm dataops-muted">{rule.description || "No description available."}</p>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: status === "rejected" ? "rgba(239, 68, 68, 0.12)" : "var(--copilot-primary-light)", color: status === "rejected" ? "var(--copilot-danger)" : "var(--copilot-primary)" }}>
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
