import type { MarketCalendarSnapshot, NormalizedMarketSession } from "./calendar.ts";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import type { AcquisitionExecutionSummary } from "./execution.ts";
import {
  planNextHistoricalRecoveryChunk,
  type HistoricalRecoveryRequest,
} from "./historical-recovery.ts";
import type { TimeRange } from "./schedule.ts";

const MAX_CAMPAIGN_JOBS = 4;
const MAX_CAMPAIGN_BARS = 390;
const MAX_PAGES_PER_CHUNK = 10;
const MAX_EXTERNAL_PER_CHUNK = 40;
const MAX_D1_PER_CHUNK = 40;

export type HistoricalRecoveryChunkResponse = {
  accepted: boolean;
  recoveryId: string;
  expectedJobId: string;
  checkpointBefore: { completeThrough: string; version: number };
  requestedRange: TimeRange;
  expectedBarCount: number;
  result: { outcome: "SUCCEEDED" | "PARTIAL" | "FAILED"; summary: AcquisitionExecutionSummary };
  checkpointAfter: {
    completeThrough?: string;
    state: string;
    missingRanges: readonly TimeRange[];
    version: number;
  } | null;
  budget: { externalSubrequests: number; d1Queries: number };
  stoppedAfterOneChunk: boolean;
};

export type PersistedChunkInspection = {
  jobId: string;
  successfulAttempts: number;
  receiptCount: number;
  canonicalBarCount: number;
  conflicts: number;
  rejected: number;
  missing: number;
};

export type HistoricalRecoveryCampaignRecord = {
  campaignId: string;
  recoveryId: string;
  calendarRevision: string;
  session: { opensAt: string; closesAt: string };
  ordinal: number;
  jobId: string;
  requestedRange: TimeRange;
  expectedBarCount: number;
  checkpointBefore: { completeThrough: string; version: number };
  checkpointAfter: { completeThrough: string; version: number };
  result: {
    outcome: "SUCCEEDED";
    pages: number;
    inserted: number;
    matched: number;
    conflicts: 0;
    rejected: 0;
    missing: 0;
  };
  persisted: {
    successfulAttempts: 1;
    receiptCount: number;
    canonicalBarCount: number;
  };
  budget: { externalSubrequests: number; d1Queries: number };
};

export type FrozenHistoricalRecoveryCampaign = {
  campaignId: string;
  request: HistoricalRecoveryRequest;
  calendar: MarketCalendarSnapshot;
  session: NormalizedMarketSession;
  chunks: readonly {
    ordinal: number;
    jobId: string;
    requestedRange: TimeRange;
    expectedBarCount: number;
    checkpointBefore: { completeThrough: string; version: number };
    checkpointAfter: { completeThrough: string; version: number };
  }[];
};

export type HistoricalRecoveryCampaignPorts = {
  readCheckpoint: (coverageKey: string) => Promise<StoredCoverageCheckpoint | undefined>;
  invokeNextChunk: (input: {
    recoveryId: string;
    jobId: string;
    checkpointVersion: number;
    completeThrough: string;
  }) => Promise<HistoricalRecoveryChunkResponse>;
  inspectChunk: (jobId: string, requestedRange: TimeRange) => Promise<PersistedChunkInspection>;
  persistEvidence: (record: HistoricalRecoveryCampaignRecord) => Promise<void>;
};

/** Builds the only network mutation used by the operator campaign. */
export function createHistoricalRecoveryHttpInvoker(
  endpoint: string,
  controlToken: string,
  fetchImpl: typeof fetch = fetch,
): HistoricalRecoveryCampaignPorts["invokeNextChunk"] {
  const url = new URL(endpoint);
  if (url.protocol !== "https:" || url.pathname !== "/control/historical-recovery/nvda/next-chunk"
    || url.search || url.hash) {
    throw new Error("campaign endpoint must be the exact HTTPS next-chunk control boundary");
  }
  if (!controlToken) throw new Error("campaign control token must be non-empty");
  return async (input) => {
    const response = await fetchImpl(url, {
      method: "POST",
      headers: {
        authorization: `Bearer ${controlToken}`,
        "x-orderscope-recovery-id": input.recoveryId,
        "x-orderscope-job-id": input.jobId,
        "x-orderscope-checkpoint-version": String(input.checkpointVersion),
        "x-orderscope-complete-through": input.completeThrough,
      },
      redirect: "error",
    });
    const payload: unknown = await response.json();
    if (!response.ok || typeof payload !== "object" || payload === null || !("accepted" in payload)) {
      throw new Error(`historical recovery endpoint rejected chunk with HTTP ${response.status}`);
    }
    return payload as HistoricalRecoveryChunkResponse;
  };
}

function sameIdentity(left: StoredCoverageCheckpoint, right: StoredCoverageCheckpoint): boolean {
  return left.coverageKey === right.coverageKey
    && left.symbol === right.symbol
    && left.interval === right.interval
    && left.sessionScope === right.sessionScope
    && left.logicalDataVariant === right.logicalDataVariant
    && left.universeRevision === right.universeRevision;
}

