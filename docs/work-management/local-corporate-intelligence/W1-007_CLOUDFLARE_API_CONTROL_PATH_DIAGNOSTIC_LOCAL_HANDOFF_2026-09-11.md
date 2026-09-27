# OrderScope — W1-007 Cloudflare API Control-Path Diagnostic Local Handoff

Status: **Ready for Local / no Live Canary activation authorized**
Date: 2026-09-11
Task: `W1-007 — Diagnose Cloudflare API authorization/control-path failure after successful W1-001 Canary evidence`

## 1. Context

The W1-001 reopen Canary collected the required 12 distinct eligible News opportunities successfully. Application-side evidence was healthy:

```text
12 distinct eligible buckets
News jobs planned/completed/failed = 13 / 13 / 0
max external = 2 / 40
max D1 = 21 / 40
Market regression = no
CPU/resource failure = no
cadence repair = live-confirmed with :30 seconds offset
News body/secret leakage = no
```

The window was rolled back because a read-only Cloudflare D1 evidence request stalled and then returned API error `7403`, preventing reliable continued monitoring/control. Final remote state is safe:

```text
WORKER_MODE=shadow
NEWS_ACQUISITION_ENABLED=false
UNIVERSE_PROFILE=canary-v0.1
rollback Worker version=16af6aeb-6818-4a09-be58-10aa7931a2de
```

W1-007 is an operations/control-plane diagnostic. Do **not** change application logic, Cron, Universe, News cadence, Worker mode, or News activation during this task.

## 2. Working hypothesis

Prioritize the Cloudflare control plane/auth path, not D1 application data semantics.

Cloudflare documents that:

- Wrangler D1 commands use the REST control plane;
- direct D1 query API requires an API token with D1 Read or D1 Write permission;
- Free-tier daily row-limit exhaustion returns dedicated row-read/row-write limit errors.

Therefore do not classify `7403` as a quota failure without separate evidence.

## 3. Diagnostic goals

Determine whether `7403` is caused by one of:

1. stale/expired/incorrect Wrangler authentication state;
2. wrong account selection;
3. API token missing D1 permission;
4. profile/environment mismatch;
5. intermittent Cloudflare control-plane/API failure;
6. command-specific D1 REST failure while Worker runtime bindings remain healthy.

Return evidence, not guesses.

## 4. Safe-state precheck

Before diagnosis:

```bash
git checkout docs/mermaid-conventions-v0.1
git pull --ff-only
git status --short
git rev-parse HEAD
```

Confirm no live mutation is needed and record the current safe remote state from the latest report.

## 5. Authentication/account checks

Run read-only identity checks first:

```bash
npx wrangler whoami
npx wrangler whoami --json
```

Record only non-secret metadata necessary for diagnosis:

```text
authenticated: yes/no
selected account name/id: <redact if shareable policy requires>
auth method/profile if shown without secret material
```

Do not print tokens, secret values, auth headers, or local credential files.

If `whoami` fails, stop remote D1 testing and classify the blocker as authentication/control-plane access.

## 6. D1 control-plane ladder

If `whoami` succeeds, test progressively:

```bash
npx wrangler d1 info orderscope-state-live-canary --env live-canary
```

Then a minimal read-only remote query:

```bash
npx wrangler d1 execute orderscope-state-live-canary \
  --env live-canary \
  --remote \
  --command="SELECT 1 AS control_path_ok;"
```

Then, only if that succeeds, a schema-only metadata query:

```bash
npx wrangler d1 execute orderscope-state-live-canary \
  --env live-canary \
  --remote \
  --command="PRAGMA table_list;"
```

Do not query News contents for this diagnostic unless needed after control-path health is proven.

For every command record:

```text
timestamp UTC/JST
command class (whoami / d1 info / SELECT 1 / PRAGMA)
success/failure
HTTP/API error code if any
elapsed time or obvious stall
```

Do not include credentials in the report.

## 7. Reproduction matrix

Run the minimal ladder at least twice if the first pass succeeds, separated by a short interval, to distinguish persistent auth/config failure from transient API behavior.

Suggested matrix:

| Attempt | whoami | d1 info | SELECT 1 | PRAGMA | 7403 | Notes |
|---|---|---|---|---|---|---|
| A | | | | | | |
| B | | | | | | |
| C if needed | | | | | | |

If 7403 reappears, stop after enough evidence to identify the failing boundary; do not keep hammering the API.

## 8. Interpretation rules

### Case A — `whoami` fails

Classification:

```text
Cloudflare auth/profile blocker
```

Next action: repair/login/token/profile outside any live Canary window, then rerun W1-007.

### Case B — `whoami` succeeds, `d1 info` fails 7403

Classification:

```text
account/token D1 control-plane authorization blocker
```

Check account selection and whether the active token/profile has D1 access. Do not alter Worker runtime.

### Case C — `d1 info` succeeds, remote `SELECT 1` fails 7403

Classification:

```text
D1 query API authorization/path blocker
```

Record exact boundary. Do not infer database corruption.

### Case D — all commands succeed repeatedly

Classification:

```text
7403 not currently reproducible; likely transient or stale auth/control state
```

This is sufficient to prepare a short monitored closeout-only or short Canary confirmation window, but does not itself authorize activation.

### Case E — quota-specific error appears

Treat separately from 7403. Capture the exact Cloudflare quota message and stop. Do not relabel it as auth failure.

## 9. Acceptance for W1-007

W1-007 may be marked `Accepted — control path restored` only if:

- `wrangler whoami` succeeds;
- target account/environment resolves as expected;
- `d1 info` succeeds;
- remote read-only `SELECT 1` succeeds;
- a schema-only query succeeds;
- at least two read-only passes complete without 7403;
- no live Worker/config mutation was required;
- final remote Worker state remains `shadow` and News disabled.

If not, return `Blocked` with the exact failing layer.

## 10. Required return report

Create/update a bounded report with:

```text
W1-007 status: Accepted | Blocked | Inconclusive
release/head commit:
whoami: pass/fail
d1 info: pass/fail
remote SELECT 1: pass/fail
PRAGMA table_list: pass/fail
attempt count:
7403 reproduced: yes/no
quota error observed: yes/no
selected environment: live-canary
Worker mode changed: no
News activation changed: no
Cron changed: no
D1 mutation performed: no
final diagnosis:
next gate:
```

Update `LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md` so the active W1-001 blocker is the Cloudflare control-path issue, not the already-fixed cadence predicate.

## 11. Next CP after W1-007

If control path is restored:

```text
W1-007 Accepted
  -> Web review of control-path evidence
  -> short monitored W1-001 confirmation/closeout window
  -> W1-001 final live acceptance decision
  -> full-v0.1 activation review (separate gate)
```

If still blocked:

```text
W1-007 Blocked
  -> fix Cloudflare auth/account/token/profile path
  -> rerun read-only diagnostic
```

No full-v0.1 activation is authorized by this handoff.
