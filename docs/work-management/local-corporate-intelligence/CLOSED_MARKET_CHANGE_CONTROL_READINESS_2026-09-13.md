# OrderScope — Closed-Market Change-Control Readiness

Status: **Reviewed — execution authorization pending per remote-mutation window**
Date: 2026-09-13 JST
Branch: `docs/mermaid-conventions-v0.1`
Scope: Approval/change-control branches that can be reviewed while U.S. markets are closed

## 1. Purpose

Separate **approval/change-control gating** from **market-day evidence gating** so remote work does not remain blocked merely because the U.S. market is closed.

This review does not itself execute or authorize remote mutation. It moves each branch to a bounded, review-complete state so that only the explicit execution authorization and, where applicable, market-day evidence remain.

## 2. Gate matrix

| Branch | Review status | Can execute while market closed? | Market-day evidence required? | Remote mutation? | Current disposition |
|---|---|---:|---:|---:|---|
| W1-001 short confirmation/closeout Canary | Ready | No for meaningful acceptance | Yes | Yes — Worker activation pair | **READY — market-day + explicit authorization gated** |
| R0-002 migration `0008_scheduler_run_evidence.sql` | Review complete | Yes | No | Yes — additive D1 schema | **READY FOR EXECUTION AUTHORIZATION** |
| L1-003 / SMOKE-007 real D1 export window | Change-control planning ready | Partially | Yes for fresh resume/catch-up acceptance | Yes — pause/resume and remote export workflow | **READY FOR WINDOW AUTHORIZATION; market-day acceptance remains** |
| R0-007 bounded remote D1 export/custody | Local contract accepted | Yes | No for export/custody itself | Remote read/export; local custody writes | **READY FOR BOUNDED REMOTE-EXPORT AUTHORIZATION** |
| R0-008 ACK / bounded purge | Local eligibility accepted | Yes technically | No | Yes — destructive D1 deletion | **NOT FIRST ACTION; keep separately authorized after real custody/ACK evidence** |
| R0-004 remote backup/restore | Local restore drill accepted | Backup may be closed-market; restore is a separate mutation | No unless recovery acceptance adds live checks | Yes for remote restore | **DEFER remote restore; no current incident requires it** |

## 3. R0-002 / migration 0008 review

`0008_scheduler_run_evidence.sql` is additive:

- creates `scheduler_run` with a primary key and bounded status enum;
- creates `scheduler_run_job` with `(run_id, job_id)` primary key and a foreign key to `scheduler_run`;
- creates indexes on run start time and job status/start time;
- uses `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`;
- contains no `DROP`, `ALTER`, `UPDATE`, `DELETE`, or data backfill.

The runtime feature remains separately gated by `SCHEDULER_RUN_EVIDENCE_ENABLED`; when unset/false the Worker uses the disabled evidence store. Therefore schema application and feature activation can remain separate operations.

### Execution boundary

If explicitly authorized, the closed-market migration window should be limited to:

1. confirm `live-canary` target and current pending migration list;
2. record pre-apply `PRAGMA table_list` / migration status;
3. apply only `0008_scheduler_run_evidence.sql` to `live-canary`;
4. verify `scheduler_run` and `scheduler_run_job` exist;
5. verify migration list is empty;
6. leave `SCHEDULER_RUN_EVIDENCE_ENABLED` unset/false;
7. do not deploy Worker, change Cron, enable News, or change Worker mode.

This operation does not require the U.S. market to be open.

## 4. L1-003 / SMOKE-007 review

WBS completion requires a real D1 export change window with pause/export/resume/catch-up semantics. The Critical Path explicitly treats remote D1 work as independently gated and market-day evidence as a separate concern.

The branch can be split into two phases:

### Phase A — closed-market preparation / custody

May be prepared or executed only under a separately approved remote-export window:

- freeze explicit source/table/time window;
- confirm current D1/control-state rows are excluded from historical drain targets;
- produce bounded export and custody manifest;
- verify row count/hash/byte size;
- import/register local immutable custody;
- run local quality checks;
- do **not** infer current acquisition checkpoint from local archive state.

### Phase B — market-day resume/catch-up evidence

Must wait for an applicable live market session if the acceptance condition requires fresh post-resume catch-up/session evidence.

Therefore approval can be prepared while closed, but L1-003 cannot be fully Accepted from closed-market evidence alone.

## 5. R0-007 remote export readiness

The local R0-007 contract is already accepted for deterministic half-open bounded export/custody. A first remote execution should remain intentionally narrow:

- one reviewed historical table/window;
- explicit `[startInclusive, endExclusive)` bounds;
- source environment/database identity recorded;
- deterministic row count/hash/byte size;
- immutable local artifact + custody manifest;
- no purge in the same first window;
- no current checkpoint/cursor/lease/schema rows exported as purge candidates.

This can be performed while markets are closed because it does not require fresh session behavior. It still requires explicit remote-export authorization.

## 6. R0-008 purge readiness

Do not pair the first real export with immediate purge.

Actual `PURGED` remains last in the sequence:

```text
EXPORTED
  -> HASH_VERIFIED
  -> IMPORTED
  -> QUALITY_ACCEPTED
  -> ACKNOWLEDGED
  -> GRACE
  -> PURGE_ELIGIBLE
  -> PURGED
```

Before a remote delete is authorized, real custody evidence must exist and the dry-run must identify an explicit bounded candidate set. Current checkpoint/control truth, unresolved blockers/conflicts, replay requirements, and FK-safe deletion order must remain protected.

Market-open state is not the blocker here; destructive-change authorization and real custody evidence are.

## 7. Recommended closed-market execution order

```text
1. R0-002 migration 0008 schema-only window
   -> no feature activation

2. R0-007 first bounded remote export/custody window
   -> no purge

3. L1-003/SMOKE-007 window package finalization
   -> execute/accept fresh resume-catch-up portion on market day

4. W1-001 short closeout Canary
   -> market day/session required

5. R0-008 real ACK/grace/purge
   -> only after real custody/quality evidence and separate destructive authorization
```

Rationale: apply the smallest reversible/additive remote change first, then collect non-destructive custody evidence, and leave live-market acceptance and destructive purge for their appropriate gates.

## 8. Current decisions

- Closed market is **not** a blocker for migration/schema review, remote-export planning, bounded custody, dry-run planning, documentation, or local quality verification.
- Closed market **is** a blocker for acceptance evidence that explicitly depends on fresh session behavior or live Market+News interaction.
- `0008` is reviewed as additive and independent from W1-001 while the feature flag remains disabled.
- First real R0-007 export should not include purge.
- R0-008 `PURGED` remains a distinct destructive change window.
- No remote mutation is performed by this review document.

## 9. Next safe action

The next closed-market task is **R0-002 migration 0008 schema-only change-window execution**, but only after explicit execution authorization. If not authorized, the next non-mutating task is to prepare the exact command/evidence packet for that window.
