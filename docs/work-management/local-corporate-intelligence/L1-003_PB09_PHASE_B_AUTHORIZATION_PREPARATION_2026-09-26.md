# L1-003 PB-09 Phase B authorization preparation

Status: **PREPARATION COMPLETE / ACTIVE-SESSION ENTRY FREEZE PENDING / NOT AUTHORIZED**
Date: 2026-09-26 JST
Branch: l1-003-local-market-recovery
Parent: L1-003 / SMOKE-007 real-D1 export change window

## Current resume point

PB-04/PB-05, PB-06/PB-07 and PB-08 catch-up remain accepted. PB-08's NVDA v65 /
Sep25 20:00Z is historical successful coverage, not a Monday pause-entry input.
Do not reopen historical recovery, acknowledgement or stability acceptance merely
because retention or the calendar changes. Phase A export/custody remains accepted.

Read-only evidence is in `L1-003_PB09_READ_ONLY_SNAPSHOT_2026-09-26.json`:
Cloudflare OAuth identity and D1 database `03c85865-1aa3-4b0c-b219-18987cd260a6`
confirmed; control_path_ok=1; all D1 queries changed_db=false. Worker shadow,
IEX, News disabled; both temporary control endpoints HTTP 404; unresolved
canary attempts=0. Current versions/coverage match PB-08 closeout:
NVDA 65 / Sep25 20:00Z, AMD 48 / Sep25 20:00Z, QQQ 16 / Sep25 20:00Z,
SPY 47 / Sep25 18:28Z, BTCUSD 56 / Sep25 19:07Z; all COMPLETE with no missing,
blocker or retry gate. Worker version `844882b8-2525-48ab-a1a8-ccd7707b93af`.

Authoritative Alpaca calendar revision `alpaca-calendar-v2:9b6adc26` identifies
the next REGULAR session:

| Boundary | UTC | JST |
|---|---|---|
| Session open | Sep28 13:30 | Sep28 22:30 |
| Session close | Sep28 20:00 | Sep29 05:00 |
| Proposed operator review start | Sep28 14:00 | Sep28 23:00 |

The operator review start is a proposal, not a scheduled task or authorization.
Re-fetch the official calendar and deployed state on the actual market day.
Current assessment: WAITING_ACTIVE_MARKET_SESSION, candidate=null.

## Read-only packet generation

```bash
export PATH=/home/y/.nvm/versions/node/v24.21.0/bin:$PATH
bash scripts/l1_003_pb09_readonly_preparation.sh
```

This records identity, D1 target, release/worktree, configuration hash, deployment
identity, health, checkpoint competition, unresolved attempts, control read,
latest digest and authoritative calendar in an ephemeral snapshot directory.
It generates `packet.json`; it never deploys, writes D1, invokes scheduled work
or grants authorization. Existing OAuth or caller-supplied authentication is used;
the old `.env.cloudflare` token is not silently substituted.

It refuses unsafe health, open control gates, unresolved attempts, unhealthy
competition, incomplete D1 reads or ambiguous deployment identity. The local
candidate rule uses the 1-minute finalization lag checked against configuration.

## Entry readiness and required authority separation

At entry the candidate must be equity 1Min REGULAR / stock:iex:raw and COMPLETE,
with missing=[], blocker=null, retry_not_before=null and equal source/coverage.
Its completeThrough must equal the official active-session finalized frontier:

```text
frontier = floor_to_minute(observed_now - configured_finalization_lag)
           clamped to the official session open/close
```

Select by evidence quality from existing canary checkpoints. No stale symbol is
forced into eligibility. The selected coverage must be after the current session
open. The entry packet is valid only for that observed session and exact current
state; missing, version, coverage, competing state or configuration drift requires
a fresh packet.

If shadow mode has left the candidates behind the current frontier, record
CURRENT_CHECKPOINT_REQUIRED. A separately approved bounded normal-scheduler
entry-acquisition window is needed before requesting the pause/resume authority.
That window advances only newly required current-session work; it does not rerun
accepted PB-06/PB-07 or the Sep25 campaign. Proposed ceiling: 16 ordinary scheduler
opportunities, unchanged universe/cron/priority/budgets, then shadow. Its exact
entry and frontier must be frozen from that day's read-only snapshot.

This preparation does not authorize that entry-acquisition window or Phase B.
Do not combine the two authorities implicitly. Phase B cannot be executed using
this closed-market packet.

## Reviewed Phase B operational envelope

