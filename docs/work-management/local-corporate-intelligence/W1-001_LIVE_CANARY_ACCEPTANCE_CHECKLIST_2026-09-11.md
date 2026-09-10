# OrderScope — W1-001 Live Canary Acceptance Checklist

Status: **Prepared — execution not authorized by this document**
Date: 2026-09-11
Task: `W1-001 — Worker/Schedule News metadata acquisition Live Canary`
Companion: `W1-001_LIVE_CANARY_CHANGE_WINDOW_RUNBOOK_2026-09-11.md`

Use this checklist during the reviewed `live-canary` change window. Mark every applicable item with evidence. Any hard-stop item failing means the Canary is not accepted.

## A. Authorization and release identity

- [ ] User explicitly approved the exact live change window.
- [ ] Target environment is `live-canary` only.
- [ ] Release branch and commit SHA are recorded.
- [ ] Release contains accepted W1-002, W1-003, and W1-005 remediation.
- [ ] W1-001 Stage B Final Web Acceptance remains applicable.
- [ ] Local full tests pass on the release SHA.
- [ ] Focused orchestration tests pass.
- [ ] Typecheck passes.
- [ ] Wrangler dry-run/build passes.
- [ ] `git diff --check` passes.

## B. Scope freeze

- [ ] `UNIVERSE_PROFILE=canary-v0.1`.
- [ ] News query symbols exactly `AMD,NVDA`.
- [ ] `NEWS_ACQUISITION_CADENCE_MINUTES=5`.
- [ ] `NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL<=2`.
- [ ] `NEWS_ACQUISITION_MAX_ARTICLES_PER_RUN<=200`.
- [ ] `ACQUISITION_MAX_JOBS_PER_TICK=2` unless separately reviewed.
- [ ] No full-v0.1 activation is included.
- [ ] No News body persistence is included.
- [ ] No unrelated Worker/Cron/provider change is bundled.

## C. D1 preflight

- [ ] `STATE_DB` resolves to the `live-canary` database only.
- [ ] Current remote migration state captured.
- [ ] Pending migrations reviewed before apply.
- [ ] `0007_news_metadata.sql` is the expected News migration if not already applied.
- [ ] No unexpected migration is pending in the same change set.
- [ ] Migration succeeds without modifying unrelated Market schema semantics.
- [ ] Migration evidence captured without credentials or sensitive data.

Failure or unexplained schema drift => **STOP**.

## D. Secret and logging boundary

- [ ] Alpaca credentials already exist as managed secrets.
- [ ] No secret value is pasted into commands, docs, tickets, or chat evidence.
- [ ] No auth header is logged.
- [ ] No credential appears in Worker response/digest.
- [ ] No raw News body/provider response body is persisted.

Any leak => **ROLL BACK / INCIDENT**.

## E. Deployment safety

- [ ] Pre-window Worker deployment/version identifier recorded.
- [ ] Reviewed build deployed only to `live-canary`.
- [ ] Worker startup/health/digest succeeds before News activation.
- [ ] Market Canary behavior remains healthy before News activation.
- [ ] While News is disabled, News provider calls = 0.
- [ ] While News is disabled, News acquisition mutations = 0.

## F. Activation delta

- [ ] Exact activation timestamp recorded.
- [ ] `WORKER_MODE=live` only after preflight succeeds.
- [ ] `NEWS_ACQUISITION_ENABLED=true` only after preflight succeeds.
- [ ] `UNIVERSE_PROFILE` remains `canary-v0.1`.
- [ ] News symbols remain `AMD,NVDA`.
- [ ] Existing Cron trigger is unchanged unless separately approved.

## G. Invocation-budget acceptance

For every reviewed invocation:

- [ ] `marketExternalSubrequests` captured.
- [ ] `newsExternalSubrequests` captured.
- [ ] `totalExternalSubrequests` captured.
- [ ] `marketD1Queries` captured.
- [ ] `newsD1Queries` captured.
- [ ] `totalD1Queries` captured.
- [ ] `totalExternalSubrequests <= 40`.
- [ ] `totalD1Queries <= 40`.
- [ ] Budget exhaustion, if triggered, rejects before the crossing call/statement.

Any actual total above 40 or unbudgeted crossing => **ROLL BACK**.

## H. News correctness

