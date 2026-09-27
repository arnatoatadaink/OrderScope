import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import type { AcquisitionJob } from "./schedule.ts";

function jobCoverageKey(job: AcquisitionJob): string {
  return job.checkpointExpectations[0]?.coverageKey ?? "";
}

/**
 * Apply the Canary fairness policy before the per-tick limit is enforced.
 * Eligible gap repair is first, newly discovered coverage is second, and
 * existing forward coverage is ordered oldest-first. Stable identity keys
 * make ties deterministic without depending on the planner's job hash.
 */
export function prioritizeAcquisitionJobs(
  jobs: readonly AcquisitionJob[],
  checkpoints: readonly StoredCoverageCheckpoint[],
): AcquisitionJob[] {
  const storedByKey = new Map(checkpoints.map((checkpoint) => [checkpoint.coverageKey, checkpoint]));
  const tier = (job: AcquisitionJob): number => {
    if (job.dueReason === "MISSING_RANGE") return 0;
    if (job.dueReason === "NO_CHECKPOINT") return 1;
    return 2;
  };
  const coverageInstant = (job: AcquisitionJob): number => {
    const value = storedByKey.get(jobCoverageKey(job))?.completeThrough;
    if (!value) return Number.NEGATIVE_INFINITY;
    const parsed = Date.parse(value);
    return Number.isFinite(parsed) ? parsed : Number.NEGATIVE_INFINITY;
  };

  return [...jobs].sort((left, right) => tier(left) - tier(right)
    || coverageInstant(left) - coverageInstant(right)
    || jobCoverageKey(left).localeCompare(jobCoverageKey(right))
    || left.jobId.localeCompare(right.jobId));
}
