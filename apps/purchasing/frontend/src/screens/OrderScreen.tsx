import { useEffect, useMemo, useState } from "react";
import { ReasoningPanel, type GenericFingerprint } from "../../../../../copilot_sdk/frontend";
import ScoreResultCard, { type RewardLine, type ScoreResult } from "../../../../../copilot_sdk/frontend/ScoreResultCard";
import {
  getAnalytics,
  getFingerprint,
  getItemProfile,
  getItems,
  getSimilarOrders,
  getTodaySummary,
  getWasteHistory,
  getWeather,
  learnOrder,
  saveOrderMetadata,
  scoreOrder,
} from "../api";
import AEManagedBadge from "../components/AEManagedBadge";
import CostAnalysis from "../components/CostAnalysis";
import EngineAssessment from "../components/EngineAssessment";
import EventBadge from "../components/EventBadge";
import MatchResultPanel from "../components/MatchResultPanel";
import OrderContext from "../components/OrderContext";
import SimilarOrdersPanel from "../components/SimilarOrdersPanel";
import WeatherWidget from "../components/WeatherWidget";
import type {
  Analytics,
  ExpectedDemandChoice,
  FactorMap,
  FingerprintResponse,
  Item,
  ItemProfile,
  LearnResponse,
  ScoreResponse,
  SimilarOrder,
  TodaySummary,
  WasteHistory,
  Weather,
} from "../types";

interface OrderScreenProps {
  selectedItem?: Item;
}

const demandValues: Record<ExpectedDemandChoice, number> = {
  high: 0.9,
  above_avg: 0.7,
  average: 0.5,
  below_avg: 0.3,
  low: 0.1,
};

const demandLabels: Record<ExpectedDemandChoice, string> = {
  high: "High",
  above_avg: "Above average",
  average: "Average",
  below_avg: "Below average",
  low: "Low",
};

const actionNames = ["Order as planned", "Order more", "Order less", "Skip"];
const actionIds = ["order_as_planned", "order_more", "order_less", "skip"];
const actionDisplay: Record<string, string> = {
  order_as_planned: "Order as planned",
  order_more: "Order more",
  order_less: "Order less",
  skip: "Skip",
};
const factorNames = [
  "expected_demand",
  "day_of_week",
  "weather_forecast",
  "event_flag",
  "historical_waste",
  "supplier_lead_time",
];
const factorLabels: Record<string, string> = {
  expected_demand: "Expected demand",
  day_of_week: "Day of week",
  weather_forecast: "Weather forecast",
  event_flag: "Event flag",
  historical_waste: "Historical waste",
  supplier_lead_time: "Supplier lead time",
};

const dayValues: Record<string, number> = {
  mon: 0.14,
  tue: 0.28,
  wed: 0.43,
  thu: 0.57,
  fri: 0.71,
  sat: 0.86,
  sun: 1,
};

function numberOr(value: unknown, fallback: number) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function averageWaste(history?: WasteHistory, profile?: ItemProfile) {
  const values =
    Array.isArray(history?.wastePct)
      ? history.wastePct
      : Array.isArray(profile?.wasteHistory)
        ? profile.wasteHistory
        : [];
  if (values.length === 0) {
    return numberOr(profile?.wasteAvg, 0);
  }
  return values.reduce((total, value) => total + numberOr(value, 0), 0) / values.length;
}

function dayFactor(day?: string) {
  return dayValues[String(day ?? "").slice(0, 3).toLowerCase()] ?? 0.5;
}

function weatherFactor(weather?: Weather) {
  const rawPrecip = weather?.precipitationProb ?? weather?.precipChance;
  const precip = numberOr(rawPrecip, 50);
  const percent = precip <= 1 ? precip * 100 : precip;
  if (percent > 50) {
    return 0.7;
  }
  if (percent < 20) {
    return 0.2;
  }
  return 0.5;
}

function eventFactor(events?: Array<Record<string, unknown>>) {
  const count = events?.length ?? 0;
  return count > 0 ? Math.min(0.6 + count * 0.1, 1) : 0;
}

function computeFactors(
  expectedDemand: ExpectedDemandChoice,
  item?: Item,
  today?: TodaySummary,
  weather?: Weather,
  wasteHistory?: WasteHistory,
  profile?: ItemProfile,
): FactorMap {
  const waste = averageWaste(wasteHistory, profile);
  return {
    expected_demand: demandValues[expectedDemand],
    day_of_week: dayFactor(today?.dayOfWeek),
    weather_forecast: weatherFactor(weather ?? today?.weather),
    event_flag: eventFactor(today?.events),
    historical_waste: Math.min(Math.max(waste / 100, 0), 1),
    supplier_lead_time: numberOr(item?.supplierLeadTime, 0.5),
  };
}

