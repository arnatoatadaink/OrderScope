import type { ProviderNeutralBar } from "./alpaca";

export const L1_003_NVDA_DEFAULT_SESSIONS = Object.freeze([
  "2026-09-09",
  "2026-09-10",
  "2026-09-11",
  "2026-09-14",
  "2026-09-15",
  "2026-09-16",
  "2026-09-17",
  "2026-09-18",
  "2026-09-21",
] as const);

export type LocalHistorySessionPlan = {
  marketDate: string;
  startInclusive: string;
  endExclusive: string;
  expectedBars: number;
};

export type LocalHistorySessionValidation = {
  marketDate: string;
  expectedBars: number;
  actualBars: number;
  firstTimestamp?: string;
  lastTimestamp?: string;
  duplicateTimestamps: string[];
  outOfRangeTimestamps: string[];
  complete: boolean;
};

function timezoneOffsetMilliseconds(instant: Date, timeZone: string): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).formatToParts(instant);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return Date.UTC(
    Number(values.year),
    Number(values.month) - 1,
    Number(values.day),
    Number(values.hour),
    Number(values.minute),
    Number(values.second),
  ) - instant.getTime();
}

function newYorkWallClockUtc(date: string, hour: number, minute: number): string {
  const [year, month, day] = date.split("-").map(Number);
  const wallClockAsUtc = Date.UTC(year, month - 1, day, hour, minute);
  let result = new Date(wallClockAsUtc);
  for (let pass = 0; pass < 2; pass += 1) {
    result = new Date(wallClockAsUtc - timezoneOffsetMilliseconds(result, "America/New_York"));
  }
  return result.toISOString();
}

export function planRegularSession(marketDate: string): LocalHistorySessionPlan {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(marketDate)) {
    throw new Error(`invalid market date: ${marketDate}`);
  }
  return {
    marketDate,
    startInclusive: newYorkWallClockUtc(marketDate, 9, 30),
    endExclusive: newYorkWallClockUtc(marketDate, 16, 0),
    expectedBars: 390,
  };
}

export function validateRegularSession(
  plan: LocalHistorySessionPlan,
  bars: readonly ProviderNeutralBar[],
): LocalHistorySessionValidation {
  const timestamps = bars.map((bar) => bar.timestamp);
  const seen = new Set<string>();
  const duplicateTimestamps: string[] = [];
  for (const timestamp of timestamps) {
    if (seen.has(timestamp)) duplicateTimestamps.push(timestamp);
    seen.add(timestamp);
  }

  const start = Date.parse(plan.startInclusive);
  const end = Date.parse(plan.endExclusive);
  const outOfRangeTimestamps = timestamps.filter((timestamp) => {
    const value = Date.parse(timestamp);
    return !Number.isFinite(value) || value < start || value >= end;
  });

  const sorted = [...timestamps].sort();
  return {
    marketDate: plan.marketDate,
    expectedBars: plan.expectedBars,
    actualBars: bars.length,
    ...(sorted[0] ? { firstTimestamp: sorted[0] } : {}),
    ...(sorted.at(-1) ? { lastTimestamp: sorted.at(-1) } : {}),
    duplicateTimestamps,
    outOfRangeTimestamps,
    complete: bars.length === plan.expectedBars
      && duplicateTimestamps.length === 0
      && outOfRangeTimestamps.length === 0,
  };
}
