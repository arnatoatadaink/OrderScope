# OrderScope — Local Corporate Intelligence Progress Tracker

Status: active operational tracker (non-normative)
Date: 2026-09-05
Parent WBS: `../../WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Integrated CP: `../../WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
Extension WBS: `../../WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Model assignment: `MODEL_ASSIGNMENT_POLICY_2026-09-05.md`

## 1. Purpose

Track Local Corporate Intelligence execution against the Parent WBS and Integrated Critical Path without changing WBS completion conditions. Record current status, dependencies, provisional artifacts, formal-acceptance work, and the next safe action. Model/Agent selection follows the Model Assignment Policy and must be recorded per cycle.

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| Accepted | WBS completion conditions and dependencies are satisfied; safe as a downstream prerequisite |
| In progress | Currently being implemented or reconciled |
| Provisional result | Artifact exists, but an upstream dependency or formal acceptance is pending |
| Ready | Dependencies are satisfied; safe to start |
| Blocked | Waiting on an external window, unresolved contract, or upstream result |
| Not started | Dependency gate is closed or work has not started |

## 3. Current critical-path snapshot

| Task | Status | Evidence / interpretation | Next action |
|---|---|---|---|
| I0-001 | Accepted | Integrated CP selects `I0-002` as current main work | Reference only during downstream reconciliation |
| I0-002 | In progress | Current main task | Finish and accept provenance types plus timestamp/source-revision contract |
| I0-003 | Not started | Depends on `I0-002` | Start after I0-002 acceptance, in parallel with I0-004 |
| I0-004 | Not started | Depends on `I0-002` | Start after I0-002 acceptance, in parallel with I0-003 |
| I0-005 | Provisional result | Fact Store logical schema exists; alignment to I0-002 provenance types remains | Reconcile and formally accept after I0-002 |
| I0-006 | Not started | Depends on `I0-005` | Define temporary-content lifecycle after I0-005 Accepted |
| I0-007 | Provisional result | Common contract-test kit exists; formal acceptance waits for I0-003/004/006 | Connect upstream contracts and formally accept |
| S0-002 | Not started | Gated by I0-007 formal acceptance and S0-001 | Start SEC adapter after gate opens |
| S0-003 | Not started | Depends on `S0-002` | Implement FilingRecord persistence |
| S0-004 | Provisional result | Form-filter implementation/report exists; integration with S0-003 remains | Reconnect after S0-003 and preserve acceptance evidence |
| S0-005 | Not started | Depends on `S0-003` + `I0-006` | Implement temporary filing-document content handling |
| S0-006 | Not started | Depends on `S0-003` | Implement Company Facts/XBRL adapter |
| S0-007 | Provisional result | Early validation evidence may exist; formal acceptance follows S0-004..006 integration | Run formal Canary acceptance after integration |
| E0-001..007 | Not started | Depends on S0 lane and I0-005 | Start after S0-007 |
| N1 / O0 / X0 | Not started | Depends on Core Fact/SEC/Earnings lanes | Start later on the Core CP |

## 4. Parallel lanes

### Lane A — Core contracts

Current: `I0-002`

1. I0-002
2. I0-003 / I0-004 in parallel
3. I0-005 alignment and acceptance
4. I0-006
5. I0-007 formal acceptance

### Lane B — Local foundation

Current next task: `L0-002`

- `L0-002 → L0-003/L0-004/L0-005 → L0-006`
- `L1-001 → L1-002 → L1-004 → L1-005` via fixture path
- `L1-003` remains blocked by the separately approved `SMOKE-007` change window and must not block fixture work.

### Lane C — Cross-Market extension

| Task | Status | Next action |
|---|---|---|
| A0-001 | Provisional result | Design complete; wait for I0-002/I0-005 acceptance, then reflect fields/schema/fixtures |
| A0-002 | Not started | Dataset/source definition may proceed before final schema write |

### Lane D — SEC / Earnings

Blocked until `I0-007` formal acceptance.
Then: `S0-002 → S0-003 → (S0-005 || S0-006) → S0-007 → E0-001..007`.

## 5. Current model / Agent assignment

| Role / task | Assignment | Reasoning | Note |
|---|---|---|---|
| Orchestrator | Sol | low | Normal cycle while WBS/CP/Tracker are already aligned; raise to medium+ for design or Accepted promotion |
| I0-002 implementation | Terra | high | Provenance/timestamp/source-revision contract affects many downstream tasks |
| I0-002 acceptance review | Sol | medium-high | Verify semantic alignment with I0-005/A0-001 and downstream contracts |
| L0-002 | Luna | medium | Bounded scaffold change |
| A0-002 dataset/source definition | Terra | medium | No final schema write or hypothesis integration yet |

Record the actual model, reasoning effort, delegation rationale, and review result at the end of each cycle.

## 6. Known non-blockers / deferred items

- `L1-003` remote D1 export change window is deferred and does not block local fixture work.
- `A0-002` is a validation lane and is not currently a serial blocker for Core Corporate Intelligence.
- Preserve and reconcile provisional artifacts for `I0-005`, `I0-007`, and `S0-004`; do not discard them.

## 7. Current restart rule

- Main local session: `I0-002`
- Second parallel local session: `L0-002`
- Cross-Market session: `A0-002` dataset/source definition only until `I0-002/I0-005` are Accepted
- SEC implementation waits for `I0-007` formal acceptance

## 8. Unresolved items

- Analyst Consensus as-of history provider and contract conditions
- AI/Semiconductor proxy definition for A0-002
- short/borrow data provider for H4 validation
- whether A0-002 becomes mandatory for v0.1 release acceptance
- exact evidence needed to promote provisional `I0-005`, `I0-007`, and `S0-004/S0-007` artifacts after dependency integration

Do not infer unresolved values. Update this tracker only from repository evidence, test results, or confirmed external contract/source information.
