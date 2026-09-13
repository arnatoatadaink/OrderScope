# OrderScope — O0-004 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `O0-004`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Research input: `REPORT_OFFICIAL_INSTRUMENT_THEME_LINKAGE_WEB_018_2026-09-04.md`
Depends on: Accepted `O0-003`, Accepted `I0-005`, Corporate Canary identity research/registry semantics

## 1. Local acceptance evidence

`O0-004` was promoted to Accepted from user-reported local evidence:

```text
focused relevance tests -> 9 passed
full pytest suite        -> 248 passed
git diff --check         -> clean / no findings
```

Semantic review boundary remains: theme-only and mention-only evidence cannot become AMD/NVDA direct instrument links without both identity and action/effect anchors.

## 2. WBS completion boundary

O0-004 distinguishes direct AMD/NVDA relevance from indirect semiconductor-theme relevance using Evidence.

Implemented classes:

- `official.direct_instrument`
- `official.theme_exposure`
- `official.mention_only`
- `official.unresolved`
- `official.no_link`

The linkage axis is separate from O0-003 semantic Fact kind. A decision, statement, proposal, or implementation Fact may independently have one or more relevance Relationships.

## 3. Changed/added files

- `analysis/app/orderscope_local/official/relevance.py`
- `analysis/app/orderscope_local/official/__init__.py`
- `analysis/tests/official/test_relevance.py`

## 4. Stable target identities

Corporate Canary instrument targets use the WEB-001 internal stable-ID proposal rather than ticker text:

- AMD: `us-sec-0000002488-common`
- NVIDIA: `us-sec-0001045810-common`

The versioned semiconductor theme target is `theme-semiconductor-v0.1` for this bounded O0-004 contract.

Ticker strings such as `AMD`/`NVDA` are rejected as durable direct-instrument relationship targets.

## 5. Direct-instrument threshold

`DIRECT_INSTRUMENT` requires all of:

1. target is one of the Corporate Canary stable instrument IDs;
2. identity basis is resolved from registry or same-document explicit identity;
3. the same Evidence establishes an action/effect basis such as license, regulation, grant, contract, enforcement, formal commitment, or measurable effect;
4. source-grounded Provenance and Tier-1 Evidence are retained.

Theme scope, mention-only, unresolved, or no-action basis cannot be promoted to a direct instrument Relationship.

## 6. Theme / mention / unresolved boundaries

`THEME_EXPOSURE`:
- targets only `theme-semiconductor-v0.1`;
- requires explicit semiconductor-theme scope;
- never fans out automatically to AMD/NVIDIA.

`MENTION_ONLY`:
- records an entity mention relation only;
- does not point to the Corporate Canary instrument ID merely because a company/CEO/product was named.

`UNRESOLVED`:
- uses `PENDING_REVIEW` Relationship assertion;
- requires explicit review reason;
- does not infer issuer/product identity.

`NO_LINK`:
- emits no Relationship or Evidence record;
- broad macro/AI/national-security language cannot fabricate a link.

## 7. Fact Store integration

Resolved/mention/unresolved links build one I0-005 external `Relationship` plus one Tier-1 `Evidence` record.

- Relationship is directed from semantic `subject_fact_id` to stable instrument/theme/entity candidate target.
- Relationship and Evidence are bidirectionally linked by record ID.
- Provenance is source-grounded and shared.
- no numeric confidence score is fabricated.

## 8. Focused fixtures encoded

Tests cover:

- AMD MI308-style direct instrument + semiconductor-theme links remain separate;
- NVIDIA H20-style direct link requires an action anchor;
- White House semiconductor proclamation can yield theme exposure but cannot auto-fan-out to AMD/NVDA;
- Jensen-Huang/NVIDIA mention remains mention-only rather than instrument relevance;
- unresolved product identity requires review reason and `PENDING_REVIEW`;
- no-link produces no durable Relationship/Evidence;
- ticker text is rejected as a durable instrument ID;
- Relationship/Evidence linkage and Tier-1 quality are preserved;
- duplicate Relationship/Evidence IDs are rejected.

Fixtures encode WEB-018 evidence thresholds and are not a complete live relevance dataset.

## 9. Explicit non-scope

O0-004 does not yet:

- parse raw official text to discover identity/action anchors automatically;
- resolve product-to-issuer registry mappings beyond supplied deterministic identity basis;
- infer Section 232/HTS applicability to AMD/NVIDIA products;
- calculate linkage confidence probabilities;
- define deeper semiconductor sub-theme taxonomy;
- run the combined Official Signal quality matrix.

Those quality/update/delete/timestamp/relevance-error cases belong to O0-005.

## 10. Current Official Context lane

```text
O0-001 Accepted
O0-002 Accepted
O0-003 Accepted
O0-004 Accepted
O0-005 Ready
```

## 11. Next action

Begin `O0-005 — Official Signal quality test`, combining O0-002 update/delete/timestamp behavior, O0-003 semantic Fact separation, and O0-004 relevance-error fixtures.
