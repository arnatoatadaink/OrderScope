# OrderScope — L1-003 Phase B Prerequisite Market Recovery Schedule

Status: **PROPOSED RECOVERY PLAN — Phase B prerequisite; no remote mutation authorized by this document**
Date: 2026-09-16 JST
Branch: `docs/mermaid-conventions-v0.1`
Parent work: `L1-003 / SMOKE-007`
Related preparation: `L1-003_SMOKE-007_PHASE_B_CLOSED_MARKET_PREP_2026-09-15.md`

## 1. Purpose

Restore at least one U.S. Market checkpoint from the pre-existing September 2-era stale state to a clean current-session state so that Phase B can create and observe a **fresh pause-created gap** that is distinguishable from older recovery work.

This recovery is a prerequisite to Phase B. It is not itself Phase B acceptance evidence.

## 2. Key conclusion

Phase B does **not** require all 106 instruments to be fully recovered first.

The shortest valid path is:

```text
recover one suitable canary Market checkpoint
  -> verify no pre-existing unresolved gap
  -> verify normal current-session following for multiple scheduler opportunities
  -> record Phase B checkpoint_before_pause
  -> begin Phase B
```

Preferred Phase B candidates remain the U.S. Market canary symbols such as `AMD`, `NVDA`, `QQQ`, or `SPY`, chosen by runtime evidence quality rather than ticker preference.

`BTCUSD` must not be selected merely because it trades continuously when an older unresolved `PARTIAL` gap is present.

## 3. Alpaca Basic planning assumption

Current planning assumes Alpaca Basic / Free remains sufficient for the bounded recovery window.

Relevant operational characteristics to re-confirm from Alpaca official documentation immediately before execution:

- historical stock-data request rate is materially higher than the rate required by this bounded recovery plan;
- historical pagination can return many bars per request;
- recent historical stock data has a latest-data restriction on the Basic plan;
- real-time stock data on Basic uses the IEX feed.

The important consequence is that the expected bottleneck is **not primarily Alpaca request-rate capacity**. The recovery must remain bounded by OrderScope safety contracts:

```text
provider request budget
D1 operation budget
bounded scheduler jobs
checkpoint CAS truth
quality acceptance
failure/retry behavior
control-path health
```

Do not increase provider/page/budget limits merely to accelerate this recovery.

## 4. Recovery scope

### 4.1 Phase B prerequisite scope

Initially recover only enough canary Market coverage to obtain one clean current checkpoint.

Candidate set:

```text
AMD
NVDA
QQQ
SPY
```

Do not require all 106 symbols before Phase B unless the existing scheduler implementation inherently performs a bounded group recovery and doing so remains within reviewed budgets.

### 4.2 Full-universe recovery

Full `106`-instrument recovery is a separate operational objective and can continue after the Phase B prerequisite is satisfied.

Phase B readiness and full-universe currentness must not be collapsed into the same completion criterion.

## 5. Estimated historical workload

For planning only, roughly nine U.S. market sessions from September 2 to the current September 15/16 recovery window imply on the order of:

```text
~3,000+ Regular-session minutes
x 106 instruments
≈ several hundred thousand 1Min bars
```

Including Pre/Regular/After materially increases the row count.

These are planning estimates, not measured runtime evidence. Actual requested ranges must come from persisted checkpoint/session truth and provider calendar data.

## 6. Proposed recovery schedule

### T+0 to T+10 minutes — Read-only preflight

Capture without remote mutation:

```text
release commit
Worker version
Worker mode
News state
Cron definition
Universe revision
Cloudflare identity
D1 binding/database identity
SELECT 1 control-path result
provider/exchange session/calendar state
AMD/NVDA/QQQ/SPY Market checkpoint rows
complete_through values
PARTIAL / missing / conflict / rejected state
shared external/D1 ceilings
```

Reject any candidate already carrying an unresolved pre-window ambiguity.

### T+10 to T+30 minutes — Historical catch-up

Under a separately reviewed change window, enable only the reviewed Market acquisition path needed for recovery.

Preserve:

```text
News = disabled
Prediction = shadow
Universe = existing reviewed canary/full profile as applicable
Cron = unchanged
schema = unchanged
provider contract = unchanged
shared budgets = unchanged
```

Recover the old gap using normal bounded historical acquisition.

Purpose:

```text
STALE / OLD GAP
  -> CURRENT-ENOUGH FOR LIVE FOLLOW
```

This historical recovery is **not** Phase B acceptance evidence.

### T+30 to T+45 minutes — Current-session transition

Observe the transition from recovered historical coverage into current-session acquisition.

Verify:

```text
new bars accepted
checkpoint advances only with accepted records
complete_through advances consistently
missing = none or explicitly bounded/understood
conflict = none
rejected = none
withinBudget = true
control path = PASS
```

Any provider latest-data restriction must not be misclassified as a pause-created Phase B gap.

### T+45 to T+60 minutes — Stability observation

Observe multiple ordinary scheduler opportunities.

Required pattern:

```text
scheduler opportunity
  -> planned Market work
  -> accepted Market bars
  -> checkpoint/complete_through advance
```

Select the first candidate satisfying:

1. current enough for the active U.S. session;
2. no unresolved pre-existing gap;
3. no unresolved missing/conflict/rejected state;
4. session identity unambiguous;
5. checkpoint movement explained by accepted records;
6. control path healthy;
7. shared budgets remain within reviewed ceilings.

