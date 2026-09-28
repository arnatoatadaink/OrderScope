# L1-003 PB-09 / Phase B: 2026-09-28 closeout readiness

Status: **PREPARATION ONLY — combined window not authorized**.
This packet is for the Sep 28 REGULAR session; it cannot be carried into another
session. The operator must replace the snapshot with fresh active-session evidence.

## Synced baseline and observed remote state

- PB branch `l1-003-local-market-recovery` is clean and matches
  `origin/l1-003-local-market-recovery` at `3d41559e06cf4aa61052cfa8449c0912339b7213`.
  The latest remote delta is the UWBS-088 local acceptance document only.
- Read-only remote packet:
  [Sep 28 snapshot](L1-003_PB09_READ_ONLY_SNAPSHOT_2026-09-28.json),
  observed 2026-09-28T07:10:11.372Z. Worker is shadow / IEX / News disabled;
  all five competition checkpoints are COMPLETE with empty missing ranges;
  unresolved canary attempts: zero; temporary control routes: 404.
- Equity checkpoints still reflect Sep 25, not the Sep 28 active frontier.
  NVDA v65, AMD v48 and QQQ v16 are through Sep 25 close; SPY v47 is through
  Sep 25 18:28Z. The Sep 28 active-session candidate is therefore not frozen.
- Alpaca calendar: Sep 28 REGULAR, 13:30–20:00Z (22:30–05:00 JST), revision
  `alpaca-calendar-v2:a13f0ea5`. Recheck the calendar at entry.
- Assessment: `WAITING_ACTIVE_MARKET_SESSION`, `candidate=null`. No remote
  mutation occurred in preparation.

## Same-session sequence

1. After 13:30Z, run `scripts/l1_003_pb09_readonly_preparation.sh` from the
   clean PB branch. Keep its `packet.json` and check the exact release,
   deployment/version, config hash, calendar, health, five checkpoint rows,
   unresolved attempts, D1 identity and closed control routes.
2. Fill the fresh fields in the
   [combined authorization template](L1-003_PB10_COMBINED_WINDOW_AUTHORIZATION_TEMPLATE.md).
   One approval can cover conditional entry acquisition and Phase B under the
   fixed script bounds. It does not authorize another session or an expanded
   retry. The approval is still pending.
3. After that approval, run `scripts/l1_003_pb10_combined_window.py --execute
   --authorization-id <approved-reference>` with stdout/stderr captured in an
   operator log. The script creates a fresh read-only packet, checks the active
   official session and safe baseline, then chooses an existing current
   candidate or uses at most 16 observed normal scheduler opportunities to
   catch up. It restores checked-in shadow before Phase B entry.
4. The script rechecks candidate identity at the pause boundary. It holds
   shadow for about three minutes (hard maximum five), performs the frozen
   one-row repeat-read, verifies an unchanged checkpoint and derives the
   pause-created gap using `freezePauseGap`. It resumes the unchanged scheduler
   for at most 16 observed opportunities and restores shadow in `finally`.
5. Close only with receipts that explain every minute in the frozen gap from
   accepted target attempts, separate overlap from fresh coverage, account for
   any additional current-session progression, show budgets within the shared
   40 external / 40 D1 limits, and verify final shadow / IEX / News disabled,
   temporary routes 404 and zero unfinished attempts. Otherwise record the
   precise stopping point and leave Phase B open.

## Preventing another day rollover

The checkpoint frontier and pause gap are valid only for the Sep 28 session.
Do not reuse this packet on Sep 29. If the market closes before the bounded
trial is authorized and completed, safe-close to shadow and create a fresh
active-session packet on the next trading day. Do not rerun PB-06, PB-07 or
the Sep 25 campaign to regain a current candidate.

The existing repeat-read helper is
`scripts/l1_003_pb09_paused_export_readonly.sh`; the entry/gap guard is
`scripts/l1_003_pb09_packet.mjs`. The combined driver is
`scripts/l1_003_pb10_combined_window.py`; its local acceptance and fresh
market-session packet must be reviewed before the single approval. This
document does not authorize deployment, D1 writes or scheduler activation.
