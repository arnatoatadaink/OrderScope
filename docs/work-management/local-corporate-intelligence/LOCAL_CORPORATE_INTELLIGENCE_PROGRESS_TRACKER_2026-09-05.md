# OrderScope — Local Corporate Intelligence Progress Tracker

Status: **Active integrated runtime tracker**
Date: 2026-09-11
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
| L1-003 | Blocked | Requires separately approved `SMOKE-007` remote D1 window |
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
quota-specific error. The earlier `7403` is not currently reproducible and is
classified as likely transient or stale OAuth/control-plane state; current
evidence cannot distinguish those recovered causes.

Rollback version `16af6aeb-6818-4a09-be58-10aa7931a2de` remains deployed.
Read-only `/health` verification returned `mode=shadow` and News disabled. No
Worker/config, Cron, activation, or D1 data mutation was performed. See
`W1-007_CLOUDFLARE_API_CONTROL_PATH_DIAGNOSTIC_LOCAL_REPORT_2026-09-11.md`.

Next CP gate: Web review of the W1-007 evidence, then a separately authorized
short monitored W1-001 confirmation/closeout window. The cadence predicate is
already repaired and live-confirmed; it is no longer the active blocker.

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
or a live Canary. The next safe local packet is Packet B shared budget /
idempotency / checkpoint regression. W1-007 Web review and a separate approved
change window remain mandatory before any confirmation/closeout Canary.

## 6. Post-X0 operational follow-ups

| Follow-up | Status | Boundary |
|---|---|---|
| PX0-001 | Not started | Reviewed operational scheduler job registration |
| PX0-002 | Not started | Durable scheduler run/job evidence and stale-lock recovery |
| PX0-003 | Not started | Operator CLI for retention and bounded reprocessing |
| PX0-004 | Not started | Reproducible backup/restore and restore drills |

These remain non-normative tracking IDs pending future WBS incorporation/remap.

## 7. Parallel/deferred lanes

- `N1-006` real 30-day benchmark is Accepted.
- `W1-001` reopen collected 12 successful eligible News opportunities and then safely rolled back after Cloudflare API authorization/control loss; W1-007 has restored the read-only control-path gate locally, pending Web review before another live window.
- `L1-003` remains externally Blocked behind `SMOKE-007` approval.
- `PX0-001..004` remain separate operations/recovery follow-ups.
- `A0-001` remains Provisional and `A0-002` remains separate validation work.
- WBS-unreflected work is tracked in `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`.
- Worker remains Shadow.

## 8. Current restart rule

1. Treat N1-006 as Accepted through the real 645-candidate review, 4/4 recall measurement, and 19 / 503 / compileall / diff evidence.
2. Treat the W1-006 cadence repair as live-evidence-confirmed for non-zero Cron seconds offsets through the 12-opportunity reopen window.
3. Treat W1-007 as locally Accepted through two successful read-only passes; obtain Web review before any separately authorized short W1-001 confirmation/closeout window.
4. Treat Packet A scheduler/cadence regression hardening as locally Accepted through canonical minute-boundary and repeated-opportunity evidence; select Packet B as the next safe local packet.
5. Keep `L1-003/SMOKE-007` and other Worker mutations separately gated.

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
| W1-001 live Canary | reopen collected 12 distinct eligible News opportunities at stable `:30` offset; 13/13 News jobs completed; max external 2/40 and D1 21/40; safely rolled back after Cloudflare API control loss |
| W1-007 | locally Accepted; two read-only passes of whoami, D1 info, SELECT 1, and PRAGMA succeeded; no 7403/quota error; rollback version remains shadow with News disabled |
| Packet A | locally Accepted; focused TypeScript 23; full TypeScript 130; full Python 503; typecheck, compileall, Wrangler dry-run, and diff check passed; same minute opportunity is canonical across `00/15/30/59` seconds and repeat execution does not re-call News or advance its checkpoint |

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
- W1-001 live Canary is safely rolled back and remains gated. The Worker is
  `shadow` with News disabled. The cadence predicate is repaired and confirmed
  by 12 live eligible opportunities. W1-007 restored the read-only Cloudflare
  control path locally; Web evidence review and separate authorization for a
  short monitored confirmation/closeout window are still required.
- Packet A is locally Accepted. Packet B shared budget / idempotency /
  checkpoint regression is the next safe local packet; this state change does
  not authorize a remote Worker or D1 mutation.
- UWBS-016 future WBS incorporation and reviewed Worker News activation.
- PX0-001..004 operations/recovery backlog.
- L1-003 / SMOKE-007 real-D1 approval window.
- A0-001 provisional validation.
- A0-002 AI/Semiconductor proxy.
- short/borrow provider for H4 validation.
- whether A0-002 becomes mandatory for v0.1 release acceptance.
- FastAPI/Starlette/AnyIO test-client deprecation warnings remain dependency-maintenance work.

## 11. Progress-update rule

When a task changes state, update this integrated tracker in the same bounded work cycle and preserve detailed acceptance evidence in the corresponding handoff/runbook.
