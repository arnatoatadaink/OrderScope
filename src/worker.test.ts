import assert from "node:assert/strict";
import test from "node:test";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { gapRetryEligibility } from "./gap-retry.ts";

const partial: StoredCoverageCheckpoint = {
  coverageKey: "BTCUSD|1Min|ALL_TRADING|crypto:us",
  symbol: "BTC/USD",
  interval: "1Min",
  sessionScope: "ALL_TRADING",
  logicalDataVariant: "crypto:us",
  completeThrough: "2026-08-29T16:28:00.000Z",
  state: "PARTIAL",
  missingRanges: [{
    startInclusive: "2026-08-29T16:28:00.000Z",
    endExclusive: "2026-08-29T16:29:00.000Z",
  }],
  lastAttemptAt: "2026-08-30T15:16:00.000Z",
  retryNotBefore: "2026-08-30T15:31:00.000Z",
  version: 2,
};

test("defers a known partial gap until its durable retry eligibility time", () => {
  assert.deepEqual(gapRetryEligibility(partial, new Date("2026-08-30T15:17:00.000Z"), 15), {
    coverageKey: partial.coverageKey,
    retryEligibleAt: "2026-08-30T15:31:00.000Z",
  });
  assert.equal(gapRetryEligibility(partial, new Date("2026-08-30T15:31:00.000Z"), 15), undefined);
});

test("does not defer complete, newly discovered, or malformed checkpoints", () => {
  assert.equal(gapRetryEligibility({ ...partial, state: "COMPLETE", missingRanges: [] }, new Date(), 15), undefined);
  assert.equal(gapRetryEligibility({ ...partial, retryNotBefore: undefined }, new Date(), 15), undefined);
  assert.equal(gapRetryEligibility({ ...partial, retryNotBefore: "invalid" }, new Date(), 15), undefined);
});
