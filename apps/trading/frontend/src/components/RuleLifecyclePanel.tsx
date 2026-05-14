import { useEffect, useState } from "react";
import { getEvolutionHistory, getEvolutionVariants, getPromotedEvolutionRules } from "../api";
import type { EvolutionHistoryEvent, EvolutionVariant } from "../api";

const states = ["proposed", "shadow", "promoted", "rejected"];
type LoadState = "loading" | "ready" | "error";

export default function RuleLifecyclePanel() {
  const [status, setStatus] = useState<LoadState>("loading");
  const [variants, setVariants] = useState<EvolutionVariant[]>([]);
  const [events, setEvents] = useState<EvolutionHistoryEvent[]>([]);
  const [promoted, setPromoted] = useState<EvolutionVariant[]>([]);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getEvolutionVariants(), getEvolutionHistory(), getPromotedEvolutionRules()])
      .then(([nextVariants, history, nextPromoted]) => {
        if (!cancelled) {
          setVariants(nextVariants);
          setEvents(history.events ?? []);
          setPromoted(nextPromoted);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStatus("error");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const lifecycleItems = buildLifecycle(variants, events, promoted);

  return (
    <section className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase" style={{ color: "var(--copilot-primary)" }}>SC-15</p>
      <h2 className="mt-1 text-xl font-semibold">Rule Lifecycle</h2>
      <div className="mt-4 grid gap-3">
        {status === "loading" ? <LifecycleCard title="Loading lifecycle" status="proposed" body="Reading Trading evolution events." /> : null}
        {status === "error" ? <LifecycleCard title="No evolution data yet" status="proposed" body="Rule lifecycle is unavailable right now." /> : null}
        {status === "ready" && lifecycleItems.length === 0 ? (
          <LifecycleCard title="No evolution data yet" status="proposed" body="Promoted, shadow, and rejected rules will appear after evolution runs." />
        ) : null}
        {status === "ready"
          ? lifecycleItems.map((item) => (
              <LifecycleCard key={`${item.title}-${item.status}`} title={item.title} status={item.status} body={item.body} />
            ))
          : null}
      </div>
      <p className="mt-4 text-xs trading-muted">Lifecycle state is backed by SDK evolution endpoints.</p>
    </section>
  );
}

function buildLifecycle(
  variants: EvolutionVariant[],
  events: EvolutionHistoryEvent[],
  promoted: EvolutionVariant[],
) {
  const fromVariants = variants.map((variant) => ({
    title: String(variant.variantId || variant.id || variant.name || "Evolution variant"),
    status: normalizeStatus(variant.status || variant.eventType),
    body: String(variant.description || "Candidate rule from Trading evolution."),
  }));
  if (fromVariants.length > 0) return fromVariants;

  const fromEvents = events.map((event) => ({
    title: String(event.variantId || event.ruleName || event.eventType || "Evolution event"),
    status: normalizeStatus(event.eventType),
    body: String(event.eventType || "Lifecycle event recorded by AgentEvolver."),
  }));
  if (fromEvents.length > 0) return fromEvents;

  return promoted.map((rule) => ({
    title: String(rule.variantId || rule.id || rule.name || "Promoted rule"),
    status: "promoted",
    body: String(rule.description || "Promoted Trading rule."),
  }));
}

function normalizeStatus(value: unknown): string {
  const text = String(value || "proposed").toLowerCase();
  if (text.includes("reject")) return "rejected";
  if (text.includes("promot") || text.includes("approved")) return "promoted";
  if (text.includes("shadow")) return "shadow";
  return "proposed";
}

function LifecycleCard({ title, status, body }: { title: string; status: string; body: string }) {
  return (
    <article className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">{title}</h3>
          <p className="mt-1 text-sm trading-muted">{body}</p>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
          {status.replace(/_/g, " ")}
        </span>
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-4">
        {states.map((state) => (
          <div key={state} className="rounded-md border p-2 text-xs" style={{ borderColor: state === status ? "var(--copilot-primary)" : "var(--copilot-border)" }}>
            {state.replace(/_/g, " ")}
          </div>
        ))}
      </div>
    </article>
  );
}
