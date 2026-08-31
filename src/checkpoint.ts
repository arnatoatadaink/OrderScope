import type { CoverageCheckpoint, SessionScope, TimeRange } from "./schedule";
import type { Cadence } from "./universe";

export type CheckpointState = "COMPLETE" | "PARTIAL" | "UNKNOWN" | "BLOCKED";

export type StoredCoverageCheckpoint = CoverageCheckpoint & {
  symbol: string;
  interval: Cadence;
  sessionScope: SessionScope;
  logicalDataVariant: string;
  state: CheckpointState;
  lastSuccessAt?: string;
  lastAttemptAt?: string;
  retryNotBefore?: string;
  sourceObservedThrough?: string;
  universeRevision?: string;
  blocker?: Readonly<Record<string, unknown>>;
};

export type DueCheckpointQuery = {
  dueBefore: string;
  limit?: number;
  interval?: Cadence;
  sessionScope?: SessionScope;
};

export type CompareAndSetOutcome =
  | { outcome: "UPDATED"; checkpoint: StoredCoverageCheckpoint }
  | { outcome: "VERSION_CONFLICT" };

export type AcquisitionAttempt = {
  attemptId: string;
  coverageKey: string;
  jobId: string;
  startedAt: string;
  finishedAt?: string;
  outcome?: string;
  diagnostic?: Readonly<Record<string, unknown>>;
};

export type StaleAttemptSummary = {
  count: number;
  oldestStartedAt?: string;
};

export type SupersedeStaleAttemptsCommand = {
  coverageKey: string;
  staleBefore: string;
  finishedAt: string;
  replacementJobId: string;
};

export interface CoverageCheckpointPort {
  get(coverageKey: string): Promise<StoredCoverageCheckpoint | undefined>;
  listDue(query: DueCheckpointQuery): Promise<readonly StoredCoverageCheckpoint[]>;
  compareAndSet(
    expectedVersion: number | undefined,
    proposed: StoredCoverageCheckpoint,
  ): Promise<CompareAndSetOutcome>;
  recordAttempt(attempt: AcquisitionAttempt): Promise<void>;
  summarizeStaleAttempts(staleBefore: string): Promise<StaleAttemptSummary>;
  supersedeStaleAttempts(command: SupersedeStaleAttemptsCommand): Promise<number>;
}

type CheckpointRow = {
  coverage_key: string;
  symbol: string;
  interval: string;
  session_scope: string;
  logical_data_variant: string;
  complete_through: string | null;
  state: string;
  missing_ranges_json: string;
  last_success_at: string | null;
  last_attempt_at: string | null;
  source_observed_through: string | null;
  universe_revision: string | null;
  version: number;
  blocker_json: string | null;
  retry_not_before: string | null;
};

const SELECT_COLUMNS = `
  coverage_key, symbol, interval, session_scope, logical_data_variant,
  complete_through, state, missing_ranges_json, last_success_at,
  last_attempt_at, source_observed_through, universe_revision, version,
  blocker_json, retry_not_before
`;

function isCheckpointState(value: string): value is CheckpointState {
  return value === "COMPLETE" || value === "PARTIAL" || value === "UNKNOWN" || value === "BLOCKED";
}

function isCadence(value: string): value is Cadence {
  return value === "1Min" || value === "15Min" || value === "1Day";
}

function isSessionScope(value: string): value is SessionScope {
  return value === "REGULAR" || value === "ALL_TRADING";
}

function parseInstant(value: string, name: string): number {
  const result = Date.parse(value);
  if (!Number.isFinite(result)) throw new Error(`${name} must be a valid instant`);
  return result;
}

function validateRange(range: TimeRange): void {
  if (parseInstant(range.startInclusive, "range start") >= parseInstant(range.endExclusive, "range end")) {
    throw new Error("missing range must be non-empty and half-open");
  }
}

function parseRanges(value: string): readonly TimeRange[] {
  const parsed: unknown = JSON.parse(value);
  if (!Array.isArray(parsed)) throw new Error("checkpoint missing_ranges_json is corrupt");
  return parsed.map((range) => {
    if (typeof range !== "object" || range === null
      || !("startInclusive" in range) || typeof range.startInclusive !== "string"
      || !("endExclusive" in range) || typeof range.endExclusive !== "string") {
      throw new Error("checkpoint missing_ranges_json is corrupt");
    }
    const result = { startInclusive: range.startInclusive, endExclusive: range.endExclusive };
    validateRange(result);
    return result;
  });
}

function parseBlocker(value: string | null): Readonly<Record<string, unknown>> | undefined {
  if (value === null) return undefined;
  const parsed: unknown = JSON.parse(value);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("checkpoint blocker_json is corrupt");
  }
  return Object.fromEntries(Object.entries(parsed));
}

