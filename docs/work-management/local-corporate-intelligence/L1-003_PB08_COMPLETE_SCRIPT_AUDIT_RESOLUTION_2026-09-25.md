# OrderScope — L1-003 PB-08 Complete Script Audit Resolution

Status: **RESOLVED ON WEB — complete script committed, local validation required**
Date: 2026-09-25 JST
Branch: `l1-003-local-market-recovery`

## Resolution

The audit at commit `c4802a07a84fe44f2b7ae600307eae9af2c0c970`
correctly found that Git contained only a deliberately non-executable PB-08
change-window skeleton.

The Web-side implementation has now replaced that skeleton with the complete
bounded PB-08 frontier catch-up operator script.

```text
0403c9acf7fc337b213c88f04ba3196fb1ebddde
  Implement complete PB-08 frontier catch-up window

1f5bd3a4922e32295f31befe8a15c710aad84c32
  Validate complete PB-08 change-window syntax locally
```

## Frozen runtime scope

```text
entry
  NVDA v61 / 2026-09-23T18:28:00.000Z

v62
  2026-09-24T15:10:00.000Z

v63
  2026-09-24T16:49:00.000Z

v64
  2026-09-24T18:28:00.000Z

v65
  2026-09-24T20:00:00.000Z

maximum scheduler opportunities
  16

final canonical Sep24 Regular bars
  390
```

The final 93-minute provider request is intentionally accepted as 93
`inserted + matched` timestamps. The first three requests require 100 each.

## Safety properties

The complete script:
- re-runs PB-08 local acceptance before remote mutation;
- checks the moving 1,440-minute retention floor before live activation;
- requires the exact v61 entry and zero unresolved NVDA attempts;
- requires Shadow / News-disabled / IEX baseline;
- requires the historical-recovery endpoint to remain closed;
- performs a dry-run before temporary live deployment;
- observes at most 16 distinct live scheduler opportunities;
- requires `budget.withinBudget=true`;
- fails on any non-SUCCEEDED selected market summary;
- separately observes v62, v63, v64 and v65;
- rejects conflicts, rejected bars, missing bars and interrupted attempts;
- requires final v65 / Sep24 20:00Z;
- requires exactly four clean NVDA attempts;
- requires exactly 390 canonical Sep24 Regular one-minute bars;
- restores the checked-in Shadow deployment in an EXIT trap.

The previous skeleton marker is absent, and the PB-07 first-range timestamp
`2026-09-23T15:09:00.000Z` is absent from the completed script.

## Required local verification

Before execution:

```bash
git pull --ff-only
bash scripts/l1_003_pb08_local_acceptance.sh
```

The local acceptance script now also runs:

```bash
bash -n scripts/l1_003_pb08_frontier_catchup_change_window.sh
```

Do not execute the remote catch-up if local acceptance fails or if the script
reports that the retained September 24 Regular open has expired.

## Authority boundary

The prior explicit authorization covers only the bounded PB-08 frontier
catch-up. It does not include PB-09, PB-10, Phase B pause/resume, retention
widening, Universe changes, priority changes, Cron changes, manual checkpoint
movement or historical-recovery use.
