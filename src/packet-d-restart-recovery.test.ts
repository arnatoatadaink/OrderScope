import assert from "node:assert/strict";
import test from "node:test";
import { decideRestartBoundary } from "./restart-recovery.ts";

const evidence = {
  runId: "run-1",
  jobId: "market-job-1",
  status: "SUPERSEDED" as const,
  boundaryStart: "2026-09-12T00:00:00Z",
  boundaryEnd: "2026-09-12T00:05:00Z",
};

test("stop before checkpoint commit replays the same bounded window", () => {
  assert.deepEqual(decideRestartBoundary(evidence, "2026-09-11T23:59:00Z"), {
    action: "REPLAY_BOUNDED",
    reason: "CHECKPOINT_BEFORE_BOUNDARY",
    boundaryStart: evidence.boundaryStart,
    boundaryEnd: evidence.boundaryEnd,
  });
});

test("stop after checkpoint commit skips replay because checkpoint truth already covers the window", () => {
  assert.deepEqual(decideRestartBoundary(evidence, evidence.boundaryEnd), {
    action: "SKIP_ALREADY_COMMITTED",
    reason: "CHECKPOINT_AT_OR_AFTER_BOUNDARY",
    boundaryEnd: evidence.boundaryEnd,
  });
});

test("missing checkpoint replays only the recorded bounded window", () => {
  assert.deepEqual(decideRestartBoundary(evidence), {
    action: "REPLAY_BOUNDED",
    reason: "NO_CHECKPOINT",
    boundaryStart: evidence.boundaryStart,
    boundaryEnd: evidence.boundaryEnd,
  });
});

test("unbounded evidence cannot trigger a broad replay", () => {
  assert.deepEqual(decideRestartBoundary({ runId: "run-2", jobId: "job-2", status: "FAILED" }), {
    action: "NO_BOUNDED_REPLAY",
    reason: "UNBOUNDED_EVIDENCE",
  });
});

test("invalid evidence boundary fails closed", () => {
  assert.throws(() => decideRestartBoundary({
    ...evidence,
    boundaryStart: "2026-09-12T00:05:00Z",
    boundaryEnd: "2026-09-12T00:05:00Z",
  }), /non-empty and half-open/);
});
