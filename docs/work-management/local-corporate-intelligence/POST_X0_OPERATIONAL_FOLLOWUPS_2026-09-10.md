# OrderScope — Post-X0 Operational Follow-ups

Status: **Active follow-up backlog — non-normative IDs pending future WBS incorporation**
Date: 2026-09-10
Source: `X0-006_CANARY_OPERATIONS_RUNBOOK_REVIEW_2026-09-10.md`

## 1. Purpose

This file records operational gaps identified after X0-006 review without reopening the accepted X0-001..006 fixture-path integration lane.

The identifiers `PX0-001..004` are tracking IDs only. They do not replace or redefine existing WBS tasks until a future WBS revision explicitly incorporates or remaps them.

## 2. Follow-up tasks

| ID | Review finding | Task | Completion condition | Related existing work | Status |
|---|---|---|---|---|---|
| PX0-001 | F1 | Register reviewed operational scheduler jobs | At least one owning adapter/integration task can register an explicit bounded scheduler plan; dry-run shows intended jobs; zero-job success cannot be mistaken for workload completion; tests preserve no-HTTP-mutation and bounded-run rules | X0-004, owning adapters | Not started |
| PX0-002 | F2 | Implement durable scheduler run evidence and stale-lock recovery | Persist run/job identity, start/end/status, completed boundary, application revision, and sanitized failure state; provide inspection path for last completed boundary; define lock path/owner evidence robust enough to address PID reuse; stale lock clearance is testable and does not allow concurrent schedulers | X0-004; I0-003 remains provider/source checkpoint contract | Not started |
| PX0-003 | F3 | Implement retention and bounded reprocessing operator commands | CLI can inspect retention backlog/overdue state, execute bounded deletion/retry through a concrete storage deleter, and plan/run bounded replay without exposing bodies/secrets; commands have focused tests and preserve N1-005 retention semantics | N1-005, L0-006, integration layer | Not started |
| PX0-004 | F4 | Implement reproducible backup/restore and restore drill | Freeze data-root layout and included paths; implement SQLite-consistent snapshot plus DuckDB/Parquet/catalog checks; define manifest/hashes, destination permissions/encryption assumptions, generations/RPO, restore validation, drill frequency/owner; demonstrate restore into a new WSL-native root with acceptance evidence | L0-005, L1 storage/datasets, X0-006 policy | Not started |

## 3. Dependency guidance

Recommended dependency order:

```text
PX0-001 ─┐
         ├─> PX0-002
I0-003 ──┘

N1-005 + L0-006 -> PX0-003

stable data-root/layout + accepted storage paths -> PX0-004
```

PX0-001 does not authorize live providers by itself. Each registered operational job must already be permitted by its owning adapter task and current provider/terms checks.

PX0-002 must not absorb provider cursor semantics from I0-003. It owns scheduler-run evidence and lock recovery; adapter checkpoints remain adapter/source-owned.

PX0-003 must not reopen the accepted storage-neutral retention rules. It adds operator execution/inspection around them.

PX0-004 is intentionally independent from the fixture-path X0 acceptance and should be completed before calling the local stack production disaster-recovery ready.

## 4. Interim operator limitations

Until the follow-ups are complete:

- `orderscope schedule run` may legitimately select zero built-in jobs; exit success is not proof an intended workload ran.
- interrupted-run resume and stale-lock clearance require manual engineering review using available adapter/checkpoint evidence; do not blindly remove locks.
- retention/reprocessing checklist items are verified through programmatic/fixture paths, not a complete operator CLI.
- backup/restore guidance is policy-level only; do not claim a reproducible disaster-recovery procedure or RPO.

## 5. Non-authorizations

This backlog does not authorize:

- `L1-003` real D1 export or `SMOKE-007`;
- Worker mutation or mode changes;
- unreviewed live-provider registration;
- external API binding;
- persistent storage of credentials or successful temporary News bodies.

## 6. Next planning action

When the main WBS is next revised, either:

1. incorporate `PX0-001..004` as a new operations/recovery package; or
2. remap each item to an existing/new owning task while preserving these completion conditions and review provenance.
