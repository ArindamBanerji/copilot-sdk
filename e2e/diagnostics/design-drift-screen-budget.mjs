import { chromium } from '@playwright/test';
import { writeFileSync } from 'node:fs';

// Counts observed calls, including children and StrictMode, rather than source
// call sites. Seven seconds is an observation window, not a readiness promise.
const copilots = [
  ['Purchasing', 5175, ['Dashboard', 'Order', 'Analysis', 'Inventory', 'Performance']],
  ['Trading', 5174, ['Dashboard', 'Log Trade', 'Analysis', 'Performance', 'Journal', 'Trade Detail']],
  ['DataOps', 5176, ['Dashboard', 'Triage', 'Insight', 'Evidence', 'Curve']],
  ['SOC', 5173, ['Runtime Evolution', 'SOC Analytics', 'Alert Triage', 'Compounding', 'Executive Narrative', 'S2P Preview', 'Evidence Room']],
  ['S2P', 5177, ['Dashboard', 'Exception Triage', 'Insight', 'Evidence', 'Suppliers', 'Performance']],
];
const result = [];
const selectedOnly = process.argv.includes('--selected-only');
const observedCopilots = selectedOnly
  ? [['Trading', 5174, ['Dashboard', 'Trade Detail (selected)']], ['DataOps', 5176, ['Dashboard', 'Triage (selected)']]]
  : copilots;
const browser = await chromium.launch();
try {
  for (const [copilot, port, tabs] of observedCopilots) {
    const page = await browser.newPage();
    const requests = [], byRequest = new WeakMap();
    page.on('request', request => {
      if (!new URL(request.url()).pathname.startsWith('/api/')) return;
      const row = { method: request.method(), url: new URL(request.url()).pathname };
      requests.push(row); byRequest.set(request, row);
    });
    page.on('response', response => {
      const row = byRequest.get(response.request());
      if (row) row.status = response.status();
    });
    page.on('requestfailed', request => {
      const row = byRequest.get(request);
      if (row) row.error = request.failure()?.errorText;
    });
    for (const [index, tab] of tabs.entries()) {
      const offset = requests.length;
      const row = { copilot, screen: tab };
      try {
        if (index === 0) await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'domcontentloaded' });
        else if (selectedOnly) {
          const candidates = copilot === 'Trading'
            ? page.getByRole('button').filter({ hasText: 'Holding period' })
            : page.locator('section').filter({ has: page.getByRole('heading', { name: 'Alert Queue', exact: true }) }).getByRole('button');
          const labels = (await candidates.allTextContents()).map(label => label.replace(/\s+/g, ' ').trim());
          const unique = labels.filter(label => labels.filter(other => other === label).length === 1).sort();
          if (!unique.length) throw new Error('No uniquely named entity card available');
          row.selectedEntity = unique[0];
          await page.getByRole('button', { name: unique[0], exact: true }).click({ timeout: 10000 });
        }
        else if (copilot === 'SOC') await page.getByRole('button', { name: tab, exact: tab !== 'Runtime Evolution' }).click({ timeout: 10000 });
        else await page.getByRole('navigation').getByRole('button', { name: tab, exact: true }).click({ timeout: 10000 });
        await page.waitForTimeout(7000);
        row.textExcerpt = (await page.locator('main').innerText()).slice(0, 600);
      } catch (error) { row.error = String(error); }
      row.requests = requests.slice(offset);
      row.total = row.requests.length;
      row.unique = new Set(row.requests.map(request => `${request.method} ${request.url}`)).size;
      result.push(row);
      console.log(JSON.stringify({ ...row, requests: undefined, textExcerpt: undefined }));
      writeFileSync(process.argv[2], JSON.stringify(result, null, 2));
    }
    await page.close();
  }
} finally { await browser.close(); }
