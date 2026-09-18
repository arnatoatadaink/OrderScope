# OrderScope — Local Corporate Intelligence Progress Tracker

Status: **Active integrated runtime tracker**
Date: 2026-09-15
Scope: Local Corporate Intelligence / X0 integration

This file is the sole integrated authority for Local Corporate Intelligence runtime progress after the 2026-09-05 consolidation. Detailed implementation notes remain in task-specific handoffs.

## 1. Working rules

- `Accepted` means implementation passed its explicitly required local acceptance evidence.
- `Provisional result` means Web-side implementation/documentation is complete but required local/operator acceptance is still pending.
- `Ready` means prerequisites are satisfied.
- `Blocked` means an external approval/dependency/gate remains.
- Real D1 work remains separate from fixture-path development unless an approved change window explicitly opens it.
- Worker remains Shadow; Local does not directly control Worker runtime.

## 2. Local foundation / ingestion state

| Task | Status | Evidence / next action |
|---|---|---|
| L0-001 | Accepted / inherited prerequisite | Reference only |
| L0-002 | Accepted | Scaffold/Git boundary complete |
| L0-003 | Accepted | focused 9; full 441; compileall success; diff clean |
| L0-004 | Accepted | focused 11; full 418; diff clean |
| L0-005 | Accepted | focused 7; full 352; compileall success; diff clean |
| L0-006 | Accepted | focused 6; full 447; compileall success; diff clean |
| L1-001 | Accepted | focused 8; full 360; diff clean |
| L1-002 | Accepted | storage 7; focused 8; full 368; compileall success; diff clean |
| L1-003 | INCONCLUSIVE — first PB-04 session campaign accepted remotely | The four-call September 4 campaign accepted 390 bars and advanced the clean NVDA checkpoint from version 10 to 14 / `2026-09-04T20:00:00.000Z`. Further session campaigns, normal-scheduler handoff, stability observation, and Phase B remain separately gated. |
| L1-004 | Accepted — fixture path | focused 11; full 372; diff clean |
| L1-005 | Accepted — fixture path | focused 12; full 391; diff clean |
| L1-006 | Accepted — fixture path | focused command 21; full 468; compileall success; diff clean |

## 3. X0 runtime state

| Task | Status | Evidence |
|---|---|---|
| X0-001 | Accepted | focused 7; full 398; diff clean |
| X0-002 | Accepted | focused 9; full 407; diff clean |
| X0-003 | Accepted | focused 14; full 432; compileall success; diff clean |
| X0-004 | Accepted | focused 16; full 457; compileall success; diff clean |
| X0-005 | Accepted | focused 4; full 461; compileall success; diff clean |
| X0-006 | Accepted — policy-level fixture path | External review accepted; F1-F4 tracked as PX0 follow-ups |

`X0-001..006` is complete for the fixture-path integration boundary. This does not authorize remote D1, Worker mutation, or live scheduler registration.


## A0 — Analyst Expectations / Cross-Market Context

| Task | Status | Evidence / next action |
|---|---|---|
| A0-001 | Accepted locally | 8 focused contract tests; 88 combined contract tests; Cross-Market capital movement remains Interpretation and FX contradiction cannot create a Fact |
| A0-002 | Accepted locally | 22 focused Cross-Market tests; 94 real observations; 12/12 required series; H1 SUPPORT, H2 SUPPORT, H3 SUPPORT, H4 UNKNOWN, H5 CONTRADICT. Consensus gap explicitly evaluated as UNKNOWN because no reviewed historical as-of source is available; no current-value backfill. See `A0-002_CBRS_MULTI_LAYER_FLOW_ACCEPTANCE_2026-09-14.md` |

## 3A. CS0 / MR0 capital structure and market reaction

| Task | Status | Evidence / boundary |
|---|---|---|
| CS0-001 | Accepted locally | Stateful instrument lifecycle, provenance/history, and allowed/forbidden transitions reviewed; included in 38 focused tests |
| CS0-002 | Accepted locally | Bounded debt-resolution attention remains Interpretation and cannot assert repayment from financing intent; included in 38 focused tests |
| CS0-003 | Accepted locally | Instrument-specific convertible-note overhang removal retains residual dilution lineage; included in 38 focused tests |
| MR0-001 | Accepted locally | Deterministic catalyst-linked reaction windows remain session-aware measurements and non-causal; included in 38 focused tests |
| MR0-002 | Accepted locally | Complete formal state vocabulary and guarded transitions; no new fixed numeric thresholds; included in 38 focused tests |
| MR0-003 | Accepted locally | TNON delayed repricing, CHPT persistent rediscovery, low-float/single-session failure, offsetting dilution, conflicting news, and market-wide confounders covered |

Acceptance evidence: 38 focused tests passed; full Python suite 696 passed; compileall passed; `git diff --check` passed. See `CS0_MR0_LOCAL_ACCEPTANCE_HANDOFF_2026-09-15.md`. This is a local deterministic acceptance only; live provider, Worker/Cron, remote D1, purge, and trading actions remain outside scope.

## 4. N1-006 — News recall evaluation state

Dependencies:

- `E0-007` Accepted;
- `N1-005` Accepted.

### Accepted evaluator framework

```text
focused evaluator tests -> 7 passed
full pytest suite        -> 475 passed
compileall               -> success
git diff --check         -> clean
```

### Accepted benchmark manifest/report path

