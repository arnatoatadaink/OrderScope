# OrderScope — O0-002 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `O0-002`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Research input: `REPORT_OFFICIAL_FEED_BEHAVIOR_WEB_016_2026-09-04.md`
Depends on: Accepted `O0-001`, Accepted common checkpoint/provenance contracts

## 1. Web implementation scope

Implemented a provider-neutral bounded official-feed adapter contract from WEB-016.

Changed/added files:

- `analysis/app/orderscope_local/official/feed_adapter.py`
- `analysis/app/orderscope_local/official/__init__.py`
- `analysis/tests/official/test_feed_adapter.py`

## 2. Route policy

The v0.1 profiles encode only feed/index routes established by WEB-016:

- White House: HTML-index first
- U.S. Treasury: HTML-index first
- Federal Reserve Board press releases: official RSS first, HTML archive fallback
- Federal Reserve Board speeches/testimony: official RSS first, HTML archive fallback
- SEC Agency press releases: official RSS first, HTML listing fallback
- SEC Agency speeches/statements: official RSS first, HTML listing fallback

No guessed White House/Treasury WordPress-style feed URL is admitted.

Umbrella Newsroom/News entries remain registry discovery sources but are not required to have a standalone incremental profile when category-specific routes provide the bounded adapter path.

## 3. Normalized item contract

`OfficialDiscoveredItem` preserves:

- registry `source_id`
- canonical item URL taken from official discovery output
- accepted SHA-256 `ContentHash`
- UTC `retrieved_at`
- optional source-established `published_at`
- optional `event_time`
- optional page-level `source_last_update`
- explicit availability state

All source timestamps use the accepted `SourceTimestamp` contract. A source that exposes only a calendar date remains DATE_ONLY; midnight or UTC time is not fabricated.

Canonical item URLs must remain on the registered official hostname and cannot contain listing query/filter state.

## 4. Incremental checkpoint boundary

`OfficialFeedCheckpoint` retains:

- source ID
- checkpoint observation time
- explicit non-zero-capable overlap start chosen by configuration/caller
- latest source-established published date/time when available
- latest canonical item identity
- last successful HTML/archive reference when relevant

The contract does not assume that RSS/HTML ordering supplies an opaque stable cursor. Overlap acquisition and canonical URL/hash identity remain required for re-observation.

## 5. Partial/error boundary

`OfficialFeedPage` distinguishes:

- `complete`
- `partial`
- `error`

Partial/error pages require a sanitized error category and may preserve the last successful/next archive reference. The caller must not advance beyond unverified acquisition coverage merely because later pages exist.

## 6. Update/delete boundary

`classify_item_change` produces:

- `new`
- `unchanged`
- `changed`
- `listing_missing`
- `canonical_unavailable`

A content-hash change at the same canonical URL is a revision candidate.

A disappearance from a recent listing/feed does **not** become a deletion. `listing_missing` remains distinct from a canonical item fetch that establishes unavailability. Even `canonical_unavailable` is an availability observation, not an instruction to hard-delete retained Evidence/history.

## 7. Focused tests encoded

Tests cover:

- White House/Treasury HTML-first route policy
- Fed/SEC RSS-first route policy
- date-only timestamp precision without midnight inference
- content-hash update classification
- listing-missing vs canonical-unavailable distinction
- partial page/error preservation
- overlap checkpoint fields
- guessed White House RSS route rejection
- cross-host item rejection
- listing query state rejection for canonical item URL

## 8. Explicit non-scope

O0-002 does not yet:

- perform live HTTP requests
- parse RSS XML or site-specific HTML payloads
- measure overlap duration
- decide ETag/Last-Modified reliability
- automatically resolve 301/302 canonical redirects
- promote 404/410 to hard deletion
- parse policy statement/effective semantics
- persist OfficialStatement Facts

Those belong to runtime adapters and O0-003+ semantic work. WEB-017 is the existing research input for the next OfficialStatement implementation task.

## 9. Local verification evidence

Local verification completed on 2026-09-09:

```text
uv run pytest -q analysis/tests/official/test_feed_adapter.py  -> 9 passed
uv run pytest -q                                             -> 231 passed
git diff --check                                             -> clean / no findings
```

Semantic acceptance confirms that source timestamp precision is preserved, HTML/RSS routes are not guessed, and listing disappearance is never silently converted into deletion.

## 10. Acceptance and next action

`O0-002` is **Accepted** and is safe as the dependency for `O0-003`.

Next Core action: begin `O0-003 — Separate statement from implementation` using `REPORT_OFFICIAL_STATEMENT_IMPLEMENTATION_WEB_017_2026-09-04.md`, preserving statement/proposal/decision/implementation as distinct source-grounded Facts.
