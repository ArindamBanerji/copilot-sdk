import { useState } from "react";
import AEManagedBadge from "./AEManagedBadge";
import CategoryEmoji from "./CategoryEmoji";
import WasteSparkline from "./WasteSparkline";
import type { Item, Variant, WasteHistory } from "../types";

interface ItemProfileProps {
  item: Item;
  wasteHistory?: WasteHistory;
  variants?: Variant[];
}

function avgWaste(history?: WasteHistory) {
  const values = history?.wastePct ?? [];
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((total, value) => total + Number(value || 0), 0) / values.length;
}

function trend(history?: WasteHistory) {
  const values = history?.wastePct ?? [];
  if (values.length < 2) {
    return "unknown";
  }
  const delta = Number(values[values.length - 1]) - Number(values[0]);
  if (Math.abs(delta) < 0.01) {
    return "flat";
  }
  return delta > 0 ? "up" : "down";
}

export default function ItemProfile({ item, wasteHistory, variants = [] }: ItemProfileProps) {
  const [open, setOpen] = useState(false);
  const wasteAvg = avgWaste(wasteHistory);
  const usage = Array.isArray(item.usageRange) ? item.usageRange.join("-") : String(item.usageRange ?? "n/a");

  return (
    <article className="item-profile">
      <button type="button" className="item-profile-summary" onClick={() => setOpen((value) => !value)}>
        <div>
          <CategoryEmoji category={item.category} />
          <strong>{item.displayName ?? item.name}</strong>
          <span>{item.category ?? "uncategorized"}</span>
        </div>
        <AEManagedBadge managed={variants.length > 0} count={variants.length} />
      </button>
      {open ? (
        <div className="item-profile-detail">
          <div className="stats-row">
            <div><span>Par level</span><strong>{item.parLevel ?? "n/a"} {item.unit ?? ""}</strong></div>
            <div><span>Usage range</span><strong>{usage}</strong></div>
            <div><span>Waste avg</span><strong>{wasteAvg.toFixed(1)}%</strong></div>
            <div><span>Trend</span><strong>{trend(wasteHistory)}</strong></div>
            <div><span>Supplier</span><strong>{item.supplier ?? "n/a"}</strong></div>
            <div><span>Lead time</span><strong>{item.supplierLeadTime ?? "n/a"}</strong></div>
            <div><span>Unit price</span><strong>${Number(item.unitPrice ?? 0).toFixed(2)}</strong></div>
            <div><span>Event sensitivity</span><strong>{(Number(item.eventSensitivity ?? 0) * 100).toFixed(0)}%</strong></div>
          </div>
          <WasteSparkline history={wasteHistory} unitPrice={item.unitPrice} />
          {variants.length > 0 ? (
            <div className="variant-list">
              {variants.map((variant) => (
                <span className="purchase-pill ae-pill" key={variant.id ?? variant.description}>
                  {variant.id ?? variant.description}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}
