interface SLACountdownProps {
  slaMinutes?: number | null;
  alertTimestamp?: string | null;
  systemName?: string;
}

export default function SLACountdown({ slaMinutes, alertTimestamp, systemName }: SLACountdownProps) {
  const parsedSla = Number(slaMinutes);
  const parsedTimestamp = alertTimestamp ? Date.parse(alertTimestamp) : Number.NaN;

  if (!Number.isFinite(parsedSla) || parsedSla <= 0 || !Number.isFinite(parsedTimestamp)) {
    return (
      <section className="copilot-card p-4">
        <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>SLA unavailable</div>
        <p className="mt-1 text-sm dataops-muted">
          {systemName || "This system"} has no reliable alert timestamp for countdown tracking.
        </p>
      </section>
    );
  }

  const elapsedMinutes = Math.max(0, Math.floor((Date.now() - parsedTimestamp) / 60000));
  const remaining = Math.ceil(parsedSla - elapsedMinutes);
  const remainingRatio = remaining / parsedSla;
  const breached = remaining <= 0;
  const tone = breached || remainingRatio < 0.2
    ? "var(--copilot-danger)"
    : remainingRatio <= 0.5
      ? "var(--copilot-warning)"
      : "var(--copilot-success)";

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-wide dataops-muted">SLA Countdown</div>
          <div className="mt-1 text-lg font-semibold" style={{ color: tone }}>
            {breached
              ? `SLA BREACHED: ${Math.abs(remaining)} minutes ago`
              : `SLA: ${remaining} minutes remaining`}
          </div>
        </div>
        <div className="text-right text-sm dataops-muted">
          <div>{systemName || "unknown system"}</div>
          <div>{parsedSla} minute SLA</div>
        </div>
      </div>
    </section>
  );
}
