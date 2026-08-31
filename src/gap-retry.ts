import type { StoredCoverageCheckpoint } from "./checkpoint.ts";

export type DeferredGapRetry = { coverageKey: string; retryEligibleAt: string };

export function gapRetryEligibility(
  checkpoint: StoredCoverageCheckpoint | undefined,
  now: Date,
  _delayMinutes: number,
  retentionFloor?: string,
): DeferredGapRetry | undefined {
  if (checkpoint?.state !== "PARTIAL" || checkpoint.missingRanges.length === 0 || !checkpoint.retryNotBefore) return undefined;
  const retentionFloorMs = retentionFloor === undefined ? undefined : Date.parse(retentionFloor);
  if (retentionFloorMs !== undefined && Number.isFinite(retentionFloorMs)
    && !checkpoint.missingRanges.some((range) => Date.parse(range.endExclusive) > retentionFloorMs)) return undefined;
  const eligibleAt = Date.parse(checkpoint.retryNotBefore);
  if (!Number.isFinite(eligibleAt) || eligibleAt <= now.getTime()) return undefined;
  return { coverageKey: checkpoint.coverageKey, retryEligibleAt: new Date(eligibleAt).toISOString() };
}
