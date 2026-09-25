import { expect, test } from "@playwright/test";

test("AGE graph health contract is ready", async ({ request }) => {
  const response = await request.get("/health");
  expect([200, 503]).toContain(response.status());
  const body = await response.json();
  expect(body.graph_backend).toBe("age");
  expect(body.graph_name).toBe("soc_graph");
  expect(body.graph_status).toHaveProperty("components");
  if (response.status() === 200) {
    expect(body.ready).toBe(true);
    expect(body.graph_connected).toBe(true);
  }
});
