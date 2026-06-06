import { useEffect, useState } from "react";
import { getEvolutionHistory } from "../api";
import type { EvolutionHistoryItem } from "../api";

type LoadState = "loading" | "ready" | "error";

export default function RuleGenealogyTree() {
  const [status, setStatus] = useState<LoadState>("loading");
  const [events, setEvents] = useState<EvolutionHistoryItem[]>([]);

  useEffect(() => {
    let cancelled = false;
    getEvolutionHistory()
      .then((payload) => {
        if (!cancelled) {
          setEvents(Array.isArray(payload.events) ? payload.events : []);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setEvents([]);
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
        SC-13
      </p>
      <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
        Rule Genealogy
      </h2>
      <div className="mt-5 grid gap-3">
        {status === "loading" ? <LineageCard title="Loading evolution lineage" body="Reading DataOps evolution history." /> : null}
        {status === "error" ? <LineageCard title="No evolution data yet" body="Evolution lineage is unavailable right now." /> : null}
        {status === "ready" && events.length === 0 ? (
          <LineageCard title="No evolution data yet" body="DataOps rule lineage will appear after evolution events are recorded." />
        ) : null}
        {status === "ready"
          ? events.slice(0, 6).map((event, index) => (
              <LineageCard
                key={`${event.variantId || event.variant_id || event.ruleName || event.rule_name || event.eventType || event.event_type || "event"}-${index}`}
                title={eventTitle(event)}
                body={eventBody(event)}
                label={eventLabel(event, index)}
              />
            ))
          : null}
      </div>
      <p className="mt-4 text-xs dataops-muted">Based on SDK evolution history.</p>
    </section>
  );
}

function eventTitle(event: EvolutionHistoryItem): string {
  return String(event.variantId || event.variant_id || event.ruleName || event.rule_name || event.eventType || event.event_type || event.type || "Evolution event");
}

function eventBody(event: EvolutionHistoryItem): string {
  const parts = [
    event.eventType || event.event_type || event.type,
    event.outcome || event.status,
    event.category,
    event.domain,
    event.timestamp,
  ].filter(Boolean);
  return parts.length > 0 ? parts.map(String).join(" · ") : "Rule genealogy event recorded by AgentEvolver.";
}

function eventLabel(event: EvolutionHistoryItem, index: number): string {
  return String(event.eventType || event.event_type || event.type || `step ${index + 1}`).replace(/_/g, " ");
}

function LineageCard({ title, body, label }: { title: string; body: string; label?: string }) {
  return (
    <article className="grid gap-3 rounded-md border p-4 sm:grid-cols-[8rem_minmax(0,1fr)]" style={{ borderColor: "var(--copilot-border)" }}>
      <div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
          {label || "event"}
        </span>
      </div>
      <div>
        <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>{title}</div>
        <p className="mt-1 text-sm dataops-muted">{body}</p>
      </div>
    </article>
  );
}
