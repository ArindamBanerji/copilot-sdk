// Run with the DataOps Vite dev server at DCEL_UI_URL (default http://127.0.0.1:5188).
// Uses the workspace's existing Playwright install, without adding app dependencies.
const { createRequire } = require('node:module');
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const workspaceRequire = createRequire(path.resolve(__dirname, '../../../../e2e/package.json'));
const { chromium } = workspaceRequire('playwright');
const { expect } = workspaceRequire('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => { errors.push(error.message); console.error('Page error:', error.message); });
    const raw = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../backend/data/process_timeline.json'), 'utf8'));
    const timeline = {
      ...raw, source: 'celonis_cache', provenance: 'sample',
      slowdown_multiplier: raw.current_duration / raw.normal_duration,
      activities: raw.activities.map(row => ({ ...row, avg_duration: row.current_duration,
        automation_rate: .7, rework_rate: .12, is_bottleneck: row.id === raw.bottleneck_id }))
    };
    const health = {
      overall: 'degraded', fusion_ready: true,
      sap: { source: 'sap_cache', cached: true, connected: false, record_count: 12 },
      celonis: { source: 'celonis_cache', cached: true, connected: false, kpi_count: 4 },
      graph: { source: 'fixture', cached: true, connected: false, pipeline_count: 11 }
    };
    await page.route('**/api/**', route => {
      const url = new URL(route.request().url());
      const payload = url.pathname === '/api/context/enterprise-health' ? health :
        url.pathname === '/api/context/process-timeline' ? timeline : {};
      return route.fulfill({ json: payload, headers: { 'Access-Control-Allow-Origin': '*' } });
    });
    const origin = process.env.DCEL_UI_URL || 'http://127.0.0.1:5188';
    // Exercise the real components and API conversion with deterministic offline responses.
    await page.route(origin + '/', route => route.fulfill({ contentType: 'text/html', body: `
      <html><head><meta charset="utf-8"></head><body><div id="root"></div><script type="module">
        import RefreshRuntime from '/@react-refresh';
        RefreshRuntime.injectIntoGlobalHook(window);
        window.$RefreshReg$ = () => {};
        window.$RefreshSig$ = () => type => type;
        window.__vite_plugin_react_preamble_installed__ = true;
      </script><script type="module">
        import React from '/node_modules/.vite/deps/react.js';
        import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
        import { EnterpriseHealthBar } from '/src/components/EnterpriseHealthBar.tsx';
        import { SAPDataBadge } from '/src/components/SAPDataBadge.tsx';
        import { CelonisBadge } from '/src/components/CelonisBadge.tsx';
        import { ProcessTimelinePanel } from '/src/components/ProcessTimelinePanel.tsx';
        ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(React.Fragment, null,
          React.createElement(EnterpriseHealthBar), React.createElement(SAPDataBadge),
          React.createElement(CelonisBadge), React.createElement(ProcessTimelinePanel)));
      </script></body></html>` }));
    await page.goto(origin);
    await expect(page.getByTestId('enterprise-health')).toBeVisible();
    await expect(page.getByTestId('enterprise-system-sap-s-4hana')).toContainText('Cached');
    await expect(page.getByTestId('enterprise-system-celonis')).toContainText('Cached');
    await expect(page.getByText('SAP S/4HANA · 12 records · Cached', { exact: true })).toBeVisible();
    await expect(page.getByText('Celonis · Process Intelligence · 4 KPIs · Cached', { exact: true })).toBeVisible();
    await expect(page.getByTestId('process-timeline')).toContainText('Match Invoice to GR');
    await expect(page.getByTestId('process-timeline')).toContainText('Cached demo scenario');
    await expect(page.getByTestId('process-timeline')).toContainText('2,520 sec');
    assert.deepEqual(errors, []);
    console.log('PASS: enterprise health, SAP badge, Celonis badge, cached timeline; no page errors.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
