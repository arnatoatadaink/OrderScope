import assert from "node:assert/strict";
import test from "node:test";

import {
  D1_RETENTION_CONTRACT_REVISION,
  d1RetentionPolicy,
  evaluateD1PurgeEligibility,
  reviewedD1RetentionTables,
} from "./d1-retention.ts";

test("R0-006 retention contract revision and reviewed table set are frozen", () => {
  assert.equal(D1_RETENTION_CONTRACT_REVISION, "r0-006-v1");
  assert.deepEqual(reviewedD1RetentionTables(), [
    "acquisition_attempt",
    "acquisition_lease",
    "bar_acceptance_receipt",
    "bar_conflict",
    "coverage_checkpoint",
    "digest_history",
    "feature_state",
    "latest_digest",
    "news_article",
    "news_checkpoint",
    "news_query_membership",
    "normalized_bar",
    "scheduler_run",
    "scheduler_run_job",
  ]);
});

test("current control truth is never purge eligible", () => {
  for (const table of ["coverage_checkpoint", "news_checkpoint", "acquisition_lease", "latest_digest"]) {
    assert.equal(d1RetentionPolicy(table).authoritativeControlTruth, true);
    assert.deepEqual(
      evaluateD1PurgeEligibility(table, {
        custodyAcknowledged: true,
        qualityAccepted: true,
        replayHorizonElapsed: true,
        graceElapsed: true,
        resolved: true,
      }),
      { eligible: false, reasons: ["CURRENT_CONTROL_TRUTH"] },
    );
  }
});

test("hot data requires verified local custody, quality acceptance, and grace", () => {
  const incomplete = evaluateD1PurgeEligibility("normalized_bar", {});
  assert.equal(incomplete.eligible, false);
  assert.deepEqual(incomplete.reasons, [
    "CUSTODY_NOT_ACKNOWLEDGED",
    "QUALITY_NOT_ACCEPTED",
    "GRACE_NOT_ELAPSED",
  ]);
  assert.deepEqual(
    evaluateD1PurgeEligibility("normalized_bar", {
      custodyAcknowledged: true,
      qualityAccepted: true,
      graceElapsed: true,
    }),
    { eligible: true, reasons: [] },
  );
});

test("idempotency and operational evidence require replay horizon before purge", () => {
  for (const table of ["bar_acceptance_receipt", "acquisition_attempt", "digest_history", "scheduler_run_job"]) {
    const decision = evaluateD1PurgeEligibility(table, {
      custodyAcknowledged: true,
      qualityAccepted: true,
      graceElapsed: true,
    });
    assert.equal(decision.eligible, false);
    assert.deepEqual(decision.reasons, ["REPLAY_HORIZON_NOT_ELAPSED"]);
  }
});

test("unresolved blockers cannot purge until explicitly resolved", () => {
  assert.deepEqual(
    evaluateD1PurgeEligibility("bar_conflict", {
      custodyAcknowledged: true,
      qualityAccepted: true,
      replayHorizonElapsed: true,
      graceElapsed: true,
    }),
    { eligible: false, reasons: ["UNRESOLVED_BLOCKER"] },
  );
  assert.deepEqual(
    evaluateD1PurgeEligibility("bar_conflict", {
      custodyAcknowledged: true,
      qualityAccepted: true,
      replayHorizonElapsed: true,
      graceElapsed: true,
      resolved: true,
    }),
    { eligible: true, reasons: [] },
  );
});

test("unknown D1 tables fail closed until explicitly classified", () => {
  assert.throws(() => d1RetentionPolicy("future_table"), /unclassified D1 table/);
  assert.throws(() => evaluateD1PurgeEligibility("future_table", {}), /unclassified D1 table/);
});
