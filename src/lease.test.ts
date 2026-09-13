import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { build } from "esbuild";
import { Miniflare } from "miniflare";
import { unstable_splitSqlQuery } from "wrangler";

test("D1 lease excludes overlap, expires, and only releases for its owner", async (t) => {
  const bundle = await build({
    stdin: {
      contents: `
        import { D1AcquisitionLeaseStore } from "./lease.ts";
        export default { async fetch(_request, env) {
          const leases = new D1AcquisitionLeaseStore(env.STATE_DB);
          const first = await leases.acquire("BTCUSD|1Min|ALL_TRADING|crypto:us", "first", "2026-08-30T10:00:00Z", 300000);
          const overlap = await leases.acquire("BTCUSD|1Min|ALL_TRADING|crypto:us", "second", "2026-08-30T10:01:00Z", 300000);
          await leases.release("BTCUSD|1Min|ALL_TRADING|crypto:us", "second");
          const stillHeld = await leases.acquire("BTCUSD|1Min|ALL_TRADING|crypto:us", "third", "2026-08-30T10:02:00Z", 300000);
          const expired = await leases.acquire("BTCUSD|1Min|ALL_TRADING|crypto:us", "fourth", "2026-08-30T10:05:00Z", 300000);
          await leases.release("BTCUSD|1Min|ALL_TRADING|crypto:us", "fourth");
          const afterRelease = await leases.acquire("BTCUSD|1Min|ALL_TRADING|crypto:us", "fifth", "2026-08-30T10:05:01Z", 300000);
          return Response.json({ first, overlap, stillHeld, expired, afterRelease });
        }};
      `,
      resolveDir: new URL(".", import.meta.url).pathname,
      sourcefile: "lease-integration-entry.ts",
    },
    bundle: true, format: "esm", platform: "browser", target: "es2022", write: false,
  });
  const mf = new Miniflare({
    modules: true, script: bundle.outputFiles[0]?.text ?? "",
    compatibilityDate: "2026-08-06", d1Databases: ["STATE_DB"],
  });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB");
  const sql = await readFile(new URL("../migrations/0004_acquisition_lease.sql", import.meta.url), "utf8");
  for (const statement of unstable_splitSqlQuery(sql)) await db.prepare(statement).run();

  assert.deepEqual(await (await mf.dispatchFetch("http://integration.test/")).json(), {
    first: true, overlap: false, stillHeld: false, expired: true, afterRelease: true,
  });
});