```text
focused benchmark/CLI command -> 15 passed
full pytest suite              -> 482 passed
compileall                     -> success
git diff --check               -> clean
```

Provides metadata-only `news-recall-benchmark-v0.1` and:

```text
quality news-recall --benchmark <json>
```

### Official 30-day reference seed — Complete

Window:

```text
2026-08-11T00:00:00Z <= timestamp < 2026-09-10T00:00:00Z
```

Reference artifacts:

- `docs/work-management/local-corporate-intelligence/N1-006_REFERENCE_SEED_2026-08-11_2026-09-10.md`
- `analysis/config/benchmarks/n1-006-amd-nvda-20260811-20260910-reference.json`

Seeded SEC events:

- AMD financing — 2026-08-17T16:05:40Z;
- NVIDIA / SB Energy partnership — 2026-08-17T08:41:33Z;
- AMD leadership change — 2026-08-19T16:16:56Z;
- NVIDIA Q2 FY2027 earnings — 2026-08-26T16:21:19Z.

The reference seed must not be interpreted as a zero-recall benchmark before News population.

### Candidate-population path — Accepted implementation

Implemented:

- metadata-only Alpaca News HTTP transport;
- bounded AMD/NVDA retrospective collector;
- output constrained beneath `ORDERSCOPE_DATA_ROOT/benchmarks/n1-006/`;
- `quality news-recall-candidates` CLI;
- `include_content=false` only.

Measured evidence:

```text
focused population/CLI command -> 15 passed
full pytest suite               -> 488 passed
compileall                      -> success / no errors
git diff --check                -> clean / no findings
```

Retrospective lag uses Alpaca provider publication time versus SEC/IR reference availability. It does not reconstruct local scheduler delay.

### Explicit labeling/finalization path — Accepted implementation

Implemented:

- `analysis/app/orderscope_local/news/recall_labeling.py`
- `analysis/tests/news/test_news_recall_labeling.py`
- `quality news-recall-label-template`
- `quality news-recall-finalize`

Measured evidence:

```text
focused labeling/CLI command -> 15 passed
full pytest suite             -> 494 passed
compileall                    -> success / no errors
git diff --check              -> clean / no findings
```

Generated templates begin as `unreviewed`; finalization fails until every candidate is explicitly reviewed. `matched` requires an explicit reference ID and News-side assigned subject. `unresolved` remains unresolved rather than guessed.

### N1-006 real-data benchmark — Accepted

The authenticated 30-day Alpaca News population and explicit review are complete. All 645 metadata-only candidates were reviewed: 51 matched, 594 unrelated, and 0 unresolved. Finalization produced 51 News discoveries covering all four frozen reference events.

Measured quality result:

```text
reference events                 -> 4
discovered references            -> 4
discovery rate / recall          -> 1.0000
News discoveries                 -> 51
subject/ticker misattributions   -> 0 (0.0000)
unresolved benchmark labels      -> 0
minimum signed lag               -> -357011 s
maximum signed lag               -> 14636 s
median signed lag                -> -44826.5 s
```

Per-reference first-discovery signed lag:

- AMD financing: `-357011 s`;
- NVIDIA / SB Energy partnership: `-104042 s`;
- AMD leadership change: `14636 s`;
- NVIDIA Q2 FY2027 earnings: `14389 s`.

Negative values mean the Alpaca publication timestamp preceded the frozen SEC availability timestamp. These retrospective provider-publication lags do not measure local scheduler delay.

Real News acquisition uses the same authenticated Alpaca Market Data credential pair already used for Alpaca market data; credentials remain process-local through:

```text
ORDERSCOPE_SECRET_ALPACA_API_KEY
ORDERSCOPE_SECRET_ALPACA_API_SECRET
```

The final benchmark remains a local ignored artifact at `var/benchmarks/n1-006/amd-nvda-news-benchmark-final.json`; it contains metadata only and no credentials or News bodies. The measured result above, rather than synthetic fixture metrics, is the N1-006 acceptance evidence.

## 5. News Worker/Schedule production follow-up

A steady-state production News acquisition design is now recorded separately from N1-006 retrospective benchmarking:

`docs/work-management/local-corporate-intelligence/NEWS_WORKER_ACQUISITION_DESIGN_2026-09-10.md`

WBS-unreflected tracking ID:

```text
UWBS-016 — Implement Worker/Schedule News metadata acquisition job
```

Boundary:

- `N0-002` continues to own provider normalization;
- `UWBS-016` owns Worker/Schedule orchestration of that accepted adapter;
- initial Canary remains AMD/NVDA only;
- metadata-only baseline; no News body in Worker acquisition;
- planning cadence is every 5 minutes during the configured U.S. observation day;
- cadence is provisional and should be validated/adjusted from N1-006 measured recall/lag;
- I0-003 checkpoint and I0-004 idempotency are reused;
- live Worker registration/change remains separately gated and Worker remains Shadow.

Current dependency sequence:

```text
N1-006 measured benchmark Accepted
  -> confirm/adjust proposed News cadence
  -> future WBS incorporation/remap of UWBS-016
  -> reviewed Worker change window
  -> AMD/NVDA Worker News Canary activation
```

### W1-001 live Canary change-window result — Rolled back

