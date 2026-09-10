import type { MarketCalendarSnapshot } from "./calendar";
import type { AcquisitionMode, CheckpointExpectation, TimeRange } from "./schedule";
import type { NewsAcquisitionRuntimeConfig } from "./news-acquisition-config";

export const NEWS_COVERAGE_KEY = "news|alpaca|AMD,NVDA|metadata-v0.1";

export type NewsCheckpoint = { coverageKey: string; completeThrough?: string; version: number };
export type NewsAcquisitionJob = {
  jobId: string; jobKind: "NEWS_METADATA"; createdAt: string;
  symbols: readonly ["AMD", "NVDA"]; requestedRange: TimeRange;
  mode: Exclude<AcquisitionMode, "RECONCILE">; checkpointExpectations: readonly CheckpointExpectation[];
  maxPagesPerSymbol: number; maxArticlesPerRun: number;
  dueReason: "NO_CHECKPOINT" | "FORWARD_COVERAGE";
};

function hash(value: string): string {
  let result = 0xcbf29ce484222325n;
  for (const character of value) {
    result ^= BigInt(character.charCodeAt(0));
    result = BigInt.asUintN(64, result * 0x100000001b3n);
  }
  return result.toString(16).padStart(16, "0");
}

export function planNewsAcquisition(
  config: NewsAcquisitionRuntimeConfig,
  calendar: MarketCalendarSnapshot,
  checkpoint: NewsCheckpoint | undefined,
  now: Date,
): readonly NewsAcquisitionJob[] {
  if (!config.enabled || !Number.isFinite(now.getTime())) return [];
  const nowMs = now.getTime();
  const cadenceMs = config.cadenceMinutes * 60_000;
  if (nowMs % cadenceMs !== 0) return [];
  const session = calendar.sessions.find((candidate) =>
    (candidate.sessionKind === "PREMARKET" || candidate.sessionKind === "REGULAR" || candidate.sessionKind === "AFTER_HOURS")
    && nowMs >= Date.parse(candidate.opensAt) && nowMs <= Date.parse(candidate.closesAt));
  if (!session) return [];
  const boundary = Math.min(nowMs, Date.parse(session.closesAt));
  const initialLookbackMs = config.overlapMinutes * 60_000;
  const checkpointMs = checkpoint?.completeThrough ? Date.parse(checkpoint.completeThrough) : undefined;
  if (checkpointMs !== undefined && checkpointMs >= boundary) return [];
  const start = Math.max(Date.parse(session.opensAt), (checkpointMs ?? boundary) - initialLookbackMs);
  if (start >= boundary) return [];
  const requestedRange = {
    startInclusive: new Date(start).toISOString(), endExclusive: new Date(boundary).toISOString(),
  };
  const mode = checkpointMs === undefined ? "CATCH_UP" : "INCREMENTAL";
  const identity = [NEWS_COVERAGE_KEY, requestedRange.startInclusive, requestedRange.endExclusive, mode].join("|");
  return [{
    jobId: `news:${hash(identity)}`, jobKind: "NEWS_METADATA", createdAt: now.toISOString(),
    symbols: config.symbols, requestedRange, mode,
    checkpointExpectations: [{ coverageKey: NEWS_COVERAGE_KEY, expectedVersion: checkpoint?.version,
      observedCompleteThrough: checkpoint?.completeThrough }],
    maxPagesPerSymbol: config.maxPagesPerSymbol, maxArticlesPerRun: config.maxArticlesPerRun,
    dueReason: checkpointMs === undefined ? "NO_CHECKPOINT" : "FORWARD_COVERAGE",
  }];
}

export function newsDryRun(job: NewsAcquisitionJob | undefined) {
  return job ? { mutationCount: 0, providerCalls: 0, job: {
    jobId: job.jobId, symbols: job.symbols, requestedRange: job.requestedRange,
    maxPagesPerSymbol: job.maxPagesPerSymbol, maxArticlesPerRun: job.maxArticlesPerRun,
  } } : { mutationCount: 0, providerCalls: 0 };
}
