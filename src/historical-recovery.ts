import type { MarketCalendarSnapshot, NormalizedMarketSession } from "./calendar.ts";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import {
  coverageKeyFor,
  type AcquisitionJob,
  type AcquisitionMode,
  type SessionScope,
  type TimeRange,
} from "./schedule.ts";
import type { UniverseInstrument } from "./universe.ts";

const INTERVAL_MS = { "1Min": 60_000, "15Min": 15 * 60_000, "1Day": 24 * 60 * 60_000 } as const;

export type HistoricalRecoveryRequest = {
  recoveryId: string;
  providerRevision: string;
  universeRevision: string;
  calendarRevision: string;
  instrument: UniverseInstrument;
  coverageKey: string;
  sessionScope: SessionScope;
  logicalDataVariant: string;
  mode: AcquisitionMode;
  recoveryRange: TimeRange;
  /** The current persisted checkpoint, read immediately before this plan. */
  checkpointBefore: StoredCoverageCheckpoint;
  maxBarsPerJob: number;
  createdAt: string;
};

type EligibleBar = { startInclusive: string; endExclusive: string; sessionKey: string };

function canonicalUtc(value: string, name: string): number {
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed) || new Date(parsed).toISOString() !== value) {
    throw new Error(`${name} must be a canonical UTC instant`);
  }
  return parsed;
}

function nonEmpty(value: string, name: string): void {
  if (!value) throw new Error(`${name} must be non-empty`);
}

function stableHash(value: string): string {
  let hash = 0xcbf29ce484222325n;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= BigInt(value.charCodeAt(index));
    hash = BigInt.asUintN(64, hash * 0x100000001b3n);
  }
  return hash.toString(16).padStart(16, "0");
}

function sessionsFor(
  request: HistoricalRecoveryRequest,
  calendar: MarketCalendarSnapshot,
): readonly NormalizedMarketSession[] {
  if (calendar.revision !== request.calendarRevision) throw new Error("calendar revision must match recovery request");
  if (request.instrument.providerRoute === "alpaca_crypto_bars") {
    if (request.sessionScope !== "ALL_TRADING") throw new Error("crypto recovery requires ALL_TRADING session scope");
    return [];
  }
  if (request.sessionScope === "ALL_TRADING") throw new Error("equity recovery requires an explicit equity session scope");
  if (request.instrument.cadence === "1Day" && request.sessionScope !== "REGULAR") {
    throw new Error("daily equity recovery requires REGULAR session scope");
  }
  const sessions = calendar.sessions
    .filter((session) => session.sessionKind === request.sessionScope)
    .sort((left, right) => left.opensAt.localeCompare(right.opensAt));
  let previousClose = -Infinity;
  for (const session of sessions) {
    const open = canonicalUtc(session.opensAt, "calendar session open");
    const close = canonicalUtc(session.closesAt, "calendar session close");
    if (session.calendarRevision !== request.calendarRevision || open >= close || open < previousClose) {
      throw new Error("calendar sessions are not eligible for historical recovery");
    }
    previousClose = close;
  }
  return sessions;
}

function eligibleBars(request: HistoricalRecoveryRequest, calendar: MarketCalendarSnapshot): EligibleBar[] {
  const start = canonicalUtc(request.recoveryRange.startInclusive, "recovery start");
  const end = canonicalUtc(request.recoveryRange.endExclusive, "recovery end");
  const interval = INTERVAL_MS[request.instrument.cadence];
  if (request.instrument.providerRoute === "alpaca_crypto_bars") {
    if (start % interval !== 0 || end % interval !== 0) throw new Error("crypto recovery bounds must align to its cadence");
    const result: EligibleBar[] = [];
    for (let at = start; at < end; at += interval) {
      result.push({ startInclusive: new Date(at).toISOString(), endExclusive: new Date(at + interval).toISOString(), sessionKey: "ALL_TRADING" });
    }
    return result;
  }

  const result: EligibleBar[] = [];
  for (const session of sessionsFor(request, calendar)) {
    const open = canonicalUtc(session.opensAt, "calendar session open");
    const close = canonicalUtc(session.closesAt, "calendar session close");
    if (request.instrument.cadence === "1Day") {
      if (open >= start && close <= end) result.push({ startInclusive: session.opensAt, endExclusive: session.closesAt, sessionKey: session.opensAt });
      continue;
    }
    for (let at = open; at + interval <= close; at += interval) {
      if (at >= start && at + interval <= end) {
        result.push({ startInclusive: new Date(at).toISOString(), endExclusive: new Date(at + interval).toISOString(), sessionKey: session.opensAt });
      }
    }
  }
  return result;
}

/**
 * Plans exactly one deterministic historical-recovery chunk.  Callers must
 * execute it through executeAcquisitionJob, verify its accepted-record result,
 * then re-read the checkpoint and call this function again.  Returning only
 * the next chunk prevents a precomputed later chunk from bypassing a failed or
 * partial earlier checkpoint update.
 */
