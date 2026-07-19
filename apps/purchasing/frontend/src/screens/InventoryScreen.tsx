import { useEffect, useMemo, useState } from "react";
import EvolutionPanel, { type EvolutionStatus, type EvolutionVariant } from "../../../../../copilot_sdk/frontend/EvolutionPanel";
import { getEvolutionVariants, getItems, getWasteHistory } from "../api";
import { AuditTrailViewer } from "../components/AuditTrailViewer";
import CategoryEmoji from "../components/CategoryEmoji";
import DeliveryScheduleCard from "../components/DeliveryScheduleCard";
import EventPlannerCard from "../components/EventPlannerCard";
import ItemProfile from "../components/ItemProfile";
import PredictiveParCard from "../components/PredictiveParCard";
import { RuleGenealogyTree } from "../components/RuleGenealogyTree";
import { RuleLifecyclePanel } from "../components/RuleLifecyclePanel";
import SupplierIntelligencePanel from "../components/SupplierIntelligencePanel";
import type { Item, Variant, WasteHistory } from "../types";

const categories = ["protein", "produce", "dairy", "dry_goods", "beverages"];

function parseJsonObject(value: unknown): Record<string, unknown> {
  if (typeof value !== "string") {
    return typeof value === "object" && value ? (value as Record<string, unknown>) : {};
  }
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function statusFromEvent(eventType?: string): EvolutionStatus {
  if (eventType === "promotion_approved") {
    return "promoted";
  }
  if (eventType === "promotion_rejected") {
    return "rejected";
  }
  return "shadow";
}

function toEvolutionVariant(variant: Variant): EvolutionVariant {
  const metadata = parseJsonObject(variant.metadata);
  const graph = parseJsonObject(variant.graphContext);
  return {
    id: String(variant.id ?? variant.variantId ?? variant.description ?? "variant"),
    name: String(variant.variantId ?? variant.name ?? variant.id ?? "Purchasing variant"),
    status: statusFromEvent(variant.eventType),
    description: String(variant.description ?? "System-generated improvement"),
    shadowCount: Number(metadata.total ?? graph.sampleSize ?? 0) || undefined,
    shadowWinRate: Number(graph.winRate ?? 0) || undefined,
    conservationAtPromotion: Number(variant.magnitude ?? 0) || undefined,
    rejectReason: String(metadata.rejectReason ?? ""),
    sourceCopilot: typeof variant.sourceCopilot === "string" ? variant.sourceCopilot : undefined,
    sourceRule: typeof variant.sourceRule === "string" ? variant.sourceRule : undefined,
  };
}

function avgWaste(history?: WasteHistory) {
  const values = history?.wastePct ?? [];
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((total, value) => total + Number(value || 0), 0) / values.length;
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

function matches(item: Item, variant: Variant) {
  if (!isApprovedVariant(variant)) {
    return false;
  }

  const match = variant.match;
  const variantCategories = match?.categories ?? [];
  return variantCategories.length === 0 || variantCategories.includes(String(item.category ?? ""));
}

export default function InventoryScreen() {
  const [items, setItems] = useState<Item[]>([]);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [wasteByItem, setWasteByItem] = useState<Record<string, WasteHistory>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const [nextItems, nextVariants] = await Promise.all([getItems(), getEvolutionVariants()]);
        const entries = await Promise.all(
          nextItems.map(async (item) => {
            try {
              return [item.name, await getWasteHistory(item.name)] as const;
            } catch {
              return [item.name, { item: item.name, wastePct: [] }] as const;
            }
          }),
        );
        if (mounted) {
          setItems(nextItems);
          setVariants(nextVariants);
          setWasteByItem(Object.fromEntries(entries));
        }
      } catch (caught) {
        if (mounted) {
          setError(caught instanceof Error ? caught.message : "Unable to load inventory");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  const grouped = useMemo(() => {
    const result: Record<string, Item[]> = {};
    items.forEach((item) => {
      const key = String(item.category ?? "uncategorized");
      result[key] = [...(result[key] ?? []), item];
    });
    return result;
  }, [items]);
  const evolutionVariants = useMemo(() => variants.map(toEvolutionVariant), [variants]);

  if (loading) {
    return <section data-screen-ready="false" className="purchase-card">Loading inventory...</section>;
  }

  if (error) {
    return (
      <section data-screen-ready="true" className="purchase-card error-card">
        <p className="purchase-kicker">Inventory unavailable</p>
        <p>{error}</p>
      </section>
    );
  }

  return (
    <div data-screen-ready="true" className="purchase-stack inventory-screen">
      <EvolutionPanel variants={evolutionVariants} title="System Improvements" />
      <RuleGenealogyTree />
      <RuleLifecyclePanel />
      <AuditTrailViewer />
      <SupplierIntelligencePanel />
      <PredictiveParCard />
      <EventPlannerCard />
      <DeliveryScheduleCard />

      <section className="purchase-card">
        <p className="purchase-kicker">Category summary</p>
        <h1 className="purchase-title">Waste pattern by category</h1>
        <div className="summary-table">
          <div className="summary-row header">
            <span>Category</span>
            <span>Items</span>
            <span>Avg Waste</span>
            <span>Best Item</span>
            <span>Worst Item</span>
          </div>
          {categories.map((category) => {
            const categoryItems = grouped[category] ?? [];
            const ranked = [...categoryItems].sort((a, b) => avgWaste(wasteByItem[a.name]) - avgWaste(wasteByItem[b.name]));
            const average =
              categoryItems.length > 0
                ? categoryItems.reduce((total, item) => total + avgWaste(wasteByItem[item.name]), 0) / categoryItems.length
                : 0;
            return (
              <div className="summary-row" key={category}>
                <span><CategoryEmoji category={category} /> {category.replace("_", " ")}</span>
                <span>{categoryItems.length}</span>
                <span>{average.toFixed(1)}%</span>
                <span>{ranked[0]?.displayName ?? ranked[0]?.name ?? "n/a"}</span>
                <span>{ranked[ranked.length - 1]?.displayName ?? ranked[ranked.length - 1]?.name ?? "n/a"}</span>
              </div>
            );
          })}
        </div>
      </section>

      {categories.map((category) => {
        const categoryItems = grouped[category] ?? [];
        if (categoryItems.length === 0) {
          return null;
        }
        return (
          <section className="purchase-card" key={category}>
            <div className="purchase-card-header">
              <div>
                <p className="purchase-kicker">Inventory</p>
                <h2 className="purchase-title">{category.replace("_", " ")}</h2>
              </div>
              <CategoryEmoji category={category} />
            </div>
            <div className="item-profile-list">
              {categoryItems.map((item) => (
                <ItemProfile
                  key={item.itemId ?? item.name}
                  item={item}
                  wasteHistory={wasteByItem[item.name]}
                  variants={variants.filter((variant) => matches(item, variant))}
                />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
