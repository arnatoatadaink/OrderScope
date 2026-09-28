# L1-003 PB-09 / Phase B: 2026-09-28 closeout readiness

Status: **PREPARATION ONLY — neither entry acquisition nor Phase B authorized**.
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
2. If status is `CURRENT_CHECKPOINT_REQUIRED`, freeze a **separate** entry
   acquisition request from that packet. Limit it to the unchanged normal
   scheduler, at most 16 observed opportunities, newly required current-session
   coverage, and immediate checked-in shadow restoration. Do not use the Sep 25
   absence gate, replay accepted PB work, or start this window without explicit
   authorization. Repeat step 1 after a successful safe close.
3. Proceed only if `ENTRY_EVIDENCE_READY_NOT_AUTHORIZED` names a current
   equity 1Min REGULAR IEX checkpoint whose source and coverage equal the
   finalized frontier, with healthy competition and zero unresolved attempts.
   Freeze the exact candidate, checkpoint version/frontier and deployment
   identity. Any change requires a new packet.
4. Before asking for Phase B authorization, attach a concrete guarded
   execution procedure or script with locally tested safe close to the
   [Phase B authorization template](L1-003_PB09_PHASE_B_AUTHORIZATION_TEMPLATE.md).
   Populate every `UNFROZEN` field, including release, current session,
   candidate, pause bounds and export range. Entry acquisition authority does
   not cover Phase B.
5. Once Phase B is explicitly authorized, run the bounded in-session trial:
   verify fresh entry; deploy the temporary live-canary configuration so the
   checked-in shadow deployment pauses acquisition; establish pauseStart only
   after shadow is observed; hold about three minutes and never over five;
   perform the frozen one-row repeat-read; verify an unchanged checkpoint
   before resume; derive the fresh gap using `freezePauseGap`; resume normal
   scheduler for at most 16 observed opportunities; restore checked-in shadow
   on success or any failure.
6. Close only with receipts that explain every minute in the frozen gap from
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
`scripts/l1_003_pb09_packet.mjs`. As of this preparation, a locally accepted
PB-10 execution driver is still outstanding. This document does not authorize
deployment, D1 writes or scheduler activation.