function assertCleanCheckpoint(checkpoint: StoredCoverageCheckpoint, name: string): void {
  if (checkpoint.state !== "COMPLETE" || checkpoint.missingRanges.length !== 0 || checkpoint.blocker !== undefined) {
    throw new Error(`${name} must be COMPLETE, gap-free, and blocker-free`);
  }
  if (!checkpoint.completeThrough || !Number.isSafeInteger(checkpoint.version) || checkpoint.version < 0) {
    throw new Error(`${name} boundary/version is invalid`);
  }
}

function exactCheckpoint(
  actual: StoredCoverageCheckpoint,
  identity: StoredCoverageCheckpoint,
  expected: { completeThrough: string; version: number },
  name: string,
): void {
  assertCleanCheckpoint(actual, name);
  if (!sameIdentity(actual, identity)
    || actual.completeThrough !== expected.completeThrough
    || actual.version !== expected.version) {
    throw new Error(`${name} does not match the frozen campaign`);
  }
}

function barCount(range: TimeRange): number {
  const count = (Date.parse(range.endExclusive) - Date.parse(range.startInclusive)) / 60_000;
  if (!Number.isSafeInteger(count) || count < 1) throw new Error("campaign chunk has an invalid one-minute range");
  return count;
}

/**
 * Freezes one full U.S. Regular session and all four deterministic chunk
 * identities. This is operator-side planning only; it performs no I/O.
 */
export function freezeHistoricalRecoveryCampaign(
  campaignId: string,
  request: HistoricalRecoveryRequest,
  calendar: MarketCalendarSnapshot,
  session: NormalizedMarketSession,
): FrozenHistoricalRecoveryCampaign {
  if (!campaignId) throw new Error("campaignId must be non-empty");
  assertCleanCheckpoint(request.checkpointBefore, "initial checkpoint");
  if (request.instrument.cadence !== "1Min" || request.sessionScope !== "REGULAR" || request.maxBarsPerJob !== 100) {
    throw new Error("campaign requires the reviewed Regular 1Min / 100-bar shape");
  }
  if (calendar.revision !== request.calendarRevision || session.calendarRevision !== request.calendarRevision
    || session.sessionKind !== "REGULAR") {
    throw new Error("campaign calendar/session identity mismatch");
  }
  const sessionBars = barCount({ startInclusive: session.opensAt, endExclusive: session.closesAt });
  if (sessionBars !== MAX_CAMPAIGN_BARS) throw new Error("campaign requires exactly one 390-bar Regular session");
  if (request.checkpointBefore.completeThrough! > session.opensAt || request.recoveryRange.endExclusive < session.closesAt) {
    throw new Error("frozen session is outside the recovery range or precedes the checkpoint");
  }

  const chunks: Array<FrozenHistoricalRecoveryCampaign["chunks"][number]> = [];
  let checkpoint = request.checkpointBefore;
  while (checkpoint.completeThrough !== session.closesAt) {
    const job = planNextHistoricalRecoveryChunk({ ...request, checkpointBefore: checkpoint }, calendar);
    if (!job) throw new Error("planner completed before the frozen session close");
    if (job.requestedRange.startInclusive < session.opensAt || job.requestedRange.endExclusive > session.closesAt) {
      throw new Error("planner attempted to cross the frozen session");
    }
    const expectedBarCount = barCount(job.requestedRange);
    const next = {
      ordinal: chunks.length + 1,
      jobId: job.jobId,
      requestedRange: job.requestedRange,
      expectedBarCount,
      checkpointBefore: { completeThrough: checkpoint.completeThrough!, version: checkpoint.version },
      checkpointAfter: { completeThrough: job.requestedRange.endExclusive, version: checkpoint.version + 1 },
    };
    chunks.push(next);
    if (chunks.length > MAX_CAMPAIGN_JOBS) throw new Error("campaign exceeds the four-job maximum");
    checkpoint = { ...checkpoint, completeThrough: next.checkpointAfter.completeThrough, version: next.checkpointAfter.version };
  }
  if (chunks.length !== MAX_CAMPAIGN_JOBS
    || chunks.reduce((total, chunk) => total + chunk.expectedBarCount, 0) !== MAX_CAMPAIGN_BARS) {
    throw new Error("campaign must freeze four chunks totaling 390 bars");
  }
  return { campaignId, request, calendar, session, chunks };
}

