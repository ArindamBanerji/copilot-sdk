export type ConservationStatusLevel = "GREEN" | "AMBER" | "RED";

export interface ConservationSliderProps {
  currentThreshold: number;
  conservationProduct: number;
  conservationThreshold: number;
  penaltyRatio: number;
  status: ConservationStatusLevel;
  onDrag: (newThreshold: number) => void;
  narrative: string;
}

function clampUnit(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
}

function statusColor(status: ConservationStatusLevel): string {
  if (status === "GREEN") {
    return "var(--copilot-success)";
  }
  if (status === "AMBER") {
    return "var(--copilot-warning)";
  }
  return "var(--copilot-danger)";
}

export default function ConservationSlider({
  currentThreshold,
  conservationProduct,
  conservationThreshold,
  penaltyRatio,
  status,
  onDrag,
  narrative,
}: ConservationSliderProps) {
  const threshold = clampUnit(currentThreshold);
  const color = statusColor(status);

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
            Conservation
          </h2>
          <p className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
            {narrative}
          </p>
        </div>
        <span className="rounded-full px-3 py-1 text-sm font-semibold" style={{ background: "var(--copilot-surface-muted)", color }}>
          {status}
        </span>
      </div>

      <label className="block">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span style={{ color: "var(--copilot-text-muted)" }}>Threshold</span>
          <span className="font-semibold" style={{ color: "var(--copilot-text)" }}>
            {(threshold * 100).toFixed(0)}%
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={threshold}
          onChange={(event) => onDrag(Number(event.target.value))}
          className="w-full"
          style={{ accentColor: color }}
        />
      </label>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <Metric label="alpha times q times V" value={conservationProduct.toFixed(3)} />
        <Metric label="theta min" value={conservationThreshold.toFixed(3)} />
        <Metric label="Penalty ratio" value={`${penaltyRatio.toFixed(1)}x`} />
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs" style={{ color: "var(--copilot-text-muted)" }}>
        {label}
      </div>
      <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
        {value}
      </div>
    </div>
  );
}
