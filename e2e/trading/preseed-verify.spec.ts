import { expect, test, type APIRequestContext } from "@playwright/test";

const TRADING_BACKEND = process.env.TRADING_BACKEND ?? "http://127.0.0.1:8010";
const PURCHASING_BACKEND = process.env.PURCHASING_BACKEND ?? "http://127.0.0.1:8020";

async function isHealthy(request: APIRequestContext, backend: string): Promise<boolean> {
  const response = await request.get(`${backend}/health`, { timeout: 5_000 }).catch((error) => {
    console.debug(`Health check unavailable for ${backend}`, error);
    return null;
  });
  return response?.ok() === true;
}

async function readTrajectory(request: APIRequestContext, backend: string): Promise<Record<string, unknown>> {
  for (const path of ["/api/trading/trajectory", "/api/trajectory"]) {
    const response = await request.get(`${backend}${path}`, { timeout: 10_000 }).catch((error) => {
      console.debug(`Trajectory endpoint unavailable: ${backend}${path}`, error);
      return null;
    });
    if (response?.ok()) {
      return (await response.json()) as Record<string, unknown>;
    }
    if (response) {
      console.debug(`Trajectory endpoint returned ${response.status()}: ${backend}${path}`);
    }
  }
  throw new Error(`No trajectory endpoint returned OK for ${backend}`);
}

function numberValue(value: unknown): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function extractIks(payload: Record<string, unknown>): number {
  const direct = [
    payload.iks,
    payload.current_iks,
    payload.currentIks,
    payload.iks_v2,
    payload.institutional_knowledge_score,
  ];
  for (const value of direct) {
    const parsed = numberValue(value);
    if (parsed !== null) return parsed;
  }

  if (payload.iks && typeof payload.iks === "object") {
    const iks = payload.iks as Record<string, unknown>;
    for (const value of [iks.score, iks.value]) {
      const parsed = numberValue(value);
      if (parsed !== null) return parsed;
    }
  }

  const points = Array.isArray(payload.points)
    ? payload.points
    : Array.isArray(payload.trajectory)
      ? payload.trajectory
      : [];
  const pointValues = points
    .map((point) => numberValue((point as Record<string, unknown>).iks ?? (point as Record<string, unknown>).currentIks))
    .filter((value): value is number => value !== null);
  return pointValues.length ? pointValues[pointValues.length - 1] : 0;
}

test("test_iks_nonflat_after_preseed", async ({ request }) => {
  test.skip(!(await isHealthy(request, TRADING_BACKEND)), "Trading backend is not running");

  const payload = await readTrajectory(request, TRADING_BACKEND);
  const iks = extractIks(payload);

  expect(iks).toBeGreaterThan(10);
});

test("test_iks_nonflat_purchasing", async ({ request }) => {
  test.skip(!(await isHealthy(request, PURCHASING_BACKEND)), "Purchasing backend is not running");

  const payload = await readTrajectory(request, PURCHASING_BACKEND);
  const iks = extractIks(payload);

  expect(iks).toBeGreaterThan(10);
});
