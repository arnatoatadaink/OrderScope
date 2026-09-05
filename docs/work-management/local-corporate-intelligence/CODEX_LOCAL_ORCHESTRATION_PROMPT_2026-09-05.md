# OrderScope — Codex Local Orchestration Resume Prompt

Status: active execution prompt template (non-normative)
Date: 2026-09-05

## Purpose

Parent-agent prompt for safely resuming Local Corporate Intelligence work in a local Codex environment. The Progress Tracker is the sole runtime-status authority; WBS and Critical Path provide task semantics and dependency structure only.

## Prompt

Treat the following four files as canonical management inputs with distinct responsibilities:

- `docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md` — current task state, restart point, blockers, evidence, next safe work
- `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md` — task definitions, completion conditions, dependencies
- `docs/WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md` — static dependency order, permanent gates, safe parallelization
- `docs/work-management/local-corporate-intelligence/MODEL_ASSIGNMENT_POLICY_2026-09-05.md` — model/reasoning selection and escalation

First inspect the Progress Tracker, then use the WBS, Critical Path, Model Assignment Policy, and current repository state to validate the selected work.

Identify:

1. the current main task from the Progress Tracker;
2. its WBS completion conditions and dependencies;
3. downstream and parallel dependency relationships from the Critical Path;
4. alignment with existing implementation, fixtures, tests, prior artifacts, and provisional results;
5. the recommended model and reasoning effort from the Model Assignment Policy.

Do not infer current progress from the Critical Path. If the Critical Path and Progress Tracker appear to disagree about runtime state, the Progress Tracker owns runtime state; investigate whether the dependency plan itself is actually wrong before proposing a Critical Path change.

By default, work on only one main task selected by the Progress Tracker. Do not automatically continue to downstream tasks or modify a parallel lane in the same work packet. Preserve provisional artifacts and treat them as integration targets.

Split the selected task into changes that can be reviewed, tested, and rolled back independently. When delegation is available, use one Agent per bounded change set by default.

Select models according to `MODEL_ASSIGNMENT_POLICY_2026-09-05.md`. For new work not explicitly covered there, classify the work as B1-B4 and record the rationale instead of guessing.

The parent Agent owns:

- task selection from the Progress Tracker;
- dependency-gate checks against WBS/CP;
- delegation scope;
- diff/test review of child results;
- comparison against WBS completion conditions;
- integration checks against provisional artifacts and existing schema/test/fixture behavior;
- acceptance-state decisions;
- Progress Tracker updates.

Never accept a child-Agent result without review. Before integration, verify:

- WBS completion conditions are satisfied;
- upstream contracts are preserved;
- downstream assumptions are not broken;
- existing and new tests pass;
- no secrets, credentials, or provider raw bodies were added to Git;
- changes remain inside the assigned task boundary.

Escalate when work would promote `Provisional result → Accepted`, alter schema across multiple lanes, conflict with existing design, or require changing dependency structure/permanent gates in the Critical Path.

After each normal work cycle, update only:

`docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`

Record at least:

- task ID;
- model / reasoning effort used;
- model-selection rationale;
- changed files;
- test results;
- completion-condition check;
- status transition;
- remaining work;
- next safe action;
- unresolved items.

Do not update the Critical Path merely because a task completed or the restart point changed. Update it only when dependency structure, permanent gates, or safe-parallelization rules change. Do not change WBS completion conditions merely for implementation convenience.

## Execution profile rule

Do not hard-code a current task or current model assignment in this prompt. Resolve both at session start from the Progress Tracker and Model Assignment Policy so this template does not become stale.

When no harness or multi-Agent launcher exists, use model assignments as responsibility and review boundaries even if work is performed across separate Codex sessions manually.