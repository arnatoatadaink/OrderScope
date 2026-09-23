# OrderScope — Requirement Coverage / Implementation Realization / Test Assurance Review

Status: non-normative review and planning-adjustment input
Date: 2026-09-06
Branch reviewed: `docs/mermaid-conventions-v0.1`
Normative source: `stock_monitoring_v0.1_spec.md` and its Code of Truth references
Requirement map: `REQUIREMENTS_TRACEABILITY_v0.1.md`
Design map: `HIGH_LEVEL_DESIGN_v0.1.md`
Worker progress: `IMPLEMENTATION_PROGRESS_TRACKER_2026-09-01.md`
Local WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Local CP: `WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
Local runtime authority: `work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md`
Cross-Market extension: `WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`

## 1. Purpose and position

This review visualizes four different questions without treating them as the same thing:

1. **Requirement coverage** — whether current requirements are represented by design and implementation work packages.
2. **Implementation realization** — whether the planned behavior exists in code and durable runtime behavior.
3. **Test assurance** — what current tests actually prove and what they do not prove.
4. **Planning adjustment need** — whether WBS / Critical Path / Progress tracking must be amended before continuing.

This document is not a new source of requirements and is not a runtime progress authority. It is an input for Web-side review sessions. When a gap is confirmed as requiring work, update the appropriate WBS, CP and/or Progress Tracker rather than silently treating this review as the execution backlog.

## 2. Review vocabulary

### 2.1 Requirement / plan coverage

| State | Meaning |
|---|---|
| `EXPLICIT` | A current Worker or Local work package has clear ownership for the requirement domain |
| `PARTIAL` | Related work exists, but the complete requirement behavior has no end-to-end work package |
| `MISSING` | No explicit implementation work package currently closes the requirement |
| `TRACEABILITY-GAP` | The normative parent specification contains behavior that is not yet represented by stable requirement IDs |

### 2.2 Implementation realization

| State | Meaning |
|---|---|
| `RUNTIME-VERIFIED` | Repository implementation plus runtime/integration evidence exists |
| `CONTRACT-ACCEPTED` | Provider-neutral/domain contract and tests are accepted, but the full runtime path is not implemented |
| `PROVISIONAL` | Early implementation or fixture evidence exists, but upstream/downstream integration remains open |
| `PLANNED` | WBS/design exists but implementation has not reached acceptance |
| `UNPLANNED` | Normative requirement exists but no sufficient implementation work package exists |

### 2.3 Test assurance

A passing test is evidence only for the behavior actually asserted by that test. It does not automatically prove persistence atomicity, crash recovery, provider compatibility, operational rate limits, end-to-end temporal correctness, or production deployment behavior.

## 3. Executive findings

### 3.1 Main findings

1. Worker-side Market acquisition is the most runtime-mature area. It has Miniflare/D1 integration coverage for scheduled execution, Shadow behavior, calendar/session boundaries, shortened sessions, durable coverage, idempotent replanning, stale attempts and sanitized summaries.
2. Local Corporate Intelligence has a strong contract foundation. `I0-002` through `I0-005` are accepted and cover provenance, checkpoints, identity/idempotency and the logical Fact Store boundary.
3. Current Local tests are strongest at immutable types and cross-record invariants, but they do not yet prove Local database transactions, crash consistency, actual provider adapters, retention deletion, or full end-to-end ingestion.
4. The current Local Corporate Intelligence WBS does not contain a dedicated FFT implementation package or a dedicated Regime Engine implementation package even though both are normative v0.1 requirements.
5. Analyst Consensus and Cross-Market Context were added to the parent specification after the existing requirement traceability map. Therefore the requirement map itself is now incomplete relative to the current parent specification.
6. The Fact Store implementation has a temporal-lineage assurance gap: current cross-record validation proves that references resolve, but does not prove that an Interpretation or Derived Metric cannot depend on records that were unavailable at its historical as-of time.
7. The Fact Store supersession check proves same record type and chronological acceptance, but does not yet prove same logical subject/fact identity. A semantically unrelated `Fact` can theoretically supersede another `Fact` if only record type and timestamp constraints are considered.

## 4. Quantitative coverage baseline

### 4.1 Current stable requirement count

The current `REQUIREMENTS_TRACEABILITY_v0.1.md` contains the following stable requirement IDs:

| Domain | Count |
|---|---:|
| SYS | 5 |
| UNI | 10 |
| MD | 7 |
| CAL | 5 |
| FFT | 6 |
| INT | 3 |
| SRC | 5 |
| SEC | 6 |
| REG | 26 |
| RET | 4 |
| PROV | 7 |
| FACT | 3 |
| **Total stable requirement IDs** | **87** |

It also contains 14 `REQ-VER-*` verification targets.

### 4.2 Explicit work-package coverage of the current stable requirements

Using the conservative rule "a requirement is plan-covered only when a current Worker or Local implementation lane explicitly owns the behavior", the largest clear planning gaps are:

- `REQ-FFT-001..006` — 6 requirements
- `REQ-REG-001..026` — 26 requirements

The remaining mapped domains have explicit Worker and/or Local ownership at some level.

Therefore, for the **existing 87 stable requirement IDs only**:

- explicit work-package covered: 55
- missing dedicated work-package coverage: 32
- **explicit plan coverage ratio: 55 / 87 = 63.2%**

This is a **planning-coverage metric**, not implementation completion. It intentionally does not count Analyst Consensus or Cross-Market requirements because those newer parent-specification sections do not yet have equivalent stable `REQ-*` IDs in the current traceability map.

### 4.3 Traceability freshness gap

The current parent specification now includes:

- Analyst Consensus Tracking
- Macro / Cross-Market Context
- `AnalystConsensusProvider`
- Consensus Snapshot / Revision Event / derived consensus-gap metrics
- Cross-Market Rotation Interpretation/Hypothesis semantics

These are not fully represented in the current stable requirement-domain map. Until `REQUIREMENTS_TRACEABILITY_v0.1.md` is updated, a single project-wide "requirement coverage percentage" would undercount the normative surface and should not be reported as complete.

## 5. Requirement-domain coverage and realization matrix

| Domain | Main owner | Plan coverage | Current realization | Review note |
|---|---|---|---|---|
| System scope / time rules | Worker + Local | EXPLICIT | PARTIAL | UTC / market-session behavior is implemented in Market paths; full continuous Corporate/Policy monitoring is not yet implemented |
| Universe / configuration | Worker | EXPLICIT | RUNTIME-VERIFIED / partial scope | Worker has fixed universe/cadence configuration behavior; Corporate entity/source registry is separate Local work |
| Market data | Worker | EXPLICIT | RUNTIME-VERIFIED | Acquisition, normalization, D1 persistence and checkpoint behavior are relatively mature |
| Calendar / sessions | Worker | EXPLICIT | RUNTIME-VERIFIED | Holiday and shortened-session behavior have integration coverage |
| FFT / market analysis | none explicit | MISSING | UNPLANNED | HLD component exists but current Worker/Local WBS has no closing implementation package |
| Corporate intelligence intake/extraction | Local | EXPLICIT | PLANNED | Common contracts exist; actual SEC/News/Official/Earnings pipelines remain mostly ahead |
| Source hierarchy / official signals | Local | EXPLICIT | PLANNED | Web research inputs are strong; adapter/runtime path is not implemented |
| SEC / fundamentals | Local | EXPLICIT | PROVISIONAL / PLANNED | SEC form filter exists; filing detection, persistence, document acquisition, XBRL and segment extraction remain |
| Regime Engine | none explicit | MISSING | UNPLANNED | Normative requirements and HLD component exist but no dedicated current WBS package closes them |
| News retention | Local | EXPLICIT | PLANNED | `I0-006` is next; deletion controller/runtime proof is not yet present |
| Provider boundary | Worker + Local | EXPLICIT | PARTIAL | Market provider boundary is runtime-tested; Corporate provider contracts/adapters remain incomplete |
| Fact model / common store | Local | EXPLICIT | CONTRACT-ACCEPTED | Logical Fact/Evidence/Relationship/DerivedMetric/Interpretation contracts accepted; physical persistence/API not complete |
| Analyst Consensus | Local extension expected | PARTIAL / TRACEABILITY-GAP | PLANNED / UNPLANNED | Parent spec is richer than A0; provider acquisition, snapshot persistence and revision extraction need explicit tasks |
| Cross-Market Context | Local A0 + Market data | PARTIAL / TRACEABILITY-GAP | PROVISIONAL | A0-001 design exists; A0-002 validation depends on datasets and provider decisions |
| Prediction research | Worker | EXPLICIT but provisional extension | PROVISIONAL / Shadow | Kept separate from observed Fact requirements by design |

## 6. Test-assurance review

### 6.1 Local common contracts

#### Provenance — strong contract assurance

Current tests prove:

- external event/published/filed/source-accepted timestamps stay distinct,
- unknown external timestamps remain unknown,
- date-only timestamps are not fabricated as instants,
- operational timestamps require UTC,
- `available_at <= retrieved_at <= accepted_at`,
- value objects reject invalid/ambiguous values,
- durable provenance structures do not contain raw body or secret fields.

Not currently proved:

- policy for obviously anomalous provider future timestamps / clock skew,
- persistence/database representation round-trip,
- compatibility with actual SEC/IR/News provider timestamp quirks.

#### Checkpoint — strong storage-neutral contract, no transaction proof

Current tests prove:

- provider/source scoped bounded windows,
- opaque resume cursor,
- partial/error state persistence round-trip,
- complete checkpoints cannot resume,
- retry timing rules,
- cursor-loop rejection,
- noncanonical/raw provider fields are rejected.

Not currently proved:

- atomic relationship between accepted data writes and checkpoint advancement,
- crash recovery between page persistence and checkpoint update,
- multi-process/scheduler concurrency,
- actual database locking/transaction semantics.

#### Identity / idempotency — strong pairwise classifier

Current tests prove:

- filing accession global identity,
- article/signal provider-scoped identity,
- distinct identity is `NEW`,
- same identity/hash is `DUPLICATE`,
- changed hash without explicit revision is `CONFLICT`,
- changed hash with an exact predecessor→successor revision is `UPDATE`,
- reversed/cross-scope/ambiguous revision relationships are rejected.

Not currently proved:

- how storage selects the correct predecessor from a multi-revision history,
- concurrent acceptance of competing candidates,
- provider-specific revision discovery and mapping into `RevisionRelationship`.

#### Fact Store — strong structural assurance, temporal-semantic follow-up needed

Current tests prove:

- Fact, Evidence, Relationship, DerivedMetric and Interpretation remain distinct,
- references resolve,
- Fact/Relationship evidence links are reciprocal,
- supersession cycles are rejected,
- mixed record-type supersession is rejected,
- immutable record values,
- numeric values require units,
- source availability and store acceptance both affect `records_available_as_of`,
- append-oriented original + amendment history remains visible.

### 6.2 High-priority assurance gaps discovered by code review

#### REVIEW-TEMP-001 — future-reference / temporal-lineage leakage

`validate_fact_store()` currently verifies that DerivedMetric inputs and Interpretation basis records exist, but not that those inputs were historically available at the metric/interpretation as-of point.

Potential invalid state:

```text
Fact B accepted/available at 11:00
        ↑
