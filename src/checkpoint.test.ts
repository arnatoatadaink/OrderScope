import assert from "node:assert/strict";
import test from "node:test";
import { D1CoverageCheckpointPort, type StoredCoverageCheckpoint } from "./checkpoint.ts";

type Row = Record<string, unknown>;

class ScriptedStatement {
  values: unknown[] = [];
  readonly sql: string;
  private readonly firstResult: Row | null;
  private readonly allResults: Row[];

  constructor(sql: string, firstResult: Row | null, allResults: Row[]) {
    this.sql = sql;
    this.firstResult = firstResult;
    this.allResults = allResults;
  }

  bind(...values: unknown[]): ScriptedStatement {
    this.values = values;
    return this;
  }

  async first(): Promise<Row | null> { return this.firstResult; }
  async all(): Promise<{ results: Row[] }> { return { results: this.allResults }; }
  async run(): Promise<{ success: true; meta: { changes: number }; results: [] }> {
    return { success: true, meta: { changes: 1 }, results: [] };
  }
}

class ScriptedD1 {
  readonly statements: ScriptedStatement[] = [];
  firstResults: Array<Row | null> = [];
  allResults: Row[][] = [];

  prepare(sql: string): ScriptedStatement {
    const statement = new ScriptedStatement(sql, this.firstResults.shift() ?? null, this.allResults.shift() ?? []);
    this.statements.push(statement);
    return statement;
  }
}

function checkpoint(overrides: Partial<StoredCoverageCheckpoint> = {}): StoredCoverageCheckpoint {
  return {
    coverageKey: "SPY|1Min|REGULAR|raw-iex", symbol: "SPY", interval: "1Min",
    sessionScope: "REGULAR", logicalDataVariant: "raw-iex",
    completeThrough: "2026-08-28T14:31:00.000Z", state: "COMPLETE",
    missingRanges: [], universeRevision: "universe-v1", version: 0, ...overrides,
  };
}

function row(value = checkpoint()): Row {
  return {
    coverage_key: value.coverageKey, symbol: value.symbol, interval: value.interval,
    session_scope: value.sessionScope, logical_data_variant: value.logicalDataVariant,
    complete_through: value.completeThrough ?? null, state: value.state,
    missing_ranges_json: JSON.stringify(value.missingRanges),
    last_success_at: value.lastSuccessAt ?? null, last_attempt_at: value.lastAttemptAt ?? null,
    retry_not_before: value.retryNotBefore ?? null,
    source_observed_through: value.sourceObservedThrough ?? null,
    universe_revision: value.universeRevision ?? null, version: value.version,
    blocker_json: value.blocker ? JSON.stringify(value.blocker) : null,
  };
}

test("creates, reads, and monotonically updates a checkpoint with CAS", async () => {
  const db = new ScriptedD1();
  db.firstResults.push(row(), row(), row(checkpoint({ version: 1, completeThrough: "2026-08-28T14:32:00.000Z" })), null, null);
  const port = new D1CoverageCheckpointPort(db);

  assert.equal((await port.compareAndSet(undefined, checkpoint())).outcome, "UPDATED");
  assert.equal((await port.get(checkpoint().coverageKey))?.version, 0);
  const updated = await port.compareAndSet(0, checkpoint({ completeThrough: "2026-08-28T14:32:00.000Z" }));
  assert.equal(updated.outcome === "UPDATED" && updated.checkpoint.version, 1);
  assert.equal((await port.compareAndSet(0, checkpoint({ completeThrough: "2026-08-28T14:33:00.000Z" }))).outcome, "VERSION_CONFLICT");
  assert.equal((await port.compareAndSet(1, checkpoint({ completeThrough: "2026-08-28T14:30:00.000Z" }))).outcome, "VERSION_CONFLICT");

  const updateSql = db.statements[2]?.sql ?? "";
  assert.match(updateSql, /version = version \+ 1/);
  assert.match(updateSql, /version = \?/);
  assert.match(updateSql, /\? >= complete_through/);
});

test("rejects a proposal that advances across an unresolved gap before querying D1", async () => {
  const db = new ScriptedD1();
  const port = new D1CoverageCheckpointPort(db);
  await assert.rejects(port.compareAndSet(undefined, checkpoint({
    completeThrough: "2026-08-28T14:35:00.000Z",
    missingRanges: [{ startInclusive: "2026-08-28T14:32:00.000Z", endExclusive: "2026-08-28T14:33:00.000Z" }],
  })), /cannot cross/);
  assert.equal(db.statements.length, 0);
});

test("maps due rows and uses bounded, prepared filters", async () => {
  const db = new ScriptedD1();
  db.allResults.push([row(checkpoint({ state: "PARTIAL" }))]);
  const port = new D1CoverageCheckpointPort(db);
  const due = await port.listDue({ dueBefore: "2026-08-28T14:40:00.000Z", interval: "1Min", sessionScope: "REGULAR", limit: 25 });

  assert.equal(due[0]?.symbol, "SPY");
  assert.match(db.statements[0]?.sql ?? "", /state <> 'BLOCKED'/);
  assert.deepEqual(db.statements[0]?.values, ["2026-08-28T14:40:00.000Z", "1Min", "1Min", "REGULAR", "REGULAR", 25]);
});

test("round-trips a Premarket checkpoint as a distinct scope", async () => {
  const db = new ScriptedD1();
  const value = checkpoint({
    coverageKey: "SPY|1Min|PREMARKET|raw-iex",
    sessionScope: "PREMARKET",
  });
  db.firstResults.push(row(value));
  const stored = await new D1CoverageCheckpointPort(db).get(value.coverageKey);

  assert.equal(stored?.sessionScope, "PREMARKET");
  assert.equal(stored?.coverageKey, value.coverageKey);
});

test("records attempt updates idempotently without interpolating values", async () => {
  const db = new ScriptedD1();
  const port = new D1CoverageCheckpointPort(db);
  await port.recordAttempt({
    attemptId: "attempt-1", coverageKey: checkpoint().coverageKey, jobId: "job-1",
    startedAt: "2026-08-28T14:31:00.000Z", finishedAt: "2026-08-28T14:31:02.000Z",
    outcome: "SUCCEEDED", diagnostic: { accepted: 1 },
  });

  assert.match(db.statements[0]?.sql ?? "", /ON CONFLICT\(attempt_id\) DO UPDATE/);
  assert.equal(db.statements[0]?.sql.includes("attempt-1"), false);
  assert.deepEqual(db.statements[0]?.values.slice(0, 4), ["attempt-1", checkpoint().coverageKey, "job-1", "2026-08-28T14:31:00.000Z"]);
});
