import type { MarketCalendarSnapshot, NormalizedMarketSession } from "./calendar";
import type { Cadence, ProviderRoute, UniverseInstrument, UniverseSnapshot } from "./universe";

export type SessionScope = "PREMARKET" | "REGULAR" | "ALL_TRADING";
export type AcquisitionMode = "INCREMENTAL" | "CATCH_UP" | "RECONCILE";

export type TimeRange = {
  startInclusive: string;
  endExclusive: string;
};

export type CoverageCheckpoint = {
  coverageKey: string;
  completeThrough?: string;
  missingRanges: readonly TimeRange[];
  version: number;
};

export type CheckpointExpectation = {
  coverageKey: string;
  expectedVersion?: number;
  observedCompleteThrough?: string;
};

export type AcquisitionJob = {
  jobId: string;
  jobKind: "MARKET_BARS";
  createdAt: string;
  universeRevision: string;
  calendarRevision: string;
  instruments: readonly UniverseInstrument[];
  interval: Cadence;
  requestedRange: TimeRange;
  sessionScope: SessionScope;
  mode: AcquisitionMode;
  providerRoute: ProviderRoute;
  checkpointExpectations: readonly CheckpointExpectation[];
  attempt: 0;
  dueReason: "MISSING_RANGE" | "NO_CHECKPOINT" | "FORWARD_COVERAGE";
};

export type SchedulePolicyConfig = {
  retentionFloor: string;
  overlapMs: Readonly<Record<Cadence, number>>;
  finalizationLagMs: Readonly<Record<Cadence, number>>;
  maxBarsPerJob: number;
  logicalDataVariant: (instrument: UniverseInstrument) => string;
  sessionScopeFor?: (instrument: UniverseInstrument) => SessionScope;
};

const INTERVAL_MS: Readonly<Record<Cadence, number>> = {
  "1Min": 60_000,
  "15Min": 15 * 60_000,
  "1Day": 24 * 60 * 60_000,
};

function instant(value: string, name: string): number {
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) throw new Error(`${name} must be a UTC instant`);
  return parsed;
}

function iso(value: number): string {
  return new Date(value).toISOString();
}

function stableHash(value: string): string {
  let hash = 0xcbf29ce484222325n;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= BigInt(value.charCodeAt(index));
    hash = BigInt.asUintN(64, hash * 0x100000001b3n);
  }
  return hash.toString(16).padStart(16, "0");
}

export function coverageKeyFor(
  instrument: UniverseInstrument,
  sessionScope: SessionScope,
  logicalDataVariant: string,
): string {
  return [instrument.symbol, instrument.cadence, sessionScope, logicalDataVariant].join("|");
}

function currentEquitySession(
  calendar: MarketCalendarSnapshot,
  nowMs: number,
  sessionScope: Exclude<SessionScope, "ALL_TRADING">,
): NormalizedMarketSession | undefined {
  return calendar.sessions.find((session) => session.sessionKind === sessionScope
    && nowMs >= instant(session.opensAt, "session open")
    && nowMs < instant(session.closesAt, "session close"));
}

function latestEquityBoundary(
  cadence: Cadence,
  calendar: MarketCalendarSnapshot,
  nowMs: number,
  lagMs: number,
  sessionScope: Exclude<SessionScope, "ALL_TRADING">,
): number | undefined {
  if (cadence === "1Day") {
    if (sessionScope !== "REGULAR") return undefined;
    const eligible = calendar.sessions
      .filter((session) => session.sessionKind === "REGULAR")
      .filter((session) => instant(session.closesAt, "session close") + lagMs <= nowMs)
      .sort((left, right) => right.closesAt.localeCompare(left.closesAt));
    return eligible[0] ? instant(eligible[0].closesAt, "session close") : undefined;
  }

  const session = currentEquitySession(calendar, nowMs, sessionScope) ?? calendar.sessions
    .filter((candidate) => candidate.sessionKind === sessionScope)
    .filter((candidate) => instant(candidate.closesAt, "session close") + lagMs <= nowMs)
    .sort((left, right) => right.closesAt.localeCompare(left.closesAt))[0];
  if (!session) return undefined;
  const openMs = instant(session.opensAt, "session open");
  const closeMs = instant(session.closesAt, "session close");
  const availableMs = Math.min(nowMs - lagMs, closeMs) - openMs;
  if (availableMs < INTERVAL_MS[cadence]) return undefined;
  return openMs + Math.floor(availableMs / INTERVAL_MS[cadence]) * INTERVAL_MS[cadence];
}

function latestCryptoBoundary(cadence: Cadence, nowMs: number, lagMs: number): number {
  const intervalMs = INTERVAL_MS[cadence];
  return Math.floor((nowMs - lagMs) / intervalMs) * intervalMs;
}

function validateConfig(config: SchedulePolicyConfig): number {
  const floor = instant(config.retentionFloor, "retentionFloor");
  for (const cadence of ["1Min", "15Min", "1Day"] as const) {
    if (!Number.isFinite(config.overlapMs[cadence]) || config.overlapMs[cadence] < INTERVAL_MS[cadence]) {
      throw new Error(`overlapMs.${cadence} must be at least one interval`);
    }
    if (!Number.isFinite(config.finalizationLagMs[cadence]) || config.finalizationLagMs[cadence] < 0) {
      throw new Error(`finalizationLagMs.${cadence} must be non-negative`);
    }
  }
  if (!Number.isSafeInteger(config.maxBarsPerJob) || config.maxBarsPerJob < 1) {
    throw new Error("maxBarsPerJob must be a positive integer");
  }
  return floor;
}

