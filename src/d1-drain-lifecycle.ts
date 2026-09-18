import { evaluateD1PurgeEligibility, type D1PurgeEvidence } from "./d1-retention.ts";

export const D1_DRAIN_LIFECYCLE_REVISION = "r0-008-v1";

export type D1DrainState =
  | "PLANNED"
  | "EXPORTED"
  | "HASH_VERIFIED"
  | "IMPORTED"
  | "QUALITY_ACCEPTED"
  | "ACKNOWLEDGED"
  | "GRACE"
  | "PURGE_ELIGIBLE"
  | "PURGED";

export type D1DrainRecord = {
  generationId: string;
  table: string;
  windowStart: string;
  windowEnd: string;
  state: D1DrainState;
  custodyAcknowledged: boolean;
  qualityAccepted: boolean;
  replayHorizonElapsed: boolean;
  graceElapsed: boolean;
  resolved: boolean;
};

const NEXT_STATE: Readonly<Record<D1DrainState, D1DrainState | undefined>> = {
  PLANNED: "EXPORTED",
  EXPORTED: "HASH_VERIFIED",
  HASH_VERIFIED: "IMPORTED",
  IMPORTED: "QUALITY_ACCEPTED",
  QUALITY_ACCEPTED: "ACKNOWLEDGED",
  ACKNOWLEDGED: "GRACE",
  GRACE: "PURGE_ELIGIBLE",
  PURGE_ELIGIBLE: "PURGED",
  PURGED: undefined,
};

function validIsoUtc(value: string): boolean {
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) && value.endsWith("Z");
}

export function createD1DrainRecord(input: {
  generationId: string;
  table: string;
  windowStart: string;
  windowEnd: string;
  replayHorizonElapsed?: boolean;
  resolved?: boolean;
}): D1DrainRecord {
  if (!input.generationId.startsWith("d1-custody-")) {
    throw new Error("generationId must reference reviewed D1 custody");
  }
  if (!input.table) throw new Error("table is required");
  if (!validIsoUtc(input.windowStart) || !validIsoUtc(input.windowEnd)) {
    throw new Error("drain window must use ISO-8601 UTC timestamps");
  }
  if (Date.parse(input.windowStart) >= Date.parse(input.windowEnd)) {
    throw new Error("drain window must be non-empty and half-open");
  }
  return {
    generationId: input.generationId,
    table: input.table,
    windowStart: input.windowStart,
    windowEnd: input.windowEnd,
    state: "PLANNED",
    custodyAcknowledged: false,
    qualityAccepted: false,
    replayHorizonElapsed: input.replayHorizonElapsed ?? false,
    graceElapsed: false,
    resolved: input.resolved ?? false,
  };
}

export function advanceD1DrainLifecycle(
  current: D1DrainRecord,
  target: D1DrainState,
  evidence: Partial<D1PurgeEvidence> = {},
): D1DrainRecord {
  const expected = NEXT_STATE[current.state];
  if (expected !== target) {
    throw new Error(`invalid D1 drain transition: ${current.state} -> ${target}`);
  }

  if (target === "PURGED") {
    throw new Error("PURGED requires separately authorized remote mutation evidence");
  }

  let next: D1DrainRecord = { ...current, state: target };
  if (target === "QUALITY_ACCEPTED") next = { ...next, qualityAccepted: true };
  if (target === "ACKNOWLEDGED") next = { ...next, custodyAcknowledged: true };
  if (target === "GRACE" && evidence.graceElapsed === true) next = { ...next, graceElapsed: true };
  if (evidence.replayHorizonElapsed === true) next = { ...next, replayHorizonElapsed: true };
  if (evidence.resolved === true) next = { ...next, resolved: true };

  if (target === "PURGE_ELIGIBLE") {
    const decision = evaluateD1PurgeEligibility(next.table, {
      custodyAcknowledged: next.custodyAcknowledged,
      qualityAccepted: next.qualityAccepted,
      replayHorizonElapsed: next.replayHorizonElapsed,
      graceElapsed: next.graceElapsed,
      resolved: next.resolved,
    });
    if (!decision.eligible) {
      throw new Error(`D1 purge remains ineligible: ${decision.reasons.join(",")}`);
    }
  }
  return next;
}
