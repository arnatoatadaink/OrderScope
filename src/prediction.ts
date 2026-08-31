import type { MarketCalendarSnapshot, NormalizedMarketSession } from "./calendar.ts";
import {
  SchedulePolicy,
  type AcquisitionJob,
  type CoverageCheckpoint,
  type SchedulePolicyConfig,
} from "./schedule.ts";
import type { Cadence, UniverseSnapshot } from "./universe.ts";

export const PREDICTION_HORIZONS = [
  "PM_OPEN",
  "PM_SESSION",
  "REG_OPEN",
  "REG_SESSION",
] as const;

export type PredictionHorizon = typeof PREDICTION_HORIZONS[number];

export type PredictionPriceAnchor =
  | "PREVIOUS_REGULAR_CLOSE"
  | "PM_OPEN_ANCHOR"
  | "PREOPEN_ANCHOR"
  | "REG_OPEN_ANCHOR"
  | "REGULAR_CLOSE_ANCHOR";

export const PREDICTION_HORIZON_ANCHORS = {
  PM_OPEN: { start: "PREVIOUS_REGULAR_CLOSE", end: "PM_OPEN_ANCHOR" },
  PM_SESSION: { start: "PM_OPEN_ANCHOR", end: "PREOPEN_ANCHOR" },
  REG_OPEN: { start: "PREOPEN_ANCHOR", end: "REG_OPEN_ANCHOR" },
  REG_SESSION: { start: "REG_OPEN_ANCHOR", end: "REGULAR_CLOSE_ANCHOR" },
} as const satisfies Readonly<Record<PredictionHorizon, {
  start: PredictionPriceAnchor;
  end: PredictionPriceAnchor;
}>>;

export type PredictionInputInstrument = {
  instrumentId: string;
  displaySymbol: string;
  providerSymbolMappings: Readonly<Record<string, string>>;
  exchange: string;
  themes: readonly string[];
  baseCadence: Cadence;
  enabled: boolean;
  validFrom: string;
  validUntil?: string;
};

export type PredictionInputRegistry = {
  revision: string;
  market: "JAPAN_EQUITIES";
  generatedAt: string;
  instruments: readonly PredictionInputInstrument[];
};

export type PredictionTarget = {
  targetId: string;
  themeOrSector: string;
  primaryLabelInstrumentId?: string;
  constituentInstrumentIds: readonly string[];
  marketProxyId?: string;
  labelPolicyVersion: string;
  enabledHorizons: readonly PredictionHorizon[];
};

export type PredictionTargetRegistry = {
  revision: string;
  generatedAt: string;
  targets: readonly PredictionTarget[];
};

export type PredictionInputSnapshot = {
  snapshotId: string;
  inputRegistryRevision: string;
  providerRoute: string;
  logicalDataVariant: string;
  japanMarketDate: string;
  featureCutoff: string;
  generatedAt: string;
  availableAtMax: string;
  calendarRevision: string;
  coverageState: "COMPLETE" | "PARTIAL" | "UNKNOWN" | "BLOCKED";
  missingInputs: readonly string[];
  featureSchemaVersion: string;
  features: Readonly<Record<string, number | null>>;
};

export type PredictionRecord = {
  predictionId: string;
  targetId: string;
  horizon: PredictionHorizon;
  generatedAt: string;
  asOf: string;
  inputSnapshotId: string;
  inputRegistryRevision: string;
  targetRegistryRevision: string;
  modelId: string;
  modelVersion: string;
  featureSchemaVersion: string;
  labelPolicyVersion: string;
  upProbability: number;
  expectedReturnPct: number;
  predictedVolatilityPct: number;
  p10ReturnPct: number;
  p90ReturnPct: number;
  quality: "COMPLETE" | "PARTIAL" | "STALE" | "UNAVAILABLE";
  qualityReasons: readonly string[];
  realizedLabelRef?: string;
};

export type ObservationAvailability = {
  eventTime: string;
  retrievedAt: string;
  availableAt: string;
};

export type PredictionAvailabilityBoundary = {
  featureCutoff: string;
  predictionGeneratedAt: string;
};

export type PredictionAnchorWindow = {
  anchor: "PM_OPEN_ANCHOR" | "PREOPEN_ANCHOR" | "REG_OPEN_ANCHOR";
  startInclusive: string;
  endExclusive: string;
};

const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const NAMESPACED_ID_PATTERN = /^[^:\s]+:[^:\s]+/;
const MINUTE_MS = 60_000;

function isCadence(value: unknown): value is Cadence {
  return value === "1Min" || value === "15Min" || value === "1Day";
}

function isPredictionHorizon(value: unknown): value is PredictionHorizon {
  return typeof value === "string" && PREDICTION_HORIZONS.includes(value as PredictionHorizon);
}

function instant(value: string, name: string): number {
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) throw new Error(`${name} must be a valid instant`);
  return parsed;
}

function date(value: string, name: string): void {
  const parsed = new Date(`${value}T00:00:00Z`);
  if (!DATE_PATTERN.test(value) || Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) {
    throw new Error(`${name} must be a valid YYYY-MM-DD date`);
  }
}

function nonEmpty(value: string, name: string): void {
  if (!value.trim()) throw new Error(`${name} must be non-empty`);
}

function unique(values: readonly string[], name: string): void {
  if (new Set(values).size !== values.length) throw new Error(`${name} must not contain duplicates`);
}

export function validatePredictionInputRegistry(
  registry: PredictionInputRegistry,
): PredictionInputRegistry {
  nonEmpty(registry.revision, "input registry revision");
  if (registry.market !== "JAPAN_EQUITIES") throw new Error("input registry market must be JAPAN_EQUITIES");
  instant(registry.generatedAt, "input registry generatedAt");
  unique(registry.instruments.map((instrument) => instrument.instrumentId), "input instrument ids");
  for (const instrument of registry.instruments) {
    if (!NAMESPACED_ID_PATTERN.test(instrument.instrumentId)) {
      throw new Error(`input instrument id must be namespaced: ${instrument.instrumentId}`);
    }
    nonEmpty(instrument.displaySymbol, "input displaySymbol");
    nonEmpty(instrument.exchange, "input exchange");
    if (!isCadence(instrument.baseCadence)) throw new Error(`input baseCadence is invalid: ${instrument.instrumentId}`);
    if (typeof instrument.enabled !== "boolean") throw new Error(`input enabled must be boolean: ${instrument.instrumentId}`);
    if (Object.keys(instrument.providerSymbolMappings).length === 0
      || Object.entries(instrument.providerSymbolMappings).some(([provider, symbol]) => !provider.trim() || !symbol.trim())) {
      throw new Error(`input provider symbol mappings must be non-empty: ${instrument.instrumentId}`);
    }
    if (instrument.themes.length === 0 || instrument.themes.some((theme) => !theme.trim())) {
      throw new Error(`input themes must be non-empty: ${instrument.instrumentId}`);
    }
    unique(instrument.themes, `input themes for ${instrument.instrumentId}`);
    date(instrument.validFrom, "input validFrom");
    if (instrument.validUntil !== undefined) {
      date(instrument.validUntil, "input validUntil");
      if (instrument.validUntil <= instrument.validFrom) {
        throw new Error(`input validUntil must follow validFrom: ${instrument.instrumentId}`);
      }
    }
  }
  return registry;
}

export function validatePredictionTargetRegistry(
  registry: PredictionTargetRegistry,
): PredictionTargetRegistry {
  nonEmpty(registry.revision, "target registry revision");
  instant(registry.generatedAt, "target registry generatedAt");
  unique(registry.targets.map((target) => target.targetId), "prediction target ids");
  for (const target of registry.targets) {
    nonEmpty(target.targetId, "targetId");
    nonEmpty(target.themeOrSector, "themeOrSector");
    nonEmpty(target.labelPolicyVersion, "labelPolicyVersion");
    if (target.primaryLabelInstrumentId !== undefined) nonEmpty(target.primaryLabelInstrumentId, "primaryLabelInstrumentId");
    if (target.marketProxyId !== undefined) nonEmpty(target.marketProxyId, "marketProxyId");
    if (target.constituentInstrumentIds.some((instrumentId) => !instrumentId.trim())) {
      throw new Error(`constituents must be non-empty: ${target.targetId}`);
    }
    unique(target.constituentInstrumentIds, `constituents for ${target.targetId}`);
    unique(target.enabledHorizons, `enabled horizons for ${target.targetId}`);
    if (!target.enabledHorizons.every(isPredictionHorizon)) {
      throw new Error(`enabled horizons contain an invalid value: ${target.targetId}`);
    }
    if (target.enabledHorizons.length === 0) {
      throw new Error(`enabled horizons must be non-empty: ${target.targetId}`);
    }
    if (!target.primaryLabelInstrumentId && target.constituentInstrumentIds.length === 0) {
      throw new Error(`target requires a primary label instrument or constituents: ${target.targetId}`);
    }
  }
  return registry;
}

