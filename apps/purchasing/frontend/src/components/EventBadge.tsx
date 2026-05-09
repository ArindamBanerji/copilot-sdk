interface EventBadgeProps {
  events?: Array<Record<string, unknown>>;
}

function eventLabel(event: Record<string, unknown>) {
  return String(event.name ?? event.event ?? event.type ?? "Event");
}

export default function EventBadge({ events }: EventBadgeProps) {
  const safeEvents = events ?? [];

  return (
    <section className="purchase-card dashboard-header-card">
      <p className="purchase-kicker">Events</p>
      <h2 className="purchase-title">{safeEvents.length > 0 ? "Demand pressure" : "No event pressure"}</h2>
      <div className="event-chip-row">
        {safeEvents.length > 0 ? (
          safeEvents.map((event, index) => (
            <span className="purchase-pill" key={`${eventLabel(event)}-${index}`}>
              {eventLabel(event)}
            </span>
          ))
        ) : (
          <span className="purchase-pill">Normal cover</span>
        )}
      </div>
    </section>
  );
}
