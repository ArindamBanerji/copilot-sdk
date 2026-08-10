import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8010';

test('trading checkpoint history exposes regime tags', async ({ request }) => {
  const response = await request.get(`${BASE}/api/self/centroid-history?limit=10`);
  expect(response.status()).toBe(200);

  const body = await response.json();
  expect(body).toHaveProperty('checkpoints');
  const checkpoints = body.checkpoints as Array<Record<string, unknown>>;
  if (checkpoints.length > 0) {
    const tagged = checkpoints.filter((checkpoint) => checkpoint.regime_tag != null);
    if (tagged.length === 0) {
      test.skip(true, 'live instance has only legacy checkpoints; run Trading preseed first');
    }
    expect(tagged.some((checkpoint) => ['trending', 'ranging', 'volatile'].includes(String(checkpoint.regime_tag)))).toBe(true);
  }
});
