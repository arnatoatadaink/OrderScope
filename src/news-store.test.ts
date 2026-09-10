import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { Miniflare } from "miniflare";
import { unstable_splitSqlQuery } from "wrangler";
import { D1NewsStore } from "./news-store.ts";

test("D1 keeps one provider identity with both query memberships and no body column", async (t) => {
  const mf = new Miniflare({ modules: true, script: "export default { fetch() { return new Response('ok') } }",
    compatibilityDate: "2026-08-06", d1Databases: ["STATE_DB"] });
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("STATE_DB") as unknown as D1Database;
  const sql = await readFile(new URL("../migrations/0007_news_metadata.sql", import.meta.url), "utf8");
  for (const statement of unstable_splitSqlQuery(sql)) await db.prepare(statement).run();
  const store = new D1NewsStore(db);
  const article = { provider: "alpaca" as const, providerArticleId: "123", headline: "headline", publisher: "publisher",
    url: "https://example.test/123", providerPublishedAt: "2026-09-10T14:00:00Z", providerSymbols: ["AMD", "NVDA"] };
  assert.deepEqual(await store.acceptBatch([{ article, querySymbol: "AMD", retrievedAt: "2026-09-10T14:01:00Z", acceptedAt: "2026-09-10T14:01:00Z" }]), [{ outcome: "NEW" }]);
  assert.deepEqual(await store.acceptBatch([{ article, querySymbol: "NVDA", retrievedAt: "2026-09-10T14:02:00Z", acceptedAt: "2026-09-10T14:02:00Z" }]), [{ outcome: "SAME" }]);
  assert.deepEqual(await store.acceptBatch([{ article: { ...article, headline: "revised headline",
    providerUpdatedAt: "2026-09-10T14:03:00Z" }, querySymbol: "AMD",
    retrievedAt: "2026-09-10T14:03:01Z", acceptedAt: "2026-09-10T14:03:01Z" }]), [{ outcome: "UPDATED" }]);
  assert.deepEqual(await db.prepare("SELECT COUNT(*) count FROM news_article").first(), { count: 1 });
  const memberships = await db.prepare("SELECT query_symbol FROM news_query_membership ORDER BY query_symbol").all<{ query_symbol: string }>();
  assert.deepEqual(memberships.results.map((row) => row.query_symbol), ["AMD", "NVDA"]);
  const columns = await db.prepare("PRAGMA table_info(news_article)").all<{ name: string }>();
  assert.equal(columns.results.some((column) => ["body", "content", "summary"].includes(column.name)), false);
});
