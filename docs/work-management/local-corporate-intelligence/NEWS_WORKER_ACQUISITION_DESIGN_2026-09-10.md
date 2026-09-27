# OrderScope — News Worker Acquisition Design

Status: **Planning design — WBS-unreflected / no live activation authorized**
Date: 2026-09-10
Scope: Cloudflare Worker / Schedule News metadata acquisition
Related WBS: `N0-002`, `I0-003`, `I0-004`, `X0-002`, `N1-006`

## 1. Decision

The production-form News acquisition path should run in the Cloudflare Worker/Schedule layer, parallel to market-price acquisition, while Local remains the heavier analysis and quality layer.

Target shape:

```text
Cloudflare Worker / Schedule
  -> Alpaca News metadata API
  -> normalized metadata + checkpoint/idempotency state
  -> D1 / Worker-side acquisition state
  -> export/import boundary
  -> Local Fact / extraction / recall / timeline analysis
```

This design does **not** authorize a live Worker mutation or scheduler registration. The Worker remains Shadow until a separate reviewed change window/task explicitly activates the job.

## 2. Boundary with existing N0-002

`N0-002 — Implement news metadata adapter` already owns provider normalization:

- bounded symbol/window request;
- cursor/page-token handling;
- provider article ID;
- headline;
- publisher;
- URL;
- timestamps;
- provider symbol tags;
- body excluded from durable metadata.

The missing production concern is **where and how the accepted adapter is invoked on schedule**. This design therefore does not redefine N0-002; it adds Worker/Schedule orchestration around the accepted adapter contract.

## 3. Proposed production acquisition behavior

### 3.1 Provider

Initial provider: Alpaca News using the same Alpaca API credential pair already used for authenticated Market Data access.

Secrets remain Worker secrets and must never be written to D1, logs, Git, exports, or Local API responses.

### 3.2 Scope

Initial Canary scope:

```text
AMD
NVDA
```

Do not expand to the full stock Universe until the Canary proves:

- stable pagination;
- bounded API-call usage;
- duplicate/update handling;
- checkpoint resume;
- acceptable recall against SEC/IR references;
- no retention/body-policy violation.

### 3.3 Payload

Durable Worker-side News acquisition stores metadata only:

- provider article ID;
- query symbol;
- headline;
- publisher;
- canonical/source URL;
- provider `created_at` / updated timestamp when present;
- provider symbols;
- retrieval/availability/acceptance timestamps;
- content identity/hash sufficient for duplicate/update classification;
- source/checkpoint status.

Do not request article body content in the Worker acquisition job for the baseline News metadata path.

### 3.4 Pagination and checkpoint

Use the accepted I0-003 provider/source bounded checkpoint contract:

- provider key;
- source key / symbol scope;
- bounded window;
- page token / cursor;
- partial/error state;
- resume boundary;
- retry-not-before where applicable.

A successful Cron invocation must not mean "News workload succeeded" unless the intended AMD/NVDA News jobs were selected and their bounded checkpoint outcome is inspectable.

### 3.5 Idempotency

Use provider article ID + accepted content identity/hash through I0-004 semantics:

```text
new
same/duplicate
updated/revision
conflict
```

Do not treat cross-symbol appearance of the same provider article as two distinct News articles. Preserve query-symbol membership separately from provider symbol tags.

## 4. Cadence proposal

For the first Canary, use a conservative **5-minute cadence during the U.S. market observation day** rather than every minute.

Reasoning:

- News is materially less latency-sensitive than bar ingestion for this v0.1 Fact pipeline;
- 5-minute polling provides sufficiently fine event timing for headline/metadata monitoring while keeping request volume small;
- it allows bounded catch-up overlap and retry without stressing Alpaca Basic limits or Cloudflare Free usage;
- N1-006 measured recall/lag can later justify a tighter or looser cadence.

The cadence is a **planning default**, not a frozen system constant. Final activation should re-check current Alpaca and Cloudflare limits/terms.

Recommended first-pass schedule:

```text
Pre-market / Regular / After-hours observation window:
  every 5 minutes

Outside the observation window:
  no News poll, or a lower-frequency catch-up job if later justified
```

Exact session boundaries should reuse the existing U.S. market session/cadence configuration rather than hard-code independent News clocks.

## 5. API-call budget model

