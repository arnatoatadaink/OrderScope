# OrderScope — Local Corporate Intelligence WBS Revision: News Worker Acquisition

Status: **Active WBS revision / no live activation authorized**
Date: 2026-09-10
Base WBS: `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Source backlog: `docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`
Source design: `docs/work-management/local-corporate-intelligence/NEWS_WORKER_ACQUISITION_DESIGN_2026-09-10.md`
Source acceptance: `N1-006 — Evaluate news recall` Accepted

## 1. Revision decision

This revision formally incorporates:

```text
UWBS-016 -> W1-001
```

The base WBS remains historical execution context. This revision extends it without rewriting accepted task meanings.

`W1-001` is a Worker/Schedule orchestration task around the already accepted News metadata boundary. It does not redefine `N0-002`, `N1-*`, Local Fact semantics, or historical N1-006 evaluation behavior.

This revision does **not** authorize live Worker mutation, live scheduler registration, remote D1 work, or a change from Worker Shadow mode.

## 2. New work package — W1 Worker News acquisition / operations integration

| ID | Task | Completion condition | Dependency | Current state |
|---|---|---|---|---|
| W1-001 | Implement Worker/Schedule News metadata acquisition job | AMD/NVDA metadata-only News acquisition is implemented behind a reviewed Worker/Schedule job with bounded session-aware polling, checkpoint/resume, idempotency, page/call budgets, inspectable retryable failure state, cross-symbol article deduplication, secret non-exposure, dry-run/fixture acceptance, and a separately gated activation step | N0-002, I0-003, I0-004, X0-002, N1-006 Accepted; coordinate with PX0-001/UWBS-001 and SMOKE-006; SMOKE-007 only for separately approved historical catch-up | Ready for implementation in non-live/fixture boundary |

## 3. Cadence decision

The initial AMD/NVDA Canary cadence is:

```text
5 minutes during the configured U.S. observation day
```

This is an **initial Canary configuration**, not a permanent system constant.

N1-006 measured result used for this decision:

```text
reference events               = 4
references discovered          = 4
recall                         = 1.0000
misattributions                = 0
unresolved                     = 0
minimum signed provider lag    = -357011 s
maximum signed provider lag    = 14636 s
median signed provider lag     = -44826.5 s
```

Interpretation boundary:

- these signed lags compare Alpaca provider publication timestamps against frozen SEC/IR reference availability;
- they do **not** measure Worker polling/retrieval delay;
- therefore N1-006 provides no evidence that a cadence tighter than 5 minutes is required;
- it also does not prove that 10- or 15-minute polling is equivalent operationally;
- Canary runtime must measure provider-publication-to-Worker-acceptance delay before any cadence relaxation.

## 4. Required W1-001 behavior

### 4.1 Canary scope

Only:

```text
AMD
NVDA
```

Full-Universe expansion is outside W1-001 initial acceptance.

### 4.2 Durable payload

Metadata only. Preserve at minimum:

- provider article ID;
- query-symbol membership;
- headline;
- publisher;
- canonical/source URL;
- provider publication/update timestamp when available;
- provider symbol tags;
- retrieved/available/accepted timestamps;
- content identity/hash needed for duplicate/update classification;
- checkpoint/run status.

No News body may cross the baseline durable Worker metadata boundary.

### 4.3 Checkpoint and replay

Reuse I0-003 semantics for bounded provider/source checkpoints. Every run must expose enough state to distinguish:

```text
not selected
selected/in progress
partial
retryable failure
complete
```

A Cron invocation must not be counted as successful News work merely because the Worker invocation itself returned successfully.

Scheduled windows must use bounded overlap behind the last accepted boundary to tolerate delayed publication, a missed invocation, or a transient failure. The overlap duration must be explicit and bounded in implementation, not an unbounded historical scan.

### 4.4 Idempotency

Reuse I0-004 semantics:

```text
new
same/duplicate
updated/revision
conflict
```

The same provider article returned from AMD and NVDA queries is one article identity. Query-symbol membership remains separately preserved.

### 4.5 Failure handling

Provider failures must:

- preserve the last completed checkpoint;
- produce a sanitized error category;
- preserve retryability;
- not falsely advance a completed window;
- permit bounded next-run recovery;
- never expose credential/header values.

Align controlled provider-failure behavior with `SMOKE-006` rather than defining a parallel failure model.

### 4.6 Request/page budget

Implementation must impose explicit per-run/per-symbol bounds. A page-token loop or unusually large response set must terminate in partial/error state rather than unbounded polling.

Planning estimate for two symbols at one page each:

```text
2 requests/poll * 12 polls/hour = 24 requests/hour
```

A ~16-hour observation day would therefore be ~384 requests/day before retries or extra pagination. This is a planning estimate only; current Alpaca/Cloudflare limits must be rechecked before live activation.

## 5. Runtime measurements required from Canary

W1-001 must make these measurable before cadence can be relaxed:

1. `provider_published_at -> worker_retrieved_at` delay;
2. `provider_published_at -> accepted_at` delay;
3. scheduled-run delay/jitter;
4. missed-poll recovery delay;
5. pagination/page count per symbol per run;
6. duplicate/update counts;
7. retryable failure and recovery counts;
8. request count/call budget consumption.

Do not reuse N1-006 retrospective signed lag as a substitute for these runtime measurements.

## 6. Fixture / non-live acceptance matrix

Before any live activation review, at minimum prove:

| Case | Expected evidence |
|---|---|
| AMD one-page success | one completed bounded job, metadata only |
| NVDA multi-page success | bounded pagination completes |
| same article across AMD/NVDA | one article identity, both query memberships |
| article update | revision/update semantics preserved |
| 429/5xx | retryable failure, checkpoint not falsely advanced |
| looping/invalid page token | bounded partial/error termination |
| missed scheduled window | bounded overlap recovery without duplicate corruption |
| max-page budget hit | inspectable partial state |
| secret scan | no API credentials/header values persisted/logged |
| body-bearing provider response | body excluded from durable Worker output |
| dry-run | intended AMD/NVDA jobs/windows shown without network mutation |

## 7. Acceptance stages

`W1-001` is intentionally split by gate even though it has one final WBS ID.

```text
Stage A — non-live implementation
  -> orchestration/config/storage/checkpoint code
  -> fixture + dry-run acceptance
  -> no live Worker mutation

