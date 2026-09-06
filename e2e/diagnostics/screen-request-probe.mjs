import { chromium } from '@playwright/test';
import { writeFileSync } from 'node:fs';

const browser = await chromium.launch();
const result = [];
const copilots = [
  ['Purchasing', 5175, ['Dashboard', 'Order', 'Analysis', 'Inventory', 'Performance']],
  ['Trading', 5174, ['Dashboard', 'Log Trade', 'Analysis', 'Performance', 'Journal', 'Trade Detail']],
  ['DataOps', 5176, ['Dashboard', 'Triage', 'Insight', 'Evidence', 'Curve']],
  ['SOC', 5173, ['Initial page']], ['S2P', 5177, ['Initial page']],
];
for (const [copilot, port, tabs] of copilots) {
  const page = await browser.newPage();
  const requests = [];
  page.on('request', request => {
    if (new URL(request.url()).pathname.startsWith('/api/')) requests.push({
      method: request.method(), url: new URL(request.url()).pathname,
    });
  });
  for (const [index, tab] of tabs.entries()) {
    const offset = requests.length;
    const row = {copilot, screen: tab};
    try {
      if (index === 0) await page.goto(`http://127.0.0.1:${port}/`, {waitUntil: 'domcontentloaded'});
      else await page.getByRole('navigation').getByRole('button', {name: tab, exact: true}).click({timeout: 10000});
      // Fixed observation window makes counts comparable without waiting on
      // optional panels that do not participate in each screen's ready marker.
      await page.waitForTimeout(7000);
    } catch (error) { row.error = String(error); }
    row.requests = requests.slice(offset);
    row.total = row.requests.length;
    row.unique = new Set(row.requests.map(request => `${request.method} ${request.url}`)).size;
    result.push(row);
    console.log(JSON.stringify({copilot, screen: tab, total: row.total, unique: row.unique, error: row.error}));
  }
  await page.close();
}
writeFileSync(process.argv[2], JSON.stringify(result, null, 2));
await browser.close();
