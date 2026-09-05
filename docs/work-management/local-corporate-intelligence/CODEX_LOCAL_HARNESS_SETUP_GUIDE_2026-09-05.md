# OrderScope — Codex Local Harness Setup Guide

Status: implementation preparation guide (non-normative)
Date: 2026-09-05
Scope: Local Corporate Intelligence work management

## 1. Purpose

Prepare the minimum structure required to delegate, review, and record OrderScope work safely in a local Codex environment that currently has no custom harness. The harness must use the existing WBS / Critical Path / Progress Tracker / Model Assignment Policy rather than inventing a separate source of truth.

This guide does not bind the project to a specific Agent framework or external orchestrator. Start with manual structured operation, then automate only repeated work.

## 2. Design principles

1. WBS / CP / Tracker remain canonical; the harness must not maintain an independent task state.
2. Default to one Agent = one bounded change set.
3. Separate parent-orchestrator and execution-Agent responsibilities.
4. Keep model assignment as a policy layer separate from task selection.
5. Parent rechecks Agent output using actual diff/test evidence.
6. Progress Tracker update is part of cycle completion.
7. Never include secrets, provider response bodies, or raw dumps in Agent handoff data.
8. Parallelize only tasks with explicit dependency safety.
9. Manual recovery must remain possible after harness failure.
10. Avoid unnecessary Codex lock-in; keep migration to CLI/IDE/other Agent harnesses possible.

## 3. Minimal operating architecture

```text
Management documents
  ├─ WBS
  ├─ Critical Path
  ├─ Progress Tracker
  └─ Model Assignment Policy
          ↓
Parent Orchestrator
  ├─ select one task
  ├─ resolve dependencies
  ├─ choose model / effort
  ├─ create bounded work packet
  └─ review result
          ↓
Execution Agent
  ├─ inspect bounded files
  ├─ implement
  ├─ run tests
  └─ return structured result
          ↓
Parent Orchestrator
  ├─ inspect diff
  ├─ verify tests
  ├─ decide acceptance state
  └─ update Progress Tracker
```

Until a harness exists, emulate this structure with separate Codex sessions or explicit parent/executor role switching.

## 4. Required artifacts

### 4.1 Management input

Required:

- `docs/WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
- `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
- `docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`
- `docs/work-management/local-corporate-intelligence/MODEL_ASSIGNMENT_POLICY_2026-09-05.md`
- `docs/work-management/local-corporate-intelligence/CODEX_LOCAL_ORCHESTRATION_PROMPT_2026-09-05.md`

### 4.2 Work packet

Minimum parent-to-executor contract:

```yaml
task_id: I0-002
objective: <WBS task text>
completion_conditions:
  - <condition>
dependencies:
  - I0-001
allowed_paths:
  - analysis/...
  - docs/... only when required
forbidden_changes:
  - WBS completion conditions
  - Critical Path ordering
known_provisional_results:
  - I0-005
required_tests:
  - <commands>
model: GPT-5.6 Terra
reasoning_effort: high
return_contract:
  - changed_files
  - tests_run
  - test_results
  - unresolved_items
  - suggested_tracker_update
```

H0 does not require generated YAML files; the same fields can be used directly in prompts.

## 5. Parent orchestrator responsibilities

Only the parent should own:

- current main-task selection;
- dependency-gate decisions;
- model / reasoning-effort selection;
- allowed/forbidden scope;
- provisional-result integration decisions;
- acceptance review of child output;
- Progress Tracker status changes;
- Critical Path change proposals.

Recommended parent profile:

- Sol low: normal cycle
- Sol medium: first audit, conflicts, Accepted promotion
- Sol high: CP changes, architecture boundaries, multi-lane conflicts

If Terra is the parent:

- medium: normal cycle
- high: integration review
- Sol review: Provisional→Accepted, CP changes, high-impact schema changes

## 6. Execution Agent responsibilities

Execution Agents stay inside their assigned task.

Do:
- read assigned paths and required dependencies;
- implement the bounded change;
- add fixtures/tests;
- run tests;
- return a structured result.

