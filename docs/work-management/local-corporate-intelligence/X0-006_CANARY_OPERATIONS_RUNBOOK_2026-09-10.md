# OrderScope — X0-006 Canary Operations Runbook

Status: **Provisional result — runbook drafted / operator review pending**
Date: 2026-09-10
Task: `X0-006`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `X0-005`

## 1. Purpose

This runbook defines the v0.1 operating procedure for the Local Corporate Intelligence Canary. It covers credentials, provider-rate handling, startup/stop/resume, bounded reprocessing, retention/deletion, backup, and incident decisions.

It does **not** authorize:

- remote D1 export or `SMOKE-007` execution;
- Cloudflare Worker mutation or mode changes;
- HTTP-triggered import, provider, scheduler, retention, or reprocessing jobs;
- API exposure beyond literal `127.0.0.1`;
- storing provider/news raw bodies, credentials, or unrestricted local paths in API responses, logs, dumps, manifests, or Git;
- automatic live-provider job registration that has not been reviewed by its owning adapter task.

Worker remains Shadow and Local remains observational/analytical.

## 2. Supported execution boundary

Authoritative runtime:

- WSL2 is the sole Python runtime and mutable-data writer.
- Persistent SQLite/DuckDB/Parquet/raw/import/lock state uses a WSL-native filesystem path.
- Source checkout may remain on a Windows-mounted path for development, but operational `ORDERSCOPE_DATA_ROOT` must not point at `/mnt/c`, `/mnt/d`, OneDrive, a Windows network share, or another synchronised folder.
- Local HTTP binds only to literal `127.0.0.1`.
- Mutating operations remain CLI-only.

Minimum startup prerequisites:

```bash
uv sync --locked
export ORDERSCOPE_DATA_ROOT="$HOME/.local/share/orderscope"
```

Use a different WSL-native path if desired, but do not commit it.

## 3. Credentials and non-secret configuration

### 3.1 Non-secret environment

Supported non-secret names:

```text
ORDERSCOPE_DATA_ROOT
ORDERSCOPE_LOG_LEVEL
ORDERSCOPE_SEC_USER_AGENT
```

`ORDERSCOPE_SEC_USER_AGENT` is operational identity metadata, not a password/token. Populate it only with the identity/contact format required by the current SEC access policy.

### 3.2 Secret environment

Registered v0.1 provider credentials:

```text
ORDERSCOPE_SECRET_ALPACA_API_KEY
ORDERSCOPE_SECRET_ALPACA_API_SECRET
```

Rules:

1. Keep secrets in the WSL process/session environment or another Git-excluded local mechanism.
2. Never place secrets in committed config, shell history examples with real values, CLI arguments, test fixtures, manifests, API payloads, database rows, or incident screenshots.
3. Adapters read only explicitly registered secret names at point of use.
4. Missing credentials fail closed.
5. Logging must use `LocalConfig.log_fields()` or the secret-redaction boundary; do not dump `os.environ` directly.
6. Rotate a credential immediately if a real value is suspected to have reached Git, logs, screenshots, issue comments, or a durable artifact.

## 4. Provider rate limits and access conditions

Provider limits and commercial terms are point-in-time operational facts. Do not hard-code assumptions from old research into incident handling.

Before enabling or materially changing a live adapter:

1. Recheck the provider's current official rate/access terms.
2. Record the checked date and source in the provider/terms verification sheet.
3. Confirm required User-Agent/contact requirements.
4. Confirm storage/body-use/redistribution rights.
5. Confirm account/plan-specific rate limits where applicable.

At runtime:

- treat rate-limit responses as bounded/retryable according to the adapter's provider-neutral error contract;
- do not increase concurrency or poll cadence merely to catch up faster;
- preserve partial/error/checkpoint state rather than presenting incomplete results as complete;
- use the scheduler's bounded-run limit and resume at job boundaries;
- provider cursors remain opaque and adapter-owned.

Repeated rate limiting, authorization failure, or upstream-contract-change errors are stop conditions for that adapter until reviewed.

## 5. Normal startup

### 5.1 Read-only API

```bash
uv run orderscope serve
```

Expected boundary:

