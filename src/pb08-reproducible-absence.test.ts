import assert from "node:assert/strict";
import test from "node:test";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import {
  acknowledgedPb08Checkpoint,
  matchesPb08ReproducibleAbsence,
  PB08_REPRODUCIBLE_ABSENCES,
} from "./pb08-reproducible-absence.ts";

function checkpoint(symbol: "AMD" | "QQQ"): StoredCoverageCheckpoint {
  const spec = PB08_REPRODUCIBLE_ABSENCES.find((item) => item.symbol === symbol)!;
  return {
    coverageKey: spec.coverageKey,
    symbol,
    interval: "1Min",
    sessionScope: "REGULAR",
    logicalDataVariant: "stock:iex:raw",
    completeThrough: spec.expectedCompleteThrough,
    sourceObservedThrough: spec.expectedSourceObservedThrough,
    state: "PARTIAL",
    missingRanges: [{
      startInclusive: spec.missingStart,
      endExclusive: spec.missingEnd,
    }],
    lastAttemptAt: "2026-09-25T06:32:52.000Z",
    retryNotBefore: "2026-09-25T06:47:52.000Z",
    universeRevision: "stock-monitoring-canary-v0.1",
    version: spec.expectedVersion,
  };
}

test("recognizes only the frozen AMD and QQQ reproduced gap checkpoints", () => {
  for (const spec of PB08_REPRODUCIBLE_ABSENCES) {
    assert.equal(matchesPb08ReproducibleAbsence(checkpoint(spec.symbol), spec), true);
  }

  const amdSpec = PB08_REPRODUCIBLE_ABSENCES[0]!;
  assert.equal(matchesPb08ReproducibleAbsence({
    ...checkpoint("AMD"),
    version: amdSpec.expectedVersion + 1,
  }, amdSpec), false);
  assert.equal(matchesPb08ReproducibleAbsence({
    ...checkpoint("AMD"),
    missingRanges: [],
  }, amdSpec), false);
});

test("acknowledgement advances only through the reproduced absent minute", () => {
  const at = "2026-09-25T07:00:00.000Z";
  for (const spec of PB08_REPRODUCIBLE_ABSENCES) {
    const before = checkpoint(spec.symbol);
    const after = acknowledgedPb08Checkpoint(before, spec, at);
    assert.equal(after.completeThrough, spec.expectedSourceObservedThrough);
    assert.equal(after.sourceObservedThrough, spec.expectedSourceObservedThrough);
    assert.equal(after.state, "COMPLETE");
    assert.deepEqual(after.missingRanges, []);
    assert.equal(after.lastSuccessAt, at);
    assert.equal(after.retryNotBefore, undefined);
    assert.equal(after.version, before.version);
  }
});

test("acknowledgement rejects non-canonical timestamps and checkpoint drift", () => {
  const spec = PB08_REPRODUCIBLE_ABSENCES[0]!;
  assert.throws(() => acknowledgedPb08Checkpoint(checkpoint("AMD"), spec, "2026-09-25T07:00:00Z"));
  assert.throws(() => acknowledgedPb08Checkpoint({
    ...checkpoint("AMD"),
    completeThrough: "2026-09-24T14:48:00.000Z",
  }, spec, "2026-09-25T07:00:00.000Z"));
});
