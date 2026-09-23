import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { freezeHistoricalRecoveryCampaign } from "./historical-recovery-campaign.ts";
import type { HistoricalRecoveryRequest } from "./historical-recovery.ts";
import {
  coverageAbsencesForRange,
  type LocalHistoryEvidenceSession,
} from "./local-history-evidence.ts";
import type { MarketCalendarSnapshot, NormalizedMarketSession } from "./calendar.ts";
import { CANARY_V01_UNIVERSE_REVISION } from "./universe.ts";

export type LocalPb04DryRunPacket = {
  schemaVersion: "l1-003-pb04-local-evidence-dry-run-v1";
  remoteMutation: false;
  campaignId: string;
  recoveryId: string;
  localEvidence: {
    marketDate: string;
    contentSha256: string;
    providerRevision: string;
    bars: number;
    denseSession: boolean;
    reproducible?: boolean;
  };
  checkpointBefore: {
    completeThrough: string;
    version: number;
  };
  session: {
    opensAt: string;
    closesAt: string;
    calendarRevision: string;
  };
  chunks: readonly {
    ordinal: number;
    jobId: string;
    requestedRange: { startInclusive: string; endExclusive: string };
    expectedGridBars: number;
    localProviderBars: number;
    acknowledgedAbsent: number;
    checkpointBefore: { completeThrough: string; version: number };
    checkpointAfter: { completeThrough: string; version: number };
  }[];
};

function nextMarketDate(date: string): string {
  const at = Date.parse(\`\${date}T00:00:00.000Z\`);
  if (!Number.isFinite(at)) throw new Error("market date is invalid");
  return new Date(at + 86_400_000).toISOString().slice(0, 10);
}

export function buildLocalPb04DryRunPacket(input: {
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
  campaignId?: string;
  recoveryId?: string;
}): LocalPb04DryRunPacket {
  const { session, checkpointBefore, calendarRevision, createdAt } = input;
  if (session.coverageKey !== checkpointBefore.coverageKey) {
    throw new Error("local evidence coverage key does not match checkpoint");
  }
  if (checkpointBefore.symbol !== "NVDA"
    || checkpointBefore.interval !== "1Min"
    || checkpointBefore.sessionScope !== "REGULAR"
    || checkpointBefore.logicalDataVariant !== "stock:iex:raw") {
    throw new Error("PB-04 local dry-run requires the frozen NVDA Regular IEX identity");
  }
  if (checkpointBefore.state !== "COMPLETE"
    || checkpointBefore.missingRanges.length !== 0
    || checkpointBefore.blocker !== undefined
    || !checkpointBefore.completeThrough) {
    throw new Error("PB-04 local dry-run requires a clean COMPLETE checkpoint");
  }

  const sessionCalendar: NormalizedMarketSession = {
    marketDate: session.plan.marketDate,
    sessionKind: "REGULAR",
    opensAt: session.plan.startInclusive,
    closesAt: session.plan.endExclusive,
    isShortened: false,
    calendarRevision,
  };
  const calendar: MarketCalendarSnapshot = {
    market: "US_EQUITIES",
    dateRange: {
      startInclusive: session.plan.marketDate,
      endExclusive: nextMarketDate(session.plan.marketDate),
    },
    generatedAt: createdAt,
    revision: calendarRevision,
    sessions: [sessionCalendar],
  };
  const recoveryId = input.recoveryId ?? \`L1-003-NVDA-\${session.plan.marketDate.replaceAll("-", "")}-LOCAL\`;
  const campaignId = input.campaignId ?? \`PB04-NVDA-\${session.plan.marketDate.replaceAll("-", "")}-LOCAL-DRYRUN\`;
  const request: HistoricalRecoveryRequest = {
    recoveryId,
    providerRevision: session.providerRevision,
    universeRevision: checkpointBefore.universeRevision ?? CANARY_V01_UNIVERSE_REVISION,
    calendarRevision,
    instrument: { symbol: "NVDA", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    coverageKey: session.coverageKey,
    sessionScope: "REGULAR",
    logicalDataVariant: "stock:iex:raw",
    mode: "CATCH_UP",
    recoveryRange: {
      startInclusive: checkpointBefore.completeThrough,
      endExclusive: session.plan.endExclusive,
    },
    checkpointBefore,
    maxBarsPerJob: 100,
    createdAt,
  };
  const frozen = freezeHistoricalRecoveryCampaign(campaignId, request, calendar, sessionCalendar);
  return {
    schemaVersion: "l1-003-pb04-local-evidence-dry-run-v1",
    remoteMutation: false,
    campaignId,
    recoveryId,
    localEvidence: {
      marketDate: session.plan.marketDate,
      contentSha256: session.contentSha256,
      providerRevision: session.providerRevision,
      bars: session.bars.length,
      denseSession: session.validation.denseSession,
      ...(session.reproducible === undefined ? {} : { reproducible: session.reproducible }),
    },
    checkpointBefore: {
      completeThrough: checkpointBefore.completeThrough,
      version: checkpointBefore.version,
    },
    session: {
      opensAt: sessionCalendar.opensAt,
      closesAt: sessionCalendar.closesAt,
      calendarRevision,
    },
    chunks: frozen.chunks.map((chunk) => {
      const absences = coverageAbsencesForRange(
        input.coverageAbsences,
        chunk.requestedRange.startInclusive,
        chunk.requestedRange.endExclusive,
      );
      return {
        ordinal: chunk.ordinal,
        jobId: chunk.jobId,
        requestedRange: chunk.requestedRange,
        expectedGridBars: chunk.expectedBarCount,
        localProviderBars: chunk.expectedBarCount - absences.length,
        acknowledgedAbsent: absences.length,
        checkpointBefore: chunk.checkpointBefore,
        checkpointAfter: chunk.checkpointAfter,
      };
    }),
  };
}