export function assertObservationUsableForPrediction(
  observation: ObservationAvailability,
  boundary: PredictionAvailabilityBoundary,
): void {
  const eventTime = instant(observation.eventTime, "eventTime");
  const retrievedAt = instant(observation.retrievedAt, "retrievedAt");
  const availableAt = instant(observation.availableAt, "availableAt");
  const featureCutoff = instant(boundary.featureCutoff, "featureCutoff");
  const generatedAt = instant(boundary.predictionGeneratedAt, "predictionGeneratedAt");
  if (eventTime > featureCutoff) throw new Error("eventTime exceeds featureCutoff");
  if (retrievedAt > generatedAt) throw new Error("retrievedAt exceeds predictionGeneratedAt");
  if (availableAt > generatedAt) throw new Error("availableAt exceeds predictionGeneratedAt");
}

function session(
  calendar: MarketCalendarSnapshot,
  marketDate: string,
  kind: "PREMARKET" | "REGULAR",
): NormalizedMarketSession {
  const matches = calendar.sessions.filter((candidate) =>
    candidate.marketDate === marketDate && candidate.sessionKind === kind,
  );
  if (matches.length !== 1) {
    throw new Error(`calendar requires exactly one ${kind} session for ${marketDate}`);
  }
  return matches[0]!;
}

export function predictionAnchorWindows(
  calendar: MarketCalendarSnapshot,
  marketDate: string,
): readonly PredictionAnchorWindow[] {
  date(marketDate, "marketDate");
  const premarket = session(calendar, marketDate, "PREMARKET");
  const regular = session(calendar, marketDate, "REGULAR");
  const premarketOpen = instant(premarket.opensAt, "Premarket open");
  const regularOpen = instant(regular.opensAt, "Regular open");
  const regularClose = instant(regular.closesAt, "Regular close");
  if (instant(premarket.closesAt, "Premarket close") !== regularOpen) {
    throw new Error("Premarket close must equal Regular open");
  }
  if (premarketOpen + 15 * MINUTE_MS > regularOpen || regularOpen + 15 * MINUTE_MS > regularClose) {
    throw new Error("calendar session is too short for prediction anchor windows");
  }
  return [{
    anchor: "PM_OPEN_ANCHOR",
    startInclusive: new Date(premarketOpen).toISOString(),
    endExclusive: new Date(premarketOpen + 15 * MINUTE_MS).toISOString(),
  }, {
    anchor: "PREOPEN_ANCHOR",
    startInclusive: new Date(regularOpen - 5 * MINUTE_MS).toISOString(),
    endExclusive: new Date(regularOpen).toISOString(),
  }, {
    anchor: "REG_OPEN_ANCHOR",
    startInclusive: new Date(regularOpen).toISOString(),
    endExclusive: new Date(regularOpen + 15 * MINUTE_MS).toISOString(),
  }];
}

export function predictionReadinessDeadline(
  calendar: MarketCalendarSnapshot,
  marketDate: string,
): string {
  date(marketDate, "marketDate");
  const premarket = session(calendar, marketDate, "PREMARKET");
  return new Date(instant(premarket.opensAt, "Premarket open") - 5 * MINUTE_MS).toISOString();
}

export type PremarketAcquisitionPlanRequest = {
  acquisitionUniverse: UniverseSnapshot;
  calendar: MarketCalendarSnapshot;
  checkpoints: readonly CoverageCheckpoint[];
  now: Date;
  scheduleConfig: Omit<SchedulePolicyConfig, "sessionScopeFor">;
};

export function planPredictionPremarketAcquisition(
  request: PremarketAcquisitionPlanRequest,
): readonly AcquisitionJob[] {
  for (const instrument of request.acquisitionUniverse.instruments) {
    if (instrument.providerRoute !== "alpaca_stock_bars") {
      throw new Error(`Premarket acquisition requires an equity route: ${instrument.symbol}`);
    }
    if (instrument.cadence === "1Day") {
      throw new Error(`Premarket acquisition requires an intraday cadence: ${instrument.symbol}`);
    }
  }
  return new SchedulePolicy({
    ...request.scheduleConfig,
    sessionScopeFor: () => "PREMARKET",
  }).plan(
    request.acquisitionUniverse,
    request.calendar,
    request.checkpoints,
    request.now,
  );
}
