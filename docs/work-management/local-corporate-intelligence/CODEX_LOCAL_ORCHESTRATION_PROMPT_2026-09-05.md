# OrderScope — Codex Local Orchestration Resume Prompt

Status: active execution prompt template (non-normative)
Date: 2026-09-05

## Purpose

Parent-agent prompt for safely resuming Local Corporate Intelligence work in a local Codex environment. It is designed to work even without a custom harness by enforcing management-document, model-selection, scope, review, and Progress Tracker rules.

## Prompt

Treat the following four files as the canonical work-management inputs:

- `docs/WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
- `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
- `docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`
- `docs/work-management/local-corporate-intelligence/MODEL_ASSIGNMENT_POLICY_2026-09-05.md`

First inspect all four files and the current repository state. Identify:

1. the current main task in the Progress Tracker;
2. its WBS completion conditions and dependencies;
3. downstream and parallel tasks in the Critical Path;
4. alignment with existing implementation, fixtures, tests, prior artifacts, and provisional results;
5. the recommended model and reasoning effort from the Model Assignment Policy.

By default, work on only one main task selected by the Progress Tracker.
Do not automatically continue to downstream tasks.
Do not modify a parallel lane in the same work packet.
Do not delete or reimplement existing provisional artifacts; treat them as integration targets.

Split the selected task into changes that can be reviewed, tested, and rolled back independently.
When delegation is available, use one Agent per bounded change set by default.

Select models according to `MODEL_ASSIGNMENT_POLICY_2026-09-05.md`.
For new work not explicitly covered by that document, classify the work as B1-B4 and record the selection rationale instead of guessing.

The parent Agent owns:

- task selection;
- dependency-gate checks;
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

If work would promote `Provisional result → Accepted`, change the Critical Path, alter schema across multiple lanes, or conflicts with existing design, stop normal implementation and escalate to higher-level review.

After the work cycle, update:
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

Do not change WBS completion conditions or Critical Path dependencies merely for implementation convenience.
Do not infer unresolved design decisions; record them as unresolved in the Progress Tracker.

## Recommended current execution profile

As of 2026-09-05:

- Parent orchestrator: Sol low
- Main task `I0-002`: Terra high + Sol acceptance review
- Parallel `L0-002`: Luna medium
- A0 dataset/source definition: Terra medium

When no harness or multi-Agent launcher exists, use these assignments as responsibility and review boundaries even if the work is performed across separate Codex sessions manually.
