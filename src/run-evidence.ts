export type SchedulerRunStatus = "RUNNING" | "SUCCEEDED" | "PARTIAL" | "FAILED" | "SUPERSEDED";
export type SchedulerRunJobStatus = "RUNNING" | "SUCCEEDED" | "PARTIAL" | "FAILED" | "SKIPPED_LOCKED" | "SUPERSEDED";

export type SchedulerRunRecord = {
  runId: string;
  scheduledAt: string;
  startedAt: string;
  finishedAt?: string;
  status: SchedulerRunStatus;
  schedulerRevision: string;
  workerMode: string;
  diagnostic?: Readonly<Record<string, unknown>>;
};

export type SchedulerRunJobRecord = {
  runId: string;
  jobId: string;
  jobKind: string;
  source: string;
  startedAt: string;
  finishedAt?: string;
  status: SchedulerRunJobStatus;
  boundaryStart?: string;
  boundaryEnd?: string;
  retryOfJobId?: string;
  failureCategory?: string;
  diagnostic?: Readonly<Record<string, unknown>>;
};

function parseInstant(value: string, name: string): void {
  if (!Number.isFinite(Date.parse(value))) throw new Error(`${name} must be a valid instant`);
}

function cleanDiagnostic(value: Readonly<Record<string, unknown>> | undefined): string | null {
  if (!value) return null;
  return JSON.stringify(value);
}

export class D1SchedulerRunEvidenceStore {
  constructor(private readonly db: D1Database) {}

  async startRun(record: SchedulerRunRecord): Promise<void> {
    if (!record.runId || !record.schedulerRevision || !record.workerMode) throw new Error("run identity fields must be non-empty");
    parseInstant(record.scheduledAt, "scheduledAt");
    parseInstant(record.startedAt, "startedAt");
    const result = await this.db.prepare(`
      INSERT INTO scheduler_run (
        run_id, scheduled_at, started_at, finished_at, status,
        scheduler_revision, worker_mode, diagnostic_json
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(run_id) DO NOTHING
    `).bind(
      record.runId, record.scheduledAt, record.startedAt, record.finishedAt ?? null,
      record.status, record.schedulerRevision, record.workerMode, cleanDiagnostic(record.diagnostic),
    ).run();
    if (result.meta.changes !== 1) throw new Error("scheduler run already exists");
  }

  async finishRun(runId: string, status: Exclude<SchedulerRunStatus, "RUNNING">, finishedAt: string,
    diagnostic?: Readonly<Record<string, unknown>>): Promise<void> {
    if (!runId) throw new Error("runId must be non-empty");
    parseInstant(finishedAt, "finishedAt");
    const result = await this.db.prepare(`
      UPDATE scheduler_run
      SET finished_at = ?, status = ?, diagnostic_json = COALESCE(?, diagnostic_json)
      WHERE run_id = ? AND status = 'RUNNING'
    `).bind(finishedAt, status, cleanDiagnostic(diagnostic), runId).run();
    if (result.meta.changes !== 1) throw new Error("scheduler run is not in RUNNING state");
  }

  async startJob(record: SchedulerRunJobRecord): Promise<void> {
    if (!record.runId || !record.jobId || !record.jobKind || !record.source) throw new Error("run job identity fields must be non-empty");
    parseInstant(record.startedAt, "startedAt");
    if (record.boundaryStart) parseInstant(record.boundaryStart, "boundaryStart");
    if (record.boundaryEnd) parseInstant(record.boundaryEnd, "boundaryEnd");
    const result = await this.db.prepare(`
      INSERT INTO scheduler_run_job (
        run_id, job_id, job_kind, source, started_at, finished_at, status,
        boundary_start, boundary_end, retry_of_job_id, failure_category, diagnostic_json
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(run_id, job_id) DO NOTHING
    `).bind(
      record.runId, record.jobId, record.jobKind, record.source, record.startedAt,
      record.finishedAt ?? null, record.status, record.boundaryStart ?? null,
      record.boundaryEnd ?? null, record.retryOfJobId ?? null,
      record.failureCategory ?? null, cleanDiagnostic(record.diagnostic),
    ).run();
    if (result.meta.changes !== 1) throw new Error("scheduler run job already exists");
  }

  async finishJob(runId: string, jobId: string, status: Exclude<SchedulerRunJobStatus, "RUNNING">,
    finishedAt: string, options: { failureCategory?: string; diagnostic?: Readonly<Record<string, unknown>> } = {}): Promise<void> {
    parseInstant(finishedAt, "finishedAt");
    const result = await this.db.prepare(`
      UPDATE scheduler_run_job
      SET finished_at = ?, status = ?, failure_category = ?,
          diagnostic_json = COALESCE(?, diagnostic_json)
      WHERE run_id = ? AND job_id = ? AND status = 'RUNNING'
    `).bind(
      finishedAt, status, options.failureCategory ?? null,
      cleanDiagnostic(options.diagnostic), runId, jobId,
    ).run();
    if (result.meta.changes !== 1) throw new Error("scheduler run job is not in RUNNING state");
  }

  async supersedeStaleJobs(staleBefore: string, finishedAt: string, replacementRunId: string): Promise<number> {
    parseInstant(staleBefore, "staleBefore");
    parseInstant(finishedAt, "finishedAt");
    if (!replacementRunId) throw new Error("replacementRunId must be non-empty");
    const result = await this.db.prepare(`
      UPDATE scheduler_run_job
      SET finished_at = ?, status = 'SUPERSEDED', failure_category = 'STALE_RUN_JOB',
          diagnostic_json = ?
      WHERE status = 'RUNNING' AND started_at < ?
    `).bind(finishedAt, JSON.stringify({ replacementRunId }), staleBefore).run();
    return result.meta.changes;
  }
}
