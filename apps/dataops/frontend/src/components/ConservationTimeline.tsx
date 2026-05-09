import type { ConservationHistory } from "../types";

interface ConservationTimelineProps {
  history: ConservationHistory | null;
}

export default function ConservationTimeline({ history }: ConservationTimelineProps) {
  const events = (history?.events || []).slice(0, 3);

  return (
    <section className="copilot-card p-4">
      <div className="mb-4">
        <h2 className="dataops-section-title">Conservation Timeline</h2>
        <p className="text-sm dataops-muted">Recent guardrail decisions from calibration.</p>
      </div>
      {events.length === 0 ? (
        <div className="rounded-md p-4 text-sm" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
          No conservation events available.
        </div>
      ) : (
        <div className="grid gap-3">
          {events.map((event) => {
            const approved = event.status === "approved";
            return (
              <article key={event.eventId || event.timestamp} className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
                    {event.requestedAction || "unknown action"}
                  </span>
                  <span className="rounded px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color: approved ? "var(--copilot-success)" : "var(--copilot-danger)" }}>
                    {event.status || "unknown"}
                  </span>
                </div>
                <p className="text-sm dataops-muted">{event.reason || "No reason recorded."}</p>
                <div className="mt-2 grid gap-2 text-xs md:grid-cols-3">
                  <Metric label="Signal" value={formatDecimal(event.metrics?.signal)} />
                  <Metric label="Theta" value={formatDecimal(event.metrics?.thetaMin)} />
                  <Metric label="Headroom" value={formatDecimal(event.metrics?.headroom)} />
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="dataops-muted">{label}</span>
      <span className="font-semibold" style={{ color: "var(--copilot-text)" }}>
        {value}
      </span>
    </div>
  );
}

function formatDecimal(value?: number): string {
  return Number.isFinite(value) ? Number(value).toFixed(2) : "--";
}
