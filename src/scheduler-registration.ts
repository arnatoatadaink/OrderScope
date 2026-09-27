export const SCHEDULER_REGISTRATION_REVISION = "px0-001-v1";
export const REVIEWED_CRON = "* * * * *";

export type SchedulerRegistrationProjection = {
  crons: readonly string[];
  workerMode: string;
  newsEnabled: string;
  schedulerEvidenceEnabled?: string;
};

export type SchedulerRegistrationReview = {
  revision: string;
  cron: string;
  shadowOnly: true;
  newsDisabled: true;
  schedulerEvidenceDisabled: true;
};

export function reviewSchedulerRegistration(
  projection: SchedulerRegistrationProjection,
): SchedulerRegistrationReview {
  if (projection.crons.length !== 1 || projection.crons[0] !== REVIEWED_CRON) {
    throw new Error("scheduler registration must remain the reviewed once-per-minute cron");
  }
  if (projection.workerMode !== "shadow") {
    throw new Error("scheduler registration review requires WORKER_MODE=shadow");
  }
  if (projection.newsEnabled !== "false") {
    throw new Error("scheduler registration review requires NEWS_ACQUISITION_ENABLED=false");
  }
  const evidence = projection.schedulerEvidenceEnabled ?? "false";
  if (evidence !== "false") {
    throw new Error("scheduler registration review requires scheduler run evidence disabled");
  }
  return {
    revision: SCHEDULER_REGISTRATION_REVISION,
    cron: REVIEWED_CRON,
    shadowOnly: true,
    newsDisabled: true,
    schedulerEvidenceDisabled: true,
  };
}
