# OrderScope — X0-001 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `X0-001`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L1-005`, `I0-005`, `E0-007`, `N1-005`, `O0-005`

## 1. Local acceptance carried into this cycle

`L1-005` is Accepted from user-reported local evidence:

```text
focused L1-005 tests -> 12 passed
full pytest suite    -> 391 passed
git diff --check     -> clean / no findings
```

This satisfies the final explicit X0-001 dependency on the fixture path. Real D1 promotion remains separately gated by `L1-003` / `SMOKE-007`.

## 2. WBS completion boundary

X0-001 implements a read-only unified timeline query over:

- canonical market bars;
- Filing Facts;
- Earnings/Fundamental Facts;
- News Facts;
- Official/Policy Facts.

The query is deterministic and as-of safe. It does not mutate records, invent source timestamps, or collapse contradictory source records.

## 3. Changed/added files

- `analysis/app/orderscope_local/integration/__init__.py`
- `analysis/app/orderscope_local/integration/timeline.py`
- `analysis/tests/integration/test_unified_timeline.py`

## 4. Versioned timeline contract

Schema version:

```text
unified-timeline-v0.1
```

Timeline source kinds:

```text
market
filing
earnings
news
official
other_fact
```

## 5. As-of / ordering semantics

The timeline is ordered by **information availability**, not by a fabricated event instant.

For Fact records:

```text
available_at = Fact.provenance.available_at
accepted_at  = Fact.accepted_at
```

A Fact is visible only when both are no later than the query `as_of` instant.

For market bars:

```text
available_at = receipt_time
accepted_at  = receipt_time
```

because the canonical market dataset preserves provider receipt provenance but does not create a separate Fact-Store acceptance timestamp.

The stable sort key is:

```text
available_at
accepted_at
source_kind
subject_ref
item_id
```

This provides deterministic knowledge-order replay.

## 6. Source event time boundary

If a Fact has an exact UTC `event_time.instant`, it is exposed as optional timeline metadata.

If the source establishes only a calendar date, X0-001 does **not** coerce it to midnight or another invented instant. Date-only source timestamps therefore remain outside the ordering key.

Publication, filing, and other source timestamps remain on the underlying Fact/Provenance record and are not silently rewritten by the timeline layer.

## 7. Market-data boundary

`read_market_timeline_bars()` reads the accepted L1-004 canonical Parquet and returns immutable market timeline records containing:

- symbol;
- bar time;
- receipt time;
- OHLCV;
- source manifest ID;
- source artifact SHA-256.

It never reads the L1-002 raw SQL fixture and does not expose provider credentials or raw dump content.

## 8. Timeline item boundary

A `TimelineItem` contains only lightweight integration metadata:

```text
schema_version
source_kind
item_id
subject_ref
available_at
accepted_at
event_time (optional exact instant)
payload_ref (source reference / manifest identity)
```

Fact values, article bodies, SEC document bodies, and raw market payloads are not copied into the timeline object. Downstream readers can resolve the referenced durable record separately.

## 9. Fact classification

Fact type prefixes are mapped conservatively:

- filing / SEC -> `filing`;
- earnings / fundamental / segment -> `earnings`;
- news -> `news`;
- official / policy -> `official`;
- otherwise -> `other_fact`.

This classification does not modify the Fact itself and does not infer economic meaning.

## 10. Focused fixtures encoded

The focused module currently contains 7 tests covering:

1. knowledge-availability ordering versus event-time ordering;
2. exclusion of future-available/future-accepted Facts;
3. no fabricated instant for date-only source event time;
4. deterministic Fact source-kind classification;
5. market receipt time as timeline availability;
6. deterministic tie-breaking independent of input order;
7. market dataset lineage preservation.

## 11. Explicit non-scope

X0-001 does not:

- implement localhost HTTP API endpoints;
- implement coverage/source-health summary;
- schedule ingestion;
- execute the real D1 export;
- mutate Facts or market datasets;
- resolve contradictions;
- synthesize missing market bars;
- convert date-only source timestamps to instants.

`X0-002` owns coverage summary. `X0-003` owns read-only API integration after its dependencies are satisfied.

## 12. Local verification boundary

Run:

```bash
uv run pytest -q analysis/tests/integration/test_unified_timeline.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Acceptance requires focused tests, full regression, compileall success, and clean diff check.

## 13. Next action after acceptance

After X0-001 acceptance, the next integration work should be selected against the runtime tracker. `X0-003` still requires `X0-002` and `L0-004`; `X0-004` requires adapter availability and `L0-006`. Therefore do not jump directly to API/scheduler work without reconciling those foundation gates.
