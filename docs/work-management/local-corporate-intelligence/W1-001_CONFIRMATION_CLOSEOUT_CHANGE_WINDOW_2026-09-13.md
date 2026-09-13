# OrderScope — W1-001 Confirmation / Closeout Change Window

Status: **Ready — remote execution requires explicit authorization**
Date: 2026-09-13 JST
Task: `W1-001 — short monitored AMD/NVDA News Canary confirmation/closeout`
Environment: `live-canary`
Depends on:
- W1-006 cadence repair live-evidence-confirmed;
- W1-007 local diagnostic Accepted;
- W1-007 Web review Accepted;
- current repository branch synchronized at or after `f6aa33f`.

## 1. Objective

Confirm that the already-proven AMD/NVDA metadata-only News Canary can be briefly re-enabled while the Cloudflare control path remains continuously usable, then return to the safe baseline and complete closeout evidence.

This is not a second full performance Canary. The previous reopen already collected 12 distinct eligible five-minute opportunities, 13/13 News job completion, maximum external `2/40`, maximum D1 `21/40`, one canonical NVDA article, duplicate handling, and safe rollback. This window should be deliberately shorter and bounded.

## 2. Frozen scope

```text
environment: live-canary
Worker baseline: shadow
News baseline: disabled
Universe: canary-v0.1
News symbols: AMD,NVDA
News content: metadata only
News cadence: 5 minutes
Cron: * * * * *
external ceiling: 40 / invocation
D1 ceiling: 40 / invocation
```

No scope expansion is allowed inside the window.

## 3. Pre-window local acceptance

Run before any remote mutation:

```bash
git checkout docs/mermaid-conventions-v0.1
git pull --ff-only origin docs/mermaid-conventions-v0.1
git status --short
git rev-parse HEAD

npm test
npm run typecheck
npm run cf-typegen
npm run deploy:check -- --env live-canary
git diff --check
```

Required result:

- working tree clean;
- full TypeScript suite passes;
- typecheck passes;
- Cloudflare type generation passes;
- named-environment dry-run passes;
- no unreviewed configuration delta is required.

Stop before remote mutation if any requirement fails.

## 4. Read-only remote preflight

The following are read-only checks and may be collected before opening the mutation window:

```bash
npx wrangler whoami
npx wrangler d1 info orderscope-state-live-canary --env live-canary
npx wrangler d1 execute STATE_DB --env live-canary --remote --command "SELECT 1 AS control_path_ok"
npx wrangler d1 execute STATE_DB --env live-canary --remote --command "PRAGMA table_list"
npx wrangler deployments list --env live-canary
```

Also verify through the deployed read-only health endpoint that:

```text
WORKER_MODE=shadow
NEWS_ACQUISITION_ENABLED=false
UNIVERSE_PROFILE=canary-v0.1
NEWS_ACQUISITION_CADENCE_MINUTES=5
NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
Cron=* * * * *
```

Do not record secret values.

### Preflight hard stop

Do not open the live mutation window if any of the following occurs:

- `7403`, auth, quota, or repeated control-path timeout;
- D1 binding/database mismatch;
- Worker not in Shadow;
- News already enabled unexpectedly;
- unexpected migration requirement;
- Cron/Universe/cadence/symbol drift;
- dry-run differs materially from reviewed config.

## 5. Mutation window — authorization boundary

The following section is **not authorized merely by this document**. Execute only after explicit user/operator approval of this W1-001 change window.

Only the reviewed activation pair may change:

```text
WORKER_MODE: shadow -> live
NEWS_ACQUISITION_ENABLED: false -> true
```

Keep all other variables unchanged.

Do not modify Cron, Universe, cadence, page limits, budgets, D1 schema, News body behavior, or symbol scope.

Record:

- pre-window active Worker version;
- activation version;
- activation timestamp UTC/JST.

## 6. Required observation

Observe at least **3 distinct eligible five-minute News opportunities** unless a hard-stop condition fires first.

