import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { build } from "esbuild";
import { Miniflare } from "miniflare";
import { unstable_splitSqlQuery } from "wrangler";

test("real D1 adapters execute against migrated Miniflare storage", async (t) => {
  const bundle = await build({
    entryPoints: [new URL("./d1-integration-worker.ts", import.meta.url).pathname],
    bundle: true,
    format: "esm",
    platform: "browser",
    target: "es2022",
    write: false,
  });

  const mf = new Miniflare({
    modules: true,
    script: bundle.outputFiles[0]?.text ?? "",
    // Miniflare 4's latest stable workerd currently supports dates through this day.
    compatibilityDate: "2026-08-06",
    d1Databases: ["STATE_DB"],
  });
  t.after(() => mf.dispose());

  const db = await mf.getD1Database("STATE_DB");
  for (const migration of ["0001_state.sql", "0002_attempt_coverage_key.sql", "0003_normalized_bar.sql", "0004_acquisition_lease.sql", "0005_gap_retry_eligibility.sql", "0006_digest_history.sql"]) {
    const sql = await readFile(new URL(`../migrations/${migration}`, import.meta.url), "utf8");
    for (const statement of unstable_splitSqlQuery(sql)) {
      await db.prepare(statement).run();
    }
  }

  const response = await mf.dispatchFetch("http://integration.test/exercise");
  assert.equal(response.status, 200);
  const result = await response.json() as Record<string, unknown>;
  assert.deepEqual(
    {
      inserted: result.inserted,
      matched: result.matched,
      created: result.created,
      updated: result.updated,
      updatedVersion: result.updatedVersion,
      stale: result.stale,
      dueCount: result.dueCount,
    },
    {
      inserted: "INSERTED",
      matched: "MATCHED",
      created: "UPDATED",
      updated: "UPDATED",
      updatedVersion: 1,
      stale: "VERSION_CONFLICT",
      dueCount: 1,
    },
  );

  const checkpoint = result.storedCheckpoint as Record<string, unknown>;
  assert.equal(checkpoint.completeThrough, "2026-08-28T14:32:00.000Z");
  assert.equal(checkpoint.version, 1);

  const counts = await db.prepare(`
    SELECT
      (SELECT COUNT(*) FROM normalized_bar) AS bars,
      (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts,
      (SELECT COUNT(*) FROM acquisition_attempt) AS attempts
  `).first<{ bars: number; receipts: number; attempts: number }>();
  assert.deepEqual(counts, { bars: 1, receipts: 2, attempts: 1 });
  const attempt = await db.prepare(
    "SELECT outcome, diagnostic_json FROM acquisition_attempt WHERE attempt_id = ?",
  ).bind("attempt-1").first<{ outcome: string; diagnostic_json: string }>();
  assert.equal(attempt?.outcome, "SUCCEEDED");
  assert.deepEqual(JSON.parse(attempt?.diagnostic_json ?? "null"), { accepted: 1 });
});
