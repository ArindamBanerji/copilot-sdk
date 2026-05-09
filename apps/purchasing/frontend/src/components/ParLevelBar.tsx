import type { Item } from "../types";

function currency(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toFixed(0)}` : "$0";
}

interface ParLevelBarProps {
  item: Item;
}

export default function ParLevelBar({ item }: ParLevelBarProps) {
  const par = Number(item.parLevel ?? 0);
  const onHand = Number(item.onHandQty ?? 0);
  const ratio = par > 0 ? Math.max(0, Math.min(onHand / par, 1)) : 0;
  const value = onHand * Number(item.unitPrice ?? 0);
  const low = ratio < 0.5;

  return (
    <div className="par-level-bar">
      <div className="par-level-row">
        <span>
          {onHand.toFixed(1)} / {par.toFixed(1)} {item.unit ?? "units"}
        </span>
        <strong>{currency(value)}</strong>
      </div>
      <div className="par-level-track" aria-label="Par level">
        <span
          className={low ? "low" : ""}
          style={{ width: `${Math.max(ratio * 100, 4)}%` }}
        />
      </div>
    </div>
  );
}
