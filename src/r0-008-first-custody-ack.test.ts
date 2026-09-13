import { describe, expect, it } from "vitest";

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

    expect(record.state).toBe("ACKNOWLEDGED");
    expect(record.qualityAccepted).toBe(true);
    expect(record.custodyAcknowledged).toBe(true);
    expect(record.replayHorizonElapsed).toBe(false);
    expect(record.graceElapsed).toBe(false);
    expect(record.generationId).toBe(GENERATION_ID);

    const grace = advanceD1DrainLifecycle(record, "GRACE");
    expect(grace.state).toBe("GRACE");
    expect(grace.graceElapsed).toBe(false);

    expect(() => advanceD1DrainLifecycle(grace, "PURGE_ELIGIBLE")).toThrow(
      /REPLAY_HORIZON_NOT_ELAPSED.*GRACE_NOT_ELAPSED/,
    );
  });
});
