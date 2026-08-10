import { useEffect, useState } from "react";
import { getEvolutionHistory, getEvolutionVariants } from "../api";
import type { EvolutionHistoryEvent } from "../api";
import type { Variant } from "../types";

type LoadState = "loading" | "ready" | "error";

export function RuleGenealogyTree() {
  const [status, setStatus] = useState<LoadState>("loading");
  const [variants, setVariants] = useState<Variant[]>([]);
  const [events, setEvents] = useState<EvolutionHistoryEvent[]>([]);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getEvolutionVariants(), getEvolutionHistory()])
      .then(([nextVariants, history]) => {
        if (!cancelled) {
          setVariants(nextVariants);
          setEvents(history.events ?? []);
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

  const lineage = buildLineage(variants, events);

  return (
    <section className="purchase-card" data-testid="rule-genealogy-panel" data-panel-ready={String(status !== "loading")}>
      <p className="purchase-kicker">SC-13 Rule Genealogy</p>
      <h3 className="purchase-title">Purchasing rule lineage</h3>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {status === "loading" ? <LineageCard title="Loading evolution lineage" body="Reading purchasing evolution history." /> : null}
        {status === "error" ? <LineageCard title="No evolution data yet" body="Evolution lineage is unavailable right now." /> : null}
        {status === "ready" && lineage.length === 0 ? (
          <LineageCard title="No evolution data yet" body="Purchasing rule lineage will appear after evolution events are recorded." />
        ) : null}
        {status === "ready"
          ? lineage.map((item, index) => <LineageCard key={`${item.title}-${index}`} title={item.title} body={item.body} label={`step ${index + 1}`} />)
          : null}
      </div>
      <p className="purchase-muted mt-4">Based on SDK evolution history and GraphStore self-computation data.</p>
    </section>
  );
}

function buildLineage(variants: Variant[], events: EvolutionHistoryEvent[]) {
  const fromVariants = variants.slice(0, 3).map((variant) => ({
    title: String(variant.variantId || variant.id || variant.name || "Evolution variant"),
    body: String(variant.description || variant.sourceRule || "Procurement rule linked to purchasing evolution history."),
  }));
  if (fromVariants.length > 0) return fromVariants;

  return events.slice(0, 3).map((event) => ({
    title: String(event.variantId || event.ruleName || event.eventType || "Evolution event"),
    body: String(event.eventType || "Rule genealogy event recorded by AgentEvolver."),
  }));
}

function LineageCard({ title, body, label }: { title: string; body: string; label?: string }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      {label ? <span className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600">{label}</span> : null}
      <h4 className="mt-2 font-semibold text-slate-900">{title}</h4>
      <p className="mt-1 text-sm text-slate-600">{body}</p>
    </article>
  );
}