function fromRow(row: CheckpointRow): StoredCoverageCheckpoint {
  if (!isCadence(row.interval)
    || !isSessionScope(row.session_scope)
    || !isCheckpointState(row.state)
    || !Number.isSafeInteger(row.version)
    || row.version < 0) {
    throw new Error(`checkpoint row is corrupt: ${row.coverage_key}`);
  }
  return {
    coverageKey: row.coverage_key,
    symbol: row.symbol,
    interval: row.interval,
    sessionScope: row.session_scope,
    logicalDataVariant: row.logical_data_variant,
    completeThrough: row.complete_through ?? undefined,
    state: row.state,
    missingRanges: parseRanges(row.missing_ranges_json),
    lastSuccessAt: row.last_success_at ?? undefined,
    lastAttemptAt: row.last_attempt_at ?? undefined,
    retryNotBefore: row.retry_not_before ?? undefined,
    sourceObservedThrough: row.source_observed_through ?? undefined,
    universeRevision: row.universe_revision ?? undefined,
    version: row.version,
    blocker: parseBlocker(row.blocker_json),
  };
}

function validateProposal(proposed: StoredCoverageCheckpoint): void {
  if (!proposed.coverageKey || !proposed.symbol || !proposed.logicalDataVariant) {
    throw new Error("checkpoint identity fields must be non-empty");
  }
  if (!isCadence(proposed.interval) || !isSessionScope(proposed.sessionScope)
    || !isCheckpointState(proposed.state)) {
    throw new Error("checkpoint enum value is invalid");
  }
  proposed.missingRanges.forEach(validateRange);
  if (proposed.retryNotBefore) parseInstant(proposed.retryNotBefore, "retryNotBefore");
  if (proposed.completeThrough) {
    const completeThrough = parseInstant(proposed.completeThrough, "completeThrough");
    if (proposed.missingRanges.some((range) => parseInstant(range.startInclusive, "missing range start") < completeThrough)) {
      throw new Error("completeThrough cannot cross an unresolved missing range");
    }
  }
}

function values(proposed: StoredCoverageCheckpoint): readonly unknown[] {
  return [
    proposed.coverageKey,
    proposed.symbol,
    proposed.interval,
    proposed.sessionScope,
    proposed.logicalDataVariant,
    proposed.completeThrough ?? null,
    proposed.state,
    JSON.stringify(proposed.missingRanges),
    proposed.lastSuccessAt ?? null,
    proposed.lastAttemptAt ?? null,
    proposed.sourceObservedThrough ?? null,
    proposed.universeRevision ?? null,
    proposed.blocker ? JSON.stringify(proposed.blocker) : null,
    proposed.retryNotBefore ?? null,
  ];
}

export class D1CoverageCheckpointPort implements CoverageCheckpointPort {
  private readonly db: D1Database;

  constructor(db: D1Database) {
    this.db = db;
  }

  async get(coverageKey: string): Promise<StoredCoverageCheckpoint | undefined> {
    const row = await this.db.prepare(`SELECT ${SELECT_COLUMNS} FROM coverage_checkpoint WHERE coverage_key = ?`)
      .bind(coverageKey)
      .first<CheckpointRow>();
    return row ? fromRow(row) : undefined;
  }

  async listDue(query: DueCheckpointQuery): Promise<readonly StoredCoverageCheckpoint[]> {
    parseInstant(query.dueBefore, "dueBefore");
    const limit = query.limit ?? 500;
    if (!Number.isSafeInteger(limit) || limit < 1 || limit > 1000) throw new Error("limit must be between 1 and 1000");
    const result = await this.db.prepare(`
      SELECT ${SELECT_COLUMNS}
      FROM coverage_checkpoint
      WHERE state <> 'BLOCKED'
        AND (complete_through IS NULL OR complete_through < ? OR missing_ranges_json <> '[]')
        AND (? IS NULL OR interval = ?)
        AND (? IS NULL OR session_scope = ?)
      ORDER BY CASE WHEN missing_ranges_json <> '[]' THEN 0 ELSE 1 END,
               complete_through ASC,
               coverage_key ASC
      LIMIT ?
    `).bind(
      query.dueBefore,
      query.interval ?? null,
      query.interval ?? null,
      query.sessionScope ?? null,
      query.sessionScope ?? null,
      limit,
    ).all<CheckpointRow>();
    return result.results.map(fromRow);
  }