The reviewed live-canary window was opened twice on 2026-09-11 JST and safely
rolled back twice. Migration `0007_news_metadata.sql` is applied to the isolated
live-canary D1 database. The first activation exposed an Alpaca calendar 401;
the managed secrets were updated and the calendar endpoint subsequently returned
HTTP 200. The resumed live tick completed one Market job within the shared
budget (`external=1/40`, `D1=21/40`) but planned no News job.

Live Cron evidence showed a stable `:15` seconds offset while the News planner
requires the full scheduled timestamp to be exactly divisible by five minutes.
Therefore no eligible News opportunity can occur under the current implementation.
The final Worker version `c2aebaa7-d82a-4f79-986a-5700b01a5146` is `shadow` with
News disabled. W1-001 live acceptance is blocked until the cadence predicate is
repaired, tested, reviewed, and a new change window is approved. See
`W1-001_LIVE_CANARY_CHANGE_WINDOW_REPORT_2026-09-11.md`.

### W1-001 live Canary reopen result — Evidence collected, safely rolled back

The reviewed W1-006 release was safely deployed and the AMD/NVDA metadata-only
News Canary was reopened on 2026-09-11. The repaired UTC minute-bucket predicate
produced News jobs at all 12 distinct reviewed five-minute opportunities despite
the stable `:30` Cron seconds offset. All 12 completed, with no News partial or
failure, no budget crossing, and no Cron change. The reviewed maximum was
`external=2/40` and `D1=21/40`; Market gap retries remained fail-closed and did
not falsely advance coverage.

One canonical NVDA article and one query membership were created during the
reviewed window. Publication-to-retrieval lag was 351 seconds and
publication-to-acceptance lag was 951 seconds. A repeat observation was counted
as a duplicate rather than another canonical article, and the D1 schema contains
no News body column.

Final disposition is `ROLLED_BACK`, not because of a cadence, News correctness,
Market, or budget failure, but because a closeout Cloudflare D1 evidence request
stalled and ultimately returned API authorization error `7403`, preventing
reliable continued monitoring. Safe rollback version
`16af6aeb-6818-4a09-be58-10aa7931a2de` is `shadow` with News disabled; a
subsequent shadow tick confirmed zero News calls/mutations. See
`W1-001_LIVE_CANARY_REOPEN_CHANGE_WINDOW_REPORT_2026-09-11.md`.

Next CP gate: review the reopen evidence and Cloudflare API authorization/control
failure before authorizing any further live Canary or `full-v0.1` activation.

### W1-007 Cloudflare control-path diagnostic — Accepted locally

On 2026-09-11, two consecutive read-only control-path passes succeeded against
the expected `live-canary` account and D1 database. Wrangler identity, `d1 info`,
remote `SELECT 1`, and `PRAGMA table_list` all passed without `7403` or a
quota-specific error. The earlier `7403` is not currently reproducible. Root
cause remains unknown; transient control-plane state or stale authentication
state remain hypotheses only and are not encoded as the failure classification.

Rollback version `16af6aeb-6818-4a09-be58-10aa7931a2de` remains deployed.
Read-only `/health` verification returned `mode=shadow` and News disabled. No
Worker/config, Cron, activation, or D1 data mutation was performed. See
`W1-007_CLOUDFLARE_API_CONTROL_PATH_DIAGNOSTIC_LOCAL_REPORT_2026-09-11.md`.

W1-007 Web review is Accepted as of 2026-09-13. The read-only diagnostic evidence,
safe rollback baseline, and current Wrangler/D1 command semantics were reviewed
without remote mutation. The next CP gate is a separately authorized short monitored
W1-001 confirmation/closeout window. See `W1-007_WEB_REVIEW_2026-09-13.md` and
`W1-001_CONFIRMATION_CLOSEOUT_CHANGE_WINDOW_2026-09-13.md`.

### W1-001 confirmation / closeout result — Accepted

The explicitly authorized short closeout window completed on 2026-09-14. Three
distinct eligible opportunities at `12:50:58Z`, `12:55:58Z`, and `13:00:58Z`
each planned and completed one News job with zero partials/failures. Ineligible
minutes produced no phantom News work. Maximum external usage was `2/40`; the
maximum D1 usage was `21/40` on an accepted fail-closed Market gap-retry tick.

Cloudflare D1 control checks succeeded before, during, and after the window with
no recurrence of `7403`. The final disposition is `ACCEPTED`. Checked-in safe
baseline version `f6b35356-a7c2-40ed-8bbb-7b957f4ead11` is deployed with
`WORKER_MODE=shadow`, News disabled, `canary-v0.1`, AMD/NVDA only, five-minute
News cadence, and the unchanged one-minute Cron. A subsequent scheduled tick
confirmed zero News work. See
`W1-001_CONFIRMATION_CLOSEOUT_CHANGE_WINDOW_REPORT_2026-09-14.md`.

### Packet A scheduler / cadence regression hardening — Accepted locally

On 2026-09-12, the News scheduler opportunity boundary was canonicalized to the
start of its eligible UTC minute bucket. Seconds offsets `00`, `15`, `30`, and
`59` now produce the same requested range and job identity. A repeated
observation within one eligible opportunity is therefore already covered by the
durable checkpoint rather than becoming a second sub-minute acquisition.

Miniflare integration evidence executes one metadata-only AMD/NVDA opportunity,
observes the same provider article through both symbol queries, and then repeats
the opportunity at a different seconds offset. The repeat performs no provider
call, creates no additional canonical article or membership, and does not
advance checkpoint version or `complete_through`. Its digest reports zero
planned and zero completed News jobs, so absence of planned work is not counted
as successful workload completion. A separate shadow-mode fixture with News
configuration enabled proves that no calendar/provider path or News D1 table is
mutated.