function verifyResponse(
  response: HistoricalRecoveryChunkResponse,
  campaign: FrozenHistoricalRecoveryCampaign,
  chunk: FrozenHistoricalRecoveryCampaign["chunks"][number],
): void {
  const summary = response.result.summary;
  if (!response.accepted || response.recoveryId !== campaign.request.recoveryId
    || response.expectedJobId !== chunk.jobId || response.result.outcome !== "SUCCEEDED"
    || summary.outcome !== "SUCCEEDED" || summary.jobId !== chunk.jobId
    || response.checkpointBefore.completeThrough !== chunk.checkpointBefore.completeThrough
    || response.checkpointBefore.version !== chunk.checkpointBefore.version
    || response.requestedRange.startInclusive !== chunk.requestedRange.startInclusive
    || response.requestedRange.endExclusive !== chunk.requestedRange.endExclusive
    || response.expectedBarCount !== chunk.expectedBarCount
    || summary.inserted + summary.matched !== chunk.expectedBarCount
    || summary.conflicts !== 0 || summary.rejected !== 0 || summary.missing !== 0
    || summary.pages < 1 || summary.pages > MAX_PAGES_PER_CHUNK
    || response.checkpointAfter?.completeThrough !== chunk.checkpointAfter.completeThrough
    || response.checkpointAfter.version !== chunk.checkpointAfter.version
    || response.checkpointAfter.state !== "COMPLETE" || response.checkpointAfter.missingRanges.length !== 0
    || response.budget.externalSubrequests > MAX_EXTERNAL_PER_CHUNK
    || response.budget.d1Queries > MAX_D1_PER_CHUNK
    || !response.stoppedAfterOneChunk) {
    throw new Error(`chunk ${chunk.ordinal} response evidence mismatch`);
  }
}

/** Runs at most the remainder of the frozen session and stops on first error. */
export async function runHistoricalRecoveryCampaign(
  campaign: FrozenHistoricalRecoveryCampaign,
  ports: HistoricalRecoveryCampaignPorts,
): Promise<{ outcome: "COMPLETED"; resumedAtOrdinal: number; records: readonly HistoricalRecoveryCampaignRecord[] }> {
  const current = await ports.readCheckpoint(campaign.request.coverageKey);
  if (!current) throw new Error("campaign checkpoint is missing");
  assertCleanCheckpoint(current, "campaign checkpoint");
  const startIndex = campaign.chunks.findIndex((chunk) =>
    chunk.checkpointBefore.completeThrough === current.completeThrough && chunk.checkpointBefore.version === current.version);
  const alreadyComplete = current.completeThrough === campaign.session.closesAt
    && current.version === campaign.chunks.at(-1)!.checkpointAfter.version;
  if (startIndex < 0 && !alreadyComplete) throw new Error("campaign checkpoint is not a resumable frozen boundary");
  exactCheckpoint(current, campaign.request.checkpointBefore,
    alreadyComplete ? campaign.chunks.at(-1)!.checkpointAfter : campaign.chunks[startIndex]!.checkpointBefore,
    "campaign checkpoint");

  const records: HistoricalRecoveryCampaignRecord[] = [];
  for (const chunk of campaign.chunks.slice(alreadyComplete ? campaign.chunks.length : startIndex)) {
    const before = await ports.readCheckpoint(campaign.request.coverageKey);
    if (!before) throw new Error(`chunk ${chunk.ordinal} checkpoint is missing`);
    exactCheckpoint(before, campaign.request.checkpointBefore, chunk.checkpointBefore, `chunk ${chunk.ordinal} checkpoint before`);
    const response = await ports.invokeNextChunk({
      recoveryId: campaign.request.recoveryId,
      jobId: chunk.jobId,
      checkpointVersion: chunk.checkpointBefore.version,
      completeThrough: chunk.checkpointBefore.completeThrough,
    });
    verifyResponse(response, campaign, chunk);
    const after = await ports.readCheckpoint(campaign.request.coverageKey);
    if (!after) throw new Error(`chunk ${chunk.ordinal} checkpoint after is missing`);
    exactCheckpoint(after, campaign.request.checkpointBefore, chunk.checkpointAfter, `chunk ${chunk.ordinal} checkpoint after`);
    const persisted = await ports.inspectChunk(chunk.jobId, chunk.requestedRange);
    if (persisted.jobId !== chunk.jobId || persisted.successfulAttempts !== 1
      || persisted.receiptCount !== chunk.expectedBarCount || persisted.canonicalBarCount !== chunk.expectedBarCount
      || persisted.conflicts !== 0 || persisted.rejected !== 0 || persisted.missing !== 0) {
      throw new Error(`chunk ${chunk.ordinal} persisted evidence mismatch`);
    }
    const summary = response.result.summary;
    const record: HistoricalRecoveryCampaignRecord = {
      campaignId: campaign.campaignId,
      recoveryId: campaign.request.recoveryId,
      calendarRevision: campaign.calendar.revision,
      session: { opensAt: campaign.session.opensAt, closesAt: campaign.session.closesAt },
      ordinal: chunk.ordinal,
      jobId: chunk.jobId,
      requestedRange: chunk.requestedRange,
      expectedBarCount: chunk.expectedBarCount,
      checkpointBefore: chunk.checkpointBefore,
      checkpointAfter: chunk.checkpointAfter,
      result: { outcome: "SUCCEEDED", pages: summary.pages, inserted: summary.inserted, matched: summary.matched,
        conflicts: 0, rejected: 0, missing: 0 },
      persisted: { successfulAttempts: 1, receiptCount: persisted.receiptCount,
        canonicalBarCount: persisted.canonicalBarCount },
      budget: response.budget,
    };
    await ports.persistEvidence(record);
    records.push(record);
  }
  return { outcome: "COMPLETED", resumedAtOrdinal: alreadyComplete ? MAX_CAMPAIGN_JOBS + 1 : startIndex + 1, records };
}
