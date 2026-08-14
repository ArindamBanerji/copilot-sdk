import { test, expect, PORTS, apiGet, type JsonRecord } from "./demo-fixture";

const SDK_COPILOTS = ["trading", "purchasing", "dataops", "s2p"] as const;

function hasField(value: JsonRecord, field: string): boolean {
  return Object.prototype.hasOwnProperty.call(value, field);
}

test.describe.serial("VC Cut — Measurement Spine (V1-V7)", () => {
  test.beforeEach(async ({ demoReady }) => {
    test.skip(!demoReady, "Demo cut skipped: backends must be healthy and preseeded (IKS > 0)");
  });

  for (const copilot of SDK_COPILOTS) {
    test.describe.serial(copilot, () => {
      const backend = PORTS[copilot].backend;

      test(`V1: ${copilot} diagnostics returns convergence and IKS`, async () => {
        const diagnostics = await apiGet(backend, "/api/self/diagnostics");
        expect(diagnostics.epsilon_firm).toBeDefined();
        expect(diagnostics.iks ?? diagnostics.iks_score).toBeGreaterThan(0);
        expect(diagnostics.measurement_state).toBeTruthy();
      });

      test(`V2: ${copilot} conservation status is observable`, async () => {
        const conservation = await apiGet(backend, "/api/conservation/status");
        expect(conservation.verified_count ?? conservation.verified ?? conservation.total_verified).toBeDefined();
        expect(conservation.q ?? conservation.conservation_q).toBeDefined();
        expect(conservation.theta_min).toBeDefined();
        expect(conservation.status).toBeTruthy();
      });

      test(`V3: ${copilot} evolution summary has schema version`, async () => {
        const evolution = await apiGet(backend, "/api/self/evolution/summary");
        expect(evolution.schema_version ?? evolution.version).toBeDefined();
        expect(evolution.recent_events).toBeDefined();
      });

      test(`V4: ${copilot} centroid history has timestamped checkpoints`, async () => {
        const history = await apiGet(backend, "/api/self/centroid-history?limit=5");
        const checkpoints = history.checkpoints ?? history.history ?? history;
        expect(Array.isArray(checkpoints)).toBe(true);
        expect(checkpoints).not.toHaveLength(0);
        for (const checkpoint of checkpoints as JsonRecord[]) {
          expect(checkpoint.created_at ?? checkpoint.timestamp ?? checkpoint.ts).toBeDefined();
        }
      });

      test(`V5: ${copilot} transfer status is discoverable`, async () => {
        const transfers = await apiGet(backend, "/api/transfer/status");
        expect(Object.keys(transfers)).not.toHaveLength(0);
        expect(transfers.warm_started).toBeDefined();
      });

      test(`V6: ${copilot} health exposes hot-path telemetry`, async () => {
        const health = await apiGet(backend, "/health");
        expect(health.status ?? health.healthy ?? health.service).toBeTruthy();
        if (copilot === "s2p") {
          expect(health.version).toBeDefined();
        } else {
          expect(hasField(health, "cache_hits")).toBe(true);
          expect(hasField(health, "cache_misses")).toBe(true);
          expect(hasField(health, "cache_size")).toBe(true);
        }
      });

      test(`V7: ${copilot} conservation state is consistent and explainable`, async () => {
        const conservation = await apiGet(backend, "/api/conservation/status");
        expect(conservation.status).toMatch(/GREEN|AMBER|RED/i);
        expect(conservation.reason).toBeTruthy();
        expect(conservation.q ?? conservation.conservation_q).toBeDefined();
        expect(conservation.theta_min).toBeDefined();
        expect(conservation.passed).toBeDefined();
      });
    });
  }
});