Changed files:

- `src/news-schedule.ts`
- `src/news-schedule.test.ts`
- `src/worker-orchestration.integration.test.ts`

Assignment: GPT-5.6 Sol acceptance role, medium reasoning, because the bounded
scheduler correction required cross-reading the runtime tracker and handoff and
promoting local Packet A evidence at a review boundary.

Acceptance evidence: focused TypeScript 23 passed; full TypeScript 130 passed;
full Python 503 passed with the two previously recorded dependency deprecation
warnings; TypeScript typecheck passed; Wrangler dry-run passed with News disabled
and Worker mode shadow; Python compileall passed; `git diff --check` passed.

Packet A does not authorize Worker deployment, Cron mutation, News activation,
or a live Canary. W1-007 Web review and a separate approved change window remain mandatory before any confirmation/closeout Canary.

### Packet B shared budget / idempotency / checkpoint regression — Accepted locally

Packet B fixed deterministic regression coverage around the already-shared `InvocationBudget` boundary. Market and News now have explicit acceptance evidence showing that one invocation-level external-call budget is consumed across both paths, News fails closed at the remaining limit, D1 budget preflight never increments beyond its ceiling, a News checkpoint CAS conflict preserves current checkpoint truth, and overlapping retries preserve one canonical article with separate AMD/NVDA query membership.

Changed files:

- `src/packet-b-regression.test.ts`

Acceptance evidence: focused Packet B TypeScript 4 passed; full TypeScript 134 passed; full Python 503 passed with the two existing dependency deprecation warnings; TypeScript typecheck passed; Python compileall passed; Wrangler dry-run passed with Worker mode shadow and News disabled; `git diff --check` passed.

Packet B does not authorize Worker deployment, Cron mutation, News activation, or remote D1 mutation.

### Packet C control-path failure classification / fail-safe — Accepted locally

Packet C distinguishes provider/auth/control-path failures without asserting an unproven root cause for the prior Cloudflare `7403`. News provider failures are categorized as authentication, authorization, transport, rate-limit, provider-unavailable, or invalid-response. Execution failures separately distinguish D1 control read, D1 control write, News store failure, budget failure, and checkpoint conflict. Raw provider bodies, credentials, socket text, and raw D1 error strings are not promoted into persisted/public diagnostics.

The fail-closed regression boundary proves that checkpoint-read failure prevents provider acquisition, News-store failure preserves prior `completeThrough`, checkpoint-write failure cannot be reported as successful new coverage, authentication failure remains a sanitized non-retryable provider category, and retryable control/data failures leave retryable state where safe.

Changed files:

- `src/news.ts`
- `src/news.test.ts`
- `src/news-execution.ts`
- `src/packet-c-control-path.test.ts`

Acceptance evidence: focused Packet C TypeScript 17 passed; full TypeScript 141 passed; full Python 503 passed with the two existing dependency deprecation warnings; TypeScript typecheck passed; Python compileall passed; Wrangler dry-run passed with Worker mode shadow and News disabled; `git diff --check` passed.

Packet C does not establish that `7403` was caused by stale OAuth or any other specific control-plane cause. Root cause remains unknown.

### Packet D durable run evidence / restart-recovery boundary — Accepted locally

Packet D adds durable scheduler run/job evidence without changing I0-003 checkpoint ownership. `scheduler_run` and `scheduler_run_job` persist invocation/job identity, scheduler revision, bounded execution window, final status, retry relation and sanitized failure category. Restart recovery compares the recorded bounded window with the provider/source checkpoint; evidence never substitutes for `completeThrough` or advances coverage by itself.

The worker integration is feature-gated by `SCHEDULER_RUN_EVIDENCE_ENABLED`. When disabled, existing behavior remains unchanged. When enabled after migration `0008_scheduler_run_evidence.sql` is present, live Market and News work record run/job evidence through the same `budgetedD1` / shared `InvocationBudget`. Shadow mode performs no scheduler-evidence mutation even when the feature flag is enabled.

Recovery behavior covers stop-before-checkpoint, stop-after-checkpoint, bounded replay, duplicate/retry behavior, stale job replacement, parent stale-run supersession, and lease ownership ambiguity. Lease takeover remains governed by expiry rather than PID/owner-name inference. Stale scheduler job/run evidence is operational evidence only; checkpoint state remains the coverage truth.

Changed files include:

- `migrations/0008_scheduler_run_evidence.sql`
- `src/run-evidence.ts`
- `src/run-evidence-session.ts`
- `src/restart-recovery.ts`
- `src/worker.ts`
- `src/packet-d-run-evidence.test.ts`
- `src/packet-d-restart-recovery.test.ts`
- `src/packet-d-run-session.test.ts`
- `src/packet-d-worker-evidence.test.ts`

Key implementation commits include `91bbf3b`, `75079a6`, `f3f6280`, `042a248`, `5b44883`, `1c23344`, `969e15a`, `42e3adf`, `a24258e`, `9fbef3d`, `1586d3e`, and `55866e5`.

Acceptance evidence: focused Packet D TypeScript 16 passed; full TypeScript 157 passed; full Python 503 passed with the two existing dependency deprecation warnings; TypeScript typecheck passed; Python compileall passed; Wrangler dry-run passed with top-level Worker mode shadow and News disabled; `git diff --check` passed with no findings.

