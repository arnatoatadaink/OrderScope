import type {
  SchedulerRunEvidenceStore,
  SchedulerRunJobStatus,
  SchedulerRunStatus,
} from "./run-evidence.ts";

export type EvidenceSessionClock = () => Date;

export type EvidenceJobDescriptor = {
  jobId: string;
  jobKind: string;
  source: string;
  boundaryStart?: string;
  boundaryEnd?: string;
  retryOfJobId?: string;
};

export type EvidenceJobCompletion = {
  status: Exclude<SchedulerRunJobStatus, "RUNNING">;
  failureCategory?: string;
  diagnostic?: Readonly<Record<string, unknown>>;
};

export class SchedulerRunEvidenceSession {
  private readonly store: SchedulerRunEvidenceStore;
  private readonly clock: EvidenceSessionClock;
  readonly runId: string;

  private constructor(store: SchedulerRunEvidenceStore, runId: string, clock: EvidenceSessionClock) {
    this.store = store;
    this.runId = runId;
    this.clock = clock;
  }

  static async start(options: {
    store: SchedulerRunEvidenceStore;
    runId: string;
    scheduledAt: string;
    schedulerRevision: string;
    workerMode: string;
    clock?: EvidenceSessionClock;
  }): Promise<SchedulerRunEvidenceSession> {
    const clock = options.clock ?? (() => new Date());
    await options.store.startRun({
      runId: options.runId,
      scheduledAt: options.scheduledAt,
      startedAt: clock().toISOString(),
      status: "RUNNING",
      schedulerRevision: options.schedulerRevision,
      workerMode: options.workerMode,
    });
    return new SchedulerRunEvidenceSession(options.store, options.runId, clock);
  }

  async supersedeStaleJobs(staleBefore: string): Promise<number> {
    return this.store.supersedeStaleJobs(
      staleBefore,
      this.clock().toISOString(),
      this.runId,
    );
  }

  async runJob<T>(
    descriptor: EvidenceJobDescriptor,
    execute: () => Promise<{ value: T; completion: EvidenceJobCompletion }>,
  ): Promise<T> {
    await this.store.startJob({
      runId: this.runId,
      jobId: descriptor.jobId,
      jobKind: descriptor.jobKind,
      source: descriptor.source,
      startedAt: this.clock().toISOString(),
      status: "RUNNING",
      ...(descriptor.boundaryStart ? { boundaryStart: descriptor.boundaryStart } : {}),
      ...(descriptor.boundaryEnd ? { boundaryEnd: descriptor.boundaryEnd } : {}),
      ...(descriptor.retryOfJobId ? { retryOfJobId: descriptor.retryOfJobId } : {}),
    });
    try {
      const executed = await execute();
      await this.store.finishJob(
        this.runId,
        descriptor.jobId,
        executed.completion.status,
        this.clock().toISOString(),
        {
          ...(executed.completion.failureCategory
            ? { failureCategory: executed.completion.failureCategory }
            : {}),
          ...(executed.completion.diagnostic
            ? { diagnostic: executed.completion.diagnostic }
            : {}),
        },
      );
      return executed.value;
    } catch (error) {
      await this.store.finishJob(
        this.runId,
        descriptor.jobId,
        "FAILED",
        this.clock().toISOString(),
        { failureCategory: "UNHANDLED_JOB_FAILURE" },
      );
      throw error;
    }
  }

  async recordLocked(descriptor: EvidenceJobDescriptor): Promise<void> {
    await this.store.startJob({
      runId: this.runId,
      jobId: descriptor.jobId,
      jobKind: descriptor.jobKind,
      source: descriptor.source,
      startedAt: this.clock().toISOString(),
      status: "RUNNING",
      ...(descriptor.boundaryStart ? { boundaryStart: descriptor.boundaryStart } : {}),
      ...(descriptor.boundaryEnd ? { boundaryEnd: descriptor.boundaryEnd } : {}),
      ...(descriptor.retryOfJobId ? { retryOfJobId: descriptor.retryOfJobId } : {}),
    });
    await this.store.finishJob(
      this.runId,
      descriptor.jobId,
      "SKIPPED_LOCKED",
      this.clock().toISOString(),
      { failureCategory: "LEASE_NOT_ACQUIRED" },
    );
  }

  async finish(
    status: Exclude<SchedulerRunStatus, "RUNNING">,
    diagnostic?: Readonly<Record<string, unknown>>,
  ): Promise<void> {
    await this.store.finishRun(
      this.runId,
      status,
      this.clock().toISOString(),
      diagnostic,
    );
  }
}
