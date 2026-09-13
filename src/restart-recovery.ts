export type RestartEvidence = {
  runId: string;
  jobId: string;
  status: "RUNNING" | "FAILED" | "PARTIAL" | "SUPERSEDED";
  boundaryStart?: string;
  boundaryEnd?: string;
};

export type RestartDecision =
  | { action: "NO_BOUNDED_REPLAY"; reason: "UNBOUNDED_EVIDENCE" }
  | { action: "SKIP_ALREADY_COMMITTED"; reason: "CHECKPOINT_AT_OR_AFTER_BOUNDARY"; boundaryEnd: string }
  | { action: "REPLAY_BOUNDED"; reason: "CHECKPOINT_BEFORE_BOUNDARY" | "NO_CHECKPOINT"; boundaryStart: string; boundaryEnd: string };

function instant(value: string, name: string): number {
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) throw new Error(`${name} must be a valid instant`);
  return parsed;
}

export function decideRestartBoundary(
  evidence: RestartEvidence,
  checkpointCompleteThrough?: string,
): RestartDecision {
  if (!evidence.boundaryStart || !evidence.boundaryEnd) {
    return { action: "NO_BOUNDED_REPLAY", reason: "UNBOUNDED_EVIDENCE" };
  }
  const start = instant(evidence.boundaryStart, "boundaryStart");
  const end = instant(evidence.boundaryEnd, "boundaryEnd");
  if (start >= end) throw new Error("restart evidence boundary must be non-empty and half-open");

  if (checkpointCompleteThrough === undefined) {
    return {
      action: "REPLAY_BOUNDED",
      reason: "NO_CHECKPOINT",
      boundaryStart: evidence.boundaryStart,
      boundaryEnd: evidence.boundaryEnd,
    };
  }

  const checkpoint = instant(checkpointCompleteThrough, "checkpointCompleteThrough");
  if (checkpoint >= end) {
    return {
      action: "SKIP_ALREADY_COMMITTED",
      reason: "CHECKPOINT_AT_OR_AFTER_BOUNDARY",
      boundaryEnd: evidence.boundaryEnd,
    };
  }
  return {
    action: "REPLAY_BOUNDED",
    reason: "CHECKPOINT_BEFORE_BOUNDARY",
    boundaryStart: evidence.boundaryStart,
    boundaryEnd: evidence.boundaryEnd,
  };
}
