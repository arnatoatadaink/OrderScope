import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import { coverageAbsencesForRange, parseLocalHistoryEvidence, localHistoryFetchPage, type LocalHistoryEvidenceSession } from "./local-history-evidence.ts";
import { validateRegularSession } from "./local-history-collector.ts";

function stableHash(session: Omit<LocalHistoryEvidenceSession, "contentSha256"> & { contentSha256?: string }): string {
  const stablePayload = JSON.stringify({
    coverageKey: session.coverageKey,
    providerRevision: session.providerRevision,
    feed: session.feed,
    adjustment: session.adjustment,
    plan: session.plan,
    validation: session.validation,
    pages: session.pages,
    bars: session.bars,
  });
  return createHash("sha256").update(stablePayload, "utf8").digest("hex");
}

function fixture(overrides: Partial<LocalHistoryEvidenceSession> = {}): LocalHistoryEvidenceSession {
  const plan = {
    marketDate: "2026-09-11",
    startInclusive: "2026-09-11T13:30:00.000Z",
    endExclusive: "2026-09-11T20:00:00.000Z",
    expectedBars: 390,
  };
  const missing = "2026-09-11T16:57:00.000Z";
  const bars = Array.from({ length: 390 }, (_, index) => {
    const timestamp = new Date(Date.parse(plan.startInclusive) + index * 60_000).toISOString();
    return {
      symbol: "NVDA",
      timestamp,
      open: 1, high: 1, low: 1, close: 1, volume: 1,
      provider: "alpaca" as const,
      dataVariant: "stock:iex:raw",
    };
  }).filter((bar) => bar.timestamp !== missing);
  const validation = validateRegularSession(plan, bars);
  const base = {
    schemaVersion: "l1-003-local-history-session-v3" as const,
    contentSha256: "",
    previousContentSha256: "x".repeat(64),
    reproducible: true,
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    providerRevision: "alpaca-stock-bars-v1",
    feed: "iex" as const,
    adjustment: "raw" as const,
    plan,
    validation,
    pages: 1,
    bars,
  };
  const merged = { ...base, ...overrides } as LocalHistoryEvidenceSession;
  merged.contentSha256 = stableHash(merged);
  return merged;
}

test("loads hash-verified reproducible sparse evidence and exposes explicit absence", async () => {
  const session = fixture();
  const loaded = await parseLocalHistoryEvidence(JSON.stringify(session));
  assert.equal(loaded.session.contentSha256, session.contentSha256);
  assert.deepEqual(loaded.coverageAbsences, [{
    symbol: "NVDA",
    identityStart: "2026-09-11T16:57:00.000Z",
    reason: "REPRODUCIBLE_PROVIDER_ABSENCE",
    evidenceHash: session.contentSha256,
  }]);
});

test("rejects tampered or unapproved sparse evidence", async () => {
  const tampered = fixture();
  tampered.bars[0]!.close = 2;
  await assert.rejects(parseLocalHistoryEvidence(JSON.stringify(tampered)), /hash mismatch/);

  const unreproduced = fixture({ reproducible: false });
  unreproduced.contentSha256 = stableHash(unreproduced);
  await assert.rejects(parseLocalHistoryEvidence(JSON.stringify(unreproduced)), /approved reproducible provider absence/);

  const wrongDate = fixture();
  wrongDate.plan = {
    ...wrongDate.plan,
    marketDate: "2026-09-14",
    startInclusive: "2026-09-14T13:30:00.000Z",
    endExclusive: "2026-09-14T20:00:00.000Z",
  };
  wrongDate.bars = wrongDate.bars.map((bar, index) => ({
    ...bar,
    timestamp: new Date(Date.parse(wrongDate.plan.startInclusive) + index * 60_000).toISOString(),
  }));
  wrongDate.validation = validateRegularSession(wrongDate.plan, wrongDate.bars);
  wrongDate.contentSha256 = stableHash(wrongDate);
  await assert.rejects(parseLocalHistoryEvidence(JSON.stringify(wrongDate)), /approved reproducible provider absence/);
});

test("serves only the requested frozen range from local evidence", async () => {
  const session = fixture();
  const missing = session.validation.missingTimestamps[0]!;
  session.bars.push({
    symbol: "NVDA", timestamp: missing, open: 2, high: 2, low: 2, close: 2, volume: 2,
    provider: "alpaca", dataVariant: "stock:iex:raw",
  });
  session.bars.sort((left, right) => Date.parse(left.timestamp) - Date.parse(right.timestamp));
  session.validation = validateRegularSession(session.plan, session.bars);
  session.reproducible = undefined;
  session.previousContentSha256 = undefined;
  session.contentSha256 = stableHash(session);
  const fetchPage = localHistoryFetchPage(session);
  const page = await fetchPage({}, {
    instrument: { symbol: "NVDA", cadence: "1Min", providerRoute: "alpaca_stock_bars" },
    startInclusive: "2026-09-11T13:31:00.000Z",
    endExclusive: "2026-09-11T13:32:00.000Z",
    feed: "iex",
  });
  assert.equal(page.bars.length, 1);
  assert.equal(page.bars[0]?.timestamp, "2026-09-11T13:31:00.000Z");
});


test("filters reproducible absence evidence to the active recovery chunk", async () => {
  const session = fixture();
  const loaded = await parseLocalHistoryEvidence(JSON.stringify(session));
  assert.equal(coverageAbsencesForRange(
    loaded.coverageAbsences,
    "2026-09-11T13:30:00.000Z",
    "2026-09-11T15:10:00.000Z",
  ).length, 0);
  assert.equal(coverageAbsencesForRange(
    loaded.coverageAbsences,
    "2026-09-11T15:10:00.000Z",
    "2026-09-11T16:50:00.000Z",
  ).length, 0);
  assert.equal(coverageAbsencesForRange(
    loaded.coverageAbsences,
    "2026-09-11T16:50:00.000Z",
    "2026-09-11T18:30:00.000Z",
  ).length, 1);
});
