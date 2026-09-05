# Local Corporate Intelligence — Work Management Index

Status: active management index (non-normative)
Date: 2026-09-05

This directory is the single entry point for Local Corporate Intelligence work-management documents. Existing canonical files remain in place to avoid breaking references.

## Core management documents

| Role | Canonical document | Purpose |
|---|---|---|
| Parent WBS | `../../WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md` | Defines tasks, completion conditions, and dependencies |
| Integrated Critical Path | `../../WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md` | Defines static dependency order, permanent gates, and safe parallelization |
| Local Progress Tracker | `LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md` | **Sole authority for runtime progress**: task state, accepted/provisional/ready/blocked status, restart point, evidence, and next safe work |
| Model / Agent Assignment Policy | `MODEL_ASSIGNMENT_POLICY_2026-09-05.md` | Defines model roles, reasoning effort, task suitability, and escalation rules |
| Codex Local Resume Prompt | `CODEX_LOCAL_ORCHESTRATION_PROMPT_2026-09-05.md` | Standard parent-agent prompt for resuming local work |
| Codex Local Harness Setup Guide | `CODEX_LOCAL_HARNESS_SETUP_GUIDE_2026-09-05.md` | Defines H0-H3 harness maturity and orchestration boundaries |

## Extension / parallel management documents

| Role | Canonical document | Purpose |
|---|---|---|
| A0 extension WBS | `../../WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md` | Analyst Consensus / Macro / Cross-Market extension |
| A0 progress tracker | `../../ANALYST_CROSS_MARKET_PROGRESS_TRACKER_2026-09-05.md` | Lane-specific A0 evidence/history; Local Progress Tracker remains the integrated runtime-status authority |
| Web workstream plan | `../../REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md` | Defines Web-side research work |
| Web progress tracker | `../../WEB_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-03.md` | Tracks Web-xxx research work within that separate workstream |
| Worker implementation plan | `../../WORK_PLAN_INITIAL_VALIDATION_AND_LONG_TERM_OPERATIONS_2026-09-01.md` | Market Worker validation / operations plan |
| Worker implementation tracker | `../../IMPLEMENTATION_PROGRESS_TRACKER_2026-09-01.md` | Worker implementation / operational evidence |
| Worker progress report | `../../PROGRESS_REPORT_2026-09-01.md` | Worker status snapshot as of 2026-09-01 |

## Role boundaries

- WBS: **what must be completed**.
- Critical Path: **dependency structure and gates**. It does not record current progress or restart state.
- Progress Tracker: **what is true now**. It is the only integrated source for current task state, blockers, accepted/provisional results, restart point, and next safe work.
- Model Assignment Policy: **who should execute/review the work**; it does not change WBS semantics.
- Codex Local Resume Prompt: how the parent agent resumes work.
- Codex Local Harness Setup Guide: how to move from structured manual operation to automation.
- Reports / Workstreams: lane-specific plans or evidence; they do not replace the Parent WBS or integrated Progress Tracker.

## Update rules

After a normal implementation cycle:

1. update code/tests as required;
2. update **only the Local Progress Tracker** for runtime status/evidence;
3. do not update the Critical Path merely because a task was completed or the restart point moved;
4. update the Critical Path only if dependency structure, permanent gates, or safe-parallelization rules change;
5. update the WBS only if task scope/completion conditions are intentionally revised.

## Resume rule

For the current main task, next safe task, blockers, or latest accepted work, consult:

`LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`

Use `MODEL_ASSIGNMENT_POLICY_2026-09-05.md` after selecting the task from the Progress Tracker. Until a harness exists, use H0 manual structured operation and `CODEX_LOCAL_ORCHESTRATION_PROMPT_2026-09-05.md` as the standard resume prompt.