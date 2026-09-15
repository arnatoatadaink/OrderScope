# OrderScope — L1-003 Phase B Prerequisite Market Recovery Schedule

Status: **SELECTED RECOVERY PLAN — bounded historical recovery path; implementation/recovery window still separately gated**
Date: 2026-09-16 JST
Branch: `docs/mermaid-conventions-v0.1`
Parent work: `L1-003 / SMOKE-007`
Related preparation: `L1-003_SMOKE-007_PHASE_B_CLOSED_MARKET_PREP_2026-09-15.md`

## 1. Purpose

Restore at least one U.S. Market checkpoint from the pre-existing September 2-era stale state to a clean current-session state so that Phase B can create and observe a **fresh pause-created gap** that is distinguishable from older recovery work.

This recovery is a prerequisite to Phase B. It is not itself Phase B acceptance evidence.

## 2. Selected recovery strategy

Phase B does **not** require all 106 instruments to be fully recovered first.

The selected path is now:

```text
implement/review bounded historical recovery path
  -> recover one suitable canary Market checkpoint from its persisted boundary
  -> prove contiguous movement only from accepted records
  -> hand off into the unchanged normal scheduler once inside its normal retention horizon
  -> verify normal current-session following for multiple scheduler opportunities
  -> record Phase B checkpoint_before_pause
  -> begin Phase B
```

The previously considered temporary retention-lookback widening is **not selected** for this recovery. The normal scheduler keeps its existing retention semantics. Historical backlog recovery is a separate bounded responsibility.

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
bounded recovery jobs
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

Do not require all 106 symbols before Phase B. Full-universe recovery is explicitly decoupled from Phase B readiness.

### 4.2 Full-universe recovery

Full `106`-instrument recovery is a separate operational objective and can continue after the Phase B prerequisite is satisfied.

Phase B readiness and full-universe currentness must not be collapsed into the same completion criterion.

## 5. Verified current-state gap

The 2026-09-16 JST market-session preflight verified:

```text
deployed Worker mode: shadow
deployed Market acquisition retention lookback: 1,440 minutes (24 hours)
latest accepted Regular bar / checkpoint activity: 2026-09-02
Phase B candidate checkpoint age at preflight: approximately 13 days
```

The deployed normal scheduler clips planned requests to its `retentionFloor` (`now - ACQUISITION_RETENTION_MINUTES`). With the current 24-hour setting it cannot request the September 2-era interval required to establish contiguous recovery from the persisted checkpoint.

Therefore merely enabling normal acquisition cannot demonstrate valid recovery of the old gap.

Hard acceptance guard:

```text
checkpoint / complete_through must never advance across an interval
without corresponding accepted-record evidence from that interval
```

Any such unexplained advance is not Phase B-ready state.

## 6. Bounded historical recovery contract

The selected recovery mechanism is a separately reviewed, normal-compatible historical path with an explicit bounded range.

It must not change the normal scheduler retention rule.

### 6.1 Required inputs

Each recovery execution must freeze:

```text
coverage key / instrument
session / cadence / variant / mode
recovery_start
recovery_end
provider revision
Universe revision
max recovery jobs
max provider pages
max bars
external-op ceiling
D1-op ceiling
checkpoint_before
```

Timestamps must use canonical UTC form:

```text
YYYY-MM-DDTHH:MM:SS.mmmZ
```

### 6.2 Chunking rule

The old interval must be divided into deterministic bounded chunks. A chunk may be session-bounded or bar/page-bounded, but the policy must be fixed before execution.

For each chunk capture:

```text
requested_start
requested_end
provider pages
provider records
accepted bars
missing
conflict
rejected
checkpoint_before_chunk
checkpoint_after_chunk
complete_through_before
complete_through_after
external ops
D1 ops
withinBudget
```

The next chunk may continue only when the previous chunk's accepted-record evidence explains its checkpoint movement.

### 6.3 Contiguity assertion

Recovery succeeds only if the historical path proves a continuous evidence chain from the persisted stale checkpoint to the handoff boundary.

Conceptually:

```text
checkpoint_after(chunk N)
  == valid predecessor of chunk N+1 accepted range
```

No manual checkpoint jump, ad-hoc bar write, synthetic fill, or inferred coverage is allowed.

Missing/partial/conflict/rejected results must remain fail-closed.

### 6.4 Initial execution scope

The first reviewed recovery should use **one canary Market coverage key** only.

Selection priority:

1. cleanest persisted checkpoint;
2. unambiguous U.S. session/calendar history;
3. no unresolved older PARTIAL/conflict/rejected state;
4. smallest operational ambiguity.

Do not widen to all 106 instruments to obtain Phase B evidence.

## 7. Proposed recovery schedule

The earlier 30–60 minute estimate assumed the normal scheduler could perform the historical catch-up. That assumption is invalid and is superseded by this schedule.

### Stage 0 — Historical-recovery implementation/review

Before remote recovery:

```text
confirm reusable Market acquisition primitives
implement the smallest bounded-range recovery entry point if missing
prove retentionFloor of normal scheduler is bypassed only by this explicit recovery path
preserve normal acceptance/checkpoint logic
add deterministic fixture tests
run focused and full regressions
review exact runtime contract
```

No remote mutation is authorized by this document.

### Stage 1 — Read-only recovery preflight

Capture:

```text
release commit
Worker version / mode
News state
Cron definition
Universe revision
Cloudflare identity
D1 binding/database identity
control-path result
provider/exchange calendar
candidate checkpoint
complete_through
PARTIAL / missing / conflict / rejected state
shared ceilings
```

Freeze the exact recovery start from persisted checkpoint truth. Compute the recovery end from the reviewed handoff target, not from a guessed wall-clock range.

### Stage 2 — Bounded historical recovery

Execute only the reviewed canary range through the selected historical recovery path.

Purpose:

```text
STALE CHECKPOINT
  -> contiguous accepted historical chunks
  -> within normal scheduler retention horizon
```

This stage is **recovery evidence**, not Phase B evidence.

### Stage 3 — Normal scheduler handoff

Once the recovered coverage enters the normal scheduler's valid retention horizon, stop historical recovery and hand off to the unchanged normal scheduler.

Verify:

```text
normal scheduler plans the next expected range
new bars are accepted
checkpoint advances only with accepted records
missing/conflict/rejected remain resolved or explicitly bounded
withinBudget = true
control path = PASS
```

### Stage 4 — Current-session stability observation

Observe multiple ordinary scheduler opportunities:

```text
scheduler opportunity
  -> planned Market work
  -> accepted Market bars
  -> checkpoint / complete_through advance
```

Select the first candidate satisfying all Phase B READY conditions.

## 8. Phase B READY condition

Phase B may begin only when one selected Market coverage key satisfies:

```text
active applicable U.S. market session
+
current clean checkpoint
+
pre-existing historical gap = none
+
unresolved missing/conflict/rejected = none
+
normal scheduler is following the session
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

## 9. Time estimate

The previous **30–60 minute / ~90 minute** estimate is retired as a complete Phase B-readiness estimate because it did not include implementation and local acceptance of the bounded historical recovery path.

Separate the estimate into two parts:

```text
A. implementation + local acceptance of bounded historical recovery path
B. remote canary recovery + normal-scheduler handoff + stability observation
```

Part B is still expected to be operationally short relative to the age of the gap because Alpaca request-rate capacity is not expected to dominate. However, no new normative duration is frozen until the historical recovery entry point and chunking policy are reviewed and measured locally.

Full 106-instrument recovery remains a later objective and must not delay Phase B once one valid canary is current and stable.

## 10. Stop conditions

Stop without widening scope if any of the following occurs:

```text
provider throttling/failure that requires config widening
7403 recurrence
D1/control-path failure
binding/environment mismatch
candidate contains unresolved older PARTIAL/conflict/rejected state
historical chunk boundary cannot be explained
checkpoint advances without accepted records
chunk-to-chunk contiguity fails
shared external/D1 ceiling would be crossed
session/calendar state is ambiguous
normal scheduler handoff is not explainable
code/schema/Cron/Universe/provider change beyond reviewed recovery contract becomes necessary
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

## 12. Final disposition

Selected path:

```text
1. bounded historical recovery path implementation/review
2. deterministic local acceptance
3. read-only remote preflight
4. one-canary historical recovery from persisted checkpoint
5. prove contiguous accepted-record chain
6. enter normal scheduler retention horizon
7. hand off to unchanged normal scheduler
8. observe multiple current-session scheduler opportunities
9. declare Phase B prerequisite satisfied
10. execute L1-003 / SMOKE-007 Phase B
11. make a separate continuous-operation promotion decision
```

Rejected for this recovery:

```text
temporary widening of ACQUISITION_RETENTION_MINUTES
as the mechanism for recovering the September 2 backlog
```

Reason: backlog recovery and normal scheduler responsibility must remain separate; widening the normal retention horizon would mix recovery semantics into ordinary acquisition and make the acceptance boundary less clear.

The next actionable work item is therefore **implementation/review of the bounded historical recovery path**, not Worker Live activation and not Phase B execution.
