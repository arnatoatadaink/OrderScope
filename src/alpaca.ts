import type { Cadence, UniverseInstrument } from "./universe";

export type AlpacaCredentials = {
  keyId: string;
  secretKey: string;
};

export type HistoricalBarRequest = {
  instrument: UniverseInstrument;
  startInclusive: string;
  endExclusive: string;
  pageToken?: string;
  feed?: "iex" | "sip" | "delayed_sip";
  limit?: number;
};

export type ProviderNeutralBar = {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  tradeCount?: number;
  vwap?: number;
  provider: "alpaca";
  dataVariant: string;
};

export type HistoricalBarPage = {
  bars: readonly ProviderNeutralBar[];
  nextPageToken?: string;
};

export type ProviderRetryPolicy = {
  maxAttempts: number;
  baseBackoffMs: number;
  maxBackoffMs: number;
  maxRetryAfterMs: number;
};

export type HistoricalBarFetchOptions = {
  retry: ProviderRetryPolicy;
  sleep?: (delayMs: number) => Promise<void>;
  now?: () => number;
};

type AlpacaBar = {
  t: string;
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
  n?: number;
  vw?: number;
};

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isAlpacaBar(value: unknown): value is AlpacaBar {
  if (typeof value !== "object" || value === null) return false;
  const bar = value as Record<string, unknown>;
  return typeof bar.t === "string"
    && Number.isFinite(Date.parse(bar.t))
    && isFiniteNumber(bar.o)
    && isFiniteNumber(bar.h)
    && isFiniteNumber(bar.l)
    && isFiniteNumber(bar.c)
    && isFiniteNumber(bar.v)
    && (bar.n === undefined || isFiniteNumber(bar.n))
    && (bar.vw === undefined || isFiniteNumber(bar.vw));
}

function parseStockPayload(value: unknown): { bars: AlpacaBar[]; nextPageToken?: string } {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("alpaca stock bars response has an invalid schema");
  }
  const payload = value as Record<string, unknown>;
  const bars = payload.bars ?? [];
  const token = payload.next_page_token;
  if (!Array.isArray(bars) || !bars.every(isAlpacaBar)
    || (token !== undefined && token !== null && typeof token !== "string")) {
    throw new Error("alpaca stock bars response has an invalid schema");
  }
  return { bars, nextPageToken: typeof token === "string" ? token : undefined };
}

function parseCryptoPayload(value: unknown, symbol: string): { bars: AlpacaBar[]; nextPageToken?: string } {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("alpaca crypto bars response has an invalid schema");
  }
  const payload = value as Record<string, unknown>;
  const groups = payload.bars ?? {};
  const token = payload.next_page_token;
  if (typeof groups !== "object" || groups === null || Array.isArray(groups)
    || !Object.values(groups).every((bars) => Array.isArray(bars) && bars.every(isAlpacaBar))
    || (token !== undefined && token !== null && typeof token !== "string")) {
    throw new Error("alpaca crypto bars response has an invalid schema");
  }
  return {
    bars: (groups as Record<string, AlpacaBar[]>)[symbol] ?? [],
    nextPageToken: typeof token === "string" ? token : undefined,
  };
}

function timeframe(cadence: Cadence): string {
  switch (cadence) {
    case "1Min": return "1Min";
    case "15Min": return "15Min";
    case "1Day": return "1Day";
  }
}

function headers(credentials: AlpacaCredentials): HeadersInit {
  return {
    "APCA-API-KEY-ID": credentials.keyId,
    "APCA-API-SECRET-KEY": credentials.secretKey,
  };
}

function normalize(symbol: string, bar: AlpacaBar, dataVariant: string): ProviderNeutralBar {
  return {
    symbol,
    timestamp: bar.t,
    open: bar.o,
    high: bar.h,
    low: bar.l,
    close: bar.c,
    volume: bar.v,
    tradeCount: bar.n,
    vwap: bar.vw,
    provider: "alpaca",
    dataVariant,
  };
}

function insideHalfOpen(bar: AlpacaBar, startInclusive: string, endExclusive: string): boolean {
  const t = Date.parse(bar.t);
  return t >= Date.parse(startInclusive) && t < Date.parse(endExclusive);
}

const NEW_YORK_DATE = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit",
});

