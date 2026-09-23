import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import type { ProviderNeutralBar } from "./alpaca.ts";
import type { CoverageAbsenceEvidence } from "./execution.ts";
import type { HistoricalBarRequest } from "./alpaca.ts";
import { validateRegularSession } from "./local-history-collector.ts";

export type LocalHistoryEvidenceSession = {
  schemaVersion: "l1-003-local-history-session-v3";
  contentSha256: string;
  previousContentSha256?: string;
  reproducible?: boolean;
  coverageKey: string;
  providerRevision: string;
  feed: "iex";
  adjustment: "raw";
  plan: {
    marketDate: string;
    startInclusive: string;
    endExclusive: string;
    expectedBars: number;
  };
  validation: {
    marketDate: string;
    expectedBars: number;
    actualBars: number;
    firstTimestamp?: string;
    lastTimestamp?: string;
    duplicateTimestamps: string[];
    outOfRangeTimestamps: string[];
    missingTimestamps: string[];
    denseSession: boolean;
    structurallyValid: boolean;
  };
  pages: number;
  bars: ProviderNeutralBar[];
};

function sha256(value: string): string {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

function canonicalStablePayload(session: LocalHistoryEvidenceSession): string {
  return JSON.stringify({
    coverageKey: session.coverageKey,
    providerRevision: session.providerRevision,
    feed: session.feed,
    adjustment: session.adjustment,
    plan: session.plan,
    validation: session.validation,
    pages: session.pages,
    bars: session.bars,
  });
}

function isSession(value: unknown): value is LocalHistoryEvidenceSession {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  return record.schemaVersion === "l1-003-local-history-session-v3"
    && typeof record.contentSha256 === "string"
    && typeof record.coverageKey === "string"
    && typeof record.providerRevision === "string"
    && record.feed === "iex"
    && record.adjustment === "raw"
    && typeof record.plan === "object"
    && record.plan !== null
    && typeof record.validation === "object"
    && record.validation !== null
    && Number.isSafeInteger(record.pages)
    && Array.isArray(record.bars);
}

export async function loadLocalHistoryEvidence(path: string): Promise<{
  session: LocalHistoryEvidenceSession;
  coverageAbsences: readonly CoverageAbsenceEvidence[];
}> {
  const parsed: unknown = JSON.parse(await readFile(path, "utf8"));
  if (!isSession(parsed)) throw new Error("local history evidence has an unsupported schema");
  const session = parsed;
  const actualHash = sha256(canonicalStablePayload(session));
  if (actualHash !== session.contentSha256) throw new Error("local history evidence hash mismatch");
  const recomputed = validateRegularSession(session.plan, session.bars);
  if (JSON.stringify(recomputed) !== JSON.stringify(session.validation)) {
    throw new Error("local history evidence validation does not match bars");
  }
  if (!session.validation.structurallyValid) throw new Error("local history evidence is not structurally valid");
  if (!session.validation.denseSession && session.reproducible !== true) {
    throw new Error("sparse local history evidence is not reproducible");
  }

  const coverageAbsences = session.validation.missingTimestamps.map((identityStart) => ({
    symbol: "NVDA",
    identityStart,
    reason: "REPRODUCIBLE_PROVIDER_ABSENCE" as const,
    evidenceHash: session.contentSha256,
  }));
  return { session, coverageAbsences };
}

export function localHistoryFetchPage(
  session: LocalHistoryEvidenceSession,
): (credentials: unknown, request: HistoricalBarRequest) => Promise<{
  bars: ProviderNeutralBar[];
  nextPageToken?: string;
}> {
  return async (_credentials, request) => {
    if (request.feed !== session.feed) throw new Error("local history evidence feed mismatch");
    const symbol = request.instrument?.symbol ?? request.instruments?.[0]?.symbol;
    if (symbol !== "NVDA") throw new Error("local history evidence only supports NVDA");
    const from = Date.parse(request.startInclusive);
    const to = Date.parse(request.endExclusive);
    if (!Number.isFinite(from) || !Number.isFinite(to) || from >= to) {
      throw new Error("local history evidence request range is invalid");
    }
    if (from < Date.parse(session.plan.startInclusive) || to > Date.parse(session.plan.endExclusive)) {
      throw new Error("local history evidence request exceeds frozen session");
    }
    return {
      bars: session.bars.filter((bar) => {
        const at = Date.parse(bar.timestamp);
        return at >= from && at < to;
      }),
    };
  };
}