Do not:
- continue to the next task;
- rewrite WBS/CP;
- infer that a blocked dependency is satisfied;
- independently promote a provisional result to Accepted;
- perform unrelated refactors in another lane.

## 7. Result contract

Minimum executor result:

```text
Task: I0-002
Status: completed / partial / blocked
Changed files:
- ...
Tests:
- command -> pass/fail
Completion condition check:
- condition A: pass
- condition B: pass/partial
Unresolved:
- ...
Potential cross-task impacts:
- I0-005: ...
Recommended next state:
- In progress / Provisional result / Accepted candidate
```

The parent compares this report with the actual diff and test output.

## 8. Progress Tracker update contract

Record at least:

- timestamp/date;
- task ID;
- previous status → new status;
- model / reasoning effort;
- model-selection rationale;
- changed files;
- test evidence;
- acceptance evidence;
- unresolved items;
- next safe action.

A child may technically edit the Tracker, but during H0 only the parent should change task status.

## 9. Failure and recovery rules

### Agent failure

- Do not pass partial edits blindly to another Agent.
- Inspect `git diff` and test state.
- Roll back inside the task boundary when safe.
- If partial work is preserved, record it as provisional.

### Parent-session interruption

On resume, recheck:
1. Progress Tracker
2. git status / diff
3. last test result
4. current task ID
5. allowed scope

### Conflicting edits

- Do not assign the same file to multiple Agents in parallel.
- Serialize tasks that modify the same schema by default.

## 10. Concurrency policy

Recommended initial maximum parallelism: 2.

Safe example:
- I0-002 and L0-002

Avoid:
- I0-002 and I0-005
- I0-003 and I0-007 formal acceptance
- S0-003 and S0-004 integration review while the same schema is changing

Parallelization requires both Critical Path independence and no unsafe file overlap.

## 11. Candidate repository structure for future implementation

```text
tools/
└─ codex-harness/
   ├─ README.md
   ├─ task_packet.schema.json
   ├─ result.schema.json
   ├─ prompts/
   │  ├─ orchestrator.md
   │  └─ executor.md
   ├─ scripts/
   │  ├─ build_task_packet.py
   │  ├─ validate_result.py
   │  └─ append_progress.py
   └─ examples/
      └─ I0-002.yaml
```

Do not implement this structure until repeated H0 work demonstrates a need.

## 12. Harness maturity phases

### H0 — Manual structured operation

- Use prompt templates.
- Build work packets manually.
- Require structured executor results.
- Parent updates the Tracker manually.
- No additional code required.

### H1 — Validation helpers

Add only repeated mechanical checks:
- task-packet schema;
- result schema;
- path-scope checker;
- test-command recorder;
- Tracker append helper.

Agent launching remains manual.

### H2 — Local orchestration wrapper

Potential responsibilities:
- task-selection assistance;
- model/effort mapping;
- child-Agent launch;
- result collection;
- diff/test validation.

Design H2 only after confirming the actual Codex CLI/Desktop sub-Agent interface.

### H3 — Parallel orchestration

Potential additions:
- dependency-aware scheduling;
- file-overlap locks;
- retry / timeout;
- interrupted-session recovery.

Do not build H3 until H0/H1 proves an operational need.

## 13. Current recommendation

Start at H0 because:
- WBS/CP/Tracker already exist;
- model assignment is already defined;
- WBS task boundaries are sufficiently fine-grained;
- building orchestration first would delay the actual I0/L0 work.

Run one or two H0 cycles on I0-002/L0-002. Promote only repeated manual steps into H1 helpers.

## 14. Open questions before H1/H2

- Can local Codex select a model per child Agent?
- Can reasoning effort be set per child Agent?
- Is there a standard sub-Agent invocation interface?
- What is the supported structured-result handoff mechanism between sessions?
- Should Codex Desktop or CLI be the primary control surface?
- Can Codex enforce allowed paths, or is an external validator required?

Resolve these from the actual local environment before implementation.