Once a genuinely current candidate exists and is frozen, fill the separate
authorization template linked below. The proposed bounded Phase B window is:

1. Verify the reviewed clean release, deployment/config hashes, official active
   session, five checkpoint identities, zero unfinished canary attempts and
   control_path_ok=1. Record the latest clean live-following evidence if an entry
   acquisition window was needed.
2. Use the already accepted mode transition mechanism: temporary live-canary
   configuration / checked-in shadow deployment. Cron remains every minute;
   shadow explicitly pauses acquisition. No new control route, token or policy.
3. Define pauseStart only after shadow is effective and health confirms it.
   Read checkpoint_before_pause and require it equals the finalized frontier at
   this boundary. Any pre-existing lag makes the proposed trial inconclusive.
4. Target three minutes of pause; hard maximum five minutes. Keep the entire
   interval inside the same official REGULAR session. Record UTC/JST timestamps
   and deployment receipts. Use a short poll/deadline, not an unobserved long wait.
5. During pause, issue the frozen one-row historical repeat-read below; verify
   immutable custody identity and control_path_ok. Do not write source/control
   state or create a new custody generation merely to repeat accepted Phase A.
6. Read checkpoint_before_resume. Coverage key, version, coverage and source
   frontier must still equal checkpoint_before_pause; state must remain clean.
   Derive the non-empty finalized gap with `freezePauseGap` in the local packet
   helper. It refuses any pre-existing gap, drift, closed-session crossing,
   non-canonical timestamps or pause longer than five minutes.
7. Resume the unchanged normal scheduler temporarily; maximum 16 ordinary
   opportunities. No Sep25 absence evidence is enabled. Every observed market
   summary and target attempt must be clean and within shared 40-external /
   40-D1 per-invocation ceilings; existing 2 jobs/tick, 100 bars/job, 10 pages/job.
8. Accept only when successfully accepted target records explain coverage of
   every minute of the frozen fresh gap, with overlap separated from fresh work.
   An open-session checkpoint may progress beyond the minimum gap frontier only
   when its recorded normal job ranges and records explain that progression.
9. Restore checked-in shadow immediately after acceptance or any stop. Verify
   IEX / News disabled, both temporary endpoints 404, absence gates false/omitted,
   no temporary configuration/token and zero unfinished attempts. Record final
   version, ranges, diagnostics, source counts and control-path result.

The local packet/gap helper is an evidence generator, not a remote execution
driver. No PB-10 execution script is activated by this preparation. Before a
Phase B approval request, the operator must attach the concrete guarded execution
procedure/script and its local acceptance to the fresh market-session packet.

## Frozen export/custody repeat-read

Accepted artifact remains locally present: one row, 581 bytes, SHA-256
`de380ae35c1ab50f5e0364585e7f3224512085dc3bcd4abff8e37631938bed56`.
Accepted export manifest:
`d1-export-db1b04ee1e3edd5f96a0c953f7f99f7ebb9876544fa8099ec2dc660127ac9b41`.
Custody generation:
`d1-custody-f25ccf63c856392778401be630ef36a2ce91610d1f696a655e9cd2b1a5687b0d`.

Frozen source: normalized_bar only, `[2026-09-01T16:03:00.000Z,
2026-09-01T16:04:00.000Z)`, ordered by bar_start_utc, identity_key, LIMIT 2 to
detect a row-count increase. Millisecond-canonical SQL boundaries are mandatory.

Inside an authorized pause only:

```bash
bash scripts/l1_003_pb09_paused_export_readonly.sh /tmp/pb10-paused-export
```

Two source reads are byte-canonicalized and compared to existing accepted
custody. More than one row, any source byte drift or changed_db=true stops the
trial. No purge, schema change, checkpoint restoration or custody replacement.
The helper was tested locally against accepted bytes and mutation/drift fixtures;
the remote export repeat-read was not executed in this preparation.

## Verification and remaining gate

Local packet tests pass: closed-session deferral, current-frontier selection,
stale/partial/unresolved/live-baseline rejection, exact pause-created gap,
version/pre-existing-gap/long-pause/empty-gap/timestamp/session-boundary rejection.
Receipt fixtures pass: inherited-byte match, D1 mutation refusal and byte drift
refusal. Shell syntax and diff checks pass. Fresh remote preparation is read-only.

PB-09 preparation is complete. The remaining gate is fresh active-session entry
evidence plus a concrete locally accepted execution packet, followed by explicit
authorization. PB-10 was not performed. No scheduler or reminder was created.
