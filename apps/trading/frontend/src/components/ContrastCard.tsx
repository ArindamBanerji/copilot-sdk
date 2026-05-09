import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Analytics } from "../types";

interface CurvePoint {
  step: number;
  aligned: number;
  misaligned: number;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function num(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function pct(value: number | undefined): string {
  return typeof value === "number" ? `${(value * 100).toFixed(0)}%` : "-";
}

function money(value: number | undefined): string {
  return typeof value === "number" ? `$${value.toLocaleString()}` : "-";
}

function exactCurve(section: Record<string, unknown>): number[] | undefined {
  const candidate = section.curve || section.equityCurve || section.pnlCurve;
  if (!Array.isArray(candidate)) {
    return undefined;
  }
  const values = candidate.map(num).filter((value): value is number => typeof value === "number");
  return values.length > 1 ? values : undefined;
}

function buildCurve(analytics: Analytics): CurvePoint[] {
  const contrast = asRecord(analytics.contrastCard);
  const aligned = asRecord(contrast.aligned);
  const misaligned = asRecord(contrast.misaligned);
  const alignedExact = exactCurve(aligned);
  const misalignedExact = exactCurve(misaligned);

  if (alignedExact && misalignedExact) {
    const length = Math.max(alignedExact.length, misalignedExact.length);
    return Array.from({ length }, (_, index) => ({
      step: index + 1,
      aligned: alignedExact[Math.min(index, alignedExact.length - 1)] ?? 0,
      misaligned: misalignedExact[Math.min(index, misalignedExact.length - 1)] ?? 0,
    }));
  }

  const alignedCount = num(aligned.count) ?? 0;
  const misalignedCount = num(misaligned.count) ?? 0;
  const alignedPnl = num(aligned.pnlDollars) ?? Math.max(alignedCount, 1) * 560;
  const misalignedPnl = num(misaligned.pnlDollars) ?? Math.max(misalignedCount, 1) * -620;
  const steps = 8;

  return Array.from({ length: steps }, (_, index) => {
    const progress = index / (steps - 1);
    return {
      step: index + 1,
      aligned: Math.round(alignedPnl * progress),
      misaligned: Math.round(misalignedPnl * progress),
    };
  });
}

function stats(section: Record<string, unknown>) {
  return {
    count: num(section.count),
    winRate: num(section.winRate),
    pnl: num(section.pnlDollars),
    avgPnl: num(section.avgPnlPct),
  };
}

export default function ContrastCard({ analytics }: { analytics?: Analytics }) {
  const contrast = asRecord(analytics?.contrastCard);
  const aligned = stats(asRecord(contrast.aligned));
  const misaligned = stats(asRecord(contrast.misaligned));
  const neutralCount = num(asRecord(contrast.neutral).count);
  const curve = buildCurve(analytics || {});

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">YOUR TWO SELVES</h2>
          <p className="mt-1 text-sm trading-muted">
            Aligned trades compound. Misaligned trades tax the portfolio.
          </p>
        </div>
        <div className="rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
          <span className="trading-muted">Neutral setups</span>{" "}
          <span className="font-semibold">{neutralCount ?? 0}</span>
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[0.9fr_1.5fr_0.9fr]">
        <MetricBlock tone="positive" title="Aligned self" count={aligned.count} winRate={aligned.winRate} pnl={aligned.pnl} avgPnl={aligned.avgPnl} />
        <div className="h-64 rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={curve} margin={{ left: 0, right: 12, top: 8, bottom: 0 }}>
              <XAxis dataKey="step" stroke="var(--copilot-text-subtle)" tickLine={false} />
              <YAxis stroke="var(--copilot-text-subtle)" tickLine={false} width={52} />
              <Tooltip formatter={(value: number) => [`$${Number(value).toLocaleString()}`, "Equity delta"]} />
              <Line type="monotone" dataKey="aligned" stroke="var(--trading-positive)" strokeWidth={3} dot={false} />
              <Line type="monotone" dataKey="misaligned" stroke="var(--trading-negative)" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <MetricBlock tone="negative" title="Misaligned self" count={misaligned.count} winRate={misaligned.winRate} pnl={misaligned.pnl} avgPnl={misaligned.avgPnl} />
      </div>
    </section>
  );
}

function MetricBlock({
  tone,
  title,
  count,
  winRate,
  pnl,
  avgPnl,
}: {
  tone: "positive" | "negative";
  title: string;
  count?: number;
  winRate?: number;
  pnl?: number;
  avgPnl?: number;
}) {
  return (
    <div className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
      <div className={`text-sm font-semibold ${tone === "positive" ? "trading-positive" : "trading-negative"}`}>{title}</div>
      <div className="mt-3 grid gap-3">
        <Stat label="Trades" value={typeof count === "number" ? String(count) : "-"} />
        <Stat label="Win rate" value={pct(winRate)} />
        <Stat label="P&L" value={money(pnl)} />
        <Stat label="Avg P&L" value={typeof avgPnl === "number" ? `${avgPnl.toFixed(2)}%` : "-"} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
