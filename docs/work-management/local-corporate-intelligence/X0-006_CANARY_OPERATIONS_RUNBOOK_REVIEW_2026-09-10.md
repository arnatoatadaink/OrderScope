# OrderScope — X0-006 Canary Operations Runbook Review

Status: **Review completed — accepted for fixture-path / follow-ups assigned**
Date: 2026-09-10
Task: `X0-006`
Reviewed document: `X0-006_CANARY_OPERATIONS_RUNBOOK_2026-09-10.md`

## 1. Review conclusion

The runbook is consistent with the current v0.1 safety and responsibility boundaries. It adequately documents the required operational policy topics: credentials, provider-rate handling, stop/resume, bounded reprocessing, temporary-content deletion, backup/restore, and incident decisions.

It is suitable as the policy-level procedure for the current fixture-path integration boundary. No contradiction was found with the implemented localhost, configuration, scheduler, retention, or Worker/D1 separation contracts.

It is not yet a fully executable production operations procedure. Four implementation or documentation gaps remain. Those gaps are explicitly assigned to post-X0 follow-up work and do not block X0-006 fixture-path acceptance.

## 2. Confirmed alignment

The following runbook statements match the current implementation and accepted handoffs:

- WSL2 is the sole mutable-data writer and the operational data root must be WSL-native.
- HTTP is read-only and bound to literal `127.0.0.1`.
- Mutating operations remain CLI-only.
- The registered Alpaca secret names and the logging redaction boundary match `orderscope_local.config`.
- Scheduler execution is bounded, single-instance, and supports job-boundary `--resume-after` selection.
- Provider cursors remain adapter-owned and opaque to the scheduler.
- Reprocessing preserves provenance and immutable/content-addressed artifacts.
- Successful News bodies are due for immediate deletion, while exception bodies have a maximum 30-day retention boundary.
- Worker mutation and real D1 operations remain separately gated and are not authorized by X0-006.

## 3. Findings and disposition

### F1 — Scheduler commands currently select no operational jobs

Severity: **Operational limitation / documentation clarification**

The documented scheduler commands and options exist, but the current CLI invokes `run_scheduler(jobs=())`. Therefore `schedule run`, `--dry-run`, and `--resume-after` do not currently operate on a registered live plan.

Disposition:

- X0-006 remains accepted as a policy/fixture boundary.
- A successful zero-job scheduler result must not be interpreted as evidence that acquisition, retention, or another intended workload ran.
- Executable live-job registration belongs to reviewed owning adapter/integration tasks and is tracked as post-X0 follow-up `PX0-001`.

### F2 — Durable completion evidence and stale-lock verification are not executable procedures

Severity: **Recovery gap**

The runbook correctly requires resume from the last fully completed job and prohibits blind lock deletion. The generic scheduler does not yet persist durable run completion history, and stale-lock inspection lacks a reproducible operator command/procedure.

Disposition:

- X0-006 remains accepted at policy level.
- Until durable run evidence exists, resume/stale-lock clearance requires manual engineering review and adapter/checkpoint evidence; operators must not infer completion from process output alone or blindly remove a lock.
- Durable scheduler run metadata and stale-lock recovery are tracked as `PX0-002`.
- Existing `I0-003` remains the provider/source cursor/checkpoint contract and is not redefined by this follow-up.

### F3 — Retention and reprocessing checks have no operator command path

Severity: **Operational verification gap**

The retention and reprocessing policies are consistent with accepted contracts, but the supported CLI does not yet expose backlog inspection, overdue detection, deletion/retry, or bounded replay commands.

Disposition:

- X0-006 remains accepted at policy level.
- Relevant pre/post-run checklist items are programmatic/fixture-verification statements until operator commands exist.
- Concrete retention/reprocessing operator commands and storage deletion integration are tracked as `PX0-003`.
- Existing `N1-005` retention-controller acceptance remains valid and is not reopened.

### F4 — Backup/restore is policy-level rather than reproducible

Severity: **Recovery procedure gap**

The backup scope and safety principles are appropriate, but exact data-layout, snapshot, hash/manifest, destination, retention/RPO, restore-validation, and restore-drill procedures are not yet executable and reproducible.

Disposition:

- X0-006 remains accepted as a Canary policy runbook, not as a production disaster-recovery runbook.
- Reproducible backup/restore implementation and drills are tracked independently as `PX0-004`.

## 4. Acceptance decision

`X0-006` is accepted for its WBS completion criterion: a policy-level Canary operations runbook for the current fixture-path integration boundary.

This acceptance means:

```text
X0-001..006 fixture-path integration lane = complete
```

It does **not** mean production operations or disaster recovery are complete. In particular, F1–F4 remain explicit post-X0 work.

This decision does not authorize remote D1 operations, Worker mutation, live-provider job registration, or any separately gated change window.

## 5. Follow-up authority

The disposition and completion boundaries for F1–F4 are recorded in:

`POST_X0_OPERATIONAL_FOLLOWUPS_2026-09-10.md`

The existing 2026-09-03 WBS contains adjacent contracts (`I0-003`, `N1-005`) but no task whose completion condition fully covers these four operational gaps. The `PX0-*` identifiers are therefore non-normative post-X0 tracking IDs until a future WBS revision formally incorporates or remaps them.

## 6. Evidence inspected

- `docs/work-management/local-corporate-intelligence/X0-006_CANARY_OPERATIONS_RUNBOOK_2026-09-10.md`
- `docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`
- `docs/work-management/local-corporate-intelligence/X0-005_WEB_IMPLEMENTATION_HANDOFF_2026-09-10.md`
- `docs/work-management/local-corporate-intelligence/N1-005_WEB_IMPLEMENTATION_HANDOFF_2026-09-09.md`
- `analysis/app/orderscope_local/cli.py`
- `analysis/app/orderscope_local/config.py`
- `analysis/app/orderscope_local/integration/scheduler.py`
- `analysis/app/orderscope_local/news/retention.py`
