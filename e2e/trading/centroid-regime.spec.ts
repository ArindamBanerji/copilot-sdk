import { test, expect } from '@playwright/test';

const HOST = process.env.COPILOT_HOST || "127.0.0.1";
const BASE = `http://${HOST}:8010`;

test('trading checkpoint history exposes regime tags', async ({ request }) => {
  const response = await request.get(`${BASE}/api/self/centroid-history?limit=10`);
  expect(response.status()).toBe(200);

  const body = await response.json();
  expect(body).toHaveProperty('checkpoints');
  const checkpoints = body.checkpoints as Array<Record<string, unknown>>;
  if (checkpoints.length > 0) {
    const tagged = checkpoints.filter((checkpoint) => checkpoint.regime_tag != null);
    expect(tagged.some((checkpoint) => ['trending', 'ranging', 'volatile'].includes(String(checkpoint.regime_tag)))).toBe(true);
  }
});
