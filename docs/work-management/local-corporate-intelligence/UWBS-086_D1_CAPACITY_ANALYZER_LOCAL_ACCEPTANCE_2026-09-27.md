# UWBS-086 — D1 Capacity Analyzer Local Acceptance — 2026-09-27

Status: **ACCEPTED — ANALYZER / EVIDENCE PARSING BOUNDARY**
Branch: `l1-003-local-market-recovery`

## Local verification

```text
D1 capacity evidence focused tests:         10 passed in 2.39s
historical Canary evaluation focused tests:  7 passed in 2.31s
full Python regression:                    825 passed in 36.06s
compileall:                                PASS
git diff --check:                          PASS
```

## Accepted boundary

The accepted analyzer parses repository-backed D1 result metadata and projects capacity from billed rows rather than statement execution counts.

Accepted fields:

```text
meta.rows_read
meta.rows_written
meta.size_after
```

Projection remains conservative by selecting the worst observed sample independently per resource and applying an explicit safety multiplier before daily scaling.

## Existing repository-backed evidence discovered locally

Two existing local custody outputs were found:

```text
var/d1-custody/r0-007-first-remote/pass1.json
var/d1-custody/r0-007-first-remote/pass2.json
```

Both report the same billing values:

```text
rows_read:    3906
rows_written: 0
size_after:   4796416
changes:      0
changed_db:   false
total_attempts: 1
```

The result payload contains exactly one QQQ 1-minute bar for `2026-09-01T16:03:00Z`.

These files therefore provide reproducible read-only billing evidence for the specific R0-007 custody query shape. They are **not** accepted as representative of one full scheduled Worker invocation and must not be multiplied by 1,440/day without proving that the normal Cron path executes the same query shape once per invocation.

## Remaining capacity boundary

Final UWBS-086 capacity acceptance still requires:

1. classification of the normal Cron D1 query mix;
2. repository-backed or defensibly bounded write-path `rows_written` evidence;
3. defensible storage-growth evidence for the write path;
4. Worker requests/day projection for the intended schedule;
5. final headroom calculation against the fresh external capacity envelope.

No live Worker/Cron/D1 mutation was performed for this acceptance.
