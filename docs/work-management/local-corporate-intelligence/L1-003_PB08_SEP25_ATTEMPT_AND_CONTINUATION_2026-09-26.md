# PB-08 Sep25 attempt and bounded continuation

Status: **FIRST WINDOW NOT ACCEPTED / SAFE CLOSED / CONTINUATION NOT AUTHORIZED**

## Authorized attempt

User explicitly approved NVDA v61→v65, Sep25 20:00Z, maximum 16 normal
scheduler opportunities, then shadow. Fresh preflight at
`2026-09-26T07:30:36.000Z` matched the accepted entry and competition snapshot.
Local tests: 34 pass; typecheck pass. Temporary live deployment version
`5cf4fe53-85e1-4785-8b51-d9850b7424d1`.

Observed opportunities: 07:33:19Z, 07:34:19Z, 07:35:19Z, 07:36:19Z.
The fourth returned AMD PARTIAL: inserted=98, matched=1, missing=1,
conflicts=0, rejected=0. The bounded script stopped with exit 1 and restored
checked-in shadow. Health independently confirmed at 07:38:02.404Z:
shadow / IEX / News disabled. Temporary config was removed; no temporary
token was created. Both checked-in control gates remain false.
Final read-only verification: unresolved canary attempts=0; both historical
recovery and absence-ack POST endpoints return HTTP 404.

## Preserved progress and new blocker

| Symbol | Version | Coverage | State |
|---|---:|---|---|
| NVDA | 62 | Sep25 15:10Z | COMPLETE |
| AMD | 45 | Sep25 15:33Z; observed through 16:49Z | PARTIAL |
| QQQ | 13 | Sep25 15:10Z | COMPLETE |
| SPY | 45 | Sep25 15:10Z | COMPLETE |
| BTCUSD | 52 | Sep25 12:31Z | COMPLETE |

NVDA's one attempt SUCCEEDED with 100 inserted bars, zero conflicts/rejected/
missing. All observed attempts finished. AMD's only missing range is
`[2026-09-25T15:33:00Z,2026-09-25T15:34:00Z)`, retry gate 07:51:19Z;
blocker=null. Two immediate IEX reads independently reproduced that absence
while adjacent 15:32Z and 15:34Z bars were present.

Forward inspection found additional provider absences. Repeating only AMD's
single-minute repair would lead to further stops in competing symbols. The
remaining IEX ranges were therefore read twice per symbol and recorded in
`L1-003_PB08_SEP25_PROVIDER_ABSENCE_EVIDENCE.json`, including returned timestamps,
observation times and response hashes. Identical missing sets: AMD 22 (includes
the current gap), QQQ 9, SPY 1, NVDA 0. Evidence hash:
`53a1128fdf51b050e39d6e4eb869102a9decccbfbace00c96be13b35cb9c1494`.

## Concrete continuation packet

Execute `scripts/l1_003_pb08_sep25_repair_and_continue.sh` only after new explicit
authorization under moving-retention runbook §9.

1. Verify shadow/IEX/News-disabled and both control endpoints closed.
2. Run local acceptance.
3. Single atomic D1 acknowledgement: AMD v45 PARTIAL→v46 COMPLETE at 16:49Z.
   Exact five-symbol entry, missing range, source coverage and retry gate are
   required; unresolved attempts, replay, any checkpoint drift or expired
   retention cause zero updates. NVDA remains v62. Existing accepted bars are
   preserved. This acknowledges absence; it does not invent a bar.
4. Temporary normal-scheduler live window with only
   `PB08_SEP25_ABSENCE_ENABLED=true`. Reuse the existing executor's evidence-aware
   absence semantics for the 32 frozen minutes. Evidence is limited to IEX,
   equity 1Min REGULAR, exact Sep25 ranges and expiry 13:30Z Sep26. NVDA has no
   absence exemptions. Unexpected missing/conflicting/returned-on-absence bars
   still fail validation. Priority/universe/cron/retention are unchanged.
5. NVDA v62→v65, exactly Sep25 20:00Z, three clean NVDA attempts with totals
   100,100,93; maximum 16 opportunities. No replay of the accepted v61→v62 job.
6. Restore checked-in shadow with absence gate omitted/disabled, both controls
   closed, IEX and News disabled; remove temporary config. No temporary secret.

Packet expires after **2026-09-26 22:30 JST**, or earlier upon any entry drift.
If AMD acknowledgement succeeds but the live window fails, retain that accepted
repair and derive the next entry from fresh state; never repeat the old SQL.

## Local verification

SQLite using repository migrations: exact one-row repair passes; NVDA preserved;
replay, each of five checkpoint version drifts and unresolved attempt refused.
Focused tests: 15 pass, including three-job competition, disabled/default gate,
expiry/feed refusal, job/symbol/time/scope selection and existing executor
absence/collision validation. Typecheck and shell syntax pass.
Worker unit/orchestration integration plus PB acceptance: 57 tests, 57 pass,
zero fail. Default-gate and temporary-gate Worker dry-run bundles succeed.
Shadow restore deployment version: `46e8311f-d7e5-416d-9683-54d446fa35a5`.

PB-06/PB-07 and previous acknowledgement evidence remain accepted. PB-08 remains
in progress; PB-09/PB-10 still require separate authorization. No remote repair
or continuation has been executed by this document.
