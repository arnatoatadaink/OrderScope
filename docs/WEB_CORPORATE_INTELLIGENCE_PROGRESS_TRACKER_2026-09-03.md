# OrderScope — Web Corporate Intelligence Progress Tracker

Status: active operational tracker (non-normative)
Date: 2026-09-03
Scope: `REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md`
Parent plan: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`

## 1. Purpose

This is the single progress ledger for `WEB-001` through `WEB-020`. It is designed to be read and updated from separate ChatGPT Web sessions without treating conversation history as the source of truth.

The workstream report defines task meaning. This tracker defines current Web status, evidence, handoff and next action. The parent work-breakdown document continues to define the completion of W0/L0/L1/I0/S0/E0/N0/N1/O0/X0 tasks.

## 2. Status rules

| Status | Meaning |
|---|---|
| `未着手` | No repository-backed research result exists yet. Dependencies may or may not be satisfied. |
| `進行中` | A named session is actively researching or drafting the task. |
| `調査完了` | The Web deliverable and official evidence are complete, but local handoff or parent-task implementation may remain. |
| `引渡し済み` | The Web result has an explicit local consumer and is sufficient for that consumer to proceed. |
| `保留（依存）` | A preceding Web result, local contract/adapter shape, or user decision is required. |
| `保留（外部）` | Access, current official disclosure, licence/contract clarification or another external condition is required. |
| `再確認要` | A formerly completed point-in-time result is stale or affected by a source/terms change. |

`調査完了` and `引渡し済み` do not mean that the mapped parent task is complete. Numerical quality claims require local measurement evidence.

## 3. Current summary

As of 2026-09-03, the Web catalogue contains 20 tasks.

| Status | Count |
|---|---:|
| 未着手 | 6 |
| 進行中 | 0 |
| 調査完了 | 0 |
| 引渡し済み | 0 |
| 保留（依存） | 14 |
| 保留（外部） | 0 |
| 再確認要 | 0 |

The immediate queue is `WEB-001`, `WEB-002`, `WEB-003`, `WEB-005`, `WEB-011`, and `WEB-015`. `WEB-011` can survey candidates immediately, but its recommendation must use the usage-condition framework from `WEB-003`.

Known adjacent state:

- `W0-001` is satisfied for starting the local MVP; remaining Worker `SMOKE-*` and `CANARY-*` work stays separate.
- `L0-001` is complete through `ADR_LOCAL_ANALYSIS_STACK_v0.1.md`.
- The next local implementation item is `L0-002`.
- Worker and Prediction modes remain Shadow according to the parent work breakdown and implementation tracker.

## 4. Task ledger

| Web ID | Parent | Wave | Status | Dependency / blocker | Result / evidence | Local handoff | Next action | Last update | Session |
|---|---|---|---|---|---|---|---|---|---|
| WEB-001 | W0-002 | A | 未着手 | none | — | I0-001, S0-002, E0-003 | Verify AMD/NVDA identity, CIK and official IR URLs | 2026-09-03 | — |
| WEB-002 | W0-003 | A | 未着手 | none | Source classes fixed by parent plan; registry not yet produced | O0-001/002 | Produce explicit included/excluded source-scope table | 2026-09-03 | — |
| WEB-003 | W0-004 | A | 未着手 | none | Existing provider research is point-in-time only | S0-001, N0-001, adapter ADRs | Create the reusable official-conditions checklist | 2026-09-03 | — |
| WEB-004 | I0-001 | B | 保留（依存） | WEB-001, WEB-002 | — | Local registry schema and tests | Convert verified identities/sources into proposed historical mappings | 2026-09-03 | — |
| WEB-005 | S0-001 | A | 未着手 | none | SEC EDGAR/XBRL is the v0.1 baseline | S0-002〜007 | Recheck current SEC official connection and fair-access rules | 2026-09-03 | — |
| WEB-006 | S0-004 | B | 保留（依存） | WEB-005 | Target form list fixed in parent plan | S0-004 tests/fixtures | Build official form-purpose and edge-case matrix | 2026-09-03 | — |
| WEB-007 | E0-001 | C | 保留（依存） | WEB-001, WEB-005 | — | Earnings contract implementation | Collect canary examples for all required time/accounting distinctions | 2026-09-03 | — |
| WEB-008 | E0-003 | B | 保留（依存） | WEB-001 | — | IR fallback adapter | Survey AMD/NVDA stable IR release/archive paths | 2026-09-03 | — |
| WEB-009 | E0-005 | C | 保留（依存） | WEB-001, WEB-005 | — | Segment fallback implementation | Map multi-quarter segment-source availability | 2026-09-03 | — |
| WEB-010 | E0-007 | D | 保留（依存） | WEB-007, WEB-008, WEB-009 and local contract shape | — | Local reconciliation and quality report | Prepare official comparison set after fields are stable | 2026-09-03 | — |
| WEB-011 | N0-001 | A | 未着手 | none for survey; WEB-003 for recommendation | Existing provider research must be refreshed | News-provider ADR | Identify candidates and update current price/history/rate/body-rights evidence | 2026-09-03 | — |
| WEB-012 | N0-003 | C | 保留（依存） | WEB-011 | — | Canonicalization fixtures/tests | Collect provider-relevant duplicate, syndication and correction cases | 2026-09-03 | — |
| WEB-013 | N1-001 | C | 保留（依存） | WEB-007 and I0-005 contract direction | Initial category list exists in parent plan | Taxonomy schema and extractor fixtures | Draft definitions and evidence-backed examples | 2026-09-03 | — |
| WEB-014 | N1-006 | D | 保留（依存） | WEB-008, WEB-010 and local evaluation shape | — | Recall/latency evaluation | Prepare one-to-three-month SEC/IR reference-event set | 2026-09-03 | — |
| WEB-015 | O0-001 | A | 未着手 | none | Official actor classes fixed by parent plan | O0-002 adapter design | Build official-source registry with permanent entry points | 2026-09-03 | — |
| WEB-016 | O0-002 | B | 保留（依存） | WEB-002, WEB-015 | — | Official feed adapter | Survey RSS/API/update-list behavior per source | 2026-09-03 | — |
| WEB-017 | O0-003 | C | 保留（依存） | WEB-015, WEB-016 | — | Official Fact type fixtures | Collect statement/proposal versus implementation/decision examples | 2026-09-03 | — |
| WEB-018 | O0-004 | C | 保留（依存） | WEB-001, WEB-015, WEB-017 | — | Instrument/theme relation implementation | Define evidence threshold and canary examples | 2026-09-03 | — |
| WEB-019 | O0-005 | D | 保留（依存） | WEB-016〜018 and local adapter shape | — | Official Signal quality tests | Prepare reproducible update/delete/duplicate/time fixture candidates | 2026-09-03 | — |
| WEB-020 | X0-006 | D | 保留（依存） | WEB-003, WEB-005, WEB-011, WEB-016 and local implementation evidence | — | Canary operating runbook | Draft public-constraint sections; keep untested operations marked | 2026-09-03 | — |

## 5. Parent-task handoff matrix

| Parent area | Web input | Local completion evidence required |
|---|---|---|
| W0 boundary | WEB-001〜003 | Registry/config review where applicable |
| I0 contracts | WEB-004 | Schema, history semantics and contract tests |
| S0 SEC | WEB-005/006 | Adapter, persistence, filter, document/XBRL and acceptance tests |
| E0 earnings | WEB-007〜010 | Detection, extraction, fallback, segment history and measured quality |
| N0/N1 news | WEB-011〜014 | Adapter, canonicalization, body lifecycle, extraction, retention and measured recall |
| O0 official context | WEB-015〜019 | Feed adapter, Fact typing, relationship logic and fixture tests |
| X0 integration | WEB-020 | Local timeline/API/scheduler/E2E evidence and tested runbook |

## 6. Update procedure

### Start a task

1. Fetch the latest tracker revision.
2. Confirm dependencies in the ledger.
3. Set one task to `進行中`.
4. Put the ChatGPT session identifier or a stable session label in `Session`.
5. Replace `Next action` with the bounded research action being executed.

### Finish Web research

1. Save the focused result under `docs/`.
2. Record its relative link and checked-at date in `Result / evidence`.
3. Record the exact consuming parent/local task in `Local handoff`.
4. Use `調査完了` if the result exists but handoff sufficiency is not reviewed.
5. Use `引渡し済み` only when the result is sufficient for the named local consumer.
6. Recalculate the status-count table.
7. Append one row to the session log.

### Handle uncertainty or changes

- Use `保留（依存）` when a named prerequisite is missing.
- Use `保留（外部）` for access, licence or unavailable official information.
- Use `再確認要` when terms, prices, URLs, APIs or official rules may have changed.
- Record `not stated`, `not found` or an explicit question; do not infer the missing value.
- Do not mark a parent task complete from Web research alone when local execution evidence is required.

## 7. Session log

| UTC date | Session | Web IDs | Change | Evidence / output | Next action |
|---|---|---|---|---|---|
| 2026-09-03 | Initial tracker creation | WEB-001〜020 | Created catalogue, dependency waves, status rules and handoff matrix | `REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md` | Start Wave A; recommended first bounded task is WEB-001 or WEB-005 |

## 8. Review checklist

- [ ] The latest branch revision was read before editing.
- [ ] Every changed task retains its original `WEB-*` and parent ID.
- [ ] Facts, interpretations and local completion claims remain separate.
- [ ] Official sources are linked directly and include checked-at dates.
- [ ] Unknown values are explicit.
- [ ] No credential, account identifier, provider response body or restricted article body is present.
- [ ] Point-in-time terms and prices have a recheck condition.
- [ ] Status counts match the ledger.
- [ ] The session log and next action were updated.

## 9. Related documents

- `REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md`
- `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
- `IMPLEMENTATION_PROGRESS_TRACKER_2026-09-01.md`
- `ADR_LOCAL_ANALYSIS_STACK_v0.1.md`
- `MERMAID_CONVENTIONS.md`
