import assert from "node:assert/strict";
import test from "node:test";
import { fetchHistoricalBars } from "./alpaca.ts";

const instrument = { symbol: "SPY", cadence: "1Min" as const, providerRoute: "alpaca_stock_bars" as const };
const dailyInstrument = { ...instrument, cadence: "1Day" as const };

test("rejects malformed Alpaca bar payloads at the adapter boundary", async (context) => {
  context.mock.method(globalThis, "fetch", async () => new Response(JSON.stringify({
    bars: [{ t: "2026-08-28T14:30:00Z", o: "bad", h: 2, l: 1, c: 2, v: 1 }],
  }), { status: 200 }));
  await assert.rejects(fetchHistoricalBars({ keyId: "key", secretKey: "secret" }, {
    instrument, startInclusive: "2026-08-28T14:30:00Z", endExclusive: "2026-08-28T14:31:00Z",
  }), /invalid schema/);
});

test("preserves half-open filtering after runtime payload validation", async (context) => {
  context.mock.method(globalThis, "fetch", async () => new Response(JSON.stringify({ bars: [
    { t: "2026-08-28T14:30:00Z", o: 1, h: 2, l: 1, c: 2, v: 3 },
    { t: "2026-08-28T14:31:00Z", o: 2, h: 2, l: 2, c: 2, v: 1 },
  ] }), { status: 200 }));
  const result = await fetchHistoricalBars({ keyId: "key", secretKey: "secret" }, {
    instrument, startInclusive: "2026-08-28T14:30:00Z", endExclusive: "2026-08-28T14:31:00Z",
  });
  assert.equal(result.bars.length, 1);
  assert.equal(result.bars[0]?.timestamp, "2026-08-28T14:30:00Z");
});

test("keeps a daily bar timestamped at the New York market-date boundary", async (context) => {
  context.mock.method(globalThis, "fetch", async (input) => {
    const url = new URL(String(input));
    assert.equal(url.searchParams.get("timeframe"), "1Day");
    assert.equal(url.searchParams.get("start"), "2026-11-27T05:00:00.000Z");
    assert.equal(url.searchParams.get("end"), "2026-11-28T05:00:00.000Z");
    return new Response(JSON.stringify({ bars: [
      { t: "2026-11-27T05:00:00Z", o: 100, h: 104, l: 99, c: 102, v: 10 },
    ] }), { status: 200 });
  });
  const result = await fetchHistoricalBars({ keyId: "key", secretKey: "secret" }, {
    instrument: dailyInstrument,
    startInclusive: "2026-11-27T14:30:00.000Z",
    endExclusive: "2026-11-27T18:00:00.000Z",
  });
  assert.equal(result.bars.length, 1);
  assert.equal(result.bars[0]?.timestamp, "2026-11-27T05:00:00Z");
});

test("uses DST-safe New York date bounds for a summer daily request", async (context) => {
  context.mock.method(globalThis, "fetch", async (input) => {
    const url = new URL(String(input));
    assert.equal(url.searchParams.get("start"), "2026-08-28T04:00:00.000Z");
    assert.equal(url.searchParams.get("end"), "2026-08-29T04:00:00.000Z");
    return new Response(JSON.stringify({ bars: [] }), { status: 200 });
  });
  await fetchHistoricalBars({ keyId: "key", secretKey: "secret" }, {
    instrument: dailyInstrument,
    startInclusive: "2026-08-28T13:30:00.000Z",
    endExclusive: "2026-08-28T20:00:00.000Z",
  });
});

test("passes the returned pagination token on the next request", async (context) => {
  context.mock.method(globalThis, "fetch", async (input) => {
    const url = new URL(String(input));
    assert.equal(url.searchParams.get("page_token"), "opaque-next");
    return new Response(JSON.stringify({ bars: [], next_page_token: null }), { status: 200 });
  });
  const result = await fetchHistoricalBars({ keyId: "key", secretKey: "secret" }, {
    instrument,
    startInclusive: "2026-08-28T14:30:00Z",
    endExclusive: "2026-08-28T14:31:00Z",
    pageToken: "opaque-next",
  });
  assert.equal(result.nextPageToken, undefined);
});

test("retries 429 using a bounded Retry-After delay", async (context) => {
  let calls = 0;
  const delays: number[] = [];
  context.mock.method(globalThis, "fetch", async () => {
    calls += 1;
    return calls === 1
      ? new Response(null, { status: 429, headers: { "retry-after": "30" } })
      : new Response(JSON.stringify({ bars: [] }), { status: 200 });
  });
  await fetchHistoricalBars({ keyId: "key", secretKey: "secret" }, {
    instrument, startInclusive: "2026-08-28T14:30:00Z", endExclusive: "2026-08-28T14:31:00Z",
  }, {
    retry: { maxAttempts: 3, baseBackoffMs: 250, maxBackoffMs: 2000, maxRetryAfterMs: 5000 },
    sleep: async (delay) => { delays.push(delay); },
  });
  assert.equal(calls, 2);
  assert.deepEqual(delays, [5000]);
});

test("retries transient 5xx with capped exponential backoff", async (context) => {
  const delays: number[] = [];
  let calls = 0;
  context.mock.method(globalThis, "fetch", async () => {
    calls += 1;
    return calls < 3 ? new Response(null, { status: 503 }) : new Response(JSON.stringify({ bars: [] }));
  });
  await fetchHistoricalBars({ keyId: "key", secretKey: "secret" }, {
    instrument, startInclusive: "2026-08-28T14:30:00Z", endExclusive: "2026-08-28T14:31:00Z",
  }, {
    retry: { maxAttempts: 3, baseBackoffMs: 1500, maxBackoffMs: 2000, maxRetryAfterMs: 5000 },
    sleep: async (delay) => { delays.push(delay); },
  });
  assert.deepEqual(delays, [1500, 2000]);
});

test("reports retry exhaustion after the configured attempt cap", async (context) => {
  let calls = 0;
  context.mock.method(globalThis, "fetch", async () => { calls += 1; return new Response(null, { status: 500 }); });
  await assert.rejects(fetchHistoricalBars({ keyId: "key", secretKey: "secret" }, {
    instrument, startInclusive: "2026-08-28T14:30:00Z", endExclusive: "2026-08-28T14:31:00Z",
  }, {
    retry: { maxAttempts: 2, baseBackoffMs: 0, maxBackoffMs: 0, maxRetryAfterMs: 0 }, sleep: async () => {},
  }), /500 after 2 attempts/);
  assert.equal(calls, 2);
});

test("does not retry non-transient provider errors", async (context) => {
  let calls = 0;
  context.mock.method(globalThis, "fetch", async () => { calls += 1; return new Response(null, { status: 401 }); });
  await assert.rejects(fetchHistoricalBars({ keyId: "key", secretKey: "secret" }, {
    instrument, startInclusive: "2026-08-28T14:30:00Z", endExclusive: "2026-08-28T14:31:00Z",
  }, {
    retry: { maxAttempts: 3, baseBackoffMs: 0, maxBackoffMs: 0, maxRetryAfterMs: 0 }, sleep: async () => {},
  }), /failed: 401/);
  assert.equal(calls, 1);
});