Packet D does not authorize migration `0008` against remote D1, Worker deployment, Cron mutation, scheduler-evidence activation, News activation, or another live Canary. Those remain separately gated.

### Packet E retention / retry / bounded replay operator path — Accepted locally

Packet E adds a CLI-only, bounded operator surface for retention inspection, explicit due-content deletion, and registered bounded replay. Operator snapshots are allow-listed metadata only; raw News bodies, credentials, and arbitrary extension fields are rejected. Replay requires an explicit source/time window, is limited to FAILED/RETRYABLE work, caps both the window and selected work count, and executes only through registered handlers.

The first concrete replay source is `alpaca-news`, restricted to the accepted AMD/NVDA metadata-only canary adapter with `include_content=false`. Local temporary News content uses an opaque `temporary:v1:<id>` reference beneath `ORDERSCOPE_DATA_ROOT`; explicit due refs only may be deleted, and CLI output does not expose body text, local paths, or deletion proofs.

Changed files include:

- `analysis/app/orderscope_local/integration/operator.py`
- `analysis/app/orderscope_local/integration/replay.py`
- `analysis/app/orderscope_local/news/temporary_store.py`
- `analysis/app/orderscope_local/cli.py`
- `analysis/tests/integration/test_operator.py`
- `analysis/tests/integration/test_operator_manifest.py`
- `analysis/tests/integration/test_registered_replay.py`
- `analysis/tests/cli/test_operator_cli.py`
- `analysis/tests/news/test_local_temporary_store.py`

Acceptance evidence: focused Packet E Python 24 passed; full Python 527 passed with the two existing dependency deprecation warnings; Python compileall passed; `git diff --check` passed with no findings.

Packet E does not authorize arbitrary HTTP job starts, unbounded reprocessing, remote D1 export/purge, or Worker/Cron mutation. `UWBS-023..026` remains the design input for later D1 drain lifecycle work rather than implicit authorization.

### Packet F local backup / restore / restore-drill boundary — Accepted locally

Packet F adds explicit-file local backup/restore with SHA-256 manifests and clean-destination restore. It does not recursively sweep `ORDERSCOPE_DATA_ROOT` and does not automatically include temporary body content. Restore verifies every selected file before and after copy and rejects absolute/root-escaping paths, duplicates, missing sources, tampered backup entries, and non-empty restore targets.

The restore drill validates the restored local SQLite catalog read-only with `PRAGMA integrity_check`, `foreign_key_check`, and migration version/name/checksum agreement. Canonical Parquet validation checks artifact SHA-256, row count, OrderScope schema metadata, `source_manifest_id`, and `source_artifact_sha256` against the referenced D1 export manifest.

Changed files include:

- `analysis/app/orderscope_local/storage/backup.py`
- `analysis/app/orderscope_local/storage/restore_drill.py`
- `analysis/tests/storage/test_backup_restore.py`
- `analysis/tests/storage/test_restore_drill.py`

Acceptance evidence: focused Packet F backup/restore tests 5 passed; focused backup/restore + restore-drill tests 10 passed; full Python 537 passed with the two existing dependency deprecation warnings; Python compileall passed; `git diff --check` passed with no findings.

Packet F covers the local reproducible recovery boundary only. It does not create or authorize remote D1 backups, remote D1 restore, live Worker mutation, or Cron changes.

## 6. Post-X0 operational follow-ups

| Follow-up | Status | Boundary |
|---|---|---|
| PX0-001 | Accepted locally / remapped to R0-001 | Reviewed scheduler registration plan accepted locally; deploy/trigger mutation remains separately gated |
| PX0-002 | Accepted locally / remapped to R0-002 | Durable scheduler run/job evidence and stale-lock/restart recovery accepted through Packet D |
| PX0-003 | Accepted locally / remapped to R0-003 | CLI-only retention inspection, explicit due-content deletion, and registered bounded replay accepted through Packet E; remote D1 export/purge remains separate |
| PX0-004 | Accepted locally / remapped to R0-004 | Explicit local backup/restore and restore drill accepted through Packet F; remote D1 backup/restore remains separate |

These legacy PX0 IDs are now formally incorporated as R0-001..004 in the main WBS; retain them here for traceability.

### Formal R0 operations/recovery status

| Task | Status | Evidence / boundary |
|---|---|---|
| R0-001 | Accepted locally | Scheduler registration review accepted; no live Cron/Worker mutation authorized |
| R0-002 | Accepted — remote schema gate closed | Packet D accepted; migration `0008_scheduler_run_evidence.sql` applied to live-canary D1 and post-apply verified; scheduler evidence activation remains separately gated |
| R0-003 | Accepted locally | Packet E bounded retention/replay operator path accepted |
| R0-004 | Accepted locally | Packet F backup/restore/restore-drill boundary accepted |
| R0-005 | Accepted evidence boundary; activation gated | AMD/NVDA metadata-only Worker/Schedule orchestration exercised through accepted local regressions and reviewed live Canary evidence; Worker remains Shadow after rollback and reactivation requires a separate change window |
| R0-006 | Accepted locally | D1 retention contract accepted; current control truth never purge eligible |
| R0-007 | Accepted locally / fixture export+custody | Deterministic half-open bounded export/custody accepted; remote D1 export remains change-window gated |
| R0-008 | Accepted locally through `PURGE_ELIGIBLE` | Ordered ACK/quality/grace/replay/resolution lifecycle accepted; `PURGED` remains remote-only and separately authorized |
| R0-009 | Accepted locally | Failure/recovery fixtures accepted; final full TypeScript 178/178, typecheck passed, full Python 555/555, compileall passed |

