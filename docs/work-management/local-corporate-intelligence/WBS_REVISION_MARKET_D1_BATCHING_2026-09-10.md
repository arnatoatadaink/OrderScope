# OrderScope — WBS Revision: Shared Worker D1 Budget Remediation

Status: **Active WBS revision / non-live only**
Date: 2026-09-10
Parent revision: `docs/work-management/local-corporate-intelligence/WBS_REVISION_NEWS_WORKER_2026-09-10.md`
Source blocker: `docs/work-management/local-corporate-intelligence/W1-001_STAGE_B_BLOCKER_REPORT_2026-09-10.md`

## 1. Revision decision

Stage B preflight for `W1-001` exposed a pre-existing Market Bars D1 persistence scalability constraint.

Add the prerequisite task:

```text
W1-002 — Batch Market Bar D1 persistence for shared invocation budget
```

This is not a reduction of Market scope. It is a persistence/query-shape remediation required to preserve existing Market semantics while allowing Market + News to share one Free-plan Worker invocation budget.

## 2. Work package update

| ID | Task | Completion condition | Dependency | Current state |
|---|---|---|---|---|
| W1-001 | Implement Worker/Schedule News metadata acquisition job | AMD/NVDA metadata-only News orchestration passes non-live implementation and combined Market+News budget preflight before separately gated Canary activation | N0-002, I0-003/004, X0-002, N1-006; W1-002 now required before Stage B can pass | Stage A Accepted; Stage B Blocked on Market D1 query shape |
| W1-002 | Batch Market Bar D1 persistence for shared invocation budget | Preserve accepted idempotency/duplicate/conflict/rejected/provenance/checkpoint semantics while reducing the reviewed 100-bar Market fixture to <=20 D1 queries and combined worst Market+News fixture to <40 D1 queries | Existing Market bar persistence/execution; W1-001 Stage-B blocker evidence | Ready for local implementation — non-live only |

## 3. Why W1-002 is separate

`W1-001` is News orchestration. The blocker is not caused by News correctness or News pagination.

The existing Market path performs several D1 statements per bar. Treating this as an internal News implementation detail would hide a cross-cutting Worker-runtime constraint and make future acquisition jobs repeat the same problem.

W1-002 therefore has an independently testable acceptance boundary.

## 4. Fixed acceptance target

OrderScope engineering ceilings remain:

```text
combined external subrequests < 40
combined D1 queries           < 40
```

Measured News-side worst reviewed fixture:

```text
News D1 queries <= 15
```

W1-002 Market target:

```text
100-bar Market fixture <= 20 D1 queries
```

This yields at least five queries of planned headroom in the reviewed worst combined fixture:

```text
20 + 15 = 35 < 40
```

Do not raise these ceilings merely to make W1-002 pass.

## 5. Preferred implementation direction

Use set-based D1 SQL rather than a one-observation/one-query family.

Cloudflare D1 supports SQLite JSON functions such as `json_each()`, allowing a bounded JSON array supplied as one parameter to be expanded into rows in SQL. This is the preferred first implementation candidate because it can reduce D1 query round trips without constructing unsafe dynamic SQL or consuming many bound parameters per row.

A large `db.batch()` containing hundreds of per-row statements is not considered proof of query-budget remediation.

## 6. Preserved Market invariants

W1-002 must preserve:

- canonical bar identity;
- canonical fingerprint comparison;
- acceptance receipt/idempotency traceability;
- same-content canonical duplicate -> `MATCHED`;
- conflicting semantic content -> `CONFLICT` with conflict evidence;
- rejected normalization -> deterministic recorded rejection;
- checkpoint advancement only after durable/reconstructable acceptance;
- existing Market coverage guarantees and max-bars behavior.

## 7. Stage B restart condition

`W1-001 Stage B` may be re-run only after W1-002 reports:

```text
100-bar Market D1 queries <= 20
combined worst Market + News D1 queries < 40
Market semantic regression = pass
checkpoint failure regression = pass
full TypeScript regression = pass
remote D1 applied = no
Worker deployed = no
Cron changed = no
Worker mode changed = no
```

## 8. Live boundary

Neither this revision nor W1-002 authorizes live infrastructure changes.

The next live gate remains:

```text
W1-002 Accepted
-> W1-001 Stage B Accepted on combined fixture
-> Web-reviewed AMD/NVDA Canary change window
-> explicit user authorization
```
