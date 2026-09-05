import assert from "node:assert/strict";
import test from "node:test";
import { canonicalBarFingerprint, D1NormalizedBarStore } from "./bar-store.ts";
import type { BarNormalizationResult, NormalizedMarketBar } from "./bar.ts";

type Row = Record<string, unknown>;

class Statement {
  values: unknown[] = [];
  readonly sql: string;
  private readonly result: Row | null;
  constructor(sql: string, result: Row | null) {
    this.sql = sql;
    this.result = result;
  }
  bind(...values: unknown[]): Statement { this.values = values; return this; }
  async first(): Promise<Row | null> { return this.result; }
  async run(): Promise<{ success: true; meta: { changes: number }; results: [] }> {
    return { success: true, meta: { changes: 1 }, results: [] };
  }
}

class ScriptedD1 {
  readonly statements: Statement[] = [];
  readonly firstResults: Array<Row | null> = [];
  prepare(sql: string): Statement {
    const statement = new Statement(sql, this.firstResults.shift() ?? null);
    this.statements.push(statement);
    return statement;
  }
}

const bar: NormalizedMarketBar = {
  instrumentId: "SPY", interval: "1Min",
  barStartUtc: "2026-08-28T14:30:00.000Z", barEndUtc: "2026-08-28T14:31:00.000Z",
  marketDate: "2026-08-28", sessionKind: "REGULAR", isShortenedSession: false,
  logicalDataVariant: "stock:iex:raw", open: 100, high: 102, low: 99, close: 101,
  volume: 1000, tradeCount: 25, vwap: 100.5, provider: "alpaca",
  sourceTimestamp: "2026-08-28T14:30:00.000Z", calendarRevision: "calendar:v1",
};
const candidate: BarNormalizationResult = { outcome: "NORMALIZED", bar };
const provenance = { idempotencyKey: "attempt-1:bar-1", jobId: "job-1", retrievedAt: "2026-08-28T14:31:02Z" };
const identity = JSON.stringify(["SPY", "1Min", bar.barStartUtc, "REGULAR", "stock:iex:raw"]);

function receipt(outcome: "INSERTED" | "MATCHED" | "CONFLICT" | "REJECTED" | null, fingerprint: string, version: number | null = null): Row {
  return {
    idempotency_key: provenance.idempotencyKey, request_fingerprint: fingerprint,
    identity_key: outcome === "REJECTED" ? null : identity, outcome,
    reason: outcome === "CONFLICT" ? "canonical identity already exists with different semantic content" : null,
    stored_version: version,
  };
}

test("inserts a new canonical bar and completes its durable receipt", async () => {
  const fingerprint = await canonicalBarFingerprint(bar);
  const db = new ScriptedD1();
  db.firstResults.push(receipt(null, fingerprint), { canonical_fingerprint: fingerprint, version: 1 }, receipt("INSERTED", fingerprint, 1));
  const result = await new D1NormalizedBarStore(db).accept(candidate, provenance);
  assert.equal(result.outcome, "INSERTED");
  assert.equal(result.provenanceAppended, true);
  assert.match(db.statements[1]?.sql ?? "", /ON CONFLICT\(identity_key\) DO NOTHING/);
  assert.equal(db.statements[1]?.sql.includes("SPY"), false);
});

test("matches identical overlap delivery without duplicating the canonical bar", async () => {
  const fingerprint = await canonicalBarFingerprint(bar);
  const db = new ScriptedD1();
  db.firstResults.push(receipt(null, fingerprint), null, { canonical_fingerprint: fingerprint, version: 1 }, receipt("MATCHED", fingerprint, 1));
  const result = await new D1NormalizedBarStore(db).accept(candidate, { ...provenance, idempotencyKey: provenance.idempotencyKey });
  assert.equal(result.outcome, "MATCHED");
  assert.equal(result.storedVersion, 1);
});

test("quarantines different content for the same identity and never overwrites", async () => {
  const fingerprint = await canonicalBarFingerprint(bar);
  const db = new ScriptedD1();
  db.firstResults.push(receipt(null, fingerprint), null, { canonical_fingerprint: "different", version: 1 }, null, receipt("CONFLICT", fingerprint, 1));
  const result = await new D1NormalizedBarStore(db).accept(candidate, provenance);
  assert.equal(result.outcome, "CONFLICT");
  assert.match(db.statements[3]?.sql ?? "", /INSERT INTO bar_conflict/);
  assert.equal(db.statements.some((statement) => /UPDATE normalized_bar/.test(statement.sql)), false);
});

test("persists normalization rejection as an idempotent terminal receipt", async () => {
  const rejected: BarNormalizationResult = { outcome: "REJECTED", code: "INVALID_OHLC", reason: "bad range" };
  const rejectionFingerprint = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify(["INVALID_OHLC", "bad range"])))
    .then((value) => [...new Uint8Array(value)].map((byte) => byte.toString(16).padStart(2, "0")).join(""));
  const db = new ScriptedD1();
  db.firstResults.push(
    { ...receipt(null, rejectionFingerprint), identity_key: null },
    { ...receipt("REJECTED", rejectionFingerprint), identity_key: null, reason: "INVALID_OHLC: bad range" },
  );
  const result = await new D1NormalizedBarStore(db).accept(rejected, provenance);
  assert.equal(result.outcome, "REJECTED");
  assert.match(result.reason ?? "", /INVALID_OHLC/);
  assert.equal(db.statements.some((statement) => /INSERT INTO normalized_bar/.test(statement.sql)), false);
});

test("rejects reuse of an idempotency key for different content", async () => {
  const fingerprint = await canonicalBarFingerprint(bar);
  const db = new ScriptedD1();
  db.firstResults.push(null, { ...receipt("MATCHED", fingerprint, 1), request_fingerprint: "other" });
  await assert.rejects(new D1NormalizedBarStore(db).accept(candidate, provenance), /different bar observation/);
});
