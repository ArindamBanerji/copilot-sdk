import { useEffect, useMemo, useState } from "react";
import { DecisionHistory, TransferBadge } from "../../../../../copilot_sdk/frontend";
import {
  BASE,
  getAnalytics,
  getEvolutionVariants,
  getHistory,
  getItems,
  getOrderMetadata,
  getTodaySummary,
  getWasteHistory,
} from "../api";
import { AccuracyAlertPanel } from "../components/AccuracyAlertPanel";
import AEStatusBar from "../components/AEStatusBar";
import AutoOrderPanel from "../components/AutoOrderPanel";
import CommodityPricePanel from "../components/CommodityPricePanel";
import EventBadge from "../components/EventBadge";
import IgnoringCostCard from "../components/IgnoringCostCard";
import OrderCard from "../components/OrderCard";
import ParLevelPanel from "../components/ParLevelPanel";
import ParLevelMonitor from "../components/ParLevelMonitor";
import SpendSummaryPanel from "../components/SpendSummaryPanel";
import WeatherWidget from "../components/WeatherWidget";
import type {
  Analytics,
  HistoryDecision,
  Item,
  JoinedOrder,
  OrderMetadata,
  TodaySummary,
  Variant,
  WasteHistory,
} from "../types";

interface DashboardScreenProps {
  onSelectItem: (item?: Item) => void;
}

interface DashboardState {
  analytics?: Analytics;
  items: Item[];
  today?: TodaySummary;
  history: HistoryDecision[];
  metadata: Record<string, OrderMetadata>;
  variants: Variant[];
  wasteByItem: Record<string, WasteHistory>;
}

function decisionId(decision: HistoryDecision) {
  return decision.decisionId ?? decision.id ?? String(decision.timestamp ?? Math.random());
}

function needsOrder(item: Item) {
  const par = Number(item.parLevel ?? 0);
  const onHand = Number(item.onHandQty ?? 0);
  return par > 0 && onHand / par < 0.5;
}

function toJoinedOrders(
  history: HistoryDecision[],
  metadata: Record<string, OrderMetadata>,
  items: Item[],
): JoinedOrder[] {
  const itemByName = new Map(items.map((item) => [item.name, item]));

  return history.map((decision) => {
    const id = decisionId(decision);
    const meta = metadata[id] ?? decision.metadata;
    const itemName = meta?.itemName ?? meta?.item ?? decision.item;
    return {
      decisionId: id,
      decision,
      metadata: meta,
      item: itemName ? itemByName.get(itemName) : undefined,
    };
  });
}

export default function DashboardScreen({ onSelectItem }: DashboardScreenProps) {
  const [state, setState] = useState<DashboardState>({
    items: [],
    history: [],
    metadata: {},
    variants: [],
    wasteByItem: {},
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    let mounted = true;

    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const [items, today, history, metadata, analytics, variants] = await Promise.all([
          getItems(),
          getTodaySummary(),
          getHistory(),
          getOrderMetadata(),
          getAnalytics(),
          getEvolutionVariants(),
        ]);
        const lowItems = items.filter(needsOrder);
        const wasteEntries = await Promise.all(
          lowItems.map(async (item) => {
            try {
              return [item.name, await getWasteHistory(item.name)] as const;
            } catch {
              return [item.name, { item: item.name }] as const;
            }
          }),
        );

        if (mounted) {
          setState({
            items,
            today,
            history,
            metadata,
            analytics,
            variants,
            wasteByItem: Object.fromEntries(wasteEntries),
          });
        }
      } catch (caught) {
        if (mounted) {
          setError(caught instanceof Error ? caught.message : "Unable to load dashboard");
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

  const lowItems = useMemo(() => state.items.filter(needsOrder), [state.items]);
  const joinedOrders = useMemo(
    () => toJoinedOrders(state.history, state.metadata, state.items),
    [state.history, state.metadata, state.items],
  );

  if (loading) {
    return <section className="purchase-card">Loading purchasing dashboard...</section>;
  }

  if (error) {
    return (
      <section className="purchase-card">
        <p className="purchase-kicker">Dashboard unavailable</p>
        <h1 className="purchase-title">Purchasing data could not load</h1>
        <p className="purchase-muted">{error}</p>
      </section>
    );
  }

  return (
    <div className="purchase-stack dashboard-screen">
      <SpendSummaryPanel />
      <CommodityPricePanel />
      <ParLevelPanel />
      <AutoOrderPanel />

      <div className="purchase-grid three">
        <WeatherWidget weather={state.today?.weather} dayOfWeek={state.today?.dayOfWeek} />
        <EventBadge events={state.today?.events} />
        <section className="purchase-card dashboard-header-card">
          <p className="purchase-kicker">Cover</p>
          <h2 className="purchase-title">{lowItems.length} items need attention</h2>
          <p className="purchase-muted">
            The dashboard prioritizes on-hand inventory below half par and historical waste signals.
          </p>
          <div className="mt-3">
            <TransferBadge apiBase={BASE} />
          </div>
        </section>
      </div>

      <ParLevelMonitor
        items={lowItems}
        wasteByItem={state.wasteByItem}
        variants={state.variants}
        onSelectItem={onSelectItem}
      />

      <IgnoringCostCard analytics={state.analytics} />
      <AEStatusBar analytics={state.analytics} variants={state.variants} />
      <AccuracyAlertPanel />

      <section className="purchase-card dashboard-history">
        <div className="purchase-card-header">
          <div>
            <p className="purchase-kicker">Completed orders</p>
            <h2 className="purchase-title">Today's decisions</h2>
          </div>
          <button className="purchase-button" type="button" onClick={() => onSelectItem(undefined)}>
            Order Something Else
          </button>
        </div>
        <DecisionHistory
          decisions={joinedOrders}
          title=""
          emptyMessage="No completed orders yet."
          renderCard={(order) => <OrderCard order={order} />}
        />
      </section>
    </div>
  );
}
