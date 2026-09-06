import { chromium, expect, request as requestFactory } from '@playwright/test';
import { writeFileSync } from 'node:fs';

const output = process.argv[2];
const browser = await chromium.launch();
const api = await requestFactory.newContext();
const results = [];
try {
  for (const screen of ['Dashboard', 'Order', 'Analysis', 'Inventory', 'Performance']) {
    const context = await browser.newContext();
    const page = await context.newPage();
    const started = performance.now();
    const rows = [], byRequest = new WeakMap(), stages = {};
    page.on('request', request => {
      if (!request.url().includes('/api/')) return;
      const row = { method: request.method(), url: request.url(), startMs: performance.now() - started };
      rows.push(row); byRequest.set(request, row);
    });
    page.on('requestfinished', async request => {
      const row = byRequest.get(request);
      if (row) {
        const response = await request.response().catch(() => null);
        Object.assign(row, { endMs: performance.now() - started, timing: request.timing(), status: response?.status() });
      }
    });
    page.on('requestfailed', request => {
      const row = byRequest.get(request);
      if (row) Object.assign(row, { endMs: performance.now() - started, error: request.failure()?.errorText });
    });
    await page.addInitScript(() => {
      window.__driftReady = [];
      const observer = new MutationObserver(() => {
        const state = [...document.querySelectorAll('[data-panel-ready]')].map(e => [e.getAttribute('data-testid'), e.getAttribute('data-panel-ready')]);
        const key = JSON.stringify(state);
        if (window.__driftReady.at(-1)?.key !== key) window.__driftReady.push({ ms: performance.now(), key });
      });
      observer.observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['data-panel-ready'] });
    });
    let error;
    try {
      for (const path of ['/health', '/api/fingerprint', '/api/conservation/status']) {
        const begin = performance.now();
        const response = await api.get(`http://127.0.0.1:8020${path}`, { timeout: 10000 });
        stages[path] = { ms: performance.now() - begin, status: response.status() };
      }
      stages.gotoMs = performance.now() - started;
      await page.goto('http://127.0.0.1:5175/', { waitUntil: 'domcontentloaded' });
      stages.domMs = performance.now() - started;
      await page.locator('main > [data-screen-ready="true"]').waitFor({ timeout: 30000 });
      stages.screenReadyMs = performance.now() - started;
      await expect(page.locator('main [data-panel-ready="false"]')).toHaveCount(0, { timeout: 30000 });
      stages.panelsReadyMs = performance.now() - started;
      if (screen !== 'Dashboard') {
        stages.navigateMs = performance.now() - started;
        await page.getByRole('navigation').getByRole('button', { name: screen, exact: true }).click();
        await page.locator('main > [data-screen-ready="true"]').waitFor({ timeout: 30000 });
        await expect(page.locator('main [data-panel-ready="false"]')).toHaveCount(0, { timeout: 30000 });
        stages.targetReadyMs = performance.now() - started;
      }
      stages.resourceTiming = await page.evaluate(() => performance.getEntriesByType('resource').filter(e => e.name.includes('/api/')).map(e => e.toJSON()));
    } catch (caught) { error = String(caught); }
    const panelHistory = await page.evaluate(() => window.__driftReady);
    results.push({ screen, elapsedMs: performance.now() - started, stages, rows, panelHistory, error });
    console.log(JSON.stringify({ screen, elapsedMs: results.at(-1).elapsedMs, requests: rows.length, stages: { ...stages, resourceTiming: undefined }, error }));
    await context.close();
    writeFileSync(output, JSON.stringify(results, null, 2));
  }
} finally { await api.dispose(); await browser.close(); }