  async compareAndSet(
    expectedVersion: number | undefined,
    proposed: StoredCoverageCheckpoint,
  ): Promise<CompareAndSetOutcome> {
    validateProposal(proposed);
    let row: CheckpointRow | null;
    if (expectedVersion === undefined) {
      row = await this.db.prepare(`
        INSERT INTO coverage_checkpoint (
          coverage_key, symbol, interval, session_scope, logical_data_variant,
          complete_through, state, missing_ranges_json, last_success_at,
          last_attempt_at, source_observed_through, universe_revision, blocker_json,
          retry_not_before, version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ON CONFLICT(coverage_key) DO NOTHING
        RETURNING ${SELECT_COLUMNS}
      `).bind(...values(proposed)).first<CheckpointRow>();
    } else {
      if (!Number.isSafeInteger(expectedVersion) || expectedVersion < 0) {
        throw new Error("expectedVersion must be a non-negative integer");
      }
      row = await this.db.prepare(`
        UPDATE coverage_checkpoint SET
          symbol = ?, interval = ?, session_scope = ?, logical_data_variant = ?,
          complete_through = ?, state = ?, missing_ranges_json = ?,
          last_success_at = ?, last_attempt_at = ?, source_observed_through = ?,
          universe_revision = ?, blocker_json = ?, retry_not_before = ?, version = version + 1
        WHERE coverage_key = ? AND version = ?
          AND (complete_through IS NULL OR (? IS NOT NULL AND ? >= complete_through))
        RETURNING ${SELECT_COLUMNS}
      `).bind(
        proposed.symbol,
        proposed.interval,
        proposed.sessionScope,
        proposed.logicalDataVariant,
        proposed.completeThrough ?? null,
        proposed.state,
        JSON.stringify(proposed.missingRanges),
        proposed.lastSuccessAt ?? null,
        proposed.lastAttemptAt ?? null,
        proposed.sourceObservedThrough ?? null,
        proposed.universeRevision ?? null,
        proposed.blocker ? JSON.stringify(proposed.blocker) : null,
        proposed.retryNotBefore ?? null,
        proposed.coverageKey,
        expectedVersion,
        proposed.completeThrough ?? null,
        proposed.completeThrough ?? null,
      ).first<CheckpointRow>();
    }
    return row ? { outcome: "UPDATED", checkpoint: fromRow(row) } : { outcome: "VERSION_CONFLICT" };
  }

  async recordAttempt(attempt: AcquisitionAttempt): Promise<void> {
    if (!attempt.attemptId || !attempt.coverageKey || !attempt.jobId) {
      throw new Error("attempt identity fields must be non-empty");
    }
    parseInstant(attempt.startedAt, "attempt startedAt");
    if (attempt.finishedAt) parseInstant(attempt.finishedAt, "attempt finishedAt");
    const result = await this.db.prepare(`
      INSERT INTO acquisition_attempt (
        attempt_id, coverage_key, job_id, started_at, finished_at, outcome, diagnostic_json
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(attempt_id) DO UPDATE SET
        finished_at = COALESCE(excluded.finished_at, acquisition_attempt.finished_at),
        outcome = COALESCE(excluded.outcome, acquisition_attempt.outcome),
        diagnostic_json = COALESCE(excluded.diagnostic_json, acquisition_attempt.diagnostic_json)
      WHERE acquisition_attempt.coverage_key = excluded.coverage_key
        AND acquisition_attempt.job_id = excluded.job_id
        AND acquisition_attempt.started_at = excluded.started_at
    `).bind(
      attempt.attemptId,
      attempt.coverageKey,
      attempt.jobId,
      attempt.startedAt,
      attempt.finishedAt ?? null,
      attempt.outcome ?? null,
      attempt.diagnostic ? JSON.stringify(attempt.diagnostic) : null,
    ).run();
    if (result.meta.changes !== 1) {
      throw new Error("attemptId is already associated with different immutable identity fields");
    }
  }

  async summarizeStaleAttempts(staleBefore: string): Promise<StaleAttemptSummary> {
    parseInstant(staleBefore, "staleBefore");
    const row = await this.db.prepare(`
      SELECT COUNT(*) AS count, MIN(started_at) AS oldest_started_at
      FROM acquisition_attempt
      WHERE finished_at IS NULL AND outcome IS NULL AND started_at < ?
    `).bind(staleBefore).first<{ count: number; oldest_started_at: string | null }>();
    const count = row?.count ?? 0;
    if (!Number.isSafeInteger(count) || count < 0) throw new Error("stale attempt summary is corrupt");
    return { count, ...(row?.oldest_started_at ? { oldestStartedAt: row.oldest_started_at } : {}) };
  }

  async supersedeStaleAttempts(command: SupersedeStaleAttemptsCommand): Promise<number> {
    if (!command.coverageKey || !command.replacementJobId) {
      throw new Error("stale attempt recovery identity fields must be non-empty");
    }
    parseInstant(command.staleBefore, "staleBefore");
    parseInstant(command.finishedAt, "finishedAt");
    const result = await this.db.prepare(`
      UPDATE acquisition_attempt
      SET finished_at = ?, outcome = 'SUPERSEDED', diagnostic_json = ?
      WHERE coverage_key = ? AND finished_at IS NULL AND outcome IS NULL AND started_at < ?
    `).bind(
      command.finishedAt,
      JSON.stringify({ reason: "STALE_ATTEMPT_REPLACED", replacementJobId: command.replacementJobId }),
      command.coverageKey,
      command.staleBefore,
    ).run();
    return result.meta.changes;
  }
}
