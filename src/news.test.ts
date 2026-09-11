import assert from "node:assert/strict";
import test from "node:test";
import { NewsProviderError, fetchNewsPage, normalizeNewsPayload } from "./news.ts";

test("normalizes symbols and discards provider body members", () => {
  const page = normalizeNewsPayload({ news: [{ id: 123, headline: " Headline ", author: "Publisher", url: "https://example.test/123",
    created_at: "2026-09-10T14:00:00Z", updated_at: "2026-09-10T14:01:00Z", symbols: [" AMD ", "NVDA", "AMD"],
    content: "must not cross boundary", summary: "must not cross boundary" }] });
  assert.deepEqual(page.articles[0]?.providerSymbols, ["AMD", "NVDA"]);
  assert.equal(JSON.stringify(page).includes("must not cross boundary"), false);
  assert.equal("content" in (page.articles[0] as unknown as Record<string, unknown>), false);
});
test("fails closed on structurally invalid metadata", () => {
  assert.throws(() => normalizeNewsPayload({ news: [{ id: 1, headline: "x" }] }), NewsProviderError);
});
test("429 failure is retryable and sanitized", async (t) => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => new Response("secret header/body", { status: 429 });
  t.after(() => { globalThis.fetch = original; });
  await assert.rejects(fetchNewsPage({ keyId: "credential-key", secretKey: "credential-secret" }, {
    symbol: "AMD", startInclusive: "2026-09-10T13:00:00Z", endExclusive: "2026-09-10T14:00:00Z",
  }), (error: unknown) => error instanceof NewsProviderError && error.retryable
    && !error.message.includes("credential") && !error.message.includes("secret header"));
});
test("401 is classified as non-retryable authentication failure", async (t) => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => new Response("credential detail must not escape", { status: 401 });
  t.after(() => { globalThis.fetch = original; });
  await assert.rejects(fetchNewsPage({ keyId: "credential-key", secretKey: "credential-secret" }, {
    symbol: "AMD", startInclusive: "2026-09-10T13:00:00Z", endExclusive: "2026-09-10T14:00:00Z",
  }), (error: unknown) => error instanceof NewsProviderError
    && error.category === "AUTHENTICATION" && error.retryable === false
    && !error.message.includes("credential-key") && !error.message.includes("credential detail"));
});
test("403 is classified as non-retryable authorization failure", async (t) => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => new Response("authorization body must not escape", { status: 403 });
  t.after(() => { globalThis.fetch = original; });
  await assert.rejects(fetchNewsPage({ keyId: "key", secretKey: "secret" }, {
    symbol: "NVDA", startInclusive: "2026-09-10T13:00:00Z", endExclusive: "2026-09-10T14:00:00Z",
  }), (error: unknown) => error instanceof NewsProviderError
    && error.category === "AUTHORIZATION" && error.retryable === false
    && !error.message.includes("authorization body"));
});
test("transport failure is retryable and exposes only a typed category", async (t) => {
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {
    calls += 1;
    throw new TypeError("socket detail with credential-secret");
  };
  t.after(() => { globalThis.fetch = original; });
  const delays: number[] = [];
  await assert.rejects(fetchNewsPage({ keyId: "key", secretKey: "credential-secret" }, {
    symbol: "AMD", startInclusive: "2026-09-10T13:00:00Z", endExclusive: "2026-09-10T14:00:00Z",
  }, {
    retry: { maxAttempts: 2, baseBackoffMs: 10, maxBackoffMs: 100, maxRetryAfterMs: 5_000 },
    sleep: async (ms) => { delays.push(ms); },
  }), (error: unknown) => error instanceof NewsProviderError
    && error.category === "TRANSPORT" && error.retryable === true
    && !error.message.includes("socket detail") && !error.message.includes("credential-secret"));
  assert.equal(calls, 2);
  assert.deepEqual(delays, [10]);
});
test("429 retry honors and caps Retry-After metadata", async (t) => {
  const original = globalThis.fetch; let calls = 0; const delays: number[] = [];
  globalThis.fetch = async () => ++calls === 1
    ? new Response(null, { status: 429, headers: { "Retry-After": "30" } })
    : Response.json({ news: [] });
  t.after(() => { globalThis.fetch = original; });
  await fetchNewsPage({ keyId: "key", secretKey: "secret" }, {
    symbol: "AMD", startInclusive: "2026-09-10T13:00:00Z", endExclusive: "2026-09-10T14:00:00Z",
  }, { retry: { maxAttempts: 2, baseBackoffMs: 10, maxBackoffMs: 100, maxRetryAfterMs: 5_000 },
    sleep: async (ms) => { delays.push(ms); } });
  assert.deepEqual(delays, [5_000]);
});