export function planNextHistoricalRecoveryChunk(
  request: HistoricalRecoveryRequest,
  calendar: MarketCalendarSnapshot,
): AcquisitionJob | undefined {
  for (const [value, name] of [[request.recoveryId, "recoveryId"], [request.providerRevision, "providerRevision"],
    [request.universeRevision, "universeRevision"], [request.calendarRevision, "calendarRevision"],
    [request.logicalDataVariant, "logicalDataVariant"], [request.coverageKey, "coverageKey"]] as const) nonEmpty(value, name);
  if (!Number.isSafeInteger(request.maxBarsPerJob) || request.maxBarsPerJob < 1) {
    throw new Error("maxBarsPerJob must be a positive integer");
  }
  const recoveryStart = canonicalUtc(request.recoveryRange.startInclusive, "recovery start");
  const recoveryEnd = canonicalUtc(request.recoveryRange.endExclusive, "recovery end");
  canonicalUtc(request.createdAt, "createdAt");
  if (recoveryStart >= recoveryEnd) throw new Error("recovery range must be non-empty and half-open");
  if (request.checkpointBefore.coverageKey !== request.coverageKey) throw new Error("checkpoint coverage key must match recovery request");
  if (request.checkpointBefore.state !== "COMPLETE") throw new Error("historical recovery requires a COMPLETE checkpoint");
  if (request.checkpointBefore.missingRanges.length > 0) throw new Error("historical recovery requires a checkpoint without unresolved missing ranges");
  if (!Number.isSafeInteger(request.checkpointBefore.version) || request.checkpointBefore.version < 0) {
    throw new Error("checkpoint version must be a non-negative integer");
  }
  const expectedKey = coverageKeyFor(request.instrument, request.sessionScope, request.logicalDataVariant);
  if (request.coverageKey !== expectedKey) throw new Error("coverage key does not match frozen recovery identity");
  if (request.checkpointBefore.symbol !== request.instrument.symbol
    || request.checkpointBefore.interval !== request.instrument.cadence
    || request.checkpointBefore.sessionScope !== request.sessionScope
    || request.checkpointBefore.logicalDataVariant !== request.logicalDataVariant) {
    throw new Error("checkpoint identity does not match frozen recovery identity");
  }
  const checkpointThrough = request.checkpointBefore.completeThrough;
  if (!checkpointThrough) throw new Error("historical recovery requires a persisted checkpoint boundary");
  const checkpointMs = canonicalUtc(checkpointThrough, "checkpoint completeThrough");
  if (checkpointMs < recoveryStart || checkpointMs > recoveryEnd) {
    throw new Error("checkpoint boundary must remain within the frozen recovery range");
  }

  const bars = eligibleBars(request, calendar);
  const boundaries = new Set([request.recoveryRange.startInclusive, request.recoveryRange.endExclusive,
    ...bars.map((bar) => bar.endExclusive)]);
  if (!boundaries.has(checkpointThrough)) throw new Error("checkpoint boundary is not eligible for the frozen recovery range");
  if (checkpointMs === recoveryEnd) return undefined;
  const pending = bars.filter((bar) => canonicalUtc(bar.endExclusive, "eligible bar end") > checkpointMs);
  if (pending.length === 0) return undefined;
  const first = pending[0]!;
  const chunk = pending.slice(0, request.maxBarsPerJob)
    .filter((bar) => bar.sessionKey === first.sessionKey);
  const last = chunk.at(-1)!;
  const requestedRange = { startInclusive: first.startInclusive, endExclusive: last.endExclusive };
  const identity = [request.recoveryId, request.providerRevision, request.universeRevision, request.calendarRevision,
    request.coverageKey, requestedRange.startInclusive, requestedRange.endExclusive, request.mode].join("|");
  return {
    jobId: `historical-market-recovery:${stableHash(identity)}`,
    jobKind: "MARKET_BARS",
    createdAt: request.createdAt,
    universeRevision: request.universeRevision,
    calendarRevision: request.calendarRevision,
    instruments: [request.instrument],
    interval: request.instrument.cadence,
    requestedRange,
    sessionScope: request.sessionScope,
    mode: request.mode,
    providerRoute: request.instrument.providerRoute,
    logicalDataVariant: request.logicalDataVariant,
    checkpointExpectations: [{ coverageKey: request.coverageKey, expectedVersion: request.checkpointBefore.version,
      observedCompleteThrough: checkpointThrough }],
    attempt: 0,
    dueReason: "HISTORICAL_RECOVERY",
    historicalRecovery: { recoveryId: request.recoveryId, providerRevision: request.providerRevision,
      recoveryStartInclusive: request.recoveryRange.startInclusive, recoveryEndExclusive: request.recoveryRange.endExclusive,
      checkpointBefore: checkpointThrough },
  };
}
