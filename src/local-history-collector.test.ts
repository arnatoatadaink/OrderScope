import assert from "node:assert/strict";
import test from "node:test";
import type { ProviderNeutralBar } from "./alpaca.ts";
import { planRegularSession, validateRegularSession } from "./local-history-collector.ts";

function bar(timestamp: string): ProviderNeutralBar {
  return {
    symbol: "NVDA",
    timestamp,
    open: 1,
    high: 1,
    low: 1,
    close: 1,
    volume: 1,
    provider: "alpaca",
    dataVariant: "stock:iex:raw",
  };
}

test("plans September Regular session in UTC", () => {
  assert.deepEqual(planRegularSession("2026-09-09"), {
    marketDate: "2026-09-09",
    startInclusive: "2026-09-09T13:30:00.000Z",
    endExclusive: "2026-09-09T20:00:00.000Z",
    expectedBars: 390,
  });
});

test("plans winter Regular session with EST offset", () => {
  assert.deepEqual(planRegularSession("2026-12-01"), {
    marketDate: "2026-12-01",
    startInclusive: "2026-12-01T14:30:00.000Z",
    endExclusive: "2026-12-01T21:00:00.000Z",
    expectedBars: 390,
  });
});

test("accepts exactly one unique bar per Regular minute", () => {
  const plan = planRegularSession("2026-09-09");
  const bars = Array.from({ length: 390 }, (_, index) =>
    bar(new Date(Date.parse(plan.startInclusive) + index * 60_000).toISOString()));
  const result = validateRegularSession(plan, bars);
  assert.equal(result.denseSession, true);
  assert.equal(result.structurallyValid, true);
  assert.equal(result.actualBars, 390);
  assert.deepEqual(result.duplicateTimestamps, []);
  assert.deepEqual(result.outOfRangeTimestamps, []);
});

test("fails closed on missing, duplicate, or out-of-range bars", () => {
  const plan = planRegularSession("2026-09-09");
  const bars = [
    bar(plan.startInclusive),
    bar(plan.startInclusive),
    bar(plan.endExclusive),
  ];
  const result = validateRegularSession(plan, bars);
  assert.equal(result.denseSession, false);
  assert.equal(result.structurallyValid, false);
  assert.equal(result.actualBars, 3);
  assert.equal(result.duplicateTimestamps.length, 1);
  assert.equal(result.outOfRangeTimestamps.length, 1);
});


test("accepts sparse provider session as structurally valid without pretending it is dense", () => {
  const plan = planRegularSession("2026-09-11");
  const missing = "2026-09-11T16:57:00.000Z";
  const bars = Array.from({ length: 390 }, (_, index) =>
    bar(new Date(Date.parse(plan.startInclusive) + index * 60_000).toISOString()))
    .filter((item) => Date.parse(item.timestamp) !== Date.parse(missing));
  const result = validateRegularSession(plan, bars);
  assert.equal(result.actualBars, 389);
  assert.equal(result.denseSession, false);
  assert.equal(result.structurallyValid, true);
  assert.deepEqual(result.missingTimestamps, [missing]);
});
