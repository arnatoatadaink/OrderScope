export const D1_RETENTION_CONTRACT_REVISION = "r0-006-v1";

export type D1RetentionClass =
  | "CURRENT_CONTROL"
  | "HOT_DATA"
  | "IDEMPOTENCY_EVIDENCE"
  | "OPERATIONAL_EVIDENCE"
  | "UNRESOLVED_BLOCKER";

export type D1RetentionPolicy = {
  table: string;
  retentionClass: D1RetentionClass;
  authoritativeControlTruth: boolean;
  requiresCustodyAcknowledgement: boolean;
  requiresQualityAcceptance: boolean;
  requiresReplayHorizonElapsed: boolean;
  requiresResolution: boolean;
};

export type D1PurgeEvidence = {
  custodyAcknowledged?: boolean;
  qualityAccepted?: boolean;
  replayHorizonElapsed?: boolean;
  graceElapsed?: boolean;
  resolved?: boolean;
};

export type D1PurgeDecision = {
  eligible: boolean;
  reasons: readonly string[];
};

const POLICIES = new Map<string, D1RetentionPolicy>([
  ["coverage_checkpoint", policy("coverage_checkpoint", "CURRENT_CONTROL", true)],
  ["latest_digest", policy("latest_digest", "CURRENT_CONTROL", true)],
  ["feature_state", policy("feature_state", "HOT_DATA", false, true, true)],
  ["acquisition_attempt", policy("acquisition_attempt", "OPERATIONAL_EVIDENCE", false, true, false, true)],
  ["normalized_bar", policy("normalized_bar", "HOT_DATA", false, true, true)],
  ["bar_acceptance_receipt", policy("bar_acceptance_receipt", "IDEMPOTENCY_EVIDENCE", false, true, true, true)],
  ["bar_conflict", policy("bar_conflict", "UNRESOLVED_BLOCKER", false, true, true, true, true)],
  ["acquisition_lease", policy("acquisition_lease", "CURRENT_CONTROL", true)],
  ["digest_history", policy("digest_history", "OPERATIONAL_EVIDENCE", false, true, false, true)],
  ["news_article", policy("news_article", "HOT_DATA", false, true, true)],
  ["news_query_membership", policy("news_query_membership", "HOT_DATA", false, true, true)],
  ["news_checkpoint", policy("news_checkpoint", "CURRENT_CONTROL", true)],
  ["scheduler_run", policy("scheduler_run", "OPERATIONAL_EVIDENCE", false, true, false, true)],
  ["scheduler_run_job", policy("scheduler_run_job", "OPERATIONAL_EVIDENCE", false, true, false, true)],
]);

function policy(
  table: string,
  retentionClass: D1RetentionClass,
  authoritativeControlTruth: boolean,
  requiresCustodyAcknowledgement = false,
  requiresQualityAcceptance = false,
  requiresReplayHorizonElapsed = false,
  requiresResolution = false,
): D1RetentionPolicy {
  return {
    table,
    retentionClass,
    authoritativeControlTruth,
    requiresCustodyAcknowledgement,
    requiresQualityAcceptance,
    requiresReplayHorizonElapsed,
    requiresResolution,
  };
}

export function d1RetentionPolicy(table: string): D1RetentionPolicy {
  const result = POLICIES.get(table);
  if (!result) throw new Error(`unclassified D1 table: ${table}`);
  return result;
}

export function reviewedD1RetentionTables(): readonly string[] {
  return [...POLICIES.keys()].sort();
}

export function evaluateD1PurgeEligibility(
  table: string,
  evidence: D1PurgeEvidence,
): D1PurgeDecision {
  const retention = d1RetentionPolicy(table);
  if (retention.authoritativeControlTruth) {
    return { eligible: false, reasons: ["CURRENT_CONTROL_TRUTH"] };
  }

  const reasons: string[] = [];
  if (retention.requiresCustodyAcknowledgement && evidence.custodyAcknowledged !== true) {
    reasons.push("CUSTODY_NOT_ACKNOWLEDGED");
  }
  if (retention.requiresQualityAcceptance && evidence.qualityAccepted !== true) {
    reasons.push("QUALITY_NOT_ACCEPTED");
  }
  if (retention.requiresReplayHorizonElapsed && evidence.replayHorizonElapsed !== true) {
    reasons.push("REPLAY_HORIZON_NOT_ELAPSED");
  }
  if (retention.requiresResolution && evidence.resolved !== true) {
    reasons.push("UNRESOLVED_BLOCKER");
  }
  if (evidence.graceElapsed !== true) {
    reasons.push("GRACE_NOT_ELAPSED");
  }
  return { eligible: reasons.length === 0, reasons };
}
