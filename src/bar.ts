import type { ProviderNeutralBar } from "./alpaca";
import type { MarketCalendarSnapshot, NormalizedMarketSession } from "./calendar";
import type { SessionScope } from "./schedule";
import type { Cadence, UniverseInstrument } from "./universe";

export type NormalizedBarSessionKind = "REGULAR" | "ALL_TRADING";

export type NormalizedMarketBar = {
  instrumentId: string;
  interval: Cadence;
  barStartUtc: string;
  barEndUtc: string;
  marketDate: string;
  sessionKind: NormalizedBarSessionKind;
  isShortenedSession: boolean;
  logicalDataVariant: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  tradeCount?: number;
  vwap?: number;
  provider: ProviderNeutralBar["provider"];
  sourceTimestamp: string;
  calendarRevision?: string;
};

export type BarRejectionCode =
  | "WRONG_INSTRUMENT"
  | "INVALID_TIMESTAMP"
  | "INVALID_NUMERIC_VALUE"
  | "INVALID_OHLC"
  | "INVALID_ACTIVITY"
  | "SESSION_MISMATCH"
  | "GRID_MISMATCH";

export type BarNormalizationResult =
  | { outcome: "NORMALIZED"; bar: NormalizedMarketBar }
  | { outcome: "REJECTED"; code: BarRejectionCode; reason: string };

const INTERVAL_MS: Record<Cadence, number> = {
  "1Min": 60_000,
  "15Min": 15 * 60_000,
  "1Day": 24 * 60 * 60_000,
};

const MARKET_DATE = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit",
});

function reject(code: BarRejectionCode, reason: string): BarNormalizationResult {
  return { outcome: "REJECTED", code, reason };
}

function iso(ms: number): string {
  return new Date(ms).toISOString();
}

function marketDate(ms: number): string {
  const parts = MARKET_DATE.formatToParts(new Date(ms));
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function regularSessionForDaily(
  calendar: MarketCalendarSnapshot,
  sourceMs: number,
): NormalizedMarketSession | undefined {
  const date = marketDate(sourceMs);
  return calendar.sessions.find((session) => session.sessionKind === "REGULAR" && session.marketDate === date);
}

function validateValues(bar: ProviderNeutralBar): BarNormalizationResult | undefined {
  const prices = [bar.open, bar.high, bar.low, bar.close];
  if (!prices.every(Number.isFinite) || prices.some((value) => value < 0)
    || (bar.vwap !== undefined && (!Number.isFinite(bar.vwap) || bar.vwap < 0))) {
    return reject("INVALID_NUMERIC_VALUE", "prices and vwap must be finite non-negative numbers");
  }
  if (bar.high < Math.max(bar.open, bar.low, bar.close)
    || bar.low > Math.min(bar.open, bar.high, bar.close)) {
    return reject("INVALID_OHLC", "high/low do not contain open and close");
  }
  if (!Number.isFinite(bar.volume) || bar.volume < 0
    || (bar.tradeCount !== undefined
      && (!Number.isSafeInteger(bar.tradeCount) || bar.tradeCount < 0))) {
    return reject("INVALID_ACTIVITY", "volume and trade count must be non-negative");
  }
}

export function normalizeMarketBar(
  source: ProviderNeutralBar,
  instrument: UniverseInstrument,
  calendar: MarketCalendarSnapshot,
  sessionScope: SessionScope,
): BarNormalizationResult {
  if (source.symbol !== instrument.symbol) {
    return reject("WRONG_INSTRUMENT", "provider symbol does not match the requested instrument");
  }
  const invalidValues = validateValues(source);
  if (invalidValues) return invalidValues;
  const sourceMs = Date.parse(source.timestamp);
  if (!Number.isFinite(sourceMs)) return reject("INVALID_TIMESTAMP", "source timestamp is not a valid instant");

  if (instrument.providerRoute === "alpaca_crypto_bars") {
    if (sessionScope !== "ALL_TRADING") return reject("SESSION_MISMATCH", "crypto bars require ALL_TRADING scope");
    const intervalMs = INTERVAL_MS[instrument.cadence];
    if (sourceMs % intervalMs !== 0) return reject("GRID_MISMATCH", "crypto bar is not aligned to the UTC interval grid");
    return { outcome: "NORMALIZED", bar: {
      instrumentId: instrument.symbol, interval: instrument.cadence,
      barStartUtc: iso(sourceMs), barEndUtc: iso(sourceMs + intervalMs),
      marketDate: iso(sourceMs).slice(0, 10), sessionKind: "ALL_TRADING",
      isShortenedSession: false, logicalDataVariant: source.dataVariant,
      open: source.open, high: source.high, low: source.low, close: source.close,
      volume: source.volume, tradeCount: source.tradeCount, vwap: source.vwap,
      provider: source.provider, sourceTimestamp: iso(sourceMs),
    } };
  }

  if (sessionScope !== "REGULAR") return reject("SESSION_MISMATCH", "equity bars require REGULAR scope in v0.1");
  let session: NormalizedMarketSession | undefined;
  let startMs: number;
  let endMs: number;
  if (instrument.cadence === "1Day") {
    session = regularSessionForDaily(calendar, sourceMs);
    if (!session) return reject("SESSION_MISMATCH", "daily bar market date has no authoritative Regular session");
    startMs = Date.parse(session.opensAt);
    endMs = Date.parse(session.closesAt);
  } else {
    const intervalMs = INTERVAL_MS[instrument.cadence];
    session = calendar.sessions.find((candidate) => candidate.sessionKind === "REGULAR"
      && sourceMs >= Date.parse(candidate.opensAt) && sourceMs < Date.parse(candidate.closesAt));
    if (!session) return reject("SESSION_MISMATCH", "intraday bar starts outside an authoritative Regular session");
    const openMs = Date.parse(session.opensAt);
    if ((sourceMs - openMs) % intervalMs !== 0) {
      return reject("GRID_MISMATCH", "intraday bar is not aligned to the session-open grid");
    }
    startMs = sourceMs;
    endMs = sourceMs + intervalMs;
    if (endMs > Date.parse(session.closesAt)) {
      return reject("SESSION_MISMATCH", "intraday bar straddles the Regular session close");
    }
  }

  return { outcome: "NORMALIZED", bar: {
    instrumentId: instrument.symbol, interval: instrument.cadence,
    barStartUtc: iso(startMs), barEndUtc: iso(endMs), marketDate: session.marketDate,
    sessionKind: "REGULAR", isShortenedSession: session.isShortened,
    logicalDataVariant: source.dataVariant,
    open: source.open, high: source.high, low: source.low, close: source.close,
    volume: source.volume, tradeCount: source.tradeCount, vwap: source.vwap,
    provider: source.provider, sourceTimestamp: iso(sourceMs), calendarRevision: session.calendarRevision,
  } };
}
