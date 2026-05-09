export interface PositionSizing {
  exposureDollars: number;
  exposurePct: number;
  rrRatio: number | null;
}

export function computePositionSizing(input: {
  shares: number;
  price: number;
  portfolioValue: number;
  stopLoss?: number;
  target?: number;
}): PositionSizing {
  const exposureDollars = Math.max(0, input.shares || 0) * Math.max(0, input.price || 0);
  const exposurePct = input.portfolioValue > 0 ? (exposureDollars / input.portfolioValue) * 100 : 0;
  const risk = input.stopLoss && input.price > input.stopLoss ? input.price - input.stopLoss : 0;
  const reward = input.target && input.target > input.price ? input.target - input.price : 0;
  return {
    exposureDollars,
    exposurePct,
    rrRatio: risk > 0 && reward > 0 ? reward / risk : null,
  };
}

export default function PositionSizer({
  shares,
  price,
  portfolioValue,
  stopLoss,
  target,
  onChange,
}: {
  shares: number;
  price: number;
  portfolioValue: number;
  stopLoss?: number;
  target?: number;
  onChange: (field: "shares" | "portfolioValue" | "stopLoss" | "target", value: number) => void;
}) {
  const sizing = computePositionSizing({ shares, price, portfolioValue, stopLoss, target });
  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Position Sizer</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <NumberField label="Shares" value={shares} onChange={(value) => onChange("shares", value)} />
        <NumberField label="Portfolio Value" value={portfolioValue} onChange={(value) => onChange("portfolioValue", value)} />
        <NumberField label="Stop Loss" value={stopLoss || 0} onChange={(value) => onChange("stopLoss", value)} />
        <NumberField label="Target" value={target || 0} onChange={(value) => onChange("target", value)} />
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <Metric label="Exposure" value={`$${sizing.exposureDollars.toLocaleString()}`} />
        <Metric label="Exposure %" value={`${sizing.exposurePct.toFixed(2)}%`} />
        <Metric label="R:R" value={sizing.rrRatio === null ? "-" : sizing.rrRatio.toFixed(2)} />
      </div>
    </section>
  );
}

function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="text-sm">
      <span className="mb-1 block trading-muted">{label}</span>
      <input
        type="number"
        className="w-full rounded-md border px-3 py-2"
        style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
        value={Number.isFinite(value) ? value : 0}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