At this point the Phase B prerequisite is satisfied.

## 7. Phase B READY condition

Phase B may begin only when one selected Market coverage key satisfies:

```text
active applicable U.S. market session
+
current clean checkpoint
+
pre-existing gap = none
+
unresolved missing/conflict/rejected = none
+
normal acquisition following the session
+
control path PASS
+
withinBudget = true
```

Then freeze:

```text
checkpoint_before_pause
```

and execute the separately reviewed Phase B sequence:

```text
short pause
  -> fresh bounded gap
  -> resume reviewed normal Market acquisition
  -> exact-gap catch-up
  -> verify no false checkpoint advance
  -> return to reviewed safe baseline
```

## 8. Time estimate

### 8.1 Phase B prerequisite only

Planning target:

```text
30–60 minutes normal case
up to ~90 minutes conservative recovery window
```

Illustrative allocation:

```text
~10 min  read-only preflight
~10–20 min bounded historical catch-up
~10–15 min current-session transition
~10–15 min stability observation
```

These are schedule estimates, not acceptance evidence.

### 8.2 Full 106-instrument recovery

Planning target:

```text
~1–2 hours as a conservative bounded operating window
```

The actual duration depends on persisted checkpoint state, session coverage, provider pagination, Worker grouping, D1 operations, retries, and shared-budget behavior.

Do not convert this estimate into a timeout or force progress by widening reviewed budgets.

## 9. Example execution window

For an execution started at `00:30 JST`:

```text
00:30–00:40  read-only preflight
00:40–01:00  bounded historical catch-up
01:00–01:15  current-session transition
01:15–01:30  stability observation
~01:30       earliest normal-case Phase B READY
~02:00       conservative planning boundary
```

This is an illustrative operator schedule only. Runtime evidence determines readiness.

## 10. Stop conditions

Stop without widening scope if any of the following occurs:

```text
provider throttling/failure that requires config widening
7403 recurrence
D1/control-path failure
binding/environment mismatch
candidate remains stale or PARTIAL for an older gap
historical/current boundary cannot be explained
checkpoint advances without accepted records
shared external/D1 ceiling would be crossed
session/calendar state is ambiguous
code/schema/Cron/Universe/provider change becomes necessary
```

Record the recovery as `INCONCLUSIVE/BLOCKED` rather than converting ambiguous state into Phase B evidence.

## 11. Post-Phase-B decision

Phase B acceptance and continuous 106-instrument collection are separate promotion decisions.

After Phase B, decide explicitly between:

```text
A. return Worker to reviewed Shadow baseline
```

or

```text
B. separately promote Market-only continuous acquisition
   News disabled
   Prediction shadow
```

Continuous Live/full-v0.1 operation is not authorized by this recovery plan.

## 12. Disposition

The recommended order is:

```text
1. read-only Market recovery preflight
2. reviewed Market-only recovery activation
3. old-gap bounded catch-up
4. obtain at least one clean current canary checkpoint
5. observe multiple normal scheduler opportunities
6. declare Phase B prerequisite satisfied
7. execute L1-003 / SMOKE-007 Phase B
8. make a separate continuous-operation promotion decision
```

Expected planning duration to Phase B readiness: **30–60 minutes normally, up to approximately 90 minutes conservatively**.

Expected planning window for full 106-instrument recovery: **approximately 1–2 hours**, subject to measured runtime state and unchanged safety budgets.

## 13. Verified current-state gap and required recovery contract

The 2026-09-16 JST market-session preflight verified that the prerequisite is
not presently executable through the deployed normal scheduler without one
additional reviewed recovery decision:

```text
deployed Worker mode: shadow
deployed Market acquisition retention lookback: 1,440 minutes (24 hours)
latest accepted Regular bar / checkpoint activity: 2026-09-02
Phase B candidate checkpoint age at preflight: approximately 13 days
```

The deployed scheduler clips every planned request to its `retentionFloor`
(`now - ACQUISITION_RETENTION_MINUTES`). With the current 24-hour setting, it
cannot request the September 2-era interval required to establish contiguous
recovery from the recorded checkpoints. Merely enabling normal acquisition
would therefore not demonstrate recovery of the old gap; it must not be
described as a valid transition from `STALE / OLD GAP` to a clean current
checkpoint.

This also creates a hard acceptance guard: stop if a checkpoint or
`complete_through` would advance over an interval for which this window has no
corresponding accepted-record evidence. Such an advance is not Phase B-ready
state and must not be used to manufacture a pause-created-gap claim.

Before §6.2 may begin, approve exactly one bounded recovery contract:

```text
A. temporary reviewed retention lookback that reaches the selected checkpoint
   boundary, while retaining the existing max-jobs, max-pages, max-bars,
   provider, D1, Cron, Universe, and News limits;

or

B. a separately reviewed normal-compatible historical recovery path that
   requests the old interval in bounded chunks and proves contiguous checkpoint
   movement from accepted records.
```

Neither option is authorized by this planning document. The selected contract
must record its exact start/end boundary, expected number of bounded jobs,
per-tick external/D1 ceilings, and a fail-closed contiguity assertion before
any Worker/Cron/runtime mutation. Phase B remains separately gated after that
recovery has produced a current clean candidate and ordinary-session stability
evidence.