Three opportunities are sufficient for this closeout because the prior reopen already established 12 distinct successful opportunities. The closeout is specifically testing control-path continuity plus repeatability of the accepted behavior.

For each reviewed eligible opportunity capture:

```text
scheduled timestamp
News planned / selected / completed / failed
Market planned / completed / failed
external subrequests / 40
D1 queries / 40
withinBudget
News pages
article observations / inserted / updated / duplicate / conflict
Market regression indicator
Worker exception / CPU / exceeded-resource indicator
```

At least once during the active window, re-run a read-only D1 control query:

```bash
npx wrangler d1 execute STATE_DB --env live-canary --remote --command "SELECT 1 AS control_path_ok"
```

If a safe, bounded metadata query already used by the prior Canary exists, use it to verify current News checkpoint/article/membership state. Do not improvise an unreviewed write query.

## 7. Acceptance criteria

All applicable criteria must pass:

1. At least 3 distinct eligible five-minute opportunities are observed.
2. Eligible buckets plan and complete News work; ineligible minutes do not create phantom News work.
3. News remains AMD/NVDA metadata-only.
4. No News body or credential leakage is observed.
5. Every reviewed invocation remains `external <= 40` and `D1 <= 40`.
6. No Market false checkpoint advance or other Market regression appears.
7. Cloudflare control-path read succeeds during the active window.
8. No repeated Worker CPU/resource/exception failure occurs.
9. Rollback to the safe baseline is successful and independently verified.

A new article is not required for closeout. If no new article arrives, stable empty-result execution is acceptable as long as the runtime/control/rollback criteria above are satisfied.

## 8. Immediate rollback / hard stop

Rollback immediately if:

- control-path read fails or stalls beyond normal command latency and cannot be promptly re-established;
- API authorization error `7403` recurs;
- combined budget attempts to cross a ceiling;
- Market path regresses;
- News false-completes after provider/control failure;
- unauthorized symbols appear;
- News body, credentials, or auth headers leak;
- unexpected destructive D1 behavior occurs;
- continuing would require an unreviewed config/code/schema change.

Do not troubleshoot by changing Cron/cadence/budget/scope inside the active window.

## 9. Mandatory safe closeout

Regardless of whether the active observation passes, finish the reviewed window in the safe baseline unless a later production activation is separately authorized:

```text
WORKER_MODE=shadow
NEWS_ACQUISITION_ENABLED=false
UNIVERSE_PROFILE=canary-v0.1
NEWS_ACQUISITION_CADENCE_MINUTES=5
NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
Cron=* * * * *
```

After rollback verify:

- `/health` reports Shadow and News disabled;
- at least one subsequent scheduled invocation has zero News provider acquisition/mutation;
- `wrangler deployments list --env live-canary` shows the expected final deployment;
- remote `SELECT 1` succeeds;
- no unexpected D1 mutation is required for closeout.

## 10. Final disposition

Choose exactly one:

```text
ACCEPTED
  = three eligible opportunities pass, control path stays usable, and rollback is verified.

INCONCLUSIVE
  = no hard safety failure, but the minimum observation/control evidence is not obtained.

ROLLED_BACK
  = a hard stop occurs and safe rollback is completed.

BLOCKED
  = a new reviewed code/config/schema/authorization change is required before retry.
```

## 11. Required report fields

```text
release commit:
pre-window Worker version:
activation version:
rollback/final version:
window UTC/JST:
eligible opportunities observed:
News jobs planned/completed/failed:
max external/tick:
max D1/tick:
control-path checks before/during/after:
7403 observed: yes/no
Market regression observed: yes/no
CPU/resource failure observed: yes/no
News body persisted: no
secret leakage observed: no
final Worker mode:
final News state:
final Universe:
final Cron:
final disposition:
reason:
```

Update the integrated Progress Tracker after closeout. Do not use this window to open `SMOKE-007`, apply migration `0008`, or start remote D1 drain/purge work.