For 2 Canary symbols at 5-minute cadence, if each symbol usually fits in one page:

```text
2 requests / poll
12 polls / hour
= 24 requests / hour
```

Even across an extended ~16-hour U.S. observation day:

```text
~384 requests/day before retries/pagination
```

This is intentionally far below typical authenticated Alpaca Basic per-minute limits. However the live change window must re-check current provider limits before activation.

Pagination can increase requests during busy News periods, so the Worker must enforce a maximum pages-per-symbol budget and expose partial/error state instead of looping without bound.

## 6. Catch-up overlap

Each scheduled invocation should request a bounded overlap behind the last accepted checkpoint rather than relying only on exact wall-clock adjacency.

Purpose:

- tolerate delayed provider publication;
- tolerate one missed Cron;
- tolerate transient provider failure;
- allow idempotent replay.

The exact overlap duration must be frozen in the Worker implementation task and tested against duplicate/update behavior. It must not create unbounded historical scans.

## 7. Failure behavior

Provider/transport failures must:

- preserve the last completed checkpoint;
- record sanitized error category;
- mark retryability;
- avoid advancing cursor/window completion falsely;
- allow the next scheduled bounded run to retry/catch up;
- never leak credential/header values.

This should align with the existing deferred Worker `SMOKE-006` controlled-provider-failure work rather than invent a parallel failure model.

Historical catch-up after a pause remains related to `SMOKE-007` and must not be implicitly authorized by this design.

## 8. Local boundary

Local does not call or control the Worker directly.

Local consumes accepted/exported acquisition state and performs:

- deterministic headline/metadata Fact extraction;
- temporary body extraction only through the separate accepted body lifecycle when needed;
- contradiction/review;
- retention;
- News recall quality;
- unified timeline and coverage reporting.

The retrospective `quality news-recall-candidates` local CLI remains a benchmark/debug tool, not the intended steady-state production acquisition path.

## 9. Proposed WBS-unreflected task

Provisional ID: `UWBS-016`

Proposed task: **Implement Worker/Schedule News metadata acquisition job**

Completion conditions:

1. reviewed Worker job invokes accepted News metadata adapter for AMD/NVDA only;
2. uses bounded 5-minute/session-aware cadence configuration or an explicitly reviewed replacement;
3. uses I0-003 checkpoint/resume semantics and I0-004 idempotency semantics;
4. metadata-only; no raw News body in baseline Worker acquisition;
5. provider secrets remain secret-boundary only;
6. dry-run/fixture verifies selected jobs and request windows without network mutation;
7. provider failure leaves an inspectable retryable checkpoint and does not fabricate success;
8. duplicate article across AMD/NVDA queries is stored once with query-symbol membership preserved;
9. call/page budget is bounded and observable;
10. activation remains behind a separate Worker change window/review.

Dependencies / related work:

```text
N0-002 Accepted News adapter
I0-003 checkpoint contract
I0-004 idempotency contract
X0-002 coverage/health semantics
N1-006 recall findings for cadence validation
PX0-001 / UWBS-001 scheduler job registration
SMOKE-006 provider failure behavior
SMOKE-007 only if historical Worker catch-up/change window is required
```

## 10. Acceptance fixtures for future implementation

Minimum fixture cases:

1. AMD one-page success;
2. NVDA multi-page success;
3. same provider article returned for both symbols;
4. article update/revision;
5. transient 429/5xx retryable failure;
6. invalid/looping page token;
7. one missed scheduled window followed by bounded overlap recovery;
8. maximum-page budget hit returns partial state;
9. secret scanner confirms no credentials in persisted/logged output;
10. body field/provider body payload cannot cross durable metadata boundary.

## 11. Explicit non-goals

This task does not:

- activate a live Worker job now;
- change Worker from Shadow;
- expand News to the full Universe;
- choose a paid News provider;
- move Local analytical responsibilities into Worker;
- store News bodies permanently;
- authorize remote D1 export/catch-up;
- redefine N0-002/N1 Fact semantics.

## 12. Next gate

Current sequence:

```text
N1-006 real benchmark execution
  -> record actual Alpaca News recall / lag / misattribution
  -> use those measurements to confirm or adjust News polling cadence
  -> incorporate/remap UWBS-016 in the next WBS revision
  -> reviewed Worker change window
  -> Canary activation for AMD/NVDA only
```
