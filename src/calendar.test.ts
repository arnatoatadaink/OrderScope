import assert from "node:assert/strict";
import test from "node:test";
import { AlpacaMarketCalendarProvider, sessionAt } from "./calendar.ts";

function provider(
  payload: unknown,
  inspect?: (request: Request) => void,
  includePremarket = false,
): AlpacaMarketCalendarProvider {
  return new AlpacaMarketCalendarProvider({
    credentials: { keyId: "test-key", secretKey: "test-secret" },
    now: () => new Date("2026-08-29T00:00:00Z"),
    fetcher: async (input, init) => {
      const request = new Request(input, init);
      inspect?.(request);
      return Response.json(payload);
    },
    includePremarket,
  });
}

test("normalizes Alpaca regular sessions to UTC across DST", async () => {
  const snapshot = await provider([
    { date: "2026-01-05", open: "09:30", close: "16:00" },
    { date: "2026-07-06", open: "09:30", close: "16:00" },
  ]).getCalendar("2026-01-01", "2026-07-07");

  assert.equal(snapshot.sessions[0]?.opensAt, "2026-01-05T14:30:00.000Z");
  assert.equal(snapshot.sessions[1]?.opensAt, "2026-07-06T13:30:00.000Z");
  assert.equal(snapshot.sessions[0]?.isShortened, false);
  assert.equal(snapshot.sessions[0]?.calendarRevision, snapshot.revision);
});

test("converts the Core end date to Alpaca's inclusive end parameter", async () => {
  await provider([], (request) => {
    assert.equal(request.url, "https://paper-api.alpaca.markets/v2/calendar?start=2026-08-01&end=2026-08-02");
    assert.equal(request.headers.get("APCA-API-KEY-ID"), "test-key");
  }).getCalendar("2026-08-01", "2026-08-03");
});

test("invokes a receiver-sensitive fetcher without binding it to the provider", async () => {
  const fetcher = async function (this: unknown, input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    assert.equal(this, undefined);
    const request = new Request(input, init);
    assert.equal(request.url, "https://paper-api.alpaca.markets/v2/calendar?start=2026-08-01&end=2026-08-01");
    return Response.json([]);
  };
  const calendar = new AlpacaMarketCalendarProvider({
    credentials: { keyId: "test-key", secretKey: "test-secret" },
    fetcher,
  });

  await calendar.getCalendar("2026-08-01", "2026-08-02");
});

test("keeps holidays absent and marks shortened sessions", async () => {
  const snapshot = await provider([
    { date: "2026-11-27", open: "09:30", close: "13:00" },
  ]).getCalendar("2026-11-26", "2026-11-28");

  assert.equal(snapshot.sessions.length, 1);
  assert.equal(snapshot.sessions[0]?.marketDate, "2026-11-27");
  assert.equal(snapshot.sessions[0]?.isShortened, true);
  assert.equal(sessionAt(snapshot, new Date("2026-11-27T17:59:59Z"))?.sessionKind, "REGULAR");
  assert.equal(sessionAt(snapshot, new Date("2026-11-27T18:00:00Z")), undefined);
});

test("derives Premarket only for authoritative trading dates across DST", async () => {
  const snapshot = await provider([
    { date: "2026-01-05", open: "09:30", close: "16:00" },
    { date: "2026-07-06", open: "09:30", close: "16:00" },
  ], undefined, true).getCalendar("2026-01-01", "2026-07-07");

  assert.deepEqual(snapshot.sessions.map((session) => ({
    date: session.marketDate,
    kind: session.sessionKind,
    opensAt: session.opensAt,
    closesAt: session.closesAt,
  })), [
    { date: "2026-01-05", kind: "PREMARKET", opensAt: "2026-01-05T09:00:00.000Z", closesAt: "2026-01-05T14:30:00.000Z" },
    { date: "2026-01-05", kind: "REGULAR", opensAt: "2026-01-05T14:30:00.000Z", closesAt: "2026-01-05T21:00:00.000Z" },
    { date: "2026-07-06", kind: "PREMARKET", opensAt: "2026-07-06T08:00:00.000Z", closesAt: "2026-07-06T13:30:00.000Z" },
    { date: "2026-07-06", kind: "REGULAR", opensAt: "2026-07-06T13:30:00.000Z", closesAt: "2026-07-06T20:00:00.000Z" },
  ]);
  assert.equal(sessionAt(snapshot, new Date("2026-07-06T12:00:00Z"))?.sessionKind, "PREMARKET");
  assert.equal(new Set(snapshot.sessions.map((session) => session.calendarRevision)).size, 1);
});

test("keeps the default calendar Regular-only", async () => {
  const regularOnly = await provider([
    { date: "2026-07-06", open: "09:30", close: "16:00" },
  ]).getCalendar("2026-07-06", "2026-07-07");
  const withPremarket = await provider([
    { date: "2026-07-06", open: "09:30", close: "16:00" },
  ], undefined, true).getCalendar("2026-07-06", "2026-07-07");

  assert.deepEqual(regularOnly.sessions.map((session) => session.sessionKind), ["REGULAR"]);
  assert.notEqual(regularOnly.revision, withPremarket.revision);
});

test("rejects malformed or out-of-range provider data", async () => {
  await assert.rejects(
    provider([{ date: "2026-08-03", open: "bad", close: "16:00" }]).getCalendar("2026-08-03", "2026-08-04"),
    /invalid schema/,
  );
  await assert.rejects(
    provider([{ date: "2026-08-05", open: "09:30", close: "16:00" }]).getCalendar("2026-08-03", "2026-08-04"),
    /out-of-range/,
  );
});
