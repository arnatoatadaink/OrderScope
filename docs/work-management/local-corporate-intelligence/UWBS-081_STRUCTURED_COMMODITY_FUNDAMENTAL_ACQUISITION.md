# OrderScope — UWBS-081 Structured Commodity Fundamental Acquisition

Status: **WEB IMPLEMENTATION READY — LOCAL ACCEPTANCE REQUIRED**
Scope: market-independent commodity fundamental Fact/acquisition boundary
Dependency: UWBS-080 ACCEPTED

## 1. Goal

Add provider-neutral structured petroleum fundamentals that can later explain
WTI/Brent moves without conflating source observations with higher-level market
interpretation.

UWBS-081 is observation/acquisition only. It does not classify:

- supply disruption;
- geopolitical escalation;
- shipping disruption;
- oil-down reason;
- inflation/growth regime;
- final consumer demand.

Those remain UWBS-082/083 or later interpretation layers.

## 2. Initial measures

The v0.1 contract covers:

- commercial crude stocks;
- Cushing crude stocks;
- Strategic Petroleum Reserve stocks;
- crude field production;
- crude refinery inputs;
- refinery utilization;
- imports;
- exports;
- product supplied.

Products initially represented are crude oil, motor gasoline, distillate fuel
oil, jet fuel, and total petroleum products. Geography is explicit for the U.S.,
PADD 1-5, and Cushing, Oklahoma.

## 3. Semantic safeguards

### Product supplied is not renamed demand

EIA describes product supplied as an approximate/proxy measure for consumption
because it measures petroleum leaving the primary supply chain. The Fact type is
therefore `commodity_fundamental.product_supplied`; downstream code must not
rename it `demand` or `consumption` without a separate interpretation/derived
metric.

Weekly product supplied can be noisy and source documentation recommends using
four-week averages for many analytical uses. A four-week average is therefore a
derived metric, not the raw UWBS-081 Fact.

### Stocks vs flows

Stock observations use `thousand_barrels` and represent period-end inventory
levels. Production, refinery inputs, imports, exports, and product supplied use
`thousand_barrels_per_day`. Refinery utilization uses `percent`.

### Cushing and SPR identities remain explicit

Cushing stocks are distinct from U.S. commercial crude stocks and are tied to
Cushing geography. SPR stocks are distinct from commercial stocks and remain a
separate measure.

### Negative source values are representable where the source can report them

Flow/accounting series are not globally forced positive. In particular, source
notes explain that product supplied can occasionally be negative because of
reclassification, late/misreported data, timing, or other accounting effects.
The contract therefore preserves finite negative source observations rather
than silently clipping them.

## 4. Initial source decision

Primary structured source candidate: **U.S. Energy Information Administration
(EIA) Open Data API v2 / petroleum routes**.

The official petroleum data surface exposes weekly supply estimates including
production, refinery inputs/utilization, stocks, imports, exports, and product
supplied, plus monthly/annual supply and disposition data.

Current EIA API v2 behavior relevant to the adapter:

- API datasets expose route metadata, data columns, facets, frequencies, and
  period formatting;
- values are returned as strings in current API v2 behavior;
- missing/withheld textual states must not be coerced into numeric observations;
- API transport credentials, pagination, retries, and quota handling remain
  outside the pure normalization function.

No live EIA API activation or secret configuration is part of UWBS-081 local
acceptance.

## 5. Code boundary

### Provider-neutral Fact contract

`analysis/app/orderscope_local/contracts/commodity_fundamental.py`

Defines:

- `CommodityFundamentalMeasure`;
- `CommodityProduct`;
- `CommodityGeography`;
- `CommodityFundamentalCadence`;
- `CommodityFundamentalObservation`.

### EIA normalization boundary

`analysis/app/orderscope_local/commodity/eia_petroleum.py`

Defines:

- `EiaPetroleumSeriesProfile`;
- `normalize_eia_petroleum_row(...)`.

The normalizer accepts one already-fetched EIA API row and produces one
provider-neutral observation. It does not perform HTTP calls.

For weekly rows, the EIA period is treated as the week-ending date and expanded
to a seven-day source period. Monthly and annual rows are expanded to their
calendar period bounds.

## 6. Provider routing rule

Production configuration must discover/verify route metadata and facets against
EIA before enabling a series. Test fixture series IDs are intentionally not
production identifiers.

A configured profile freezes:

- petroleum API route;
- provider series/facet identity;
- subject identity;
- normalized measure/product/geography/cadence;
- normalized unit.

A returned row with a conflicting series identity or unit is rejected rather
than reinterpreted.

## 7. Local acceptance

Run after pulling the implementation:

```bash
uv run pytest -q analysis/tests/contracts/test_commodity_fundamental.py
uv run pytest -q analysis/tests/commodity/test_eia_petroleum.py
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

Expected focused tests at this freeze:

```text
commodity fundamental contract: 9 tests
EIA petroleum normalizer:        7 tests
```

Full-suite count may increase if another lane lands concurrently; acceptance is
all tests passing rather than a permanently frozen repository-wide count.

## 8. Acceptance criteria

UWBS-081 can be Accepted when:

- both focused suites pass;
- full Python regression passes;
- compileall passes;
- git diff check passes;
- no live provider/runtime mutation was required;
- product supplied remains a proxy-labelled Fact;
- no UWBS-082/083 interpretation leaks into the observation contract.

## 9. Next dependencies

After UWBS-081 acceptance:

```text
UWBS-082 commodity supply/shipping/geopolitical event taxonomy
   |
   v
UWBS-083 oil-down-reason / inflation-growth-risk interpretation
```

UWBS-082 may use UWBS-081 observations as evidence but must not rewrite their
source semantics.
