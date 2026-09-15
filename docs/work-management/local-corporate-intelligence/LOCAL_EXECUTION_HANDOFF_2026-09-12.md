# OrderScope — Local Execution Handoff

Status: active local handoff (non-normative)
Date: 2026-09-12
Scope: Local Corporate Intelligence / Market + News operational hardening
Target branch: `docs/mermaid-conventions-v0.1`

## 1. Purpose

This handoff converts the current project state into the next local execution sequence.

The immediate goal is **not** to expand feature scope. The goal is to harden the already accepted Local / News / Scheduler path so that the next reviewed Worker Canary can collect reliable operational evidence without weakening existing Fact, checkpoint, budget, idempotency, or fail-closed guarantees.

Use this file as a bounded execution handoff only. It does not replace the runtime tracker, WBS, Critical Path, or model-assignment policy.

## 2. Authoritative management inputs

Resolve runtime state and task eligibility from these files before starting work:

1. `docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`
   - sole authority for current runtime progress, restart point, blockers, acceptance evidence, and next safe action.
2. `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
   - task definitions, dependencies, completion conditions, and Definition of Done.
3. `docs/WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
   - static dependency order, permanent gates, and safe parallelization.
4. `docs/work-management/local-corporate-intelligence/MODEL_ASSIGNMENT_POLICY_2026-09-05.md`
   - model/reasoning assignment and escalation rules.
5. `docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md`
   - non-normative follow-up scope such as PX0/UWBS work.

Do not infer current progress from the Critical Path when it disagrees with the Progress Tracker. Investigate the mismatch; do not silently rewrite runtime state.

## 3. Current baseline

Treat the following as the current baseline unless the Progress Tracker has newer evidence:

- `L0-001..006`: Accepted.
- `L1-001`, `L1-002`, `L1-004`, `L1-005`, `L1-006`: Accepted for their current fixture/local boundary.
- `L1-003`: externally blocked behind an approved `SMOKE-007` real-D1 change window.
- `X0-001..006`: Accepted for the fixture-path integration boundary.
- `N1-006`: Accepted using the real 30-day AMD/NVDA Alpaca News benchmark.
- News benchmark evidence: 645/645 candidates reviewed; 51 matched; 594 unrelated; 0 unresolved; 4/4 reference events discovered; recall `1.0000`; ticker/subject misattribution `0`.
- W1 cadence repair has live evidence for non-zero Cron seconds offsets.
- A reopened News Canary observed 12 distinct five-minute opportunities and completed its News jobs without cadence, budget, or duplicate-canonicalization failure.
- The live Canary was rolled back after a Cloudflare D1 control-path authorization failure (`7403`) prevented reliable continued monitoring.
- `W1-007` subsequently passed two read-only control-path diagnostic passes and could not reproduce `7403`.
- Root cause of the earlier `7403` remains **unknown**. Treat transient/stale OAuth or control-plane state as hypotheses only.
- Worker remains `shadow`; News remains disabled after rollback unless a separately reviewed change window authorizes otherwise.

## 4. Execution objective

Prepare the local codebase and tests for one short, reviewed W1-001 confirmation/closeout Canary.

The local work should prove four properties before another live window is considered:

1. scheduler opportunity calculation is robust to non-zero Cron seconds and duplicate execution;
2. Market + News work remains within shared bounded budgets and preserves per-symbol checkpoint truth;
3. control-path and provider/data-path failures are distinguishable and fail closed;
4. interruption/retry/replay state is inspectable enough to identify the last completed boundary and safe restart point.

## 5. Execution order

### Packet A — Scheduler / cadence regression hardening

Primary objective: lock in the already live-confirmed cadence repair and prevent regression.

Required checks:

- exercise scheduled timestamps with seconds `00`, `15`, `30`, and `59`;
- prove timestamps belonging to the same five-minute UTC minute bucket resolve to the same eligibility decision;
- prove a repeated observation of the same eligible opportunity does not create an additional canonical News article or double-advance checkpoint state;
- preserve existing session-aware configuration rather than adding a second hard-coded News clock;
- verify AMD/NVDA News planning remains metadata-only;
- verify `shadow` / News-disabled mode performs no News mutation;
- verify zero planned News jobs cannot be interpreted as evidence that News workload was successfully completed when an eligible job should have existed.