- [ ] `include_content=false` behavior retained.
- [ ] Provider article ID remains durable article identity.
- [ ] AMD/NVDA query memberships remain explicit and independently preserved.
- [ ] Duplicate article across AMD/NVDA persists one article identity with both memberships.
- [ ] Newer provider update follows UPDATED semantics.
- [ ] Conflicting content without valid newer-update basis follows CONFLICT semantics and does not overwrite canonical content.
- [ ] Page-cap with continuation remains PARTIAL/retryable.
- [ ] 429 remains retryable and honors bounded Retry-After behavior.
- [ ] 5xx remains retryable.
- [ ] Invalid/looping token fails closed.
- [ ] Incomplete/omitted symbol coverage cannot falsely advance that symbol's checkpoint.

Any false checkpoint advance => **ROLL BACK**.

## I. Market regression check

- [ ] Existing Canary Market symbols continue progressing.
- [ ] No material increase in Market acquisition failure after News activation.
- [ ] Multi-symbol Market batching remains deterministic.
- [ ] Checkpoint/CAS semantics remain per symbol.
- [ ] No unexpected Tier/Universe expansion occurs.

Material Market regression attributable to News/combined runtime => **disable News first**.

## J. Runtime performance evidence

Capture, where platform observability permits:

- [ ] scheduled_at.
- [ ] run_started_at.
- [ ] run_finished_at.
- [ ] scheduler delay = run_started_at - scheduled_at.
- [ ] invocation duration = run_finished_at - run_started_at.
- [ ] CPU/exceeded-resource event state.
- [ ] News pages/request count.
- [ ] article observation/new/duplicate/update/conflict counts.
- [ ] D1 rows read/written evidence or best available measured projection.

Repeated resource-limit failures => **ROLL BACK**.

## K. News lag evidence

When a real article is observed:

- [ ] provider `published_at` captured.
- [ ] Worker `retrieved_at` captured.
- [ ] `accepted_at` captured.
- [ ] publication -> retrieved lag calculated.
- [ ] publication -> accepted lag calculated.

If no real article appears, mark this section `INCONCLUSIVE`; do not infer production lag from N1-006 retrospective publication timestamps.

## L. Observation-window minimum

- [ ] At least 12 eligible 5-minute News opportunities observed, or a hard stop occurred earlier.
- [ ] Empty-result ticks, if any, remained bounded and checkpoint-safe.
- [ ] Provider retry behavior did not create request amplification beyond the shared envelope.
- [ ] No unexplained mutation occurred.

## M. Rollback verification

If rollback is required:

- [ ] First attempt independent `NEWS_ACQUISITION_ENABLED=false` when Market remains healthy.
- [ ] Subsequent News provider calls = 0.
- [ ] Subsequent News acquisition mutations = 0.
- [ ] Market continues normally after News disable.
- [ ] If needed, `WORKER_MODE=shadow` restored.
- [ ] If needed, previous Worker deployment/version restored.
- [ ] No destructive reverse D1 migration performed ad hoc.
- [ ] Final remote state recorded.

## N. Final acceptance decision

Mark exactly one:

- [ ] `CANARY_ACCEPTED_CONTINUE`
- [ ] `CANARY_ACCEPTED_DISABLE`
- [ ] `ROLLED_BACK`
- [ ] `INCONCLUSIVE`

For `CANARY_ACCEPTED_CONTINUE`, all hard conditions must be true:

```text
scope stayed canary-v0.1 + AMD/NVDA News only
combined external <= 40
combined D1 <= 40
no repeated CPU/resource failure
no false checkpoint advancement
no News body persistence
no secret leakage
Market Canary did not materially regress
rollback path was proven available
```

A successful first Canary does **not** authorize `full-v0.1` live activation.

## O. Post-window review fields

```text
release SHA:
window start/end UTC:
window start/end JST:
remote migration result:
Worker deployment/version before/after:
activation delta:
eligible News opportunities observed:
News runs completed/partial/failed:
external p50/p95/max:
D1 queries p50/p95/max:
CPU/resource-limit observations:
scheduler delay p50/p95/max:
publication->retrieved lag samples:
publication->accepted lag samples:
429 count:
5xx count:
checkpoint anomalies:
Market regressions:
rollback performed:
final state:
reviewer decision:
follow-up task:
```
