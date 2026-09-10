import assert from "node:assert/strict";
import test from "node:test";
import { loadNewsAcquisitionRuntimeConfig } from "./news-acquisition-config.ts";

test("news is disabled by default with the reviewed bounded canary values", () => {
  assert.deepEqual(loadNewsAcquisitionRuntimeConfig({}), {
    enabled: false, cadenceMinutes: 5, overlapMinutes: 15, maxPagesPerSymbol: 2,
    maxArticlesPerRun: 200, symbols: ["AMD", "NVDA"],
  });
});
test("normalizes only the exact reviewed canary symbol order", () => {
  assert.deepEqual(loadNewsAcquisitionRuntimeConfig({ NEWS_ACQUISITION_CANARY_SYMBOLS: " amd, nvda " }).symbols, ["AMD", "NVDA"]);
  assert.throws(() => loadNewsAcquisitionRuntimeConfig({ NEWS_ACQUISITION_CANARY_SYMBOLS: "NVDA,AMD" }), /exactly AMD,NVDA/);
  assert.throws(() => loadNewsAcquisitionRuntimeConfig({ NEWS_ACQUISITION_CANARY_SYMBOLS: "AMD,NVDA,AAPL" }), /exactly AMD,NVDA/);
});
test("validates cadence and bounded budgets", () => {
  assert.throws(() => loadNewsAcquisitionRuntimeConfig({ NEWS_ACQUISITION_CADENCE_MINUTES: "0" }), /positive/);
  assert.throws(() => loadNewsAcquisitionRuntimeConfig({ NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL: "3" }), /between/);
});
