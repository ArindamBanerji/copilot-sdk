import { test, expect } from "@playwright/test";
const API = "http://127.0.0.1:8010";
test("TRD-02 throttle", async ({ request }) => {
  const response = await request.get(API + "/api/trading/regime-status");
  test.skip(!response.ok(), `Regime status returned ${response.status()}`);
  const body = await response.json();
  test.skip(!body.regime_break_active, "TRD-02 requires an active seeded regime break");
  expect(body.current_regime).toBe("volatile");
  expect(body.previous_regime).toBeTruthy();
  expect(body.previous_regime).not.toBe(body.current_regime);
  expect(body.autonomy_level).toBe("restricted");
  expect(body.decisions_in_new_regime).toBeGreaterThan(0);
  expect(body.restrictions.length).toBeGreaterThan(0);
  expect(body.decisions_in_new_regime).toBeLessThan(body.decisions_to_stabilize);
});
