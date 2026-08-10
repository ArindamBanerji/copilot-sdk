import { test, expect } from "@playwright/test";

test("Purchasing health exposes hot-path cache stats", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/health");
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.cache_hits).toBeDefined();
  expect(data.cache_misses).toBeDefined();
  expect(data.cache_size).toBeDefined();
});
