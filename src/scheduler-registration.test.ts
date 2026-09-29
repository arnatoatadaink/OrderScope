import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  REVIEWED_CRON,
  SCHEDULER_REGISTRATION_REVISION,
  reviewSchedulerRegistration,
} from "./scheduler-registration.ts";

function configProjection(text: string) {
  const cronMatch = text.match(/"triggers"\s*:\s*\{\s*"crons"\s*:\s*\[\s*"([^"]+)"\s*\]/s);
  assert.ok(cronMatch, "wrangler.jsonc must declare one top-level cron trigger");
  const liveCanaryIndex = text.indexOf('"live-canary"');
  assert.ok(liveCanaryIndex >= 0, "wrangler.jsonc must define live-canary environment");
  const liveCanary = text.slice(liveCanaryIndex);
  const workerMode = liveCanary.match(/"WORKER_MODE"\s*:\s*"([^"]+)"/)?.[1];
  const newsEnabled = liveCanary.match(/"NEWS_ACQUISITION_ENABLED"\s*:\s*"([^"]+)"/)?.[1];
  const schedulerEvidenceEnabled = liveCanary.match(/"SCHEDULER_RUN_EVIDENCE_ENABLED"\s*:\s*"([^"]+)"/)?.[1];
  assert.ok(workerMode);
  assert.ok(newsEnabled);
  return {
    crons: [cronMatch[1]],
    workerMode,
    newsEnabled,
    ...(schedulerEvidenceEnabled ? { schedulerEvidenceEnabled } : {}),
  };
}

test("reviewed scheduler registration is fixed to shadow once-per-minute", () => {
  const result = reviewSchedulerRegistration({
    crons: [REVIEWED_CRON],
    workerMode: "shadow",
    newsEnabled: "false",
  });
  assert.deepEqual(result, {
    revision: SCHEDULER_REGISTRATION_REVISION,
    cron: "* * * * *",
    shadowOnly: true,
    newsDisabled: true,
    schedulerEvidenceDisabled: true,
  });
});

test("registration review rejects cron or activation drift", () => {
  assert.throws(() => reviewSchedulerRegistration({
    crons: ["*/5 * * * *"], workerMode: "shadow", newsEnabled: "false",
  }), /once-per-minute/);
  assert.throws(() => reviewSchedulerRegistration({
    crons: [REVIEWED_CRON], workerMode: "live", newsEnabled: "false",
  }), /WORKER_MODE=shadow/);
  assert.throws(() => reviewSchedulerRegistration({
    crons: [REVIEWED_CRON], workerMode: "shadow", newsEnabled: "true",
  }), /NEWS_ACQUISITION_ENABLED=false/);
  assert.throws(() => reviewSchedulerRegistration({
    crons: [REVIEWED_CRON], workerMode: "shadow", newsEnabled: "false", schedulerEvidenceEnabled: "true",
  }), /scheduler run evidence disabled/);
});

test("current wrangler registration matches reviewed live-canary boundary", () => {
  const text = readFileSync(new URL("../wrangler.jsonc", import.meta.url), "utf8");
  const projection = configProjection(text);
  const result = reviewSchedulerRegistration(projection);
  assert.equal(result.cron, REVIEWED_CRON);
  assert.equal(result.shadowOnly, true);
});

test("reviewed Worker entrypoint retains scheduled orchestration", () => {
  const text = readFileSync(new URL("./worker.ts", import.meta.url), "utf8");
  assert.match(text, /async scheduled\s*\(controller:\s*ScheduledController,/);
  assert.match(text, /ctx\.waitUntil\(runScheduledTick\(controller, env, dependencies\)\)/);
});
