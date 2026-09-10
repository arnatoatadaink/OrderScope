export type NewsAcquisitionConfigEnv = {
  NEWS_ACQUISITION_ENABLED?: string;
  NEWS_ACQUISITION_CADENCE_MINUTES?: string;
  NEWS_ACQUISITION_OVERLAP_MINUTES?: string;
  NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL?: string;
  NEWS_ACQUISITION_MAX_ARTICLES_PER_RUN?: string;
  NEWS_ACQUISITION_CANARY_SYMBOLS?: string;
};

export type NewsAcquisitionRuntimeConfig = {
  enabled: boolean;
  cadenceMinutes: number;
  overlapMinutes: number;
  maxPagesPerSymbol: number;
  maxArticlesPerRun: number;
  symbols: readonly ["AMD", "NVDA"];
};

function integer(value: string, name: string, minimum: number, maximum: number): number {
  if (!/^[1-9]\d*$/.test(value)) throw new Error(`${name} must be a positive base-10 integer`);
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new Error(`${name} must be between ${minimum} and ${maximum}`);
  }
  return parsed;
}

export function loadNewsAcquisitionRuntimeConfig(env: NewsAcquisitionConfigEnv): NewsAcquisitionRuntimeConfig {
  const enabledValue = env.NEWS_ACQUISITION_ENABLED ?? "false";
  if (enabledValue !== "true" && enabledValue !== "false") {
    throw new Error("NEWS_ACQUISITION_ENABLED must be true or false");
  }
  const symbols = (env.NEWS_ACQUISITION_CANARY_SYMBOLS ?? "AMD,NVDA")
    .split(",").map((symbol) => symbol.trim().toUpperCase()).filter(Boolean);
  if (symbols.length !== 2 || symbols[0] !== "AMD" || symbols[1] !== "NVDA") {
    throw new Error("NEWS_ACQUISITION_CANARY_SYMBOLS must be exactly AMD,NVDA");
  }
  const cadenceMinutes = integer(env.NEWS_ACQUISITION_CADENCE_MINUTES ?? "5", "NEWS_ACQUISITION_CADENCE_MINUTES", 1, 60);
  const overlapMinutes = integer(env.NEWS_ACQUISITION_OVERLAP_MINUTES ?? "15", "NEWS_ACQUISITION_OVERLAP_MINUTES", cadenceMinutes, 1_440);
  return {
    enabled: enabledValue === "true", cadenceMinutes, overlapMinutes,
    maxPagesPerSymbol: integer(env.NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL ?? "2", "NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL", 1, 2),
    maxArticlesPerRun: integer(env.NEWS_ACQUISITION_MAX_ARTICLES_PER_RUN ?? "200", "NEWS_ACQUISITION_MAX_ARTICLES_PER_RUN", 1, 200),
    symbols: ["AMD", "NVDA"],
  };
}
