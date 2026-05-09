import type { Incident } from "../types";

interface IncidentReplayCardProps {
  incident: Incident | null;
}

export default function IncidentReplayCard({ incident }: IncidentReplayCardProps) {
  if (!incident) {
    return (
      <section className="copilot-card p-5 text-sm dataops-muted">
        No incident replay available.
      </section>
    );
  }

  const date = incident.incidentId?.match(/\d{4}-\d{2}-\d{2}/)?.[0] || "unknown date";

  return (
    <section className="copilot-card p-5">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="dataops-section-title">Incident Replay</h2>
          <p className="mt-1 text-sm dataops-muted">{incident.title || "Untitled incident"}</p>
        </div>
        <span className="rounded-full px-3 py-1 text-sm font-semibold" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-danger)" }}>
          {formatMoney(incident.estimatedCost)}
        </span>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <Metric label="Date" value={date} />
        <Metric label="Primary alert" value={incident.primaryAlertId || "unknown"} />
        <Metric label="Systems" value={(incident.affectedSystems || []).join(", ") || "unknown"} />
      </div>

      <div className="mt-4 rounded-md p-4" style={{ background: "var(--copilot-surface-muted)" }}>
        <div className="grid gap-3 md:grid-cols-2">
          <Metric label="Source reliability" value={formatPercent(incident.fingerprintInsight?.sourceReliability)} />
          <Metric label="Recurrence frequency" value={formatPercent(incident.fingerprintInsight?.recurrenceFrequency)} />
        </div>
        <p className="mt-3 text-sm dataops-muted">
          {incident.fingerprintInsight?.summary || "No fingerprint insight recorded."}
        </p>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <Callout
          title="System recommendation"
          body="Escalate freshness breaches when business criticality and downstream urgency combine with unreliable source signals."
        />
        <Callout
          title="Lesson"
          body="A narrow dataset issue can still become expensive when it feeds executive dashboards and downstream marts."
        />
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs dataops-muted">{label}</div>
      <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</div>
    </div>
  );
}

function Callout({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{title}</div>
      <p className="mt-1 text-sm dataops-muted">{body}</p>
    </div>
  );
}

function formatMoney(value?: number): string {
  return Number.isFinite(value) ? `$${Number(value).toLocaleString()}` : "Cost n/a";
}

function formatPercent(value?: number): string {
  return Number.isFinite(value) ? `${Math.round(Number(value) * 100)}%` : "n/a";
}