Interpretation X accepted at 10:05, basis includes Fact B
```

A historical query at 10:05 can then expose an Interpretation whose basis is not visible at that time.

Recommended invariant candidates:

- Interpretation basis records must be accepted no later than the Interpretation acceptance/as-of boundary used by the design.
- DerivedMetric input records/datasets must not introduce information unavailable at `metric.as_of`.
- If late backfill is intentionally allowed, preserve both calculation time and source/data availability time so historical replay cannot leak future information.

This should be resolved before Regime and Cross-Market calculations depend heavily on as-of reconstruction.

#### REVIEW-SUP-001 — supersession semantic identity is too weak

Current validation requires the predecessor to be the same `record_type`, but not necessarily the same logical subject/fact/metric/relationship identity.

A future persistence implementation should prevent semantically unrelated Facts from superseding each other merely because both are `Fact` records.

The exact logical-identity rule is a design decision and should be defined before physical persistence is frozen.

#### REVIEW-EVID-001 — late evidence / evidence-time semantics

Current reciprocal references prove graph consistency, but do not explicitly define whether a Fact may initially reference Evidence accepted later than the Fact, or how late evidence/backfill affects as-of reconstruction.

This should be explicit because later confirmation and contradiction are first-class Corporate Intelligence behaviors.

### 6.3 Provider contract kit

Current fixture-based tests prove bounded pagination, cursor continuation, partial retryable failure, timestamp shape, page bounds, provider revision typing, cursor-loop rejection and secret/raw-payload exclusion.

They do **not** prove that real SEC/IR/News/Official provider payloads conform to the adapter contract. Those guarantees belong to I0-007 formal acceptance plus individual adapter acceptance tests.

### 6.4 SEC form filter

Current tests strongly cover the reviewed strict allowlist, amendments, legacy/current 13D/13G names, near-miss rejection and replay identity behavior.

They do not prove the full SEC pipeline: incremental filing detection, FilingRecord persistence, filing-document acquisition, XBRL normalization, segment fallback or Canary acceptance.

### 6.5 Worker runtime tests

Worker integration tests provide stronger runtime assurance than the current Local Corporate stack. Verified repository behavior includes scheduled Shadow execution, digest persistence/history, no-write Prediction Shadow planning, injected-provider Live acquisition, D1 bars/receipts/checkpoints, stale-attempt replacement, holiday no-work behavior, shortened sessions, finalization lag and idempotent replanning.

Known Worker operational gaps remain separately tracked, including controlled provider failure/next-Cron retry, pause + historical catch-up, complete Canary symbol progress and remaining operational regression/coverage evidence.

## 7. Worker / Local responsibility review

### Worker responsibility currently realized or strongly planned

- fixed monitoring universe and cadence
- MarketData provider route
- market calendar/session normalization
- scheduled market acquisition
- overlap/checkpoint/idempotent bar acceptance
- D1 market-state persistence
- Shadow/Live execution boundary
- Prediction Shadow/provisional market-prediction path

### Local responsibility currently realized or strongly planned

- Corporate source/entity/provenance contracts
- Corporate checkpoint/idempotency contracts
- logical Fact Store
- temporary-content lifecycle
- SEC Filing / fundamental extraction
- Earnings
- News metadata/extraction/retention
- Official source/signals
- Local read-only API / timeline integration
- Cross-Market validation extension

### Responsibility gaps requiring planning decision

#### GAP-WBS-FFT-001 — FFT implementation ownership

Normative requirement and HLD component exist, but no current Worker/Local implementation package closes `REQ-FFT-001..006` and `REQ-VER-012`.

Decision required:

- assign FFT to Local analysis after Worker/D1 import, or
- explicitly place computation in Worker/another component while keeping Derived Metrics provider-neutral.

The current architecture suggests Local is the safer default because long-window 1/7/20/60-day analysis is not required for the Worker acquisition critical path, but this review does not make that ownership decision normative.

#### GAP-WBS-REG-001 — Regime Engine implementation ownership

`REQ-REG-001..026`, `REQ-VER-006..010` and `REQ-VER-014` have an HLD component but no dedicated current Corporate Intelligence WBS package.

The Local Corporate pipeline currently reaches SEC/Earnings/News/Official/X0 without a dedicated Regime workstream. The project cannot satisfy the v0.1 Definition of Done without adding one.

#### GAP-WBS-ANL-001 — Analyst Consensus implementation package

A0 currently focuses on Cross-Market hypothesis validation. It does not fully implement the parent-specification Analyst Consensus requirements:

- as-of Consensus Snapshot acquisition/persistence,
- analyst/firm rating revision events,
- price-target revision events,
- median/average/dispersion derived metrics,
- current-price-to-consensus-gap metrics.

A dedicated work package or an expanded A0 package is required.

#### GAP-REQ-TRACE-001 — requirement map must be refreshed

Before presenting a project-wide coverage ratio as authoritative, update `REQUIREMENTS_TRACEABILITY_v0.1.md` to assign stable IDs to Analyst Consensus and Cross-Market normative behavior added to the current parent specification.

## 8. Recommended planning-adjustment candidates

The following are **review recommendations only**. Do not mark them as accepted backlog until the Web review updates the appropriate authority documents.

| Review candidate | Suggested target | Priority | Reason |
|---|---|---|---|
| `REVIEW-TEMP-001` temporal lineage/as-of tests | I0-005 follow-up or new I0 hardening task | High | Prevent future-information leakage before Regime/Cross-Market logic builds on Fact Store |
| `REVIEW-SUP-001` supersession logical identity | I0-005 follow-up / physical-store design prerequisite | High | Same record type alone is not a sufficient historical identity invariant |
| `REVIEW-EVID-001` late-evidence semantics | I0-005/I0-006 integration decision | Medium-High | Contradiction and later confirmation depend on explicit temporal semantics |
| `GAP-REQ-TRACE-001` refresh traceability | Requirements traceability | High | Current 87-ID baseline does not cover all current normative parent sections |
| `GAP-WBS-FFT-001` add FFT package | WBS + CP + PROG | High for v0.1 DoD | Six normative FFT requirements currently have no closing work package |
| `GAP-WBS-REG-001` add Regime package | WBS + CP + PROG | Critical for v0.1 DoD | 26 Regime requirements and multiple verification targets lack a dedicated implementation lane |
| `GAP-WBS-ANL-001` add Analyst Consensus package | WBS extension + CP + PROG | High | Parent specification exceeds current A0 implementation scope |
| Local persistence transaction/crash tests | L0/L1/I0/X0 placement decision | Medium-High | Current Local contracts do not prove database atomicity or crash consistency |

## 9. Proposed Web review procedure

Use this file as a repeatable review input rather than editing WBS/CP/PROG during every observation.

Recommended review sequence:

1. **Requirement freshness check**
   - compare current Code of Truth against `REQUIREMENTS_TRACEABILITY_v0.1.md`;
   - add missing stable requirement IDs first.
2. **Coverage check**
   - map each requirement or requirement group to HLD and Worker/Local work packages;
   - classify `EXPLICIT / PARTIAL / MISSING`.
3. **Realization check**
   - classify `RUNTIME-VERIFIED / CONTRACT-ACCEPTED / PROVISIONAL / PLANNED / UNPLANNED` from repository evidence only.
4. **Test-assurance check**
   - record what current tests prove and separately record untested semantics.
5. **Adjustment decision**
   - only confirmed gaps become WBS changes;
   - update CP only when dependency/gate structure changes;
   - update PROG only when runtime status or restart point changes.
6. **Recalculate coverage indicators**
   - never use the 63.2% baseline after requirement IDs or work-package ownership change without recalculation.

## 10. Current review disposition

### Confirmed gaps requiring Web-side planning review

- Requirement traceability is stale relative to Analyst Consensus / Cross-Market parent-spec additions.
- FFT has no dedicated closing implementation package.
- Regime Engine has no dedicated closing implementation package.
- Analyst Consensus acquisition/snapshot/revision behavior is only partially represented by A0.
- Fact Store temporal-lineage/future-reference behavior requires explicit hardening before as-of-sensitive downstream analytics.

### Not a reason to revoke current Accepted status by itself

The above findings do not automatically invalidate `I0-002..005` Accepted status. Those tasks satisfy their currently documented contract completion conditions. The review instead identifies additional integration/hardening work necessary to guarantee broader system requirements and end-to-end historical correctness.

### Recommended immediate ordering for planning discussion

1. refresh requirement traceability for the current parent specification;
2. decide whether temporal-lineage hardening is inserted before or alongside `I0-006`;
3. add Regime and FFT packages to the implementation plan;
4. define the Analyst Consensus implementation package;
5. recalculate Worker/Local requirement-plan coverage;
6. then amend CP/PROG only where the newly accepted work changes dependency order or restart state.
