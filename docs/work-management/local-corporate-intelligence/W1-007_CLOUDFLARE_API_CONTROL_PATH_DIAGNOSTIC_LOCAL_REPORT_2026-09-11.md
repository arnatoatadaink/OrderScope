# OrderScope — W1-007 Cloudflare API Control-Path Diagnostic Local Report

Status: **Accepted — control path restored**
Date: 2026-09-11 JST
Task: `W1-007 — Diagnose Cloudflare API authorization/control-path failure after successful W1-001 Canary evidence`
Release/head commit: `1e489a6d98f88ba9ade33a4ddda9eb3ede31e266`
Branch: `docs/mermaid-conventions-v0.1`
Environment: `live-canary`
Handoff: `W1-007_CLOUDFLARE_API_CONTROL_PATH_DIAGNOSTIC_LOCAL_HANDOFF_2026-09-11.md`

## 1. Disposition

The Cloudflare D1 control path completed two consecutive read-only diagnostic
passes without API error `7403`, quota errors, or a command stall. Wrangler
identity resolution, D1 resource metadata, a minimal remote query, and a
schema-only query all succeeded against the expected `live-canary` account and
database.

The earlier `7403` is not currently reproducible. The bounded evidence supports
classification as a likely transient or stale authentication/control-plane
state, rather than a D1 data-semantic, database-corruption, or quota failure.
This diagnostic cannot distinguish transient Cloudflare API behavior from a
stale OAuth/control state that recovered before the test.

No application, Worker configuration, Cron, Universe, News cadence, activation,
secret, or D1 data mutation was performed.

## 2. Identity and target resolution

Wrangler `4.127.1` reported an authenticated OAuth session. The selected account
matched the configured live-canary account, and the reported OAuth scopes
included D1 write access (therefore also sufficient for the tested reads).
Personal identity and full account identifiers are intentionally omitted from
this report.

The target resolved consistently as:

```text
environment: live-canary
database: orderscope-state-live-canary
database binding: STATE_DB
database identifier: 03c85865-...-260a6
region: APAC
```

## 3. Reproduction matrix

All timestamps are UTC. Add nine hours for JST. Elapsed time includes Wrangler
startup and control-plane round trips; the SQL engine durations were below one
millisecond in both passes.

| Attempt | Start UTC | whoami | d1 info | SELECT 1 | PRAGMA table_list | 7403 | Notes |
|---|---|---:|---:|---:|---:|---|---|
| A | 2026-09-11 14:30 | pass (8.06 s; JSON 6.46 s) | pass (6.75 s) | pass (5.66 s) | pass (5.85 s) | no | `control_path_ok=1`; query metadata reported zero rows written |
| B | 2026-09-11 14:32:39 | pass (6.89 s) | pass (6.71 s) | pass (5.83 s) | pass (5.83 s) | no | Same account/database boundary; query metadata reported zero rows written |

The apparent 30-second tool duration during each grouped pass was the sum of
sequential successful Wrangler calls, not an individual stalled API request.

## 4. Safe-state verification

At `2026-09-11T14:33:22Z`, read-only deployment status still reported rollback
version `16af6aeb-6818-4a09-be58-10aa7931a2de`. At
`2026-09-11T14:33:29.551Z`, `/health` returned:

```text
ok=true
mode=shadow
status=shadow
News mode=disabled
News planned/selected/completed/failed=0/0/0/0
```

The checked-in and previously reported remote baseline remains
`UNIVERSE_PROFILE=canary-v0.1`, `NEWS_ACQUISITION_CADENCE_MINUTES=5`, and
Cron `* * * * *`. This task made no deployment or configuration change.

## 5. Required return summary

```text
W1-007 status: Accepted — control path restored
release/head commit: 1e489a6d98f88ba9ade33a4ddda9eb3ede31e266
whoami: pass
d1 info: pass
remote SELECT 1: pass
PRAGMA table_list: pass
attempt count: 2
7403 reproduced: no
quota error observed: no
selected environment: live-canary
Worker mode changed: no
News activation changed: no
Cron changed: no
D1 mutation performed: no
final diagnosis: 7403 not currently reproducible; likely transient or stale OAuth/control-plane state, with the exact recovered cause not distinguishable from current evidence
next gate: Web review of W1-007 evidence, then separately authorized short monitored W1-001 confirmation/closeout window
```

This acceptance restores the read-only control-path gate only. It does not
authorize another Canary activation or `full-v0.1` activation.
