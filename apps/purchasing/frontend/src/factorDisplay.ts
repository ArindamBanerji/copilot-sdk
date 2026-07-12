export const factorDisplayNames: Record<string, string> = {
  expected_demand: "Whether They Show Up",
  expectedDemand: "Whether They Show Up",
  supplier_reliability: "What We Can Count On",
  supplierReliability: "What We Can Count On",
  price_stability: "What They Charge",
  priceStability: "What They Charge",
  product_quality: "What Arrives",
  productQuality: "What Arrives",
  delivery_timing: "When It Shows Up",
  deliveryTiming: "When It Shows Up",
  seasonal_pattern: "What the Calendar Says",
  seasonalPattern: "What the Calendar Says",
  waste_history: "What Gets Thrown Away",
  wasteHistory: "What Gets Thrown Away",
  price_memory_index: "What They Used to Charge",
  priceMemoryIndex: "What They Used to Charge",
  day_of_week: "What the Calendar Says",
  dayOfWeek: "What the Calendar Says",
  weather_forecast: "What the Weather Says",
  weatherForecast: "What the Weather Says",
  event_flag: "What Events Change",
  eventFlag: "What Events Change",
  historical_waste: "What Gets Thrown Away",
  historicalWaste: "What Gets Thrown Away",
  supplier_lead_time: "When It Shows Up",
  supplierLeadTime: "When It Shows Up",
  coverage_depth: "Match confidence",
  coverageDepth: "Match confidence",
};

export function factorDisplayName(key: string): string {
  return factorDisplayNames[key] ?? key;
}
