# OrderScope — X0-006 Canary Operations Runbook Review

Status: **Review completed — follow-up disposition pending**
Date: 2026-09-10
Task: `X0-006`
Reviewed document: `X0-006_CANARY_OPERATIONS_RUNBOOK_2026-09-10.md`

## 1. Review conclusion

The runbook is consistent with the current v0.1 safety and responsibility boundaries. It adequately documents the required operational policy topics: credentials, provider-rate handling, stop/resume, bounded reprocessing, temporary-content deletion, backup/restore, and incident decisions.

It is suitable as the policy-level procedure for the current fixture-path integration boundary. No contradiction was found with the implemented localhost, configuration, scheduler, retention, or Worker/D1 separation contracts.

It is not yet a fully executable production operations procedure. Four implementation or documentation gaps remain. Their disposition—address under X0-006 or defer to owning follow-up tasks—requires a separate decision.

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

## 3. Findings requiring disposition

### F1 — Scheduler commands currently select no operational jobs

Severity: **Operational limitation / documentation clarification**

The documented scheduler commands and options exist, but the current CLI invokes `run_scheduler(jobs=())`. Therefore `schedule run`, `--dry-run`, and `--resume-after` do not currently operate on a registered live plan.

The runbook acknowledges that the built-in registry may be empty, but it should explicitly state that the current command is a boundary/contract surface until reviewed owning adapter tasks register jobs. An operator must not interpret a successful zero-job result as proof that an intended acquisition or retention workload ran.

Possible disposition:

- clarify the current no-job operational limit in X0-006; or
- defer executable job registration and job-specific commands to each owning adapter/integration task.

### F2 — Durable completion evidence and stale-lock verification are not executable procedures

Severity: **Recovery gap**

The runbook correctly requires resume from the last fully completed job and prohibits blind lock deletion. It does not specify the evidence store, query/inspection command, or record format used to identify the last completed job.

The scheduler result is currently returned in process memory, and the generic scheduler layer does not itself persist run completion history. The lock contains a PID, but the runbook does not define the exact inspection procedure, PID-reuse consideration, or the precise lock path derived from `ORDERSCOPE_DATA_ROOT`.

Possible disposition:

- add exact evidence and lock-inspection commands after durable run metadata is implemented; or
- state that resume/stale-lock clearance requires adapter-owned evidence and manual engineering review until that capability exists.

### F3 — Retention and reprocessing checks have no operator command path

Severity: **Operational verification gap**

The retention and reprocessing policies are consistent with the accepted contracts, but the current CLI exposes no retention backlog, deletion/retry, overdue detection, or reprocessing command. As a result, the pre/post-run checklist items cannot yet be independently executed by an operator through the supported CLI.

The retention controller is presently a storage-neutral library boundary using an injected deleter; a concrete storage deleter remains outside that implementation.

Possible disposition:

- defer concrete deletion, backlog inspection, and replay commands to the owning News/integration tasks; and
- mark the relevant checklist items as programmatic/fixture verification until those commands exist.

### F4 — Backup/restore is policy-level rather than reproducible

Severity: **Recovery procedure gap**

The backup scope and safety principles are appropriate, but the procedure does not yet define:

- the exact data-root layout and included paths;
- a concrete SQLite snapshot method;
- DuckDB/Parquet/catalog consistency checks;
- manifest format and required hashes;
- backup destination permissions/encryption;
- retention generations, schedule, or recovery-point objective;
- exact restore validation commands and acceptance evidence;
- a restore-drill frequency or owner.

Without these details, two operators can produce materially different backup sets, and successful restoration is not reproducible from the runbook alone.

Possible disposition:

- keep X0-006 explicitly policy-level and create an owning backup/restore implementation task; or
- add a tested, data-layout-specific backup and restore appendix before treating it as a disaster-recovery runbook.

## 4. Acceptance recommendation

X0-006 may be accepted if its intended completion criterion is a policy-level Canary procedure for the current fixture-path integration boundary, provided the four findings above are recorded as explicit limitations or follow-up work.

X0-006 should not be represented as a complete production recovery runbook until F2–F4 have executable, tested procedures and F1 has an operational job registry.

This review does not authorize remote D1 operations, Worker mutation, live-provider job registration, or implementation changes. The owner must separately decide whether each finding remains in X0-006 or moves to a follow-up task.

## 5. Evidence inspected

- `docs/work-management/local-corporate-intelligence/X0-006_CANARY_OPERATIONS_RUNBOOK_2026-09-10.md`
- `docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`
- `docs/work-management/local-corporate-intelligence/X0-005_WEB_IMPLEMENTATION_HANDOFF_2026-09-10.md`
- `docs/work-management/local-corporate-intelligence/N1-005_WEB_IMPLEMENTATION_HANDOFF_2026-09-09.md`
- `analysis/app/orderscope_local/cli.py`
- `analysis/app/orderscope_local/config.py`
- `analysis/app/orderscope_local/integration/scheduler.py`
- `analysis/app/orderscope_local/news/retention.py`
