import {
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TickerData } from "../types";

function buildSeries(ticker?: TickerData) {
  const price = typeof ticker?.price === "number" ? ticker.price : 100;
  const change = typeof ticker?.change30dPct === "number" ? ticker.change30dPct : 0;
  const start = price / (1 + change / 100 || 1);
  return Array.from({ length: 30 }, (_item, index) => {
    const trend = start + ((price - start) * index) / 29;
    const wave = Math.sin(index * 0.85) * price * 0.006 + Math.cos(index * 0.33) * price * 0.004;
    return {
      day: index + 1,
      price: Number((trend + wave).toFixed(2)),
      ma50: Number((price * 0.985).toFixed(2)),
    };
  });
}

export default function PriceSparkline({ ticker }: { ticker?: TickerData }) {
  const data = buildSeries(ticker);
  return (
    <div className="h-36 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <XAxis dataKey="day" hide />
          <YAxis hide domain={["dataMin", "dataMax"]} />
          <Tooltip formatter={(value: number) => [`$${Number(value).toFixed(2)}`, "Price"]} />
          <ReferenceLine
            y={data[data.length - 1]?.ma50}
            stroke="var(--copilot-text-subtle)"
            strokeDasharray="4 4"
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke="var(--copilot-chart-stroke)"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
