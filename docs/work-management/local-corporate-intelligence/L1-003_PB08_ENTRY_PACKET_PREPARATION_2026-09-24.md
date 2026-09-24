# OrderScope — L1-003 PB-08 Phase B Entry-Packet Preparation

Status: **READ-ONLY PREPARATION — Phase B not authorized**
Date: 2026-09-24 JST

## PB-07 closeout

PB-07 is ACCEPTED remotely.

```text
final checkpoint        v61 / 2026-09-23T18:28:00.000Z
canonical bars          199
clean NVDA attempts     2
bad NVDA attempts       0
clean live digests      2
nonclean summaries      0
safe baseline           Shadow / News disabled / IEX
```

## PB-08 objective

PB-08 freezes the complete Phase B entry packet before any pause/resume
experiment.

Required packet fields:

```text
checkpoint_before_pause
git/deployment identity
wrangler/config identity
Universe profile/revision
calendar/session identity
retention / overlap / finalization lag
pause duration
expected exact fresh gap
expected resume request
expected checkpoint transition
budget bounds
rollback path
stop criteria
```

## Important readiness gate

PB-07 proves stable normal following, but its final checkpoint is not
automatically a valid pause entry.

Phase B READY requires the selected coverage to be current enough that a short
pause creates only a fresh bounded gap. Therefore PB-08 must first establish
whether NVDA has reached the applicable current Regular-session frontier.

Do not manufacture this condition by:
- widening retention;
- moving a checkpoint manually;
- changing Universe/fairness;
- changing Cron;
- using the historical-recovery route.

If catch-up is required, it must occur through the accepted normal scheduler
under a separately bounded window before the entry packet is frozen.

## Candidate pause shape

After current-frontier readiness is proven, the initial candidate is:

```text
pause duration      2 Cron intervals
Cron                1 minute
1Min overlap        1 minute
finalization lag    1 minute
```

This is only a planning candidate. PB-08 does not freeze the two-minute pause
until the actual authoritative current checkpoint and session boundary are
captured.

The desired Phase B behavior is:

```text
normal live and current
  -> freeze checkpoint_before_pause
  -> pause acquisition briefly
  -> checkpoint must not falsely advance
  -> fresh bounded gap appears only from elapsed eligible market minutes
  -> resume unchanged normal scheduler
  -> exact gap is caught up
  -> no older/unrelated gap is introduced
  -> safe Shadow baseline restored
```

## Read-only preflight

Run:

```bash
git pull --ff-only
bash scripts/l1_003_pb08_entry_packet_preflight.sh
```

The output freezes:
- current UTC;
- Git commit;
- `wrangler.jsonc` SHA-256;
- deployed Shadow/News-disabled/IEX identity;
- canary Universe profile/revision/symbols;
- exact NVDA checkpoint and unresolved state;
- latest scheduler evidence;
- current competing canary checkpoint frontier.

## Decision after preflight

If NVDA is not current enough for a fresh-gap experiment:
- PB-08 remains open;
- prepare a bounded normal-scheduler catch-up window;
- do not authorize pause/resume.

If NVDA is current enough:
- freeze the authoritative session/calendar boundary;
- choose the exact pause interval;
- calculate the exact expected gap and resume request;
- freeze rollback/stop criteria;
- close PB-08;
- only then proceed to PB-09 authorization.

## Authority boundary

This preparation authorizes no Worker live activation, provider acquisition,
D1 mutation, Cron change, checkpoint movement, pause/resume, PB-09 or PB-10.
