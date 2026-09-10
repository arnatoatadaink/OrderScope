import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import { loadNewsAcquisitionRuntimeConfig } from "./news-acquisition-config.ts";
import { NEWS_COVERAGE_KEY, newsDryRun, planNewsAcquisition } from "./news-schedule.ts";

const config = loadNewsAcquisitionRuntimeConfig({ NEWS_ACQUISITION_ENABLED: "true" });
const calendar: MarketCalendarSnapshot = { market: "US_EQUITIES", revision: "fixture-v1", generatedAt: "2026-09-10T00:00:00Z",
  dateRange: { startInclusive: "2026-09-10", endExclusive: "2026-09-11" }, sessions: [
    { marketDate: "2026-09-10", sessionKind: "PREMARKET", opensAt: "2026-09-10T08:00:00.000Z", closesAt: "2026-09-10T13:30:00.000Z", isShortened: false, calendarRevision: "fixture-v1" },
    { marketDate: "2026-09-10", sessionKind: "REGULAR", opensAt: "2026-09-10T13:30:00.000Z", closesAt: "2026-09-10T20:00:00.000Z", isShortened: false, calendarRevision: "fixture-v1" },
  ] };

test("plans once only on an eligible five-minute boundary", () => {
  assert.equal(planNewsAcquisition(config, calendar, undefined, new Date("2026-09-10T14:00:00Z")).length, 1);
  assert.equal(planNewsAcquisition(config, calendar, undefined, new Date("2026-09-10T14:01:00Z")).length, 0);
  assert.equal(planNewsAcquisition(config, calendar, undefined, new Date("2026-09-10T21:00:00Z")).length, 0);
});
test("no checkpoint is bounded and an existing checkpoint receives overlap", () => {
  const initial = planNewsAcquisition(config, calendar, undefined, new Date("2026-09-10T14:00:00Z"))[0]!;
  assert.deepEqual(initial.requestedRange, { startInclusive: "2026-09-10T13:45:00.000Z", endExclusive: "2026-09-10T14:00:00.000Z" });
  const incremental = planNewsAcquisition(config, calendar, { coverageKey: NEWS_COVERAGE_KEY,
    completeThrough: "2026-09-10T13:55:00.000Z", version: 2 }, new Date("2026-09-10T14:05:00Z"))[0]!;
  assert.deepEqual(incremental.requestedRange, { startInclusive: "2026-09-10T13:40:00.000Z", endExclusive: "2026-09-10T14:05:00.000Z" });
});
test("missed ticks recover through the next bounded range and dry-run is side-effect free", () => {
  const job = planNewsAcquisition(config, calendar, { coverageKey: NEWS_COVERAGE_KEY,
    completeThrough: "2026-09-10T13:50:00.000Z", version: 1 }, new Date("2026-09-10T14:10:00Z"))[0]!;
  assert.deepEqual(job.requestedRange, { startInclusive: "2026-09-10T13:35:00.000Z", endExclusive: "2026-09-10T14:10:00.000Z" });
  assert.deepEqual(newsDryRun(job), { mutationCount: 0, providerCalls: 0, job: {
    jobId: job.jobId, symbols: ["AMD", "NVDA"], requestedRange: job.requestedRange,
    maxPagesPerSymbol: 2, maxArticlesPerRun: 200,
  } });
});
test("disabled news does not affect market scheduling", () => {
  assert.deepEqual(planNewsAcquisition({ ...config, enabled: false }, calendar, undefined, new Date("2026-09-10T14:00:00Z")), []);
});
test("plans News during an authoritative After-hours session", () => {
  const afterHours = { ...calendar, sessions: [{ marketDate: "2026-09-10", sessionKind: "AFTER_HOURS" as const,
    opensAt: "2026-09-10T20:00:00Z", closesAt: "2026-09-11T00:00:00Z", isShortened: false,
    calendarRevision: calendar.revision }] };
  assert.equal(planNewsAcquisition(config, afterHours, undefined, new Date("2026-09-10T21:00:00Z")).length, 1);
});