function newYorkDate(timestamp: string): string {
  const parts = NEW_YORK_DATE.formatToParts(new Date(timestamp));
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function nextDate(date: string): string {
  const value = new Date(`${date}T00:00:00Z`);
  value.setUTCDate(value.getUTCDate() + 1);
  return value.toISOString().slice(0, 10);
}

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

function newYorkMidnight(date: string): string {
  const [year, month, day] = date.split("-").map(Number);
  const wallClockAsUtc = Date.UTC(year, month - 1, day);
  let result = new Date(wallClockAsUtc);
  for (let pass = 0; pass < 2; pass += 1) {
    result = new Date(wallClockAsUtc - timezoneOffsetMilliseconds(result, "America/New_York"));
  }
  return result.toISOString();
}

function providerStockRange(request: HistoricalBarRequest): {
  startInclusive: string;
  endExclusive: string;
} {
  if (request.instrument.cadence !== "1Day") {
    return { startInclusive: request.startInclusive, endExclusive: request.endExclusive };
  }
  const firstMarketDate = newYorkDate(request.startInclusive);
  const lastMarketDate = newYorkDate(request.endExclusive);
  return {
    startInclusive: newYorkMidnight(firstMarketDate),
    endExclusive: newYorkMidnight(nextDate(lastMarketDate)),
  };
}

function insideRequestedStockRange(
  bar: AlpacaBar,
  request: HistoricalBarRequest,
): boolean {
  if (request.instrument.cadence !== "1Day") {
    return insideHalfOpen(bar, request.startInclusive, request.endExclusive);
  }
  // Alpaca timestamps daily stock bars at the left edge of the New York market
  // date, which is before the Regular-session open represented by Core ranges.
  const barDate = newYorkDate(bar.t);
  return barDate >= newYorkDate(request.startInclusive)
    && barDate <= newYorkDate(request.endExclusive);
}

function retryAfterMilliseconds(value: string | null, now: number): number | undefined {
  if (value === null) return undefined;
  const seconds = Number(value);
  if (Number.isFinite(seconds) && seconds >= 0) return seconds * 1_000;
  const date = Date.parse(value);
  if (!Number.isFinite(date)) return undefined;
  return Math.max(0, date - now);
}

function isTransientStatus(status: number): boolean {
  return status === 429 || status >= 500 && status <= 599;
}

async function fetchWithRetry(
  url: URL,
  credentials: AlpacaCredentials,
  resource: string,
  options?: HistoricalBarFetchOptions,
): Promise<Response> {
  const retry = options?.retry;
  const maxAttempts = retry?.maxAttempts ?? 1;
  const sleep = options?.sleep ?? ((delayMs) => new Promise((resolve) => setTimeout(resolve, delayMs)));
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const response = await fetch(url, { headers: headers(credentials) });
    if (response.ok) return response;
    if (!retry || !isTransientStatus(response.status) || attempt === maxAttempts) {
      throw new Error(`${resource} failed: ${response.status}${isTransientStatus(response.status) && attempt === maxAttempts ? ` after ${attempt} attempts` : ""}`);
    }
    const exponential = Math.min(retry.baseBackoffMs * 2 ** (attempt - 1), retry.maxBackoffMs);
    const requested = retryAfterMilliseconds(response.headers.get("retry-after"), (options?.now ?? Date.now)());
    await sleep(Math.min(requested ?? exponential, retry.maxRetryAfterMs));
  }
  throw new Error(`${resource} failed after ${maxAttempts} attempts`);
}

export async function fetchHistoricalBars(
  credentials: AlpacaCredentials,
  request: HistoricalBarRequest,
  options?: HistoricalBarFetchOptions,
): Promise<HistoricalBarPage> {
  const { instrument } = request;
  const limit = Math.min(Math.max(request.limit ?? 1000, 1), 10000);

  if (instrument.providerRoute === "alpaca_stock_bars") {
    const logicalFeed = request.feed ?? "iex";
    const apiFeed = logicalFeed === "delayed_sip" ? "sip" : logicalFeed;
    const url = new URL(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(instrument.symbol)}/bars`);
    url.searchParams.set("timeframe", timeframe(instrument.cadence));
    const providerRange = providerStockRange(request);
    url.searchParams.set("start", providerRange.startInclusive);
    // Alpaca's end parameter is inclusive while Core windows are half-open.
    // Request the boundary and filter locally so the adapter preserves [start, end).
    url.searchParams.set("end", providerRange.endExclusive);
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("adjustment", "raw");
    url.searchParams.set("feed", apiFeed);
    url.searchParams.set("sort", "asc");
    if (request.pageToken) url.searchParams.set("page_token", request.pageToken);

    const response = await fetchWithRetry(url, credentials, "alpaca stock bars", options);
    const payload = parseStockPayload(await response.json());
    return {
      bars: payload.bars
        .filter((bar) => insideRequestedStockRange(bar, request))
        .map((bar) => normalize(instrument.symbol, bar, `stock:${logicalFeed}:raw`)),
      nextPageToken: payload.nextPageToken,
    };
  }

  const alpacaSymbol = instrument.symbol === "BTCUSD" ? "BTC/USD" : instrument.symbol === "ETHUSD" ? "ETH/USD" : instrument.symbol;
  const url = new URL("https://data.alpaca.markets/v1beta3/crypto/us/bars");
  url.searchParams.set("symbols", alpacaSymbol);
  url.searchParams.set("timeframe", timeframe(instrument.cadence));
  url.searchParams.set("start", request.startInclusive);
  url.searchParams.set("end", request.endExclusive);
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("sort", "asc");
  if (request.pageToken) url.searchParams.set("page_token", request.pageToken);

  const response = await fetchWithRetry(url, credentials, "alpaca crypto bars", options);
  const payload = parseCryptoPayload(await response.json(), alpacaSymbol);
  return {
    bars: payload.bars
      .filter((bar) => insideHalfOpen(bar, request.startInclusive, request.endExclusive))
      .map((bar) => normalize(instrument.symbol, bar, "crypto:us")),
    nextPageToken: payload.nextPageToken,
  };
}
