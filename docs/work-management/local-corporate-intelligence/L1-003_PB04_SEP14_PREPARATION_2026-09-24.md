# OrderScope — L1-003 PB-04 September 14 Preparation

Status: **LOCAL PREPARATION COMPLETE — remote mutation not authorized**
Date: 2026-09-24 JST

## Frozen target

```text
coverage key       NVDA|1Min|REGULAR|stock:iex:raw
session            2026-09-14 REGULAR
evidence SHA-256   d8e608efbedbef1c0657de01709ce7cfda594d3108355724c26bf56cee68fa55
checkpoint entry   v30 / 2026-09-11T20:00:00.000Z
checkpoint target  v34 / 2026-09-14T20:00:00.000Z
expected bars      390
expected absences  0
```

Frozen job IDs:

```text
1 historical-market-recovery:45f7b21fb39a49eb
2 historical-market-recovery:a36db20a321743de
3 historical-market-recovery:9911442053a42595
4 historical-market-recovery:843809d1b9e52a87
```

Expected chunk shape is 100 / 100 / 100 / 90 provider bars with no
acknowledged absence.

## Operator artifact

`scripts/l1_003_pb04_sep14_change_window.sh` is prepared with:
- entry assertion v30 / Sep11 close;
- final assertion v34 / Sep14 close;
- exact Sep14 evidence SHA-256;
- bounded 404 rollout retries;
- per-chunk persisted evidence checks;
- fail-closed safe-close restoring the false gate and removing the temporary secret.

## Remaining gates

1. local dry-run from the actual Sep14 evidence;
2. remote execution packet freeze;
3. focused tests, TypeScript, clean diff;
4. exact PB-01 read-only remote preflight;
5. separate operator authorization;
6. only then run the Sep14 change window.