function configuredEquitySessionScope(
  config: SchedulePolicyConfig,
  instrument: UniverseInstrument,
): Exclude<SessionScope, "ALL_TRADING"> {
  const scope = config.sessionScopeFor?.(instrument) ?? "REGULAR";
  if (scope === "ALL_TRADING") {
    throw new Error("equity acquisition scope must be PREMARKET or REGULAR");
  }
  return scope;
}

export class SchedulePolicy {
  private readonly config: SchedulePolicyConfig;

  constructor(config: SchedulePolicyConfig) {
    validateConfig(config);
    this.config = config;
  }

  plan(
    universe: UniverseSnapshot,
    calendar: MarketCalendarSnapshot,
    checkpoints: readonly CoverageCheckpoint[],
    now: Date,
  ): readonly AcquisitionJob[] {
    const nowMs = now.getTime();
    if (!Number.isFinite(nowMs)) throw new Error("now must be valid");
    const retentionFloorMs = validateConfig(this.config);
    const checkpointByKey = new Map(checkpoints.map((checkpoint) => [checkpoint.coverageKey, checkpoint]));
    const jobs: AcquisitionJob[] = [];

    for (const instrument of universe.instruments) {
      const isCrypto = instrument.providerRoute === "alpaca_crypto_bars";
      const equitySessionScope = isCrypto
        ? undefined
        : configuredEquitySessionScope(this.config, instrument);
      const sessionScope: SessionScope = isCrypto
        ? "ALL_TRADING"
        : equitySessionScope!;
      const variant = this.config.logicalDataVariant(instrument);
      const coverageKey = coverageKeyFor(instrument, sessionScope, variant);
      const checkpoint = checkpointByKey.get(coverageKey);
      const boundary = isCrypto
        ? latestCryptoBoundary(instrument.cadence, nowMs, this.config.finalizationLagMs[instrument.cadence])
        : latestEquityBoundary(
          instrument.cadence,
          calendar,
          nowMs,
          this.config.finalizationLagMs[instrument.cadence],
          equitySessionScope!,
        );
      if (boundary === undefined || boundary <= retentionFloorMs) continue;

      const missing = checkpoint?.missingRanges
        .map((range) => ({ start: instant(range.startInclusive, "missing range start"), end: instant(range.endExclusive, "missing range end") }))
        .filter((range) => range.start < range.end && range.start < boundary && range.end > retentionFloorMs)
        .sort((left, right) => left.start - right.start)[0];

      let startMs: number;
      let endMs = boundary;
      let mode: AcquisitionMode;
      let dueReason: AcquisitionJob["dueReason"];
      if (missing) {
        startMs = Math.max(retentionFloorMs, missing.start - this.config.overlapMs[instrument.cadence]);
        endMs = Math.min(boundary, missing.end);
        mode = "RECONCILE";
        dueReason = "MISSING_RANGE";
      } else if (!checkpoint?.completeThrough) {
        startMs = retentionFloorMs;
        mode = "CATCH_UP";
        dueReason = "NO_CHECKPOINT";
      } else {
        const completeThroughMs = instant(checkpoint.completeThrough, "checkpoint completeThrough");
        if (completeThroughMs >= boundary) continue;
        startMs = Math.max(retentionFloorMs, completeThroughMs - this.config.overlapMs[instrument.cadence]);
        mode = "INCREMENTAL";
        dueReason = "FORWARD_COVERAGE";
      }
      if (startMs >= endMs) continue;

      // Bound the provider range itself. Checking a bar count only after a page
      // has arrived is too late: a 24-hour crypto request can return 1,440 bars.
      // A checkpoint advances this deterministic window on the next Cron tick.
      endMs = Math.min(endMs, startMs + configRangeMs(instrument.cadence, this.config.maxBarsPerJob));

      const requestedRange = { startInclusive: iso(startMs), endExclusive: iso(endMs) };
      const identity = [universe.revision, calendar.revision, coverageKey, requestedRange.startInclusive, requestedRange.endExclusive, mode].join("|");
      jobs.push({
        jobId: `market-bars:${stableHash(identity)}`,
        jobKind: "MARKET_BARS",
        createdAt: now.toISOString(),
        universeRevision: universe.revision,
        calendarRevision: calendar.revision,
        instruments: [instrument],
        interval: instrument.cadence,
        requestedRange,
        sessionScope,
        mode,
        providerRoute: instrument.providerRoute,
        checkpointExpectations: [{
          coverageKey,
          expectedVersion: checkpoint?.version,
          observedCompleteThrough: checkpoint?.completeThrough,
        }],
        attempt: 0,
        dueReason,
      });
    }

    return jobs.sort((left, right) => left.jobId.localeCompare(right.jobId));
  }
}

function configRangeMs(cadence: Cadence, maxBarsPerJob: number): number {
  return INTERVAL_MS[cadence] * maxBarsPerJob;
}