Detailed R0-006..009 acceptance: `R0_D1_DRAIN_LOCAL_ACCEPTANCE_2026-09-13.md`.

## 7. Parallel/deferred lanes

- `N1-006` real 30-day benchmark is Accepted.
- `W1-001` confirmation/closeout is Accepted after three additional successful eligible News opportunities, continuous control-path evidence, and verified safe rollback. Further Worker activation remains separately gated.
- `L1-003 / SMOKE-007` Phase A real-D1 export/custody is accepted; the window is INCONCLUSIVE pending fresh pause-created market-session catch-up evidence.
- `PX0-001..004` are Accepted locally and formally remapped to `R0-001..004`.
- `R0-006..009` D1 hot-store drain local/fixture boundaries are Accepted; remote export/purge and the actual `PURGED` transition remain separately gated.
- `A0-001` and `A0-002` are Accepted locally; A0 is complete at the current v0.1 validation boundary.
- `CS0-001..003` and `MR0-001..003` are Accepted locally at the deterministic contract/fixture boundary.
- WBS-unreflected work is tracked in `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`.
- Worker remains Shadow.

## 8. Current restart rule

1. Treat N1-006 as Accepted through the real 645-candidate review, 4/4 recall measurement, and 19 / 503 / compileall / diff evidence.
2. Treat the W1-006 cadence repair as live-evidence-confirmed for non-zero Cron seconds offsets through the 12-opportunity reopen window.
3. Treat W1-007 and the short W1-001 confirmation/closeout window as Accepted. The earlier `7403` did not recur; its historical root cause remains unknown. Any further Worker activation remains separately gated.
4. Treat Packets A through F as locally Accepted through their recorded deterministic regression, operator, recovery, and full-suite evidence.
5. Treat `R0-001..004` and `R0-006..009` as locally Accepted at their recorded non-live boundaries. Treat `R0-005` as evidence-complete for reviewed orchestration while activation remains separately gated after rollback.
6. Treat the earlier one-shot windows and the PB-04 September 4 and September 8 session campaigns as remotely accepted. The current clean checkpoint is version 18 through `2026-09-08T20:00:00.000Z`; against the current September 16 boundary, PB-05 remains blocked by six sessions / 2,340 bars of unfinished PB-04 work. Any next-session campaign requires a fresh moving-retention-horizon preflight and a separately authorized one-session window; only after recovery reaches the re-frozen handoff boundary, the unchanged normal scheduler takes ownership, and at least two clean scheduler opportunities are observed may a reviewed market-session Phase B window create a fresh pause-created gap. Keep purge/`PURGED`, scheduler-evidence activation, remote backup/restore, and other Worker/Cron mutations separately gated.

## 9. Latest acceptance evidence

