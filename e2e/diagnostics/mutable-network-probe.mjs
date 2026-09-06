import { chromium, expect } from '@playwright/test';
import { writeFileSync } from 'node:fs';

const browser = await chromium.launch();
const page = await browser.newPage();
const started = performance.now();
const requests = [];
const requestRows = new WeakMap();
const stages = {};
const failures = [];
page.on('request', request => {
  if (!request.url().includes('/api/')) return;
  const row = { url: request.url(), method: request.method(), startMs: performance.now() - started,
    body: request.postData() };
  requests.push(row);
  requestRows.set(request, row);
});
page.on('requestfinished', async request => {
  if (!request.url().includes('/api/')) return;
  const row = requestRows.get(request);
  if (row) Object.assign(row, {endMs: performance.now() - started, timing: request.timing(),
    status: (await request.response())?.status()});
});
page.on('requestfailed', request => failures.push({url: request.url(), error: request.failure()}));
try {
  await page.goto('http://127.0.0.1:5175/', {waitUntil: 'domcontentloaded'});
  await page.locator('main > [data-screen-ready="true"]').waitFor({timeout: 30000});
  await expect(page.locator('main [data-panel-ready="false"]')).toHaveCount(0, {timeout: 30000});
  stages.dashboardReadyMs = performance.now() - started;
  await page.getByRole('navigation').getByRole('button', {name: 'Order', exact: true}).click();
  await expect(page.getByRole('button', {name: 'Score This Order'})).toBeEnabled({timeout: 30000});
  stages.clickMs = performance.now() - started;
  const responsePromise = page.waitForResponse(r => new URL(r.url()).pathname === '/api/score' && r.request().method() === 'POST', {timeout: 45000});
  await page.getByRole('button', {name: 'Score This Order'}).click();
  const response = await responsePromise;
  stages.scoreResponseMs = performance.now() - started;
  stages.scoreStatus = response.status();
  stages.scoreBody = await response.json();
  await expect(page.getByRole('button', {name: 'Confirm', exact: true})).toBeVisible({timeout: 15000});
  stages.resultVisibleMs = performance.now() - started;
  const verifyPromise = page.waitForResponse(r => new URL(r.url()).pathname === '/api/purchasing/verify' && r.request().method() === 'POST', {timeout: 45000});
  stages.confirmClickMs = performance.now() - started;
  await page.getByRole('button', {name: 'Confirm', exact: true}).click();
  const verified = await verifyPromise;
  stages.verifyResponseMs = performance.now() - started;
  stages.verifyStatus = verified.status();
  stages.verifyBody = await verified.json();
  await page.waitForTimeout(10000);
} catch (error) {
  failures.push({error: String(error)});
}
const result = {elapsedMs: performance.now() - started, stages, requests, failures};
writeFileSync(process.argv[2], JSON.stringify(result, null, 2));
console.log(JSON.stringify({elapsedMs: result.elapsedMs, stages, failures}, null, 2));
await browser.close();