Acceptance evidence:

- focused scheduler/cadence tests pass;
- full relevant TypeScript/Python regression passes;
- typecheck / compile checks pass where applicable;
- `git diff --check` is clean;
- no behavior change outside the assigned scheduler boundary unless explicitly justified and reviewed.

Do not change the five-minute cadence merely because it is provisional. Cadence optimization is a later evidence-driven decision.

### Packet B — Shared budget / idempotency / checkpoint regression

Primary objective: ensure Market and News can coexist in one tick without weakening bounded execution.

Required checks:

- Market and News consume the shared external-call budget consistently;
- D1 operation accounting remains bounded and fail closed;
- a News duplicate does not consume canonical-article insertion state twice;
- cross-symbol article identity remains canonical while query/symbol membership can be recorded separately;
- per-symbol checkpoint CAS truth is preserved;
- partial Market or News work does not falsely advance coverage;
- retry paths do not create a second accepted canonical article from the same provider identity/content revision.

Acceptance evidence should include deterministic fixtures for budget-near-limit behavior, duplicates, partial results, and checkpoint conflicts.

### Packet C — Control-path failure classification and fail-safe behavior

Primary objective: make failures like the prior Cloudflare `7403` diagnosable without guessing the cause.

Add or refine fixture coverage for at least:

- authentication failure;
- authorization failure;
- timeout / transport failure;
- transient control API failure;
- D1 read/control request failure;
- provider acquisition failure;
- partial provider/data response.

Required behavior:

- do not encode `7403 == stale OAuth` or any other unproven root cause;
- distinguish control-path failure from provider acquisition failure and data-processing failure;
- preserve sanitized error evidence without credentials or raw provider bodies;
- do not advance checkpoint/coverage on a failed control or data boundary;
- leave a retryable state where retry is semantically safe;
- fail closed when success cannot be proven.

Prefer typed/status-class boundaries over string-matching a single Cloudflare error code where practical.

### Packet D — Durable run evidence and restart/recovery boundary

Primary objective: implement or prototype the local acceptance evidence needed for the `PX0-002` follow-up without silently declaring the non-normative PX0 item formally complete.

Capture enough durable execution evidence to inspect:

- run identity;
- job identity;
- scheduler/code revision;
- provider/source;
- start/completion time;
- final status;
- last completed bounded window / checkpoint boundary;
- sanitized failure classification;
- retry/replay relationship when applicable.

Test at least:

- process stop before checkpoint persistence;
- process stop after checkpoint persistence;
- retry of an already accepted duplicate;
- stale lock;
- lock ownership ambiguity / PID reuse case;
- bounded replay from an explicitly selected window.

Constraint:

`I0-003` remains the owner of provider/source checkpoint semantics. Durable operator/run evidence must not become a second source of checkpoint truth.

### Packet E — Retention / retry / bounded replay operator path

Primary objective: prepare the `PX0-003` operational boundary after Packet D is stable.

Keep mutation operator-only / CLI-only. Do not add arbitrary HTTP job-start endpoints.

Candidate capabilities:

- inspect retention backlog and overdue state;
- inspect failed/retryable work;
- dry-run a bounded replay;
- execute replay for a bounded provider/source/time window;
- retry bounded deletion/retention work through concrete storage;
- display metadata/evidence only, never raw News bodies or secrets.

Do not implement an unbounded "reprocess everything" command.

### Packet F — Backup / restore drill

Primary objective: prepare the `PX0-004` recovery boundary after run evidence and replay semantics are stable.

Define and test a reproducible backup set covering the currently accepted local data boundary, including as applicable:

- SQLite metadata/catalog state;
- schema/migration revision;
- dataset manifest/catalog references;
- Parquet / generated dataset artifacts required for reconstruction;
- hashes and backup generation metadata.

Acceptance should be based on a restore drill, not file-copy success alone:

1. create backup/snapshot;
2. restore into a clean destination;
3. validate migrations/catalog;
4. validate manifest/hash relationships;
5. run representative read-only API / quality checks;
6. record the drill result.

## 6. Live Canary re-entry gate

Do **not** open another Worker change window as part of normal local implementation.

A future short W1-001 confirmation/closeout Canary should be considered only after:

