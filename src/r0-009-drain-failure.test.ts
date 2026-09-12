import assert from "node:assert/strict";
import test from "node:test";

import { budgetedD1 } from "./budgeted-d1.ts";
import {
  advanceD1DrainLifecycle,
  createD1DrainRecord,
} from "./d1-drain-lifecycle.ts";
import { evaluateD1PurgeEligibility } from "./d1-retention.ts";
import { InvocationBudget } from "./invocation-budget.ts";

function drain(table = "normalized_bar") {
  return createD1DrainRecord({
    generationId: "d1-custody-" + "a".repeat(64),
    table,
    windowStart: "2026-09-10T00:00:00.000Z",
    windowEnd: "2026-09-11T00:00:00.000Z",
  });
}

function throughImported() {
  let current = drain();
  current = advanceD1DrainLifecycle(current, "EXPORTED");
  current = advanceD1DrainLifecycle(current, "HASH_VERIFIED");
  current = advanceD1DrainLifecycle(current, "IMPORTED");
  return current;
}

test("quality block prevents acknowledgement and purge eligibility", () => {
  const current = throughImported();
  assert.equal(current.state, "IMPORTED");
  assert.throws(
    () => advanceD1DrainLifecycle(current, "ACKNOWLEDGED"),
    /invalid D1 drain transition/,
  );
  const decision = evaluateD1PurgeEligibility("normalized_bar", {
    custodyAcknowledged: false,
    qualityAccepted: false,
    graceElapsed: true,
  });
  assert.equal(decision.eligible, false);
  assert.deepEqual(decision.reasons, ["CUSTODY_NOT_ACKNOWLEDGED", "QUALITY_NOT_ACCEPTED"]);
});

test("checkpoint/control truth stays protected even with all purge evidence", () => {
  const decision = evaluateD1PurgeEligibility("coverage_checkpoint", {
    custodyAcknowledged: true,
    qualityAccepted: true,
    replayHorizonElapsed: true,
    graceElapsed: true,
    resolved: true,
  });
  assert.deepEqual(decision, { eligible: false, reasons: ["CURRENT_CONTROL_TRUTH"] });
});

test("failed purge attempt can be retried without changing lifecycle truth", () => {
  let current = drain();
  current = advanceD1DrainLifecycle(current, "EXPORTED");
  current = advanceD1DrainLifecycle(current, "HASH_VERIFIED");
  current = advanceD1DrainLifecycle(current, "IMPORTED");
  current = advanceD1DrainLifecycle(current, "QUALITY_ACCEPTED");
  current = advanceD1DrainLifecycle(current, "ACKNOWLEDGED");
  current = advanceD1DrainLifecycle(current, "GRACE", { graceElapsed: true });
  current = advanceD1DrainLifecycle(current, "PURGE_ELIGIBLE");

  assert.equal(current.state, "PURGE_ELIGIBLE");
  assert.throws(
    () => advanceD1DrainLifecycle(current, "PURGED"),
    /separately authorized remote mutation/,
  );
  assert.equal(current.state, "PURGE_ELIGIBLE");
  assert.throws(
    () => advanceD1DrainLifecycle(current, "PURGED"),
    /separately authorized remote mutation/,
  );
});

test("D1 budget fails closed before issuing a statement beyond the ceiling", async () => {
  let executions = 0;
  const statement = {
    bind: () => statement,
    run: async () => { executions += 1; return { success: true }; },
  } as unknown as D1PreparedStatement;
  const db = {
    prepare: () => statement,
  } as unknown as D1Database;
  const budget = new InvocationBudget(40, 1);
  const wrapped = budgetedD1(db, budget);

  await wrapped.prepare("SELECT 1").run();
  assert.equal(executions, 1);
  assert.equal(budget.snapshot().d1Queries, 1);

  await assert.rejects(
    async () => wrapped.prepare("SELECT 2").run(),
    /D1_BUDGET/,
  );
  assert.equal(executions, 1);
  assert.equal(budget.snapshot().d1Queries, 1);
});
