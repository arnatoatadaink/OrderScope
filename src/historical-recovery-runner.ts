import { MAX_BARS_WITHIN_D1_OPERATION_BUDGET } from "./acquisition-config.ts";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { executeAcquisitionJob, type AcquisitionExecutionSummary, type AcquisitionExecutorOptions } from "./execution.ts";
import { planNextHistoricalRecoveryChunk, type HistoricalRecoveryRequest } from "./historical-recovery.ts";

export type HistoricalRecoveryRunnerOptions = Omit<AcquisitionExecutorOptions, "calendar">;

export type HistoricalRecoveryChunkResult =
  | { outcome: "NO_WORK" }
  | { outcome: "SUCCEEDED" | "PARTIAL" | "FAILED"; summary: AcquisitionExecutionSummary };

function sameCheckpoint(left: StoredCoverageCheckpoint, right: StoredCoverageCheckpoint): boolean {
  return left.coverageKey === right.coverageKey
    && left.symbol === right.symbol
    && left.interval === right.interval
    && left.sessionScope === right.sessionScope
    && left.logicalDataVariant === right.logicalDataVariant
    && left.state === right.state
    && left.completeThrough === right.completeThrough
    && left.version === right.version
    && JSON.stringify(left.missingRanges) === JSON.stringify(right.missingRanges);
}

/**
 * Executes one, and only one, previously frozen historical-recovery chunk.
 * It deliberately has no Worker handler or Cron registration. A change-window
 * caller must preflight and supply the same checkpoint it expects to find just
 * before execution; a drift is rejected before any provider request or write.
 */
export async function runHistoricalRecoveryChunk(
  request: HistoricalRecoveryRequest,
  calendar: MarketCalendarSnapshot,
  options: HistoricalRecoveryRunnerOptions,
): Promise<HistoricalRecoveryChunkResult> {
  if (request.instrument.providerRoute !== "alpaca_stock_bars" || request.sessionScope !== "REGULAR") {
    throw new Error("historical Market recovery runner requires one Regular equity instrument");
  }
  if (request.mode !== "CATCH_UP") throw new Error("historical Market recovery runner requires CATCH_UP mode");
  if (request.maxBarsPerJob > MAX_BARS_WITHIN_D1_OPERATION_BUDGET || options.maxBars !== request.maxBarsPerJob) {
    throw new Error("historical recovery runner maxBars must equal the reviewed bounded request");
  }
  const expectedVariant = `stock:${options.feed}:raw`;
  if (request.logicalDataVariant !== expectedVariant) {
    throw new Error("historical recovery logical data variant must match the executor feed");
  }

  const current = await options.checkpoints.get(request.coverageKey);
  if (!current || !sameCheckpoint(current, request.checkpointBefore)) {
    throw new Error("historical recovery checkpoint drifted since preflight");
  }
  const job = planNextHistoricalRecoveryChunk(request, calendar);
  if (!job) return { outcome: "NO_WORK" };

  const summary = await executeAcquisitionJob(job, { ...options, calendar });
  return { outcome: summary.outcome, summary };
}
