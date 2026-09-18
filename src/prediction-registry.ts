import {
  PREDICTION_HORIZONS,
  validatePredictionInputRegistry,
  validatePredictionTargetRegistry,
  type PredictionInputRegistry,
  type PredictionTargetRegistry,
} from "./prediction.ts";

export const SEMICONDUCTOR_CANARY_PROFILE = "semiconductor-canary-v0.1";

export type PredictionRegistryBundle = {
  input: PredictionInputRegistry;
  target: PredictionTargetRegistry;
};

export const SEMICONDUCTOR_CANARY_INPUT_REGISTRY: PredictionInputRegistry = Object.freeze({
  revision: "prediction-input:semiconductor-canary-v0.1",
  market: "JAPAN_EQUITIES",
  generatedAt: "2026-08-31T00:00:00.000Z",
  instruments: Object.freeze([
    {
      instrumentId: "tse:8035",
      displaySymbol: "8035",
      providerSymbolMappings: Object.freeze({ jquants: "8035" }),
      exchange: "TSE",
      themes: Object.freeze(["Semiconductor Manufacturing"]),
      baseCadence: "1Min" as const,
      enabled: true,
      validFrom: "2026-08-31",
    },
    {
      instrumentId: "tse:6857",
      displaySymbol: "6857",
      providerSymbolMappings: Object.freeze({ jquants: "6857" }),
      exchange: "TSE",
      themes: Object.freeze(["Semiconductor Manufacturing"]),
      baseCadence: "1Min" as const,
      enabled: true,
      validFrom: "2026-08-31",
    },
    {
      instrumentId: "tse:6146",
      displaySymbol: "6146",
      providerSymbolMappings: Object.freeze({ jquants: "6146" }),
      exchange: "TSE",
      themes: Object.freeze(["Semiconductor Manufacturing"]),
      baseCadence: "1Min" as const,
      enabled: true,
      validFrom: "2026-08-31",
    },
    {
      instrumentId: "tse:7735",
      displaySymbol: "7735",
      providerSymbolMappings: Object.freeze({ jquants: "7735" }),
      exchange: "TSE",
      themes: Object.freeze(["Semiconductor Manufacturing"]),
      baseCadence: "1Min" as const,
      enabled: true,
      validFrom: "2026-08-31",
    },
    {
      instrumentId: "tse:6920",
      displaySymbol: "6920",
      providerSymbolMappings: Object.freeze({ jquants: "6920" }),
      exchange: "TSE",
      themes: Object.freeze(["Semiconductor Manufacturing"]),
      baseCadence: "1Min" as const,
      enabled: true,
      validFrom: "2026-08-31",
    },
    {
      instrumentId: "tse:6525",
      displaySymbol: "6525",
      providerSymbolMappings: Object.freeze({ jquants: "6525" }),
      exchange: "TSE",
      themes: Object.freeze(["Semiconductor Manufacturing"]),
      baseCadence: "1Min" as const,
      enabled: true,
      validFrom: "2026-08-31",
    },
    {
      instrumentId: "tse:4063",
      displaySymbol: "4063",
      providerSymbolMappings: Object.freeze({ jquants: "4063" }),
      exchange: "TSE",
      themes: Object.freeze(["Semiconductor Materials"]),
      baseCadence: "1Min" as const,
      enabled: true,
      validFrom: "2026-08-31",
    },
    {
      instrumentId: "tse:3436",
      displaySymbol: "3436",
      providerSymbolMappings: Object.freeze({ jquants: "3436" }),
      exchange: "TSE",
      themes: Object.freeze(["Semiconductor Materials"]),
      baseCadence: "1Min" as const,
      enabled: true,
      validFrom: "2026-08-31",
    },
  ]),
});

export const SEMICONDUCTOR_CANARY_TARGET_REGISTRY: PredictionTargetRegistry = Object.freeze({
  revision: "prediction-target:semiconductor-canary-v0.1",
  generatedAt: "2026-08-31T00:00:00.000Z",
  targets: Object.freeze([
    {
      targetId: "us-theme:semiconductor-manufacturing",
      themeOrSector: "Semiconductor Manufacturing",
      constituentInstrumentIds: Object.freeze(["TSM", "ASML", "AMAT", "LRCX", "KLAC"]),
      labelPolicyVersion: "constituent-median-return-v0.1",
      enabledHorizons: PREDICTION_HORIZONS,
    },
    {
      targetId: "us-theme:semiconductor-materials",
      themeOrSector: "Semiconductor Materials",
      constituentInstrumentIds: Object.freeze(["ENTG", "Q", "MKSI", "MTRN"]),
      labelPolicyVersion: "constituent-median-return-v0.1",
      enabledHorizons: PREDICTION_HORIZONS,
    },
  ]),
});

export function loadPredictionRegistries(profile: string): PredictionRegistryBundle {
  if (profile !== SEMICONDUCTOR_CANARY_PROFILE) {
    throw new Error(`unsupported PREDICTION_TARGET_PROFILE: ${profile}`);
  }
  return {
    input: validatePredictionInputRegistry(SEMICONDUCTOR_CANARY_INPUT_REGISTRY),
    target: validatePredictionTargetRegistry(SEMICONDUCTOR_CANARY_TARGET_REGISTRY),
  };
}
