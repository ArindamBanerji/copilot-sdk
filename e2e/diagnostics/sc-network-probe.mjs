import { chromium } from '@playwright/test';
import { writeFileSync } from 'node:fs';

const browser = await chromium.launch();
const page = await browser.newPage();
const requests = [];
const failures = [];
page.on('requestfinished', (request) => {
  if (request.url().includes('/api/')) requests.push({
    url: new URL(request.url()).pathname, timing: request.timing(),
  });
});
page.on('requestfailed', (request) => failures.push({url: request.url(), error: request.failure()}));
const started = performance.now();
const stages = {};
try {
  await page.goto('http://127.0.0.1:5175/', {waitUntil: 'domcontentloaded'});
  stages.domContentLoadedMs = performance.now() - started;
  await page.locator('main > [data-screen-ready="true"]').waitFor({timeout: 25000});
  stages.screenReadyMs = performance.now() - started;
  await page.locator('main [data-panel-ready="false"]').waitFor({state: 'detached', timeout: 25000});
} catch (error) {
  failures.push({error: String(error)});
}
const resources = await page.evaluate(() => performance.getEntriesByType('resource').map((entry) => ({
  url: entry.name, startTime: entry.startTime, duration: entry.duration,
})));
const result = {elapsedMs: performance.now() - started, stages, requests, failures, resources};
writeFileSync(process.argv[2], JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
await browser.close();
