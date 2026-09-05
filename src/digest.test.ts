import assert from "node:assert/strict";
import test from "node:test";
import { D1LatestDigestStore } from "./digest.ts";

type Row = { digest_key: string; generated_at: string; payload_json: string; schema_version: number };
class DigestDb {
  row?: Row;
  history = new Map<string, Row>();
  prepare(sql: string) {
    let bindings: unknown[] = [];
    const statement = {
      bind: (...values: unknown[]) => { bindings = values; return statement; },
      run: async () => {
        const [digestKey, generatedAt, payloadJson, schemaVersion] = bindings as [string, string, string, number];
        if (sql.includes("INSERT INTO latest_digest") && (!this.row || generatedAt >= this.row.generated_at)) {
          this.row = { digest_key: digestKey, generated_at: generatedAt, payload_json: payloadJson, schema_version: schemaVersion };
        }
        if (sql.includes("INSERT INTO digest_history")) {
          this.history.set(`${digestKey}/${generatedAt}`, {
            digest_key: digestKey, generated_at: generatedAt, payload_json: payloadJson, schema_version: schemaVersion,
          });
        }
        return { meta: { changes: 1 } };
      },
      first: async () => sql.includes("SELECT") && this.row?.digest_key === bindings[0] ? this.row : null,
      all: async () => ({ results: [...this.history.values()]
        .filter((row) => row.digest_key === bindings[0])
        .sort((a, b) => b.generated_at.localeCompare(a.generated_at))
        .slice(0, Number(bindings[1])) }),
    };
    return statement;
  }
  async batch(statements: Array<{ run: () => Promise<unknown> }>) {
    return Promise.all(statements.map((statement) => statement.run()));
  }
}

test("persists and reads a compact versioned latest digest", async () => {
  const store = new D1LatestDigestStore(new DigestDb() as never);
  await store.put("market", "2026-08-30T12:00:00.000Z", { status: "ok", plannedJobs: 2 });
  assert.deepEqual(await store.get("market"), { digestKey: "market", generatedAt: "2026-08-30T12:00:00.000Z",
    schemaVersion: 1, payload: { status: "ok", plannedJobs: 2 } });
});

test("does not replace a newer digest with a stale cron completion", async () => {
  const store = new D1LatestDigestStore(new DigestDb() as never);
  await store.put("market", "2026-08-30T12:01:00.000Z", { tick: 2 });
  await store.put("market", "2026-08-30T12:00:00.000Z", { tick: 1 });
  assert.deepEqual((await store.get("market"))?.payload, { tick: 2 });
  assert.deepEqual((await store.list("market", 2)).map((item) => item.payload), [{ tick: 2 }, { tick: 1 }]);
});

test("rejects corrupt persisted payloads", async () => {
  const db = new DigestDb();
  db.row = { digest_key: "market", generated_at: "2026-08-30T12:00:00.000Z", payload_json: "[]", schema_version: 1 };
  await assert.rejects(new D1LatestDigestStore(db as never).get("market"), /corrupt/);
});