- Packet A scheduler/cadence regression is accepted locally;
- Packet B budget/idempotency/checkpoint regression is accepted locally;
- Packet C control-path fail-safe coverage is accepted locally;
- the current W1-007 evidence receives the required review;
- a separate change window is explicitly authorized.

The live confirmation should remain short and evidence-oriented. Capture at least:

- distinct eligible News opportunities;
- News jobs planned/completed/failed/partial;
- external and D1 budget maxima;
- duplicate/canonicalization behavior;
- checkpoint behavior;
- publication-to-retrieval lag;
- publication-to-acceptance lag;
- control-path health;
- successful rollback evidence.

Do not use one observed article lag to freeze or optimize the long-term News cadence.

## 7. Explicit non-goals for this local sequence

Do not pull the following work into the current hardening packets unless a dependency forces a narrowly scoped compatibility change:

- real D1 export / `L1-003` without `SMOKE-007` approval;
- Worker live activation or Cron mutation outside an approved change window;
- broad News body persistence;
- LLM News extraction expansion;
- five-minute cadence optimization;
- Macro / rates / FX Fact expansion;
- Corporate Action / TOB lifecycle implementation;
- TNON convertible-debt lifecycle implementation;
- TNON/CHPT price-rediscovery model implementation;
- Regime scoring expansion.

These remain later lanes or WBS-unreflected scope until formally incorporated/remapped.

## 8. Recommended local session protocol

For each local Codex session:

1. read the Progress Tracker first;
2. identify one main task / packet only;
3. verify dependencies and completion conditions in WBS/CP;
4. inspect existing implementation, fixtures, and provisional results before editing;
5. split work into independently reviewable changes;
6. run focused tests during implementation;
7. run full relevant regression before acceptance;
8. run compile/typecheck and `git diff --check` as applicable;
9. compare evidence against the task completion condition, not merely test pass/fail;
10. classify the result as Accepted / Provisional / Blocked according to existing project rules;
11. update the runtime Progress Tracker with changed files, model/reasoning, tests, status transition, unresolved items, and next safe action;
12. stop at the defined packet boundary unless the Progress Tracker explicitly selects the next task.

Do not update the Critical Path solely because runtime progress changed. Do not relax WBS completion conditions for implementation convenience.

## 9. Suggested immediate restart point

Default next local packet:

`Packet A — Scheduler / cadence regression hardening`

Suggested implementation sequence inside Packet A:

1. locate the repaired minute-bucket eligibility predicate and its existing tests;
2. add deterministic second-offset cases (`00/15/30/59`);
3. add repeated-opportunity / duplicate-execution cases;
4. verify `shadow` and News-disabled behavior;
5. verify eligible-zero-job behavior cannot be misreported as workload completion;
6. run focused tests;
7. run full scheduler/Worker regression;
8. typecheck / dry-run as appropriate;
9. review diff against W1-005/W1-006/W1-007 assumptions;
10. record evidence in the Progress Tracker.

If Packet A uncovers a cross-lane schema or checkpoint-contract change, stop and escalate instead of expanding scope automatically.

## 10. Later expansion queue

After Worker/Scheduler operational hardening reaches a stable boundary, return to WBS incorporation/design for:

- Macro non-price Fact contract and rate/FX Derived Metrics (`UWBS-011..015`);
- Corporate Action / TOB lifecycle (`UWBS-005..010`);
- Worker/Schedule News acquisition formal remap (`UWBS-016`, if not already remapped by newer planning state);
- TNON convertible-debt / dilution-overhang lifecycle (`UWBS-017..019`);
- TNON/CHPT price rediscovery (`UWBS-020..022`).

Preserve the boundary:

`Fact -> Derived Metric -> Interpretation -> Prediction`

Do not store inferred capital movement, repricing interpretation, or Regime conclusions as observed Fact.

## 11. Completion condition for this handoff

This handoff is consumed successfully when a local agent can:

- identify Packet A as the default restart point;
- explain why another live Canary is not yet automatically authorized;
- execute the current local hardening work without pulling in WBS-unreflected feature expansion;
- produce test/review evidence that can be recorded in the Progress Tracker;
- stop at the review boundary when a cross-lane contract, remote change window, or unresolved external gate is encountered.
