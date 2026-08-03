import { useEffect, useMemo, useState } from "react";
import { fetchAuditTrail } from "../api";
import type { AuditTrailEntry } from "../types";

const eventTypes = ["score", "learn", "rule_promoted", "rule_rejected", "conservation_event", "configuration_change"];

type AuditEvent = {
  id: string;
  timestamp?: number | string;
  type: string;
  description: string;
  actor: string;
};

export default function AuditTrailPanel() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [eventType, setEventType] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchAuditTrail()
      .then((payload) => {
        if (!cancelled) {
          setEvents((payload?.trails || []).map(toAuditEvent).sort((left, right) => timestampValue(right.timestamp) - timestampValue(left.timestamp)).slice(0, 100));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const visibleEvents = useMemo(() => {
    const query = search.trim().toLowerCase();
    return events.filter((event) => (!eventType || event.type === eventType) && (!query || `${event.type} ${event.description} ${event.actor}`.toLowerCase().includes(query)));
  }, [eventType, events, search]);
  const recentCount = events.filter((event) => Date.now() - timestampValue(event.timestamp) < 24 * 60 * 60 * 1000).length;

  return (
    <section data-testid="audit-trail" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>SC-16</p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>Audit Trail</h2>
          <p className="mt-1 text-sm dataops-muted">Chronological record of scores, learning, rule changes, and conservation events.</p>
        </div>
        <span data-testid="audit-recent-summary" className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>{recentCount} events in last 24h</span>
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-[14rem_1fr]">
        <label className="grid gap-1 text-xs font-semibold dataops-muted">
          Event type
          <select data-testid="audit-event-filter" className="rounded-md border px-2 py-2 text-sm" style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)", color: "var(--copilot-text)" }} value={eventType} onChange={(event) => setEventType(event.target.value)}>
            <option value="">All events</option>
            {eventTypes.map((type) => <option key={type} value={type}>{humanize(type)}</option>)}
          </select>
        </label>
        <label className="grid gap-1 text-xs font-semibold dataops-muted">
          Search
          <input data-testid="audit-search" className="rounded-md border px-2 py-2 text-sm" style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)", color: "var(--copilot-text)" }} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search audit events" />
        </label>
      </div>
      {loading ? <p className="mt-4 text-sm dataops-muted">Loading audit events...</p> : null}
      {!loading && visibleEvents.length === 0 ? <p className="mt-4 text-sm dataops-muted">No audit events match these filters.</p> : null}
      {visibleEvents.length > 0 ? (
        <div data-testid="audit-events" className="mt-5 grid gap-2">
          {visibleEvents.map((event) => (
            <article data-testid="audit-event" key={event.id} className="grid gap-2 rounded-md border p-3 sm:grid-cols-[10rem_9rem_1fr_8rem] sm:items-center" style={{ borderColor: "var(--copilot-border)" }}>
              <time data-testid="audit-event-timestamp" className="text-xs dataops-muted">{formatTimestamp(event.timestamp)}</time>
              <span data-testid="audit-event-type" className="w-fit rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>{humanize(event.type)}</span>
              <span className="text-sm" style={{ color: "var(--copilot-text)" }}>{event.description}</span>
              <span className="text-xs dataops-muted">{event.actor}</span>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function toAuditEvent(entry: AuditTrailEntry, index: number): AuditEvent {
  const raw = entry as unknown as Record<string, unknown>;
  const metadata = typeof raw.metadata === "object" && raw.metadata !== null ? raw.metadata as Record<string, unknown> : {};
  const type = String(metadata.eventType || metadata.event_type || raw.eventType || raw.event_type || (entry.isCorrect === undefined ? "score" : "learn"));
  const id = String(entry.decisionId || entry.decision_id || raw.id || `audit-${index}`);
  return {
    id,
    timestamp: entry.createdAt ?? entry.created_at ?? entry.verifiedAt ?? entry.verified_at,
    type,
    description: String(metadata.description || raw.description || `${entry.category || "Decision"} ${entry.recommendedAction || entry.recommended_action || "action"}`),
    actor: String(metadata.actor || raw.source || "GraphStore"),
  };
}

function timestampValue(value: number | string | undefined): number {
  if (typeof value === "number") return value < 100000000000 ? value * 1000 : value;
  const parsed = value ? Date.parse(value) : 0;
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatTimestamp(value: number | string | undefined): string {
  const timestamp = timestampValue(value);
  return timestamp ? new Date(timestamp).toLocaleString() : "n/a";
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}
