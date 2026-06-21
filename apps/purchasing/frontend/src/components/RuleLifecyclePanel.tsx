import { useEffect, useState } from "react";
import { getEvolutionHistory, getEvolutionVariants, getPromotedEvolutionRules } from "../api";
import type { EvolutionHistoryEvent } from "../api";
import type { Variant } from "../types";

const STATES = ["proposed", "shadow", "promoted", "rejected"];
type LoadState = "loading" | "ready" | "error";

export function RuleLifecyclePanel() {
  const [status, setStatus] = useState<LoadState>("loading");
  const [variants, setVariants] = useState<Variant[]>([]);
  const [events, setEvents] = useState<EvolutionHistoryEvent[]>([]);
  const [promoted, setPromoted] = useState<Variant[]>([]);

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

  const lifecycle = buildLifecycle(variants, events, promoted);

  return (
    <section className="purchase-card" data-testid="rule-lifecycle-panel">
      <p className="purchase-kicker">SC-15 Rule Lifecycle</p>
      <h3 className="purchase-title">Rule promotion states</h3>
      <div className="mt-4 grid gap-3">
        {status === "loading" ? <LifecycleCard title="Loading lifecycle" status="proposed" body="Reading purchasing evolution events." /> : null}
        {status === "error" ? <LifecycleCard title="No evolution data yet" status="proposed" body="Rule lifecycle is unavailable right now." /> : null}
        {status === "ready" && lifecycle.length === 0 ? (
          <LifecycleCard title="No evolution data yet" status="proposed" body="Promoted, shadow, and rejected rules will appear after evolution runs." />
        ) : null}
        {status === "ready"
          ? lifecycle.map((item) => <LifecycleCard key={`${item.title}-${item.status}`} title={item.title} status={item.status} body={item.body} />)
          : null}
      </div>
      <p className="purchase-muted mt-4">Based on SDK evolution data and GraphStore verification.</p>
    </section>
  );
}

function buildLifecycle(variants: Variant[], events: EvolutionHistoryEvent[], promoted: Variant[]) {
  const fromVariants = variants.map((variant) => ({
    title: String(variant.variantId || variant.id || variant.name || "Evolution variant"),
    status: normalizeStatus(variant.status || variant.eventType),
    body: String(variant.description || "Candidate rule from purchasing evolution."),
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
    body: String(rule.description || "Promoted purchasing rule."),
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
    <article className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h4 className="font-semibold text-slate-900">{title}</h4>
          <p className="mt-2 text-sm text-slate-600">{body}</p>
        </div>
        <span className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600">{status}</span>
      </div>
      <div className="mt-4 grid gap-2 md:grid-cols-4">
        {STATES.map((state) => (
          <div key={state} className={`rounded-lg border p-2 text-xs ${state === status ? "border-emerald-400 bg-emerald-50 text-emerald-700" : "border-slate-200 text-slate-600"}`}>
            {state}
          </div>
        ))}
      </div>
    </article>
  );
}