| Task | Evidence |
|---|---|
| L1-006 fixture | focused command 21; full 468; compileall success; diff clean |
| N1-006 evaluator | focused 7; full 475; compileall success; diff clean |
| N1-006 benchmark path | focused command 15; full 482; compileall success; diff clean |
| N1-006 population path | focused command 15; full 488; compileall success; diff clean |
| N1-006 labeling path | focused command 15; full 494; compileall success; diff clean |
| N1-006 real-data benchmark | 645/645 reviewed; 51 matched; 594 unrelated; 0 unresolved; 4/4 discovered; recall 1.0000; misattribution 0; focused 19; full 503; compileall success; diff clean |
| X0-006 | operator/external review accepted for policy-level fixture path; F1-F4 deferred to PX0-001..004 |
| W1-005 | local multi-symbol scheduler accepted; 106 instruments preserved; normal/shortened Tier A max age 3m; close+30m outstanding 1Min=0; full TypeScript suite 124; focused 33; typecheck and Wrangler dry-run passed |
| W1-001 live Canary | confirmation/closeout Accepted; three additional distinct eligible opportunities completed 3/3 News jobs at `:58` offset; max external 2/40 and D1 21/40; control before/during/after passed; final version safely restored to Shadow with News disabled |
| W1-007 | local diagnostic + Web review Accepted; control path remained available through the W1-001 closeout with no recurring 7403; historical root cause remains unknown |
| L1-003 / SMOKE-007 Phase A | authorized real-D1 one-row export; two reads identical; 581 bytes; SHA-256 `de380ae35c1ab50f5e0364585e7f3224512085dc3bcd4abff8e37631938bed56`; custody quality accepted; checkpoints unchanged; final Shadow/News disabled; Phase B pending |
| L1-003 bounded historical recovery planner/runner | locally Accepted; explicit one-instrument, one-next-chunk planner and preflight-drift-checked runner; COMPLETE/no-gap identity-checked checkpoint required; canonical UTC/calendar revision, session-bounded range, feed and max-bars constraints enforced; 8 focused tests, TypeScript typecheck and diff check passed; no Worker/Cron/remote mutation |
| L1-003 NVDA recovery Stage 1 | read-only preflight complete at `2026-09-16T08:00:24.138Z`; Shadow/News disabled/control PASS; NVDA `COMPLETE`, no gaps, complete-through `2026-09-02T20:00:00.000Z`, version 6; calendar `alpaca-calendar-v2:da7d32f3`; first 100-bar chunk frozen; remote mutation not authorized |
| L1-003 NVDA one-shot invocation | locally Accepted; fixed POST route hidden behind default-false feature gate, constant-time Bearer-secret verification, exact recovery/job headers, frozen runtime/checkpoint/calendar validation, D1 lease, one-chunk stop and replay closure; focused 20 passed, full suite/typecheck/typegen check/live-canary dry-run/diff check passed; no deploy or remote write |
| L1-003 NVDA first remote recovery chunk | Accepted at `2026-09-16T09:30:33.980Z`; job `historical-market-recovery:ef94f87d37bf2746`; 1 page, 100 inserted, 0 matched/conflict/rejected/missing; one SUCCEEDED attempt, 100 INSERTED receipts and 100 canonical bars independently verified; checkpoint COMPLETE/no gaps/version 7/through `2026-09-03T15:10:00.000Z`; external 1/40, D1 15/40; final Shadow/News disabled/gate false/endpoint 404/control secret deleted |
| L1-003 NVDA continuation mechanism | locally Accepted; `/control/historical-recovery/nvda/next-chunk` requires exact recovery/job/version/complete-through headers, replans from current persisted truth, uses D1 lease/CAS and stops after one chunk; version-7 next job `historical-market-recovery:aac843c098bae3a3`, range `[2026-09-03T15:10:00Z, 16:50:00Z)`, expected 100 bars/version 8; focused 22 and full 192 passed, typecheck/typegen check/live-canary dry-run/diff check passed; deploy and remote execution not authorized |
| L1-003 NVDA version-7 continuation window | Accepted at `2026-09-16T19:16:40.531Z`; job `historical-market-recovery:aac843c098bae3a3`; 1 page, 100 inserted, 0 matched/conflict/rejected/missing; exactly one SUCCEEDED attempt, 100 INSERTED receipts and 100 canonical bars independently verified; checkpoint COMPLETE/no gaps/version 8/through `2026-09-03T16:50:00.000Z`; external 1/40, D1 15/40; final Shadow/News disabled/gate false/endpoint 404/control secret deleted |
| L1-003 NVDA version-8 continuation window | Accepted at `2026-09-17T07:19:52.552Z`; job `historical-market-recovery:75cf6e5907896220`; range `[2026-09-03T16:50:00Z, 18:30:00Z)`; 1 page, 100 inserted, 0 matched/conflict/rejected/missing; checkpoint COMPLETE/no gaps/version 9/through `2026-09-03T18:30:00.000Z`; external 1/40, D1 15/40; gate returned false and control secret deleted |
| L1-003 NVDA version-9 continuation window | Accepted at `2026-09-17T14:43:35.721Z`; job `historical-market-recovery:74025ff8e1e78c42`; range `[2026-09-03T18:30:00Z, 20:00:00Z)`; 1 page, 90 inserted, 0 matched/conflict/rejected/missing; checkpoint COMPLETE/no gaps/version 10/through `2026-09-03T20:00:00.000Z`; external 1/40, D1 15/40; final Shadow/News disabled/gate false/endpoint 404/control secret deleted |
| L1-003 Phase B start-readiness WBS/CP | PB-01 was repeated at `2026-09-17T19:49:05Z`; the handoff target remains the September 16 close. PB-04 is in progress: September 4 accepted through four independent 100/100/100/90-bar calls, 4/4 SUCCEEDED, 390 INSERTED, zero conflict/rejected/missing, checkpoint version 14 / `2026-09-04T20:00:00.000Z`; final Shadow/News disabled/gate false/endpoint 404/control secret deleted. September 8 is the next separately gated one-session campaign |
| L1-003 PB-05 handoff-boundary gate | Read-only assessment at `2026-09-18T01:44:18Z` found Worker Shadow / News disabled / control PASS and the selected checkpoint COMPLETE, gap-free and blocker-free, but still version 14 / September 4 close. Eight historical attempts and 780 INSERTED receipts have zero conflict/rejected evidence; nevertheless `[September 4 close, September 16 close)` contains zero NVDA Regular bars, leaving seven sessions / 2,730 bars. PB-05 is blocked on PB-04; next is a freshly preflighted, separately authorized September 8 campaign |
| L1-003 PB-04 September 8 campaign | Accepted 4/4 independent chunks for 100/100/100/90 bars; 390 INSERTED, zero conflict/rejected/missing, exactly four SUCCEEDED attempts, checkpoint COMPLETE/no gaps/no blocker/version 18/through `2026-09-08T20:00:00.000Z`; each invocation used 1 external and 15 D1 operations. Final Worker Shadow / News disabled / gate false / endpoint 404 / control secret deleted. September 9 is the next separately gated one-session campaign |
| Packet A | locally Accepted; focused TypeScript 23; full TypeScript 130; full Python 503; typecheck, compileall, Wrangler dry-run, and diff check passed; same minute opportunity is canonical across `00/15/30/59` seconds and repeat execution does not re-call News or advance its checkpoint |
| Packet B | locally Accepted; focused TypeScript 4; full TypeScript 134; full Python 503; typecheck, compileall, Wrangler dry-run, and diff check passed; shared budget, CAS conflict, retry canonicalization, and D1 ceiling regressions covered |
| Packet C | locally Accepted; focused TypeScript 17; full TypeScript 141; full Python 503; typecheck, compileall, Wrangler dry-run, and diff check passed; provider/control-path failures classified and fail closed without guessing `7403` root cause |
| Packet D | locally Accepted; focused TypeScript 16; full TypeScript 157; full Python 503; typecheck, compileall, Wrangler dry-run, and diff check passed; durable bounded run/job evidence, restart recovery, stale parent/job supersession, lease ambiguity, feature-gated Worker integration, shared D1 budget accounting, and Shadow no-mutation covered |
| Packet E | locally Accepted; focused Python 24; full Python 527; compileall and diff check passed; bounded CLI-only retention/deletion/replay, registered Alpaca News metadata replay, opaque temporary refs, and no arbitrary HTTP/unbounded replay covered |
| Packet F | locally Accepted; focused backup/restore 5 then focused backup/restore+drill 10; full Python 537; compileall and diff check passed; clean restore, hash verification, SQLite integrity/migration checks, and Parquet/manifest provenance validation covered |
| R0-001 | locally Accepted; reviewed scheduler registration plan; no live trigger mutation |
| R0-002 | Accepted; `0008` remote schema applied and verified; scheduler-evidence activation still gated |
| R0-003 | locally Accepted through Packet E |
| R0-004 | locally Accepted through Packet F |
| R0-005 | reviewed orchestration evidence complete; activation still change-window gated |
| R0-006 | locally Accepted; retention contract focused 6; TypeScript 167; Python 537 |
| R0-007 | locally Accepted fixture export/custody; focused 22; Python 551; compileall passed |
| R0-008 | locally Accepted through `PURGE_ELIGIBLE`; focused 13/13; TypeScript 174/174; Python 551/551; typecheck/compileall passed |
| R0-009 | locally Accepted; targeted provider-digest fixture 5/5 after false-positive repair; lease contention 6/6 after deterministic barrier repair; full TypeScript 178/178; typecheck passed; full Python 555/555; compileall passed |
| CS0-001..003 / MR0-001..003 | locally Accepted; focused 38; full Python 696; compileall passed; diff check passed; TNON/CHPT and required confounder fixtures covered |

