# OrderScope — L1-003 PB-03 Session Campaign Local Acceptance

Status: **ACCEPTED LOCALLY — PB-04 remote execution not authorized**
Date: 2026-09-18 JST
Environment target: `live-canary`
Parent: `L1-003_PHASE_B_START_READINESS_WBS_CP_2026-09-18.md`

## 1. Outcome and authority boundary

PB-03's operator-side historical-recovery campaign is implemented and accepted
locally. It preserves the existing one-chunk Worker mutation boundary and does
not add a Worker loop, Cron path, direct D1 write, retention override, or wider
recovery endpoint.

This acceptance authorizes no deployment, feature-gate or secret mutation,
provider request, D1 write, historical campaign, scheduler activation, or
Phase B action. PB-04 still requires a fresh moving-horizon PB-01 preflight and
a separately reviewed change window.

## 2. Accepted implementation

`src/historical-recovery-campaign.ts` provides three operator-side boundaries:

- `freezeHistoricalRecoveryCampaign` freezes one authoritative 390-bar Regular
  session, initial recovery/checkpoint/calendar identity, and exactly four
  deterministic 100/100/100/90-bar job identities;
- `runHistoricalRecoveryCampaign` re-reads persisted checkpoint truth before
  every invocation and after every accepted result, independently inspects the
  successful attempt/receipt/canonical-bar evidence, persists an allow-listed
  record, and stops on the first mismatch;
- `createHistoricalRecoveryHttpInvoker` permits only an HTTPS POST to the
  existing `/control/historical-recovery/nvda/next-chunk` boundary with the
  bearer token and four frozen identity headers. It sends no request body.

The campaign keeps the reviewed immutable maxima:

```text
jobs / Worker invocations       4
session                         1 Regular session
eligible bars                   390 (100 + 100 + 100 + 90)
pages                           <= 10 per invocation
external subrequests            <= 40 per invocation
D1 operations                   <= 40 per invocation
automatic retry                 none
cross-session continuation      none
```

Each call receives its own Worker `InvocationBudget`. Aggregate campaign
counts are evidence only and cannot weaken a per-invocation ceiling.

## 3. Fail-closed and replay behavior

The local acceptance proves:

- deterministic four-chunk planning reaches exactly the selected session close;
- checkpoint state must remain `COMPLETE`, gap-free and blocker-free;
- identity, boundary and version must equal a frozen boundary before every call;
- response outcome, range, exact accepted count, zero conflict/rejected/missing,
  checkpoint version increment, stopped-after-one-chunk marker and budget all
  match before another call is possible;
- independent persisted evidence contains exactly one successful attempt and
  exact receipt/canonical-bar counts;
- a mismatch on chunk N records no acceptance for that chunk and invokes no
  chunk N+1;
- restart at an already accepted frozen checkpoint resumes only with the next
  frozen chunk;
- replay at the frozen session close returns complete without a Worker call;
- a non-boundary checkpoint and a plan that would leave the selected session
  fail closed.

Evidence records intentionally allow-list campaign/recovery/calendar/session,
ordinal/job/range/count, before/after checkpoint, sanitized result counts,
persisted acceptance counts and budget. Control tokens, provider credentials,
raw responses and arbitrary diagnostics are not persisted.

## 4. Local verification

```text
focused PB-03 TypeScript tests       7 passed
full TypeScript suite                199 passed
TypeScript typecheck                 passed
Wrangler                             4.127.1
Wrangler generated-type check        passed
live-canary deploy dry-run            passed
full Python suite                    696 passed
git diff check                       passed
remote writes                        none
```

The live-canary dry run retained Shadow mode, disabled News, and
`HISTORICAL_RECOVERY_ENABLED=false`.

## 5. Next gate

PB-04 is the next critical-path item but is not authorized by this record. Its
entry sequence is:

```text
repeat PB-01 read-only moving-horizon preflight
  -> freeze current calendar / checkpoint / handoff target
  -> freeze one exact session and four deterministic chunk identities
  -> review safe gate/secret restoration and per-chunk evidence queries
  -> obtain separate change-window authorization
  -> only then execute the bounded campaign
```

If the current retention horizon makes the planned handoff stale, repeat the
target calculation rather than jumping a checkpoint or widening retention.
