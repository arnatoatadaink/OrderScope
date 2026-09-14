import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  advanceD1DrainLifecycle,
  createD1DrainRecord,
} from "./d1-drain-lifecycle.ts";

const GENERATION_ID =
  "d1-custody-5b7c680a337a817950b2de12fa5ee18be54ef06b3336e7386872ded4d87494c7";

describe("R0-008 first real custody acknowledgement", () => {
  it("advances the reviewed one-row normalized_bar generation through ACKNOWLEDGED only", () => {
    let record = createD1DrainRecord({
      generationId: GENERATION_ID,
      table: "normalized_bar",
      windowStart: "2026-09-01T16:03:00.000Z",
      windowEnd: "2026-09-01T16:04:00.000Z",
    });

    record = advanceD1DrainLifecycle(record, "EXPORTED");
    record = advanceD1DrainLifecycle(record, "HASH_VERIFIED");
    record = advanceD1DrainLifecycle(record, "IMPORTED");
    record = advanceD1DrainLifecycle(record, "QUALITY_ACCEPTED");
    record = advanceD1DrainLifecycle(record, "ACKNOWLEDGED");

    assert.equal(record.state, "ACKNOWLEDGED");
    assert.equal(record.qualityAccepted, true);
    assert.equal(record.custodyAcknowledged, true);
    assert.equal(record.replayHorizonElapsed, false);
    assert.equal(record.graceElapsed, false);
    assert.equal(record.generationId, GENERATION_ID);

    const grace = advanceD1DrainLifecycle(record, "GRACE");
    assert.equal(grace.state, "GRACE");
    assert.equal(grace.graceElapsed, false);

    assert.throws(
      () => advanceD1DrainLifecycle(grace, "PURGE_ELIGIBLE"),
      /GRACE_NOT_ELAPSED/,
    );
  });
});
