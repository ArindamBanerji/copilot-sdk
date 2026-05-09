import AEManagedBadge from "./AEManagedBadge";
import CategoryEmoji from "./CategoryEmoji";
import ParLevelBar from "./ParLevelBar";
import WasteSparkline from "./WasteSparkline";
import type { Item, Variant, WasteHistory } from "../types";

interface ParLevelMonitorProps {
  items: Item[];
  wasteByItem: Record<string, WasteHistory>;
  variants: Variant[];
  onSelectItem: (item: Item) => void;
}

function itemRatio(item: Item) {
  const par = Number(item.parLevel ?? 0);
  return par > 0 ? Number(item.onHandQty ?? 0) / par : 1;
}

function isApprovedVariant(variant: Variant) {
  const eventType = String(variant.eventType ?? variant.event_type ?? "");
  const status = String(variant.status ?? "");
  const rejected = eventType === "promotion_rejected" || status === "rejected";
  if (rejected) {
    return false;
  }
  return (
    eventType === "promotion_approved" ||
    status === "promoted" ||
    status === "approved"
  );
}

function variantMatches(item: Item, variant: Variant) {
  if (!isApprovedVariant(variant)) {
    return false;
  }

  const match = variant.match;
  if (!match) {
    return false;
  }

  const categories = match.categories ?? [];
  return categories.length === 0 || categories.includes(String(item.category ?? ""));
}

export default function ParLevelMonitor({ items, wasteByItem, variants, onSelectItem }: ParLevelMonitorProps) {
  const sorted = [...items].sort((left, right) => {
    const leftAe = variants.some((variant) => variantMatches(left, variant));
    const rightAe = variants.some((variant) => variantMatches(right, variant));
    if (leftAe !== rightAe) {
      return leftAe ? -1 : 1;
    }
    return itemRatio(left) - itemRatio(right);
  });

  return (
    <section className="purchase-card par-monitor">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Par level monitor</p>
          <h2 className="purchase-title">Real inventory, ranked by reorder pressure</h2>
        </div>
        <span className="purchase-pill">{sorted.length} below half par</span>
      </div>
      {sorted.length === 0 ? (
        <p className="purchase-muted">No item is below the reorder threshold.</p>
      ) : (
        <div className="par-monitor-list">
          {sorted.map((item) => {
            const matchingVariants = variants.filter((variant) => variantMatches(item, variant));
            return (
              <article className="par-item" key={item.itemId ?? item.name}>
                <div className="par-item-main">
                  <CategoryEmoji category={item.category} />
                  <div>
                    <h3>{item.displayName ?? item.name}</h3>
                    <p className="purchase-muted">
                      {item.supplier ?? "Supplier unknown"} | lead time {item.supplierLeadTime ?? "n/a"} days
                    </p>
                  </div>
                </div>
                <ParLevelBar item={item} />
                <WasteSparkline history={wasteByItem[item.name]} unitPrice={item.unitPrice} />
                <AEManagedBadge managed={matchingVariants.length > 0} count={matchingVariants.length} />
                <button className="purchase-button secondary" type="button" onClick={() => onSelectItem(item)}>
                  Order
                </button>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
