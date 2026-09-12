import assert from "node:assert/strict";
import test from "node:test";

import {
  advanceD1DrainLifecycle,
  createD1DrainRecord,
  type D1DrainRecord,
} from "./d1-drain-lifecycle.ts";

function record(table = "normalized_bar", options: { replay?: boolean; resolved?: boolean } = {}): D1DrainRecord {
  return createD1DrainRecord({
    generationId: "d1-custody-" + "a".repeat(64),
    table,
    windowStart: "2026-09-10T00:00:00.000Z",
    windowEnd: "2026-09-11T00:00:00.000Z",
    replayHorizonElapsed: options.replay,
    resolved: options.resolved,
  });
}

function advanceThroughGrace(current: D1DrainRecord, evidence = {}) {
  current = advanceD1DrainLifecycle(current, "EXPORTED");
  current = advanceD1DrainLifecycle(current, "HASH_VERIFIED");
  current = advanceD1DrainLifecycle(current, "IMPORTED");
  current = advanceD1DrainLifecycle(current, "QUALITY_ACCEPTED");
  current = advanceD1DrainLifecycle(current, "ACKNOWLEDGED");
  current = advanceD1DrainLifecycle(current, "GRACE", evidence);
  return current;
}

test("hot data reaches PURGE_ELIGIBLE only after custody quality and grace", () => {
  let current = record();
  current = advanceThroughGrace(current, { graceElapsed: true });
  current = advanceD1DrainLifecycle(current, "PURGE_ELIGIBLE");
  assert.equal(current.state, "PURGE_ELIGIBLE");
  assert.equal(current.custodyAcknowledged, true);
  assert.equal(current.qualityAccepted, true);
  assert.equal(current.graceElapsed, true);
});

test("lifecycle rejects skipped or reverse transitions", () => {
  const current = record();
  assert.throws(() => advanceD1DrainLifecycle(current, "HASH_VERIFIED"), /invalid D1 drain transition/);
  const exported = advanceD1DrainLifecycle(current, "EXPORTED");
  assert.throws(() => advanceD1DrainLifecycle(exported, "PLANNED"), /invalid D1 drain transition/);
});

test("idempotency evidence requires replay horizon before purge eligibility", () => {
  let current = record("bar_acceptance_receipt");
  current = advanceThroughGrace(current, { graceElapsed: true });
  assert.throws(() => advanceD1DrainLifecycle(current, "PURGE_ELIGIBLE"), /REPLAY_HORIZON_NOT_ELAPSED/);
  current = { ...current, replayHorizonElapsed: true };
  current = advanceD1DrainLifecycle(current, "PURGE_ELIGIBLE");
  assert.equal(current.state, "PURGE_ELIGIBLE");
});

test("unresolved conflict cannot become purge eligible", () => {
  let current = record("bar_conflict", { replay: true });
  current = advanceThroughGrace(current, { graceElapsed: true });
  assert.throws(() => advanceD1DrainLifecycle(current, "PURGE_ELIGIBLE"), /UNRESOLVED_BLOCKER/);
  current = { ...current, resolved: true };
  current = advanceD1DrainLifecycle(current, "PURGE_ELIGIBLE");
  assert.equal(current.state, "PURGE_ELIGIBLE");
});

test("current control truth never reaches purge eligibility", () => {
  let current = record("coverage_checkpoint", { replay: true, resolved: true });
  current = advanceThroughGrace(current, { graceElapsed: true });
  assert.throws(() => advanceD1DrainLifecycle(current, "PURGE_ELIGIBLE"), /CURRENT_CONTROL_TRUTH/);
});

test("PURGED is blocked without separately authorized remote mutation evidence", () => {
  let current = record();
  current = advanceThroughGrace(current, { graceElapsed: true });
  current = advanceD1DrainLifecycle(current, "PURGE_ELIGIBLE");
  assert.throws(() => advanceD1DrainLifecycle(current, "PURGED"), /separately authorized remote mutation/);
});

test("drain record validates custody identity and half-open UTC window", () => {
  assert.throws(() => createD1DrainRecord({
    generationId: "bad",
    table: "normalized_bar",
    windowStart: "2026-09-10T00:00:00.000Z",
    windowEnd: "2026-09-11T00:00:00.000Z",
  }), /reviewed D1 custody/);
  assert.throws(() => createD1DrainRecord({
    generationId: "d1-custody-" + "a".repeat(64),
    table: "normalized_bar",
    windowStart: "2026-09-11T00:00:00.000Z",
    windowEnd: "2026-09-10T00:00:00.000Z",
  }), /non-empty and half-open/);
});
