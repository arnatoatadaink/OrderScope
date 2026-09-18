# OrderScope — L1-003 / SMOKE-007 Execution Report

Status: **INCONCLUSIVE — Phase A accepted; market-open Phase B pending**
Date: 2026-09-15 JST
Branch: `docs/mermaid-conventions-v0.1`
Environment: `live-canary`
Change window: `L1-003_SMOKE-007_REAL_D1_EXPORT_CHANGE_WINDOW_2026-09-14.md`

## 1. Final disposition

The explicitly authorized window completed the bounded remote-D1 export and local
custody/quality portion without remote mutation. The frozen one-row source range
was read twice and produced identical canonical bytes, manifest identity, and
custody identity. A final source query confirmed that the range remained one row.

Phase B was not activated because the window reached the US market closed period.
The only continuously tradable checkpoint, BTCUSD, already had an older `PARTIAL`
gap before this window. Activating it could not distinguish fresh catch-up caused
by this pause from pre-existing recovery work. That does not meet SMOKE-007's
requirement for a fresh bounded gap created by the recorded pause.

The final disposition is `INCONCLUSIVE`, not `ROLLED_BACK`: no hard safety failure
occurred and no Worker mutation needed rollback. The Worker remained at the safe
baseline throughout.

## 2. Frozen scope and release

```text
release commit: 12cec24904737f9d28fd8f3df1dce31ae95cfdb7
pre-window Worker version: f6b35356-a7c2-40ed-8bbb-7b957f4ead11
final Worker version: f6b35356-a7c2-40ed-8bbb-7b957f4ead11
environment: live-canary
source DB: orderscope-state-live-canary
source DB id: 03c85865-1aa3-4b0c-b219-18987cd260a6
source table: normalized_bar
export start inclusive: 2026-09-01T16:03:00.000Z
export end exclusive: 2026-09-01T16:04:00.000Z
Worker mode: shadow
News: disabled
Universe: canary-v0.1
Cron: unchanged
schema: unchanged
purge: forbidden / not performed
```

## 3. Window timing

```text
pause/window start UTC: 2026-09-15T00:01:38.256Z
pause/window start JST: 2026-09-15T09:01:38.258+09:00
Phase A closeout UTC: 2026-09-15T01:50:50.938Z
Phase A closeout JST: 2026-09-15T10:50:50.940+09:00
resume time: not executed
```

The checked-in and deployed runtime was already Shadow. That state was adopted as
the explicit pause boundary rather than performing a redundant deployment.

## 4. Export and custody evidence

```text
source row count: 1
artifact bytes: 581
artifact SHA-256: de380ae35c1ab50f5e0364585e7f3224512085dc3bcd4abff8e37631938bed56
export manifest: d1-export-db1b04ee1e3edd5f96a0c953f7f99f7ebb9876544fa8099ec2dc660127ac9b41
custody manifest: d1-custody-f25ccf63c856392778401be630ef36a2ce91610d1f696a655e9cd2b1a5687b0d
local destination: var/d1-custody/l1-003-smoke-007-20260915
quality result: accepted
repeat identity: pass
```

The remote query used explicit `.000Z` boundaries and deterministic ordering by
`bar_start_utc, identity_key`. Two independent reads produced identical canonical
NDJSON. The existing D1 custody quality validator accepted the artifact.

The second boundary check found an operator-input hazard: using an end value of
`2026-09-01T16:04:00Z` against stored text ending in `.000Z` includes the boundary
row under lexical comparison. All accepted evidence therefore uses the exact
millisecond form `2026-09-01T16:04:00.000Z`.

## 5. Checkpoint preservation

The before and after snapshots were identical:

| Coverage key | Complete through | State | Version |
|---|---|---|---:|
| `AMD|1Min|REGULAR|stock:iex:raw` | `2026-09-02T13:51:00.000Z` | PARTIAL | 40 |
| `BTCUSD|1Min|ALL_TRADING|crypto:us` | `2026-09-13T13:01:00.000Z` | PARTIAL | 45 |
| `NVDA|1Min|REGULAR|stock:iex:raw` | `2026-09-02T20:00:00.000Z` | COMPLETE | 6 |
| `QQQ|1Min|REGULAR|stock:iex:raw` | `2026-09-02T15:57:00.000Z` | PARTIAL | 9 |
| `SPY|1Min|REGULAR|stock:iex:raw` | `2026-09-02T16:49:00.000Z` | COMPLETE | 43 |

No local custody value was written back as remote checkpoint truth.

## 6. Phase B disposition

```text
checkpoint before pause: captured above
checkpoint before resume: captured; unchanged
checkpoint after catch-up: not applicable
complete_through before/after: unchanged
catch-up jobs planned/completed/failed: not observed
partial/missing/conflict/rejected: not observed in a fresh catch-up
max external/tick: not applicable
max D1/tick: not applicable
```

Phase B must be reopened during a reviewed US market session. The next window must
capture a short pause-created gap on a previously current Market checkpoint, then
activate only the reviewed normal Market acquisition path with News disabled and
return immediately to Shadow after catch-up evidence is obtained.

## 7. Safety and control summary

```text
control-path before/during/after: PASS / PASS / PASS
7403 observed: no
false coverage advance observed: no
CPU/resource failure observed: no
remote purge performed: no
schema mutation performed: no
secret/body leakage observed: no
final Worker mode: shadow
final News state: disabled
final disposition: INCONCLUSIVE
reason: Phase A passed, but market-closed timing and pre-existing BTCUSD gap prevented fresh pause-created catch-up evidence
```

One attempted checkpoint query used a non-existent `instrument_id` column and
failed read-only with SQLite error 7500. It was corrected from `PRAGMA table_info`
to `symbol`; no row was written. Local validation first encountered a missing
system-Python dependency and stale `uv.lock`; the accepted run used the existing
virtual environment with `uv run --no-sync`, leaving dependency files unchanged.
