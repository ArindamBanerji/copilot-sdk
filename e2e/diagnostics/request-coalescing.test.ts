import assert from "node:assert/strict";
import { createServer, type ServerResponse } from "node:http";
import { test } from "node:test";
import { coalesceRead, withReadInvalidation } from "../../copilot_sdk/frontend/requestCoalescing";

test("overlapping HTTP reads share work; completed and failed reads are not cached", async () => {
  let hits = 0;
  const server = createServer((request, response) => {
    hits++;
    response.writeHead(request.url === "/error" ? 503 : 200, { "Content-Type": "application/json" });
    setTimeout(() => response.end(JSON.stringify({ hits })), 15);
  });
  await new Promise<void>(resolve => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert(address && typeof address !== "string");
  const base = `http://127.0.0.1:${address.port}`;
  const read = (path: string) => coalesceRead(base + path, async () => {
    const response = await fetch(base + path);
    if (!response.ok) throw new Error(String(response.status));
    return response.json();
  });
  try {
    const values = await Promise.all(Array.from({ length: 12 }, () => read("/value")));
    assert.equal(hits, 1);
    assert(values.every(value => value.hits === 1));
    await read("/value");
    assert.equal(hits, 2);
    const failures = await Promise.allSettled([read("/error"), read("/error")]);
    assert(failures.every(value => value.status === "rejected"));
    assert.equal(hits, 3);
    await assert.rejects(read("/error"));
    assert.equal(hits, 4);
  } finally {
    server.closeAllConnections();
    await new Promise<void>(resolve => server.close(() => resolve()));
  }
});

test("a mutation separates pending reads, including late completion of an older read", async () => {
  const held: ServerResponse[] = [];
  const server = createServer((request, response) => {
    if (request.method === "POST") response.end("written");
    else held.push(response);
  });
  await new Promise<void>(resolve => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert(address && typeof address !== "string");
  const url = `http://127.0.0.1:${address.port}`;
  const read = () => coalesceRead(url, async () => (await fetch(url)).text());
  const waitForRequests = async (count: number) => {
    const deadline = Date.now() + 2000;
    while (held.length < count && Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 5));
    assert.equal(held.length, count);
  };
  try {
    const before = read();
    await waitForRequests(1);
    await withReadInvalidation(async () => { await (await fetch(url, { method: "POST" })).text(); });
    const after = read();
    await waitForRequests(2);
    held[0].end("old");
    assert.equal(await before, "old");
    const joined = read();
    held[1].end("new");
    assert.deepEqual(await Promise.all([after, joined]), ["new", "new"]);
    assert.equal(held.length, 2);
  } finally {
    for (const response of held) response.end();
    server.closeAllConnections();
    await new Promise<void>(resolve => server.close(() => resolve()));
  }
});
