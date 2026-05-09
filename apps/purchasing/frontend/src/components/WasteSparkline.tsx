import type { WasteHistory } from "../types";

interface WasteSparklineProps {
  history?: WasteHistory;
  unitPrice?: number;
}

export default function WasteSparkline({ history, unitPrice }: WasteSparklineProps) {
  const values = Array.isArray(history?.wastePct) ? history.wastePct.slice(-5) : [];
  const max = Math.max(...values, 1);
  const average =
    values.length > 0 ? values.reduce((total, value) => total + Number(value || 0), 0) / values.length : 0;
  const dollars = average * Number(unitPrice ?? 0);

  return (
    <div className="waste-sparkline">
      <div className="spark-bars" aria-label="Waste history">
        {values.length > 0 ? (
          values.map((value, index) => (
            <span
              key={`${value}-${index}`}
              style={{ height: `${Math.max((Number(value) / max) * 100, 8)}%` }}
            />
          ))
        ) : (
          <span className="empty" />
        )}
      </div>
      <small>
        {values.length > 0 ? `${average.toFixed(1)}% waste avg` : "No waste history"}
        {dollars > 0 ? ` | ${dollars.toFixed(0)} dollars/unit signal` : ""}
      </small>
    </div>
  );
}