function defaultQuantity(item?: Item) {
  if (!item) {
    return 0;
  }
  return Math.max(numberOr(item.parLevel, 0) - numberOr(item.onHandQty, 0), 0);
}

function toScoreResult(score: ScoreResponse): ScoreResult {
  const actionIndex = Number.isFinite(score.actionIndex) ? Number(score.actionIndex) : Math.max(actionIds.indexOf(String(score.action)), 0);
  const actionId = String(score.action ?? actionIds[actionIndex] ?? "order_as_planned");
  return {
    decisionId: String(score.decisionId ?? ""),
    action: actionDisplay[actionId] ?? actionId,
    actionIndex,
    confidence: numberOr(score.confidence, 0),
    probabilities: Array.isArray(score.probabilities) ? score.probabilities : [0.25, 0.25, 0.25, 0.25],
    category: String(score.category ?? "purchasing"),
    factors: score.factors as Record<string, number> | undefined,
    actionNames,
  };
}

function actionIdFromDisplay(action: string) {
  const index = actionNames.indexOf(action);
  return actionIds[index] ?? action;
}

function getSimilarAction(order: SimilarOrder): string | undefined {
  for (const key of ["actionTaken", "action_taken", "action", "actualAction", "confirmedAction", "recommendedAction", "scoreAction"]) {
    const value = order[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }
  return undefined;
}

function normalizeFingerprint(fingerprint?: FingerprintResponse): GenericFingerprint | null {
  if (!fingerprint) {
    return null;
  }
  if (Array.isArray(fingerprint.factors)) {
    return {
      ...fingerprint,
      factors: fingerprint.factors,
    };
  }
  const signal = fingerprint.signal || {};
  const noise = fingerprint.noise || {};
  return {
    ...fingerprint,
    factors: Object.entries({ ...signal, ...noise }).map(([name, weight]) => ({
      name,
      weight: numberOr(weight, 0),
      sigma: 0,
    })),
  };
}

export default function OrderScreen({ selectedItem }: OrderScreenProps) {
  const [items, setItems] = useState<Item[]>(selectedItem ? [selectedItem] : []);
  const [itemName, setItemName] = useState(selectedItem?.name ?? "");
  const [profile, setProfile] = useState<ItemProfile | undefined>();
  const [weather, setWeather] = useState<Weather | undefined>();
  const [today, setToday] = useState<TodaySummary | undefined>();
  const [wasteHistory, setWasteHistory] = useState<WasteHistory | undefined>();
  const [analytics, setAnalytics] = useState<Analytics | undefined>();
  const [fingerprint, setFingerprint] = useState<FingerprintResponse | undefined>();
  const [expectedDemand, setExpectedDemand] = useState<ExpectedDemandChoice>("average");
  const [quantity, setQuantity] = useState(defaultQuantity(selectedItem));
  const [loading, setLoading] = useState(true);
  const [itemLoading, setItemLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();
  const [score, setScore] = useState<ScoreResponse | undefined>();
  const [similarOrders, setSimilarOrders] = useState<SimilarOrder[]>([]);
  const [similarCount, setSimilarCount] = useState(0);
  const [scoring, setScoring] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [learnResult, setLearnResult] = useState<LearnResponse | undefined>();

  useEffect(() => {
    let mounted = true;
    async function loadBase() {
      setLoading(true);
      setError(undefined);
      try {
        const [catalog, summary, currentWeather, currentAnalytics, currentFingerprint] = await Promise.all([
          getItems(),
          getTodaySummary(),
          getWeather(),
          getAnalytics(),
          getFingerprint(),
        ]);
        if (mounted) {
          setItems(catalog);
          setToday(summary);
          setWeather(currentWeather);
          setAnalytics(currentAnalytics);
          setFingerprint(currentFingerprint);
          if (!itemName && catalog[0]) {
            setItemName(catalog[0].name);
          }
        }
      } catch (caught) {
        if (mounted) {
          setError(caught instanceof Error ? caught.message : "Unable to load order context");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    loadBase();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (selectedItem?.name) {
      setItemName(selectedItem.name);
      setQuantity(defaultQuantity(selectedItem));
    }
  }, [selectedItem]);

  const currentItem = useMemo(
    () => items.find((item) => item.name === itemName) ?? selectedItem,
    [items, itemName, selectedItem],
  );

  useEffect(() => {
    let mounted = true;
    async function loadItem() {
      if (!currentItem?.name) {
        return;
      }
      setItemLoading(true);
      setError(undefined);
      setScore(undefined);
      setSimilarOrders([]);
      setLearnResult(undefined);
      try {
        const [nextProfile, nextWaste] = await Promise.all([
          getItemProfile(currentItem.name),
          getWasteHistory(currentItem.name),
        ]);
        if (mounted) {
          setProfile(nextProfile);
          setWasteHistory(nextWaste);
          setQuantity(defaultQuantity(currentItem));
        }
      } catch (caught) {
        if (mounted) {
          setError(caught instanceof Error ? caught.message : "Unable to load item context");
        }
      } finally {
        if (mounted) {
          setItemLoading(false);
        }
      }
    }
    loadItem();
    return () => {
      mounted = false;
    };
  }, [currentItem?.name]);

  const factors = useMemo(
    () => computeFactors(expectedDemand, currentItem, today, weather, wasteHistory, profile),
    [expectedDemand, currentItem, today, weather, wasteHistory, profile],
  );

  const costs = useMemo(() => {
    const unitPrice = numberOr(currentItem?.unitPrice, 0);
    const safeQuantity = numberOr(quantity, 0);
    const orderCost = safeQuantity * unitPrice;
    const stockoutEstimate = unitPrice * safeQuantity * 20;
    const wasteEstimate = unitPrice * safeQuantity * factors.historical_waste;
    return {
      orderCost,
      stockoutEstimate,
      wasteEstimate,
      riskRatio: wasteEstimate > 0 ? stockoutEstimate / wasteEstimate : null,
    };
  }, [currentItem?.unitPrice, quantity, factors.historical_waste]);

  async function runScore() {
    if (!currentItem?.category) {
      setError("Select an item before scoring.");
      return;
    }
    setScoring(true);
    setError(undefined);
    try {
      const nextScore = await scoreOrder({
        category: String(currentItem.category),
        factors,
        context: {
          item: currentItem.name,
          quantity,
          expectedDemandChoice: expectedDemand,
          day: today?.dayOfWeek,
          events: today?.events ?? [],
          cost: costs.orderCost,
        },
      });
      const similar = await getSimilarOrders(String(currentItem.category), factors, 5);
      setScore(nextScore);
      setSimilarOrders(similar.similar ?? []);
      setSimilarCount(similar.count ?? similar.similar?.length ?? 0);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to score order");
    } finally {
      setScoring(false);
    }
  }

  async function confirm(decisionId: string, displayAction?: string) {
    if (!currentItem || !score) {
      return;
    }
    const actionId = displayAction ? actionIdFromDisplay(displayAction) : String(score.action ?? "order_as_planned");
    setConfirming(true);
    setError(undefined);
    try {
      const learned = await learnOrder({
        decisionId,
        actualAction: actionId,
        outcome: "confirmed",
        context: {
          item: currentItem.name,
          quantity,
          orderCost: costs.orderCost,
          stockoutEstimate: costs.stockoutEstimate,
          wasteEstimate: costs.wasteEstimate,
        },
      });
      await saveOrderMetadata({
        decisionId,
        item: currentItem.name,
        displayName: currentItem.displayName,
        emoji: currentItem.emoji,
        category: String(currentItem.category ?? ""),
        quantity,
        quantityLbs: quantity,
        unit: currentItem.unit,
        day: today?.dayOfWeek,
        events: today?.events ?? [],
        cost: costs.orderCost,
        totalCost: costs.orderCost,
        stockoutEstimate: costs.stockoutEstimate,
        wasteEstimate: costs.wasteEstimate,
        riskRatio: costs.riskRatio,
        autoComputedFactors: factors,
        expectedDemandChoice: expectedDemand,
        expectedDemand: factors.expected_demand,
        action: String(score.action ?? ""),
        confirmedAction: actionId,
        reward: learned.reward,
        createdAt: new Date().toISOString(),
      });
      setLearnResult(learned);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to confirm order");
    } finally {
      setConfirming(false);
    }
  }

  const scoreResult = score ? toScoreResult(score) : undefined;
  const rewardLine: RewardLine | undefined = learnResult
    ? {
        reward: numberOr(learnResult.reward, 0),
        previousReward: learnResult.previousReward ?? null,
        rewardMultiplier: learnResult.rewardMultiplier,
      }
    : undefined;

  if (loading) {
    return <section className="purchase-card">Loading order workflow...</section>;
  }

  return (
    <div className="purchase-stack order-screen">
      {error && (
        <section className="purchase-card error-card">
          <p className="purchase-kicker">Order workflow issue</p>
          <p>{error}</p>
        </section>
      )}

      <section className="purchase-card">
        <div className="purchase-card-header">
          <div>
            <p className="purchase-kicker">Order</p>
            <h1 className="purchase-title">Score the next purchase</h1>
            <p className="purchase-muted">Choose one demand input. The rest is computed from inventory history.</p>
          </div>
          <AEManagedBadge managed={Boolean(profile?.aeManaged || profile?.aeRules?.length)} count={profile?.aeRules?.length} />
        </div>

        <div className="order-form-grid">
          <label>
            <span>Item</span>
            <select value={itemName} onChange={(event) => setItemName(event.target.value)}>
              {items.map((item) => (
                <option key={item.itemId ?? item.name} value={item.name}>
                  {item.displayName ?? item.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Expected demand</span>
            <select
              value={expectedDemand}
              onChange={(event) => setExpectedDemand(event.target.value as ExpectedDemandChoice)}
            >
              {Object.entries(demandLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Quantity</span>
            <input
              min="0"
              step="1"
              type="number"
              value={quantity}
              onChange={(event) => setQuantity(Math.max(0, Number(event.target.value)))}
            />
          </label>
          <div className="quantity-summary">
            <span>{currentItem?.unit ?? "units"}</span>
            <strong>{currentItem ? `$${costs.orderCost.toFixed(0)}` : "$0"}</strong>
          </div>
        </div>
      </section>

      <MatchResultPanel />

      {itemLoading ? <section className="purchase-card">Loading item profile...</section> : null}

      <OrderContext
        today={today}
        weather={weather}
        events={today?.events}
        wasteHistory={wasteHistory}
        analytics={analytics}
        factors={factors}
      />

      <div className="purchase-grid three">
        <WeatherWidget weather={weather ?? today?.weather} dayOfWeek={today?.dayOfWeek} />
        <EventBadge events={today?.events} />
        <CostAnalysis item={currentItem} quantity={quantity} historicalWaste={factors.historical_waste} />
      </div>

      <section className="purchase-card">
        <div className="purchase-card-header">
          <div>
            <p className="purchase-kicker">Auto-computed factors</p>
            <h2 className="purchase-title">Six scorer inputs</h2>
          </div>
          <button className="purchase-button" type="button" disabled={scoring || !currentItem} onClick={runScore}>
            {scoring ? "Scoring..." : "Score This Order"}
          </button>
        </div>
        <div className="factor-grid">
          {[
            ["Expected demand", factors.expected_demand],
            ["Day of week", factors.day_of_week],
            ["Weather", factors.weather_forecast],
            ["Events", factors.event_flag],
            ["Historical waste", factors.historical_waste],
            ["Supplier lead time", factors.supplier_lead_time],
          ].map(([label, value]) => (
            <div className="factor-row" key={String(label)}>
              <span>{label}</span>
              <div className="factor-track">
                <span style={{ width: `${Number(value) * 100}%` }} />
              </div>
              <strong>{Number(value).toFixed(2)}</strong>
            </div>
          ))}
        </div>
      </section>

      {score && scoreResult ? (
        <>
          <EngineAssessment factors={factors} fingerprint={fingerprint} analytics={analytics} similarCount={similarCount} />
          <SimilarOrdersPanel orders={similarOrders} count={similarCount} />
          <ScoreResultCard
            result={scoreResult}
            onConfirm={(decisionId) => confirm(decisionId)}
            onOverride={(decisionId, action) => confirm(decisionId, action)}
            rewardLine={rewardLine}
          />
          <ReasoningPanel
            scoreResult={{
              ...score,
              action: String(score.action ?? actionIds[scoreResult.actionIndex] ?? "order_as_planned"),
              actionIndex: scoreResult.actionIndex,
              probabilities: scoreResult.probabilities,
              category: scoreResult.category,
              factors,
            }}
            similarItems={similarOrders.map((order) => ({
              ...order,
              action: getSimilarAction(order),
              correct: order.isCorrect,
            }))}
            fingerprint={normalizeFingerprint(fingerprint)}
            factorValues={factors}
            actionNames={actionIds}
            factorNames={factorNames}
            actionLabels={actionDisplay}
            factorLabels={factorLabels}
          />
          {confirming ? <p className="purchase-muted">Confirming and storing order metadata...</p> : null}
          {learnResult ? (
            <section className="purchase-card">
              <p className="purchase-kicker">Learned</p>
              <h2 className="purchase-title">
                {numberOr(learnResult.rewardMultiplier, 0) > 2
                  ? `The system learned ${numberOr(learnResult.rewardMultiplier, 0).toFixed(1)}x more from this ordering decision.`
                  : "The system learned from this ordering decision."}
              </h2>
              <p className="purchase-muted">
                {currentItem?.displayName ?? currentItem?.name}, {quantity} {currentItem?.unit ?? "units"}
              </p>
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