Stage B — reviewed Canary activation
  -> recheck provider/platform limits and terms
  -> explicit Worker change window
  -> AMD/NVDA only
  -> Worker remains within approved operating mode

Stage C — Canary evidence
  -> collect runtime retrieval/acceptance lag and reliability evidence
  -> decide retain 5 min / relax to 10 or 15 / tighten only if evidence requires
  -> separate approval before Universe expansion
```

Stage A may proceed now. Stages B/C require their respective external/runtime gates.

## 8. Explicit non-goals

W1-001 does not:

- activate the Worker merely by being incorporated into the WBS;
- change Worker Shadow status;
- register a production Cron without review;
- authorize remote D1 export or catch-up;
- expand News acquisition beyond AMD/NVDA Canary;
- store News bodies;
- select or purchase another News provider;
- redefine News Fact extraction or N1-006 benchmark semantics;
- declare 5 minutes permanently optimal.

## 9. Traceability / backlog disposition

Formal mapping:

| Provisional ID | Final ID | Disposition | Reason |
|---|---|---|---|
| UWBS-016 | W1-001 | Incorporated | N1-006 real benchmark is Accepted; production orchestration boundary and initial cadence are sufficiently specified for non-live implementation |

`UWBS-001/PX0-001` remains separately unincorporated operations work. W1-001 may build a concrete reviewed News job plan, but actual scheduler registration must still respect that operations gate.

## 10. Next execution step

Proceed with **W1-001 Stage A only**:

```text
inspect existing Worker schedule/acquisition architecture
-> freeze News job config shape and bounded overlap/page budgets
-> implement fixture/dry-run orchestration for AMD/NVDA
-> reuse accepted checkpoint/idempotency contracts
-> add runtime timing fields needed for later Canary measurement
-> run focused/full test acceptance
-> produce W1-001 Stage A handoff/result
```

Do not perform live activation as part of Stage A.