Earlier accepted task evidence remains preserved in task-specific handoffs.

## 10. Unresolved items

- W1-003 resolved the 106-point checkpoint-read blocker with a bounded bulk read
  and shared fail-closed D1 accounting.
- W1-005 is Accepted for the local/non-live boundary. Compatible Market work is
  now batched by provider/cadence/session/variant/mode/range/revisions with
  per-symbol checkpoint CAS truth retained. The deterministic full-v0.1 normal
  and shortened fixtures measured 3-minute maximum Tier A age and zero 1Min
  jobs outstanding at close+30 minutes with two groups per tick. See
  `W1-005_MULTI_SYMBOL_TIER_SCHEDULER_LOCAL_ACCEPTANCE_2026-09-11.md`. Remote D1,
  deployment, Cron, Worker mode, and live profile activation remain unauthorized.
- W1-001 confirmation/closeout is Accepted after three additional live eligible
  opportunities and control checks before/during/after. The Worker is safely
  rolled back to `shadow` with News disabled. Continuous Live, `full-v0.1`,
  Cron changes, and any later activation remain separately authorized.
- Packet D is Accepted and remote migration `0008` is applied/verified on live-canary. Scheduler-evidence activation, Worker deployment/Cron mutation, and any live confirmation remain separately gated.
- Packet E / PX0-003 is locally Accepted. Remote D1 export/purge and unrestricted provider execution remain outside that acceptance boundary.
- Packet F / PX0-004 is locally Accepted. Remote D1 backup/restore and live recovery operations remain outside that acceptance boundary.
- `UWBS-023..026` are formally incorporated as `R0-006..009` and locally accepted; remote D1 drain/purge remains unauthorized.
- `UWBS-016` is incorporated as `R0-005`; reviewed Worker News activation remains separately gated after rollback.
- `PX0-001` is incorporated as `R0-001` and accepted locally; live scheduler/Cron mutation remains separately gated.
- L1-003 / SMOKE-007 PB-04 is in progress. The September 4 one-session campaign is remotely accepted and the clean checkpoint is version 14 at that close. Repeat the read-only entry check, freeze September 8 identities, and separately authorize only that next one-session campaign; no cross-session execution is automatic. After recovery reaches the September 16 target, hand off to the unchanged normal scheduler and observe at least two clean opportunities. Only after those gates may a separately authorized market-session Phase B window create and catch up a fresh pause-created gap.
- A0-001 provisional validation.
- A0-002 AI/Semiconductor proxy.
- short/borrow provider for H4 validation.
- whether A0-002 becomes mandatory for v0.1 release acceptance.
- FastAPI/Starlette/AnyIO test-client deprecation warnings remain dependency-maintenance work.

## 11. Progress-update rule

When a task changes state, update this integrated tracker in the same bounded work cycle and preserve detailed acceptance evidence in the corresponding handoff/runbook.

## Maintenance — Python warning/resource lifecycle

- SQLite connection lifecycle remediation: **Accepted locally**.
- Strict warning policy remains enabled; SQLite warnings are not suppressed.
- Acceptance evidence: `595 passed in 20.93s`; with `PYTHONTRACEMALLOC=10`, `595 passed in 43.12s`.
- See `PYTEST_SQLITE_RESOURCE_WARNING_INVESTIGATION_2026-09-14.md`.
