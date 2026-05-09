export type EvolutionStatus = "promoted" | "rejected" | "shadow" | "created";

export interface EvolutionVariant {
  id: string;
  name: string;
  status: EvolutionStatus;
  description: string;
  shadowCount?: number;
  shadowWinRate?: number;
  conservationAtPromotion?: number;
  rejectReason?: string;
  sourceCopilot?: string;
  sourceRule?: string;
}

export interface EvolutionPanelProps {
  variants: EvolutionVariant[];
  title?: string;
}

function statusColor(status: EvolutionStatus): string {
  if (status === "promoted") {
    return "var(--copilot-success)";
  }
  if (status === "rejected") {
    return "var(--copilot-danger)";
  }
  if (status === "shadow") {
    return "var(--copilot-warning)";
  }
  return "var(--copilot-info)";
}

function statusIcon(status: EvolutionStatus): string {
  if (status === "promoted") {
    return "UP";
  }
  if (status === "rejected") {
    return "NO";
  }
  if (status === "shadow") {
    return "SH";
  }
  return "NEW";
}

function clampUnit(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
}

export default function EvolutionPanel({ variants, title = "Evolution" }: EvolutionPanelProps) {
  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
          {title}
        </h2>
        <span className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
          {variants.length} variants
        </span>
      </div>

      {variants.length === 0 ? (
        <div className="rounded-md p-4 text-sm" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
          No evolution variants available.
        </div>
      ) : (
        <div className="grid gap-3">
          {variants.map((variant) => {
            const color = statusColor(variant.status);
            const winRate = clampUnit(variant.shadowWinRate ?? 0);
            return (
              <article key={variant.id} className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className="rounded px-2 py-1 text-xs font-semibold"
                        style={{ background: "var(--copilot-surface-muted)", color }}
                      >
                        {statusIcon(variant.status)}
                      </span>
                      <h3 className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
                        {variant.name}
                      </h3>
                    </div>
                    <p className="mt-2 text-sm" style={{ color: "var(--copilot-text-muted)" }}>
                      {variant.description}
                    </p>
                  </div>
                  {(variant.sourceCopilot || variant.sourceRule) ? (
                    <span
                      className="shrink-0 rounded-full px-2 py-1 text-xs font-semibold"
                      style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}
                    >
                      {variant.sourceCopilot || variant.sourceRule}
                    </span>
                  ) : null}
                </div>

                <div className="mt-3 grid gap-3 md:grid-cols-3">
                  {typeof variant.shadowCount === "number" ? (
                    <Metric label="Shadow count" value={variant.shadowCount.toString()} />
                  ) : null}
                  {typeof variant.shadowWinRate === "number" ? (
                    <div>
                      <Metric label="Shadow win rate" value={`${(winRate * 100).toFixed(0)}%`} />
                      <div className="mt-1 h-2 rounded-full" style={{ background: "var(--copilot-surface-muted)" }}>
                        <div className="h-full rounded-full" style={{ width: `${winRate * 100}%`, background: color }} />
                      </div>
                    </div>
                  ) : null}
                  {typeof variant.conservationAtPromotion === "number" ? (
                    <Metric label="Conservation" value={variant.conservationAtPromotion.toFixed(3)} />
                  ) : null}
                </div>

                {variant.rejectReason ? (
                  <div className="mt-3 rounded-md p-2 text-sm" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-danger)" }}>
                    {variant.rejectReason}
                  </div>
                ) : null}
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
    <div>
      <div className="text-xs" style={{ color: "var(--copilot-text-muted)" }}>
        {label}
      </div>
      <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
        {value}
      </div>
    </div>
  );
}
