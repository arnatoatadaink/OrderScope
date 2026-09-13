import { D1NormalizedBarStore } from "./bar-store";
import type { BarNormalizationResult, NormalizedMarketBar } from "./bar";
import { D1CoverageCheckpointPort, type StoredCoverageCheckpoint } from "./checkpoint";

type IntegrationEnv = { STATE_DB: D1Database };

const bar: NormalizedMarketBar = {
  instrumentId: "SPY",
  interval: "1Min",
  barStartUtc: "2026-08-28T14:30:00.000Z",
  barEndUtc: "2026-08-28T14:31:00.000Z",
  marketDate: "2026-08-28",
  sessionKind: "REGULAR",
  isShortenedSession: false,
  logicalDataVariant: "stock:iex:raw",
  open: 100,
  high: 102,
  low: 99,
  close: 101,
  volume: 1000,
  tradeCount: 25,
  vwap: 100.5,
  provider: "alpaca",
  sourceTimestamp: "2026-08-28T14:30:00.000Z",
  calendarRevision: "calendar:v1",
};

const checkpoint: StoredCoverageCheckpoint = {
  coverageKey: "SPY|1Min|REGULAR|stock:iex:raw",
  symbol: "SPY",
  interval: "1Min",
  sessionScope: "REGULAR",
  logicalDataVariant: "stock:iex:raw",
  completeThrough: "2026-08-28T14:31:00.000Z",
  state: "COMPLETE",
  missingRanges: [],
  universeRevision: "v0.1",
  version: 0,
};

async function exercise(db: D1Database): Promise<Record<string, unknown>> {
  const bars = new D1NormalizedBarStore(db);
  const candidate: BarNormalizationResult = { outcome: "NORMALIZED", bar };
  const inserted = await bars.accept(candidate, {
    idempotencyKey: "attempt-1:bar-1",
    jobId: "job-1",
    retrievedAt: "2026-08-28T14:31:02.000Z",
  });
  const matched = await bars.accept(candidate, {
    idempotencyKey: "attempt-2:bar-1",
    jobId: "job-2",
    retrievedAt: "2026-08-28T14:32:02.000Z",
  });

  const checkpoints = new D1CoverageCheckpointPort(db);
  const created = await checkpoints.compareAndSet(undefined, checkpoint);
  const updated = await checkpoints.compareAndSet(0, {
    ...checkpoint,
    completeThrough: "2026-08-28T14:32:00.000Z",
    lastSuccessAt: "2026-08-28T14:32:02.000Z",
  });
  const stale = await checkpoints.compareAndSet(0, {
    ...checkpoint,
    completeThrough: "2026-08-28T14:33:00.000Z",
  });
  await checkpoints.recordAttempt({
    attemptId: "attempt-1",
    coverageKey: checkpoint.coverageKey,
    jobId: "job-1",
    startedAt: "2026-08-28T14:31:00.000Z",
  });
  await checkpoints.recordAttempt({
    attemptId: "attempt-1",
    coverageKey: checkpoint.coverageKey,
    jobId: "job-1",
    startedAt: "2026-08-28T14:31:00.000Z",
    finishedAt: "2026-08-28T14:31:02.000Z",
    outcome: "SUCCEEDED",
    diagnostic: { accepted: 1 },
  });

  return {
    inserted: inserted.outcome,
    matched: matched.outcome,
    created: created.outcome,
    updated: updated.outcome,
    updatedVersion: updated.outcome === "UPDATED" ? updated.checkpoint.version : undefined,
    stale: stale.outcome,
    storedCheckpoint: await checkpoints.get(checkpoint.coverageKey),
    dueCount: (await checkpoints.listDue({
      dueBefore: "2026-08-28T14:33:00.000Z",
      limit: 10,
    })).length,
  };
}

export default {
  async fetch(request: Request, env: IntegrationEnv): Promise<Response> {
    if (new URL(request.url).pathname !== "/exercise") {
      return new Response("not found", { status: 404 });
    }
    return Response.json(await exercise(env.STATE_DB));
  },
} satisfies ExportedHandler<IntegrationEnv>;
