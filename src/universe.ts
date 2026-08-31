export type Cadence = "1Min" | "15Min" | "1Day";
export type ProviderRoute = "alpaca_stock_bars" | "alpaca_crypto_bars";

export type UniverseInstrument = {
  symbol: string;
  cadence: Cadence;
  providerRoute: ProviderRoute;
};

export type UniverseSnapshot = {
  revision: string;
  generatedAt: string;
  instruments: readonly UniverseInstrument[];
};

export const V01_UNIVERSE_REVISION = "stock-monitoring-universe-v0.1";
export const CANARY_V01_UNIVERSE_REVISION = "stock-monitoring-canary-v0.1";
export type UniverseProfile = "canary-v0.1" | "full-v0.1";

const TIER_A = [
  "SPY","QQQ","IWM","RSP","XLK","XLF","XLE","XLI","XLU",
  "NVDA","AMD","AVGO","CBRS","VRT","ANET","CEG","VST",
  "MSFT","GOOGL","AMZN","META","MSTR","RIOT","COIN","BTCUSD",
] as const;

const TIER_B = [
  "XLC","XLY","XLP","XLV","XLB","XLRE","MRVL","INTC","TSM","ASML","AMAT","LRCX","KLAC","MU","ARM",
  "ETN","PWR","GEV","NEE","MARA","CLSK","CORZ","IREN","CIFR",
] as const;

const TIER_C = [
  "EWJ","EWU","EWG","EWC","EWA","MCHI","EWT","EWY","INDA","EWZ","EWW",
  "TLT","IEF","HYG","LQD","GLD","SLV","USO","ETHUSD",
  "ORCL","PLTR","CRM","NOW","SNOW","WDC","STX","SNDK","HOOD",
  "JPM","BAC","GS","SCHW","COF","CAT","DE","UPS","FDX","UNP",
  "LMT","RTX","NOC","GD","XOM","CVX","FCX","NEM","WMT","COST","HD","TSLA","LLY","UNH","MRNA",
] as const;

const CRYPTO = new Set(["BTCUSD", "ETHUSD"]);

function routeFor(symbol: string): ProviderRoute {
  return CRYPTO.has(symbol) ? "alpaca_crypto_bars" : "alpaca_stock_bars";
}

function tier(symbols: readonly string[], cadence: Cadence): UniverseInstrument[] {
  return symbols.map((symbol) => ({ symbol, cadence, providerRoute: routeFor(symbol) }));
}

export const V01_UNIVERSE: readonly UniverseInstrument[] = Object.freeze([
  ...tier(TIER_A, "1Min"),
  ...tier(TIER_B, "15Min"),
  ...tier(TIER_C, "1Day"),
]);

const CANARY_SYMBOLS = ["SPY", "QQQ", "NVDA", "AMD", "BTCUSD"] as const;

export const CANARY_V01_UNIVERSE: readonly UniverseInstrument[] = Object.freeze(
  tier(CANARY_SYMBOLS, "1Min"),
);

export function loadUniverseV01(): readonly UniverseInstrument[] {
  return V01_UNIVERSE;
}

export function loadUniverseSnapshotV01(generatedAt = "2026-08-29T00:00:00.000Z"): UniverseSnapshot {
  return {
    revision: V01_UNIVERSE_REVISION,
    generatedAt,
    instruments: V01_UNIVERSE,
  };
}

export function loadUniverseSnapshot(
  profile: string,
  generatedAt = "2026-08-29T00:00:00.000Z",
): UniverseSnapshot {
  if (profile === "canary-v0.1") {
    return { revision: CANARY_V01_UNIVERSE_REVISION, generatedAt, instruments: CANARY_V01_UNIVERSE };
  }
  if (profile === "full-v0.1") return loadUniverseSnapshotV01(generatedAt);
  throw new Error(`unsupported UNIVERSE_PROFILE: ${profile}`);
}
