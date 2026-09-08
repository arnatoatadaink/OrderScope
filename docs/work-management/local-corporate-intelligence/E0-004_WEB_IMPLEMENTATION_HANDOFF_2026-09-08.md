# OrderScope — E0-004 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-08
Task: `E0-004`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `E0-002`, Accepted `E0-003`, Accepted I0-005 Fact Store

## 1. Web implementation scope

Implemented deterministic, provider-neutral extraction of basic observed earnings metrics into the accepted Fact Store boundary.

Changed/added files:

- `analysis/app/orderscope_local/earnings/basic_facts.py`
- `analysis/app/orderscope_local/earnings/__init__.py`
- `analysis/tests/earnings/test_basic_facts.py`
- `analysis/tests/earnings/test_basic_facts_idempotency.py`

## 2. Supported basic metrics

The bounded v0.1 extractor supports:

- revenue
- net income
- basic EPS
- diluted EPS

Each input observation must explicitly provide:

- Corporate Canary instrument (`AMD` or `NVDA`)
- issuer fiscal-year label
- issuer fiscal quarter
- `period_end`
- optional `period_start` only when established
- metric type
- finite Decimal value
- explicit currency
- GAAP/non-GAAP accounting basis
- Fact assertion kind
- accepted I0-002 `Provenance`
- optional extraction confidence only when established

No missing value, fiscal label, period, currency, source timestamp, or accounting basis is inferred.

## 3. Fact Store mapping

Each source-grounded observation creates one deterministic Fact/Evidence pair:

- Fact type: `earnings.<metric>`
- exact observed Decimal is serialized as plain decimal text in `value.amount`
- `value` also preserves currency, accounting basis, fiscal-year label, and fiscal quarter
- unit is explicit: currency for revenue/net income, `<currency>_per_share` for EPS
- `period_start` remains null when absent
- `period_end` is preserved as source date precision
- Fact provenance remains the observation source provenance
- reciprocal Tier-1 official Evidence points to the durable source locator

The result is validated through the accepted I0-005 `validate_fact_store` contract.

## 4. Cross-source and idempotency boundary

E0-004 deliberately does not collapse SEC and issuer-IR observations into one Fact even when their semantic value is identical.

Reason: the accepted Fact contract carries one primary `Provenance` per Fact. Keeping source-grounded Facts independent preserves both source histories without inventing a primary source. Cross-source agreement/disagreement reconciliation remains E0-007 work.

For repeat acquisition of the same canonical source URL and content hash:

- identical source-established semantics collapse idempotently even if retrieval/availability/acceptance operational timestamps differ;
- the earliest operational observation is retained deterministically;
- if source-established timestamps or provider revision semantics conflict for the same source/hash extraction identity, extraction raises an explicit conflict instead of silently choosing one.

## 5. Canary fixtures encoded

Focused tests cover:

- AMD Q2 FY2026 revenue Fact/Evidence mapping
- AMD diluted EPS exact decimal text and per-share unit
- GAAP vs non-GAAP as distinct Facts
- identical SEC and IR semantic values retained as separate source Facts
- exact duplicate observation idempotency
- repeat retrieval with changed operational timestamps retaining the first observation
- same source/hash with conflicting source timestamp rejected
- NVIDIA `FY2027` preserved while `period_end` remains calendar 2026
- rejection of non-finite values, implicit/lowercase currency, and non-Canary instruments
- no inference of missing period start or source publication/event timestamps

## 6. Explicit non-scope

E0-004 does not:

- parse raw SEC/IR HTML or XBRL into observed values
- infer missing values or fiscal periods
- calculate consensus, surprise, growth, or other Derived Metrics
- reconcile conflicting SEC/IR values
- implement segment revenue fallback

Those remain later tasks. E0-005 consumes the E0-004 Fact boundary for segment-revenue fallback.

## 7. Local verification boundary

Before promoting `E0-004` to Accepted, run:

```bash
uv run pytest -q analysis/tests/earnings/test_basic_facts.py analysis/tests/earnings/test_basic_facts_idempotency.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full regression suite, and clean diff check. Semantic review should confirm that source-specific Facts are retained and that no absent value/time/period is synthesized.

## 8. Next action after acceptance

If local verification passes, promote `E0-004` to Accepted and begin `E0-005` segment-revenue fallback chain as a separate cycle using the existing WEB-009 research input.
