# OrderScope — W1-007 Cloudflare API Control-Path Web Acceptance

Status: **Accepted — control path restored**
Date: 2026-09-11 JST
Task: `W1-007 — Diagnose Cloudflare API authorization/control-path failure after successful W1-001 Canary evidence`

## 1. Decision

Web review accepts the Local W1-007 result.

Two consecutive read-only diagnostic passes succeeded against the expected `live-canary` account/database boundary:

```text
wrangler whoami          -> pass
wrangler d1 info         -> pass
remote SELECT 1          -> pass
PRAGMA table_list        -> pass
7403 reproduced          -> no
quota error observed     -> no
D1 mutation              -> no
Worker/config mutation   -> no
```

The earlier Cloudflare API `7403` is therefore treated as a recovered control-plane/authentication incident, with the exact cause unresolved between a transient Cloudflare control-plane failure and stale OAuth/control state.

## 2. Safety boundary

Current safe state remains:

```text
Worker version: 16af6aeb-6818-4a09-be58-10aa7931a2de
WORKER_MODE=shadow
NEWS_ACQUISITION_ENABLED=false
UNIVERSE_PROFILE=canary-v0.1
NEWS_ACQUISITION_CADENCE_MINUTES=5
Cron=* * * * *
```

No deployment, Cron change, News activation, secret mutation, or D1 data mutation was required for W1-007 acceptance.

## 3. Interpretation

W1-007 acceptance clears the previous control-path blocker only.

It does not by itself convert W1-001 to final `Accepted`, because the prior Canary closeout ended in rollback after monitoring control was lost. However, the application-side runtime evidence from the 12-bucket reopen window remains valid:

- W1-006 cadence repair live-confirmed at non-zero seconds offset;
- 12 distinct eligible News opportunities completed;
- no News partial/failure;
- no budget crossing;
- max combined D1 observed 21/40;
- max external observed 2/40;
- one canonical NVDA article and one membership observed;
- duplicate re-observation did not create a second canonical article;
- Market regression not observed;
- News body/secret leakage not observed.

## 4. Next gate

Proceed to a separately authorized **short W1-001 confirmation/closeout window** whose purpose is not to repeat the full one-hour Canary, but to prove that:

1. the read-only Cloudflare control path remains available before activation;
2. a small number of eligible News buckets execute successfully;
3. control-path reads remain available during the active window;
4. News can be disabled and the Worker returned to `shadow` while monitoring remains available;
5. post-rollback verification succeeds.

If those checks pass without a new application/control-path failure, Web review may use the prior 12-bucket evidence plus the short confirmation as the basis for final W1-001 live acceptance.

No `full-v0.1` activation is authorized by this document.