- literal `127.0.0.1` only;
- no `--host` override;
- read-only routes only;
- no scheduler/import/provider mutation via HTTP.

Before leaving the API running unattended, verify `/health` locally and confirm no external bind exists.

### 5.2 Scheduler

Scheduler start is manual CLI only:

```bash
uv run orderscope schedule run --max-jobs <N>
```

For a no-execution plan check:

```bash
uv run orderscope schedule run --max-jobs <N> --dry-run
```

Do not interpret an empty built-in job registry as a failure; live jobs are registered only by reviewed owning tasks.

## 6. Stop, interruption, and resume

### 6.1 Normal stop

For the serving process, normal interactive stop is `Ctrl+C`.

For bounded scheduler runs, prefer allowing the current explicit job to finish. Forced termination is not the normal stop path.

### 6.2 Interrupted scheduler run

After interruption:

1. Determine the last fully completed job from durable run/checkpoint evidence; never infer completion from a partially written output.
2. Confirm no stale scheduler process still owns the runtime.
3. Confirm the scheduler lock is not legitimately held by another active process.
4. Resume only from a known completed job boundary:

```bash
uv run orderscope schedule run --max-jobs <N> --resume-after <completed-job-name>
```

5. Do not manually edit provider cursors to force progress.
6. If the completion boundary is ambiguous, stop and re-run from an earlier safe idempotent boundary rather than skipping forward.

### 6.3 Lock handling

A present scheduler lock means "already running" until proven otherwise.

Do not blindly delete a lock file. First verify that no live OrderScope scheduler process owns it. If a stale lock is confirmed after a crash, record the incident and remove only that stale lock before a bounded restart.

## 7. Reprocessing policy

Reprocessing must be explicit, bounded, deterministic where the source contract permits, and must preserve provenance.

Allowed v0.1 patterns:

- fixture replay for validation;
- idempotent import of the same immutable artifact/hash;
- bounded adapter window replay using accepted checkpoint/idempotency contracts;
- deterministic Fact/timeline regeneration from unchanged accepted inputs;
- retention reevaluation for still-existing temporary-content metadata.

Do not:

- overwrite immutable raw/content-addressed artifacts in place;
- fabricate missing source values;
- collapse update/conflict/duplicate distinctions;
- reprocess an unbounded history because a narrow catch-up failed;
- use a live remote D1 export unless the separate L1-003 / `SMOKE-007` approval window is open.

Before reprocessing, record:

```text
reason
source/adapter
bounded window or fixture revision
starting checkpoint/job boundary
expected outputs
rollback/stop condition
```

After reprocessing, compare counts/hashes/Fact identities/quality results as appropriate before treating the result as accepted.

## 8. Temporary-content retention and deletion

News body content is temporary and is not durable Fact Store data.

Rules:

- successful extraction content is due for deletion immediately after extraction succeeds;
- exception content must expire within 30 days;
- durable metadata, Fact/Evidence, and deletion proof may remain;
- deletion proof must not contain secret-like material;
- a failed delete must not fabricate `DELETED` state;
- already-deleted content is idempotent and should not be deleted again;
- raw/news bodies must not be exposed by the localhost API.

If deletion fails:

1. keep the content state non-deleted;
2. record a sanitized failure state/reason;
3. retry under the retention controller's bounded policy;
4. escalate before an exception body reaches mandatory expiry;
5. never copy the body into an incident ticket to preserve it.

A body at/past mandatory exception expiry is an incident requiring immediate cleanup and review.

## 9. Backup and restore

### 9.1 What to back up

Back up durable/reconstructable Local state deliberately from the WSL filesystem:

- SQLite operational metadata/catalog;
- accepted versioned migrations/config schemas;
- immutable imported raw artifacts that policy permits retaining;
- curated Parquet datasets and manifests/hashes;
- source/checkpoint/quality/run metadata;
- durable Fact/Evidence/relationship/derived records;
- deletion audit metadata/proofs.

Do **not** include:

- provider credentials;
- active lock files;
- temporary successful news bodies awaiting immediate deletion;
- exception bodies beyond their allowed retention;
- cache files that can be rebuilt unless explicitly useful for recovery.

### 9.2 Consistent backup procedure

