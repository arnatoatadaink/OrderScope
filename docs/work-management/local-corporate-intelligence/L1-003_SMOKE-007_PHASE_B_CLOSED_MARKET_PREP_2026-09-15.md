# OrderScope — L1-003 / SMOKE-007 Phase B Closed-Market Preparation

Status: **READY FOR MARKET-OPEN REVIEW — preparation only; no remote mutation authorized**
Date: 2026-09-15 JST
Branch: `docs/mermaid-conventions-v0.1`
Parent runbook: `L1-003_SMOKE-007_REAL_D1_EXPORT_CHANGE_WINDOW_2026-09-14.md`
Execution evidence: `L1-003_SMOKE-007_EXECUTION_REPORT_2026-09-15.md`

## 1. Purpose

Prepare the remaining market-day-gated Phase B acceptance work while the U.S. market is closed.

Phase A is already accepted for the bounded real-D1 export/custody path. Do not repeat Phase A unless its accepted evidence is invalidated by a later review finding.

The remaining acceptance objective is strictly:

```text
choose a previously-current Market checkpoint
  -> record explicit pause boundary
  -> create a fresh bounded gap during an applicable U.S. market session
  -> resume only the reviewed normal Market acquisition path
  -> observe catch-up of that exact gap
  -> verify no false checkpoint advance / budget breach
  -> return immediately to the reviewed Shadow baseline
```

This document does not authorize Worker/Cron mutation, News activation, schema change, remote purge, or the market-open Phase B window itself.

## 2. Evidence already accepted and inherited

Do not re-open these unless contradictory evidence appears:

- bounded real-D1 export/custody from the 2026-09-15 Phase A window;
- deterministic repeat-read identity;
- local custody quality acceptance;
- checkpoint preservation before/after Phase A;
- no remote purge;
- no schema mutation;
- no credential/body leakage;
- control-path PASS before/during/after;
- no recurring `7403`;
- final Worker `shadow` with News disabled.

## 3. Closed-market preparation completed

### 3.1 Candidate-selection rule

The Phase B target must be a **Market** checkpoint that is current enough at window entry to make the pause-created gap distinguishable from pre-existing recovery work.

Reject a candidate before activation when any of the following is true:

- state is already `PARTIAL` because of an older unresolved gap;
- `complete_through` is stale relative to the applicable reviewed session boundary;
- the candidate has unresolved missing/conflict/rejected evidence;
- the provider/session/calendar state cannot identify the active U.S. market session;
- selecting the candidate would require widening Universe/provider/budget/Cron configuration.

BTCUSD must not be used merely because it trades continuously when its checkpoint contains a pre-existing unresolved gap. The 2026-09-15 Phase A attempt established that such a case cannot prove a fresh pause-created catch-up.

### 3.2 Preferred candidate order

At market-open preflight, inspect the existing canary Market checkpoints and select the first candidate satisfying the rule above. Do not freeze a symbol in advance if runtime checkpoint state may change before the window.

Priority is therefore by **evidence quality**, not ticker preference:

1. current `COMPLETE` Market checkpoint in the applicable active session;
2. current checkpoint with no unresolved pre-window gap and an unambiguous `complete_through`;
3. otherwise stop as `INCONCLUSIVE/BLOCKED` rather than using stale pre-existing recovery state.

### 3.3 Pause-created gap rule

The window must record all three boundaries:

```text
checkpoint_before_pause
checkpoint_before_resume
gap = expected session progress during pause - checkpoint_before_resume
```

The gap must be non-empty and attributable to the recorded pause interval. A gap that existed before `checkpoint_before_pause` is not acceptance evidence.

The pause should be only long enough to create a small observable bounded gap. Do not widen it to manufacture more work.

### 3.4 Resume rule

Resume only the reviewed normal Market acquisition path. Do not:

- manually advance checkpoint or `complete_through`;
- issue ad-hoc bar writes;
- enable News;
- change Cron cadence;
- change Universe;
- change provider/page limits;
- change shared external/D1 budgets.

After the exact pause-created gap is caught up, return to the reviewed Shadow baseline immediately.

