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

export async function fetchHistoricalBars(
  credentials: AlpacaCredentials,
  request: HistoricalBarRequest,
): Promise<HistoricalBarPage> {
  const { instrument } = request;
  const limit = Math.min(Math.max(request.limit ?? 1000, 1), 10000);

  if (instrument.providerRoute === "alpaca_stock_bars") {
    const url = new URL(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(instrument.symbol)}/bars`);
    url.searchParams.set("timeframe", timeframe(instrument.cadence));
    url.searchParams.set("start", request.startInclusive);
    url.searchParams.set("end", request.endExclusive);
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("adjustment", "raw");
    url.searchParams.set("feed", request.feed ?? "iex");
    url.searchParams.set("sort", "asc");
    if (request.pageToken) url.searchParams.set("page_token", request.pageToken);

    const response = await fetch(url, { headers: headers(credentials) });
    if (!response.ok) throw new Error(`alpaca stock bars failed: ${response.status}`);
    const payload = await response.json() as { bars?: AlpacaBar[]; next_page_token?: string | null };
    return {
      bars: (payload.bars ?? []).map((bar) => normalize(instrument.symbol, bar, `stock:${request.feed ?? "iex"}:raw`)),
      nextPageToken: payload.next_page_token ?? undefined,
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

  const response = await fetch(url, { headers: headers(credentials) });
  if (!response.ok) throw new Error(`alpaca crypto bars failed: ${response.status}`);
  const payload = await response.json() as { bars?: Record<string, AlpacaBar[]>; next_page_token?: string | null };
  const bars = payload.bars?.[alpacaSymbol] ?? [];
  return {
    bars: bars.map((bar) => normalize(instrument.symbol, bar, "crypto:us")),
    nextPageToken: payload.next_page_token ?? undefined,
  };
}
