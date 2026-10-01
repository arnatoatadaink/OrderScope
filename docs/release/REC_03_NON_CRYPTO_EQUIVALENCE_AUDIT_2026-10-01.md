# REC-03 — Non-crypto reconstructed lane semantic-equivalence audit — 2026-10-01

Status: **IMPLEMENTED / VALIDATION PENDING**

Branch:

```text
codex/post-v0-1-6-reconciliation-audit
```

REC-02 acceptance:

```text
bb5b68c28015e59af8a3fe216465ed8c8d114683
```

REC-03 selective replay commit:

```text
9a40e29112e0cfae50828be7270cf1995ec53b97
```

## Purpose

REC-03 audits non-crypto paths that exist on the reconstructed v0.1.6 lineage against the later UWBS-100 baseline. The goal is not to merge the old branch. The goal is to preserve later accepted implementations and replay only reconstructed capabilities that are actually absent.

## Classification

### Macro contracts — PRESERVED / IDENTICAL OR LATER SUPERSET

The cumulative branch already contains the reconstructed macro contracts, including:

```text
analysis/app/orderscope_local/contracts/macro_market.py
analysis/app/orderscope_local/contracts/macro_stress.py
analysis/app/orderscope_local/contracts/market_reaction.py
analysis/app/orderscope_local/contracts/market_relationship.py
analysis/app/orderscope_local/contracts/repricing_state.py
```

Direct blob verification for `macro_market.py` shows the same blob on both lineages:

```text
055cf78931def136d396fb86e145d04adfa77da8
```

The later `contracts/__init__.py` is already classified by REC-02 as a later accepted superset.

Decision:

```text
KEEP LATER ACCEPTED
NO REPLAY
```

### Cross-market macro adapters and metrics — PRESERVED / IDENTICAL CORE + LATER EXTENSIONS

The cumulative branch contains the reconstructed files such as:

```text
cftc_positioning.py
fred_alfred.py
fred_fallback_policy.py
japan_macro_sources.py
macro_metrics.py
ny_fed_rates.py
official_macro_sources.py
relative_repricing.py
validation.py
```

Representative blob checks show reconstructed core files retained unchanged while the cumulative branch additionally contains later work including Alpaca daily, BTC/MSTR IV, cross-asset replay/capacity, and other UWBS-080..100 extensions.

Decision:

```text
KEEP LATER ACCEPTED SUPERSET
NO REPLAY
```

### Storage / custody / restore — PRESERVED / IDENTICAL CORE + LATER EXTENSION

The cumulative branch already contains the reconstructed storage modules:

```text
backup.py
d1_bounded_export.py
d1_custody.py
d1_custody_quality.py
migrations.py
restore_drill.py
```

Their checked blobs match the reconstructed lineage. The cumulative branch additionally contains later storage functionality such as `d1_remote_export.py`.

Decision:

```text
KEEP LATER ACCEPTED SUPERSET
NO REPLAY
```

### Worker / news / scheduler / D1 lifecycle — PRESERVED

Representative Worker/news files and migrations are present on the cumulative branch. Direct checks include:

```text
src/news.ts
migrations/0007_news_metadata.sql
```

with identical blobs between the reconstructed and cumulative lineages:

```text
src/news.ts                     d806d6eb7fd3e0a6c6f69dd5065b6c56f4887850
migrations/0007_news_metadata.sql 60f60703bac30a657cbcc6ff92b2d1832e8fccfe
```

The cumulative branch has extensive later Worker history beyond these reconstructed changes, so wholesale replay is prohibited.

Decision:

```text
KEEP LATER ACCEPTED
NO WHOLESALE REPLAY
```

### Listing compliance — MISSING / REPLAYED

Before REC-03, this package was absent from the cumulative branch:

```text
analysis/app/orderscope_local/listing_compliance/
```

The reconstructed package and focused test were replayed unchanged:

```text
analysis/app/orderscope_local/listing_compliance/__init__.py
analysis/app/orderscope_local/listing_compliance/models.py
analysis/app/orderscope_local/listing_compliance/rules.py
analysis/tests/listing_compliance/test_listing_compliance.py
```

Decision:

```text
RECONSTRUCTED_ONLY_REQUIRED
REPLAYED
```

### Theme model — MISSING / REPLAYED

Before REC-03, this package was absent from the cumulative branch:

```text
analysis/app/orderscope_local/theme/
```

The reconstructed package and focused test were replayed unchanged:

```text
analysis/app/orderscope_local/theme/__init__.py
analysis/app/orderscope_local/theme/calibration.py
analysis/app/orderscope_local/theme/observation.py
analysis/app/orderscope_local/theme/ontology.py
analysis/app/orderscope_local/theme/reaction.py
analysis/app/orderscope_local/theme/state.py
analysis/tests/theme/test_theme.py
```

Decision:

```text
RECONSTRUCTED_ONLY_REQUIRED
REPLAYED
```

## Explicit exclusions

Historical release/work-management reports are evidence documents, not runtime dependencies. They are not bulk-replayed merely because they occur on the reconstructed branch.

The direct v0.1.6-to-main merge remains prohibited because the lineages diverged substantially and later accepted work must remain authoritative.

## Validation gate

Run after pulling the REC-03 replay:

```text
uv run pytest -q analysis/tests/listing_compliance
uv run pytest -q analysis/tests/theme
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check

npm test
npm run typecheck
```

Python focused tests prove the two replayed packages remain valid in the cumulative environment. Full Python regression checks interaction with UWBS-068..100. Worker tests/typecheck protect the later TypeScript/Cloudflare lineage that REC-03 intentionally kept rather than replacing.

## Acceptance rule

REC-03 may be marked Accepted only after the validation gate passes.

Current state:

```text
macro/contracts             PRESERVED
cross-market                PRESERVED / LATER SUPERSET
storage                     PRESERVED / LATER SUPERSET
Worker/news/scheduler       PRESERVED / LATER SUPERSET
listing_compliance          REPLAYED
Theme                       REPLAYED
REC-03 implementation       COMPLETE
REC-03 validation           PENDING
```