## 4. UTC boundary canonicalization guard

Phase A discovered an operator-input hazard when ISO UTC timestamps are persisted and compared as text:

```text
2026-09-01T16:04:00Z
2026-09-01T16:04:00.000Z
```

These strings represent the same instant but do not have identical lexical form. For half-open SQL/text comparisons, an uncanonicalized operator boundary can therefore include/exclude an unintended boundary row.

For all L1-003 evidence and future bounded D1 export planning, use one canonical UTC representation before query construction:

```text
YYYY-MM-DDTHH:MM:SS.mmmZ
```

Examples:

```text
accepted: 2026-09-01T16:04:00.000Z
reject/normalize before query: 2026-09-01T16:04:00Z
```

This preparation records the operational guard only. A code-level parser/query-builder hardening change should be tracked separately if the accepted implementation does not already canonicalize boundaries internally. Do not silently alter production query semantics inside the Phase B change window.

## 5. Market-open preflight checklist

Before requesting Phase B activation authorization, capture read-only evidence for:

```text
release commit
Worker version
Worker mode == shadow
News == disabled
Cron unchanged
Universe == canary-v0.1
Cloudflare identity
D1 binding/database identity
SELECT 1 control_path_ok
provider/exchange session/calendar state
candidate Market checkpoint rows
candidate state and complete_through
unresolved partial/missing/conflict/rejected state
shared external/D1 ceilings
```

Run `scripts/l1_003_phase_b_readonly_preflight.sh` during the applicable U.S.
regular session to collect the repository release, Cloudflare/D1 identity,
deployed health, control-path result, candidate checkpoint rows, unresolved
checkpoint evidence, recent digest, and recent Market-acquisition outcomes in
one read-only transcript. Review the returned health/digest configuration and
the session/calendar state separately before choosing a candidate. The script
does not pause, resume, deploy, invoke scheduled work, or write to D1.

Then choose the candidate under §3.1 and record why it is free of a pre-existing catch-up ambiguity.

If no candidate passes, do not activate Phase B. Record `market-day evidence unavailable` and retry at a later reviewed session.

## 6. Phase B acceptance capture

The market-open execution report must capture at minimum:

```text
selected coverage key
session identity
pause start UTC/JST
checkpoint_before_pause
pause end / resume UTC/JST
checkpoint_before_resume
fresh gap start/end
scheduled timestamp(s)
requested range(s)
planned / selected / completed / failed jobs
accepted bars/records
partial/missing/conflict/rejected
checkpoint_after_catch_up
complete_through_before/after
max external/tick
max D1/tick
withinBudget
control-path before/during/after
false coverage advance observed: yes/no
final Worker mode
final News state
```

Acceptance requires the checkpoint/complete-through movement to be explained by successfully accepted records from the exact fresh pause-created gap. Missing/partial/failure paths must remain fail-closed.

## 7. Stop conditions

Stop without widening scope if:

- no unambiguous current Market checkpoint exists;
- candidate state changes to a pre-existing `PARTIAL`/stale condition before pause;
- session/calendar state is ambiguous;
- `7403`, control-path failure, binding mismatch, or quota/resource failure appears;
- catch-up would require config/code/schema change;
- external/D1 ceiling would be crossed;
- checkpoint advances without corresponding accepted gap records.

Final safe state remains Worker Shadow with News disabled.

## 8. Closed-market disposition

Closed-market preparation is complete when this document is reviewed against the accepted Phase A report and the integrated Progress Tracker.

It does **not** change `L1-003` from:

```text
INCONCLUSIVE — Phase A accepted; market-open Phase B pending
```

The next state change requires fresh market-session evidence from a separately authorized Phase B window.

## 9. 2026-09-16 JST market-session preflight result

The authorized read-only preflight found no current unambiguous Market
checkpoint: the `COMPLETE` candidates were stale and `AMD`/`QQQ` had
pre-existing `PARTIAL` gaps. Phase B was not activated. See
`L1-003_SMOKE-007_PHASE_B_MARKET_SESSION_PREFLIGHT_2026-09-16.md` for the
bounded evidence and disposition.