1. Stop mutating CLI/scheduler activity or otherwise guarantee a quiescent snapshot.
2. Ensure no SQLite/DuckDB/catalog writer remains active.
3. Copy to a temporary backup location on a suitable filesystem.
4. Hash backup artifacts/manifests where applicable.
5. Atomically publish/rename the completed backup set.
6. Record backup time, application revision, schema/migration revision, and hashes.

### 9.3 Restore procedure

1. Restore into a new WSL-native data root; do not overwrite the only working copy first.
2. Verify hashes/manifests.
3. Rebuild/validate SQLite migration state and rebuildable analytical catalog as applicable.
4. Run local quality checks and read-only API validation before switching the operational data root.
5. Never restore expired temporary content merely because it exists in an old backup.

## 10. Incident decision table

| Condition | Immediate action | Resume condition |
|---|---|---|
| Missing/invalid credential | Stop affected adapter; do not log value | Credential corrected/rotated and local secret boundary revalidated |
| Repeated rate limiting | Stop increasing load; preserve checkpoint/partial state | Current provider limits reviewed; bounded cadence approved |
| Authorization/terms uncertainty | Stop affected provider use | Official terms/account permission rechecked |
| Upstream contract/schema change | Stop adapter and mark incomplete/error | Adapter updated and contract tests pass |
| Duplicate/conflict anomaly | Stop promotion of affected records | Identity/update/conflict classification reviewed |
| Scheduler lock conflict | Do not start second scheduler | Existing owner exits or stale lock is proven and cleared |
| Job crash/partial output | Preserve evidence; do not skip ahead | Last complete idempotent/job boundary identified |
| Retention deletion failure | Keep non-deleted state; sanitize diagnostics | Delete succeeds before mandatory expiry |
| Exception body at/past expiry | Immediate cleanup + incident review | Body deleted and retention cause reviewed |
| Suspected secret leakage | Stop use of credential and rotate | Leak source removed/contained and new credential installed |
| SQLite/DuckDB corruption suspicion | Stop writes; preserve copy | Restore/rebuild validated on separate data root |
| API external-bind attempt | Reject configuration; stop process | Literal `127.0.0.1` restored and verified |
| Remote D1 action requested outside window | Do not execute | Separate L1-003/`SMOKE-007` approval granted |
| Worker mutation requested from Local | Do not execute | Separate Worker change process authorizes it |

## 11. Pre-run checklist

Before a canary run:

```text
[ ] Worker remains Shadow
[ ] no remote D1 change window is being implied
[ ] WSL2 is the sole writer
[ ] ORDERSCOPE_DATA_ROOT is WSL-native
[ ] secrets are process-local/Git-excluded
[ ] current provider terms/rate assumptions are known for enabled adapters
[ ] scheduler plan is bounded
[ ] dry-run used when changing the plan
[ ] no second scheduler instance is active
[ ] temporary-content retention backlog is within policy
[ ] recent backup/restore path is known
```

## 12. Post-run checklist

After a canary run:

```text
[ ] selected/completed jobs are recorded
[ ] checkpoint/partial/error state is inspectable
[ ] Fact/Evidence outputs pass their validation boundaries
[ ] timeline/coverage reflects only accepted/as-of-visible records
[ ] successful temporary bodies are deleted
[ ] exception content is below mandatory expiry
[ ] no secret/raw body appeared in logs or API output
[ ] no unexpected Worker/D1 mutation occurred
[ ] anomalies are recorded before the next run
```

## 13. Current v0.1 limits

The following remain separate from X0-006 completion:

- `L1-003` real D1 export under the separately approved `SMOKE-007` window;
- `L1-006` read-only import/dataset API;
- `N1-006` news recall/quality evaluation;
- provisional `A0-001` and separate `A0-002` validation work;
- dependency-maintenance cleanup for FastAPI/Starlette/AnyIO warnings.

This runbook does not convert any of those items into completed work.

## 14. X0-006 completion mapping

| WBS requirement | Runbook section |
|---|---|
| credentials | §3 |
| rate limits | §4 |
| stop/resume | §6 |
| reprocessing | §7 |
| deletion | §8 |
| backup | §9 |
| incident decisions | §10 |

All requested operational topics are explicitly documented. Operator review is the remaining acceptance step.
