import type { Analytics } from "../types";

interface EventImpactCardProps {
  analytics?: Analytics;
}

function pct(value?: number) {
  return Number.isFinite(value) ? `${(Number(value) * 100).toFixed(0)}%` : "n/a";
}

export default function EventImpactCard({ analytics }: EventImpactCardProps) {
  const event = analytics?.eventImpact?.event;
  const nonEvent = analytics?.eventImpact?.nonEvent;
  const eventAccuracy = Number(event?.accuracy ?? 0);
  const nonEventAccuracy = Number(nonEvent?.accuracy ?? 0);

  return (
    <section className="purchase-card">
      <p className="purchase-kicker">Event impact</p>
      <h2 className="purchase-title">Events create under-ordering risk</h2>
      <div className="stats-row">
        <div><span>Event accuracy</span><strong>{pct(event?.accuracy)}</strong></div>
        <div><span>Event orders</span><strong>{event?.count ?? 0}</strong></div>
        <div><span>Non-event accuracy</span><strong>{pct(nonEvent?.accuracy)}</strong></div>
        <div><span>Non-event orders</span><strong>{nonEvent?.count ?? 0}</strong></div>
      </div>
      <p className="purchase-muted">
        {eventAccuracy < nonEventAccuracy
          ? "Event-day orders need a stronger guardrail before service."
          : "Event-day ordering is not currently worse than non-event ordering."}
      </p>
    </section>
  );
}
