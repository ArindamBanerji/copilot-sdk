import { test, expect } from "@playwright/test";

const BACKEND = process.env.TRADING_BACKEND || "http://127.0.0.1:8010";

test.describe("Market Data API - spot checks", () => {
  test("GET /api/context/market-snapshot returns provenance", async ({ request }) => {
    const res = await request.get(`${BACKEND}/api/context/market-snapshot`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("provenance");
    expect(body.provenance).toHaveProperty("source");
    expect(["live", "cached", "fixture", "demo_fixture"]).toContain(body.provenance.source);
  });

  test("GET /api/context/market-snapshot has spy price", async ({ request }) => {
    const res = await request.get(`${BACKEND}/api/context/market-snapshot`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("spy");
    if (body.spy && body.spy.price !== null) {
      expect(typeof body.spy.price).toBe("number");
    }
  });

  test("GET /api/context/ticker/SPY returns enriched data", async ({ request }) => {
    const res = await request.get(`${BACKEND}/api/context/ticker/SPY`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("ticker", "SPY");
    expect(body).toHaveProperty("provenance");
    for (const field of ["price", "change30dPct", "volRankPctl"]) {
      expect(body).toHaveProperty(field);
    }
  });

  test("POST /api/trading/market/refresh returns provenance", async ({ request }) => {
    const res = await request.post(`${BACKEND}/api/trading/market/refresh`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("refreshed", true);
    expect(body).toHaveProperty("provenance");
    expect(body.provenance).toHaveProperty("source");
  });

  test("GET /api/trading/regime returns regime data", async ({ request }) => {
    const res = await request.get(`${BACKEND}/api/trading/regime`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("current");
    expect(body.current).toHaveProperty("regime");
  });

  test("GET /api/trading/market/ohlcv returns rows", async ({ request }) => {
    const res = await request.get(`${BACKEND}/api/trading/market/ohlcv?ticker=SPY`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("ticker", "SPY");
    expect(body).toHaveProperty("rows");
    expect(Array.isArray(body.rows)).toBe(true);
  });

  test("GET /api/trading/market/vix returns VIX data", async ({ request }) => {
    const res = await request.get(`${BACKEND}/api/trading/market/vix`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty("ticker", "^VIX");
  });
});

test.describe("Market Data API - flow checks", () => {
  test("refresh then snapshot keeps market data provenanced", async ({ request }) => {
    const refresh = await request.post(`${BACKEND}/api/trading/market/refresh`);
    expect(refresh.status()).toBe(200);
    const refreshBody = await refresh.json();
    expect(refreshBody).toHaveProperty("refreshed", true);
    expect(refreshBody).toHaveProperty("provenance");

    const snapshot = await request.get(`${BACKEND}/api/context/market-snapshot`);
    expect(snapshot.status()).toBe(200);
    const snapshotBody = await snapshot.json();
    expect(snapshotBody).toHaveProperty("provenance");
    expect(["live", "cached", "fixture", "demo_fixture"]).toContain(snapshotBody.provenance.source);
  });
});
