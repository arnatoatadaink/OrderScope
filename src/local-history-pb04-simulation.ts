import { executeAcquisitionJob, type AcquisitionExecutionSummary } from "./execution.ts";
import type { BarAcceptanceInput, BarAcceptanceResult, BarProvenance } from "./bar-store.ts";
import type { BarNormalizationResult } from "./bar.ts";
import { coverageAbsencesForRange, localHistoryFetchPage, type LocalHistoryEvidenceSession } from "./local-history-evidence.ts";
import { planNextHistoricalRecoveryChunk, type HistoricalRecoveryRequest } from "./historical-recovery.ts";
import type { MarketCalendarSnapshot, NormalizedMarketSession } from "./calendar.ts";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { CANARY_V01_UNIVERSE_REVISION } from "./universe.ts";

export type LocalPb04SimulationResult = {
  remoteMutation: false;
  initialCheckpoint: { completeThrough: string; version: number };
  finalCheckpoint: { completeThrough?: string; version: number; state: string };
  chunks: readonly {
    ordinal: number;
    summary: AcquisitionExecutionSummary;
    checkpointBefore: { completeThrough?: string; version: number };
    checkpointAfter: { completeThrough?: string; version: number; state: string };
  }[];
};

function nextDate(date: string): string {
  const at = Date.parse(date + "T00:00:00.000Z");
  return new Date(at + 86_400_000).toISOString().slice(0, 10);
}

export async function simulateLocalPb04Session(input: {
  session: LocalHistoryEvidenceSession;
  coverageAbsences: readonly {
    symbol: string;
    identityStart: string;
    reason: "REPRODUCIBLE_PROVIDER_ABSENCE";
    evidenceHash: string;
  }[];
  checkpointBefore: StoredCoverageCheckpoint;
  calendarRevision: string;
  createdAt: string;
}): Promise<LocalPb04SimulationResult> {
  const marketSession: NormalizedMarketSession = {
    marketDate: input.session.plan.marketDate,
    sessionKind: "REGULAR",
    opensAt: input.session.plan.startInclusive,
    closesAt: input.session.plan.endExclusive,
    isShortened: false,
    calendarRevision: input.calendarRevision,
  };
  const calendar: MarketCalendarSnapshot = {
    market: "US_EQUITIES",
    dateRange: {
      startInclusive: input.session.plan.marketDate,
      endExclusive: nextDate(input.session.plan.marketDate),
    },
    generatedAt: input.createdAt,
    revision: input.calendarRevision,
    sessions: [marketSession],
  };

  let current: StoredCoverageCheckpoint = { ...input.checkpointBefore };
  const accepted = new Set<string>();
  const attempts: Record<string, unknown>[] = [];
  const chunks: Array<LocalPb04SimulationResult["chunks"][number]> = [];
  const fetchPage = localHistoryFetchPage(input.session);

  for (let ordinal = 1; ordinal <= 4; ordinal += 1) {
    const request: HistoricalRecoveryRequest = {
      recoveryId: "L1-003-NVDA-" + input.session.plan.marketDate.replaceAll("-", "") + "-LOCAL-SIM",
      providerRevision: input.session.providerRevision,
      universeRevision: current.universeRevision ?? CANARY_V01_UNIVERSE_REVISION,
      calendarRevision: input.calendarRevision,
      instrument: { symbol: "NVDA", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
      coverageKey: input.session.coverageKey,
      sessionScope: "REGULAR",
      logicalDataVariant: "stock:iex:raw",
      mode: "CATCH_UP",
      recoveryRange: {
        startInclusive: input.checkpointBefore.completeThrough!,
        endExclusive: input.session.plan.endExclusive,
      },
      checkpointBefore: current,
      maxBarsPerJob: 100,
      createdAt: input.createdAt,
    };
    const job = planNextHistoricalRecoveryChunk(request, calendar);
    if (!job) break;
    const before = { completeThrough: current.completeThrough, version: current.version };
    const chunkAbsences = coverageAbsencesForRange(
      input.coverageAbsences,
      job.requestedRange.startInclusive,
      job.requestedRange.endExclusive,
    );
    const summary = await executeAcquisitionJob(job, {
      credentials: { keyId: "local-evidence", secretKey: "local-evidence" },
      calendar,
      feed: "iex",
      maxPages: 1,
      maxBars: 100,
      fetchPage,
      coverageAbsences: chunkAbsences,
      checkpoints: {
        get: async () => current,
        getMany: async () => [current],
        listDue: async () => [],
        recordAttempt: async (attempt: Record<string, unknown>) => { attempts.push(attempt); },
        summarizeStaleAttempts: async () => ({ count: 0 }),
        supersedeStaleAttempts: async () => 0,
        compareAndSet: async (expectedVersion: number | undefined, proposed: StoredCoverageCheckpoint) => {
          if (expectedVersion !== current.version) return { outcome: "VERSION_CONFLICT" as const, current };
          current = { ...proposed, version: current.version + 1 };
          return { outcome: "UPDATED" as const, checkpoint: current };
        },
      },
      bars: {
        acceptBatch: async (inputs: readonly BarAcceptanceInput[]): Promise<readonly BarAcceptanceResult[]> => inputs.map((item: BarAcceptanceInput) => {
          if (item.candidate.outcome !== "NORMALIZED") {
            return { outcome: "REJECTED" as const, acceptanceReceipt: item.provenance.idempotencyKey, provenanceAppended: true };
          }
          const key = item.candidate.bar.barStartUtc;
          const matched = accepted.has(key);
          accepted.add(key);
          return {
            outcome: matched ? "MATCHED" as const : "INSERTED" as const,
            acceptanceReceipt: item.provenance.idempotencyKey,
            provenanceAppended: true,
          };
        }),
        accept: async (candidate: BarNormalizationResult, provenance: BarProvenance): Promise<BarAcceptanceResult> => {
          if (candidate.outcome !== "NORMALIZED") {
            return { outcome: "REJECTED" as const, acceptanceReceipt: provenance.idempotencyKey, provenanceAppended: true };
          }
          const key = candidate.bar.barStartUtc;
          const matched = accepted.has(key);
          accepted.add(key);
          return {
            outcome: matched ? "MATCHED" as const : "INSERTED" as const,
            acceptanceReceipt: provenance.idempotencyKey,
            provenanceAppended: true,
          };
        },
      },
      now: () => new Date(input.createdAt),
    } as never);
    chunks.push({
      ordinal,
      summary,
      checkpointBefore: before,
      checkpointAfter: { completeThrough: current.completeThrough, version: current.version, state: current.state },
    });
  }

  return {
    remoteMutation: false,
    initialCheckpoint: {
      completeThrough: input.checkpointBefore.completeThrough!,
      version: input.checkpointBefore.version,
    },
    finalCheckpoint: {
      completeThrough: current.completeThrough,
      version: current.version,
      state: current.state,
    },
    chunks,
  };
}
