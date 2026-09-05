# Local Corporate Intelligence — Work Management Index

Status: active management index (non-normative)
Date: 2026-09-05

This directory is the single entry point for Local Corporate Intelligence work-management documents. Existing canonical files remain in place to avoid breaking references.

## Core management documents

| Role | Canonical document | Purpose |
|---|---|---|
| Parent WBS | `../../WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md` | Defines tasks, completion conditions, and dependencies |
| Integrated Critical Path | `../../WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md` | Defines the main CP, parallel lanes, and restart order |
| Local Progress Tracker | `LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md` | Records task state, gates, provisional artifacts, blockers, and next safe work |
| Model / Agent Assignment Policy | `MODEL_ASSIGNMENT_POLICY_2026-09-05.md` | Defines model roles, reasoning effort, task suitability, and escalation rules |
| Codex Local Resume Prompt | `CODEX_LOCAL_ORCHESTRATION_PROMPT_2026-09-05.md` | Standard parent-agent prompt for resuming local work |
| Codex Local Harness Setup Guide | `CODEX_LOCAL_HARNESS_SETUP_GUIDE_2026-09-05.md` | Defines H0-H3 harness maturity and orchestration boundaries |

## Extension / parallel management documents

| Role | Canonical document | Purpose |
|---|---|---|
| A0 extension WBS | `../../WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md` | Analyst Consensus / Macro / Cross-Market extension |
| A0 progress tracker | `../../ANALYST_CROSS_MARKET_PROGRESS_TRACKER_2026-09-05.md` | Tracks A0-001/A0-002 |
| Web workstream plan | `../../REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md` | Defines Web-side research work |
| Web progress tracker | `../../WEB_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-03.md` | Tracks Web-xxx tasks |
| Worker implementation plan | `../../WORK_PLAN_INITIAL_VALIDATION_AND_LONG_TERM_OPERATIONS_2026-09-01.md` | Market Worker validation / operations plan |
| Worker implementation tracker | `../../IMPLEMENTATION_PROGRESS_TRACKER_2026-09-01.md` | Worker implementation / operational evidence |
| Worker progress report | `../../PROGRESS_REPORT_2026-09-01.md` | Worker status snapshot as of 2026-09-01 |

## Role boundaries

- WBS: what must be completed.
- Critical Path: dependency order toward completion.
- Progress Tracker: current state, blockers, and next safe work.
- Model Assignment Policy: execution/review ownership; it does not change WBS semantics.
- Codex Local Resume Prompt: how the parent agent resumes work.
- Codex Local Harness Setup Guide: how to move from structured manual operation to automation.
- Reports / Workstreams: lane-specific plans or evidence; they do not replace the Parent WBS.

## Current restart point

- Main task: `I0-002`.
- Parallel local lane: `L0-002`.
- A0 may advance through `A0-002` dataset/source definition only.
- Preserve provisional artifacts for `I0-005`, `I0-007`, and `S0-004`; reconcile them after dependencies are satisfied.
- Use `MODEL_ASSIGNMENT_POLICY_2026-09-05.md` for model selection.
- Current recommended assignments: Sol orchestrator, Terra for `I0-002`, Luna for `L0-002`, Terra for `A0-002` dataset/source definition.
- Until a harness exists, use H0 manual structured operation and `CODEX_LOCAL_ORCHESTRATION_PROMPT_2026-09-05.md` as the standard resume prompt.
