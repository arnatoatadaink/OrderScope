import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { Miniflare } from "miniflare";
import { unstable_splitSqlQuery } from "wrangler";
import { D1NormalizedBarStore, type BarAcceptanceInput } from "./bar-store.ts";
import type { NormalizedMarketBar } from "./bar.ts";

class CountingD1 {
  statements = 0;
  private readonly db: D1Database;
  constructor(db: D1Database) { this.db = db; }
  prepare(sql: string) { this.statements += 1; return this.db.prepare(sql); }
}

function input(index: number, receiptPrefix = "new", closeDelta = 0): BarAcceptanceInput {
  const start = new Date(Date.parse("2026-09-10T14:00:00Z") + index * 60_000);
  const bar: NormalizedMarketBar = {
    instrumentId: "SPY", interval: "1Min", barStartUtc: start.toISOString(),
    barEndUtc: new Date(start.getTime() + 60_000).toISOString(), marketDate: "2026-09-10",
    sessionKind: "REGULAR", isShortenedSession: false, logicalDataVariant: "stock:iex:raw",
    open: 100, high: 102, low: 99, close: 101 + closeDelta, volume: 1000,
    tradeCount: 10, vwap: 100.5, provider: "alpaca", sourceTimestamp: start.toISOString(),
    calendarRevision: "fixture-v1",
  };
  return { candidate: { outcome: "NORMALIZED", bar }, provenance: {
    idempotencyKey: `${receiptPrefix}:${index}`, jobId: "batch-job", retrievedAt: "2026-09-10T20:00:00Z",
  } };
}

test("100-bar D1 batch is bounded, ordered, replayable, and conflict preserving", async (t) => {
  const mf = new Miniflare({ modules: true, script: "export default { fetch() { return new Response('ok') } }",
    compatibilityDate: "2026-08-06", d1Databases: ["STATE_DB"] });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB") as unknown as D1Database;
  const sql = await readFile(new URL("../migrations/0003_normalized_bar.sql", import.meta.url), "utf8");
  for (const statement of unstable_splitSqlQuery(sql)) await db.prepare(statement).run();
  const counting = new CountingD1(db);
  const store = new D1NormalizedBarStore(counting as unknown as D1Database);
  const inputs = Array.from({ length: 100 }, (_, index) => input(index));

  const inserted = await store.acceptBatch(inputs);
  assert.equal(counting.statements, 7);
  assert.deepEqual(inserted.map((result) => result.outcome), Array(100).fill("INSERTED"));
  assert.deepEqual(inserted.map((result) => result.acceptanceReceipt), inputs.map((item) => item.provenance.idempotencyKey));
  const firstCounts = await db.prepare(`SELECT (SELECT COUNT(*) FROM normalized_bar) bars,
    (SELECT COUNT(*) FROM bar_acceptance_receipt) receipts, (SELECT COUNT(*) FROM bar_conflict) conflicts`).first();
  assert.deepEqual(firstCounts, { bars: 100, receipts: 100, conflicts: 0 });

  counting.statements = 0;
  const replay = await store.acceptBatch(inputs);
  assert.equal(counting.statements, 7);
  assert.deepEqual(replay.map((result) => [result.outcome, result.provenanceAppended]), Array(100).fill(null).map(() => ["INSERTED", false]));

  counting.statements = 0;
  const matches = await store.acceptBatch(Array.from({ length: 100 }, (_, index) => input(index, "match")));
  assert.equal(counting.statements, 7);
  assert.deepEqual(matches.map((result) => result.outcome), Array(100).fill("MATCHED"));

  const conflicts = await store.acceptBatch([input(1, "conflict", 5), input(2, "conflict", 7)]);
  assert.deepEqual(conflicts.map((result) => result.outcome), ["CONFLICT", "CONFLICT"]);
  assert.equal((await db.prepare("SELECT COUNT(*) count FROM bar_conflict").first<{ count: number }>())?.count, 2);
  assert.equal((await db.prepare("SELECT close FROM normalized_bar WHERE bar_start_utc = ?")
    .bind((inputs[1]!.candidate as { outcome: "NORMALIZED"; bar: NormalizedMarketBar }).bar.barStartUtc)
    .first<{ close: number }>())?.close, 101);

  await assert.rejects(store.acceptBatch([input(0, "new", 1)]), /different bar observation/);
});
