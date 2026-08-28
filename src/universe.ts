export type Cadence = "1Min" | "15Min" | "1Day";
export type ProviderRoute = "alpaca_stock_bars" | "alpaca_crypto_bars";

export type UniverseInstrument = {
  symbol: string;
  cadence: Cadence;
  providerRoute: ProviderRoute;
};

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

export function loadUniverseV01(): readonly UniverseInstrument[] {
  return V01_UNIVERSE;
}
