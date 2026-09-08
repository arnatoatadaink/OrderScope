# OrderScope — O0-001 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `O0-001`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Research input: `REPORT_OFFICIAL_SOURCE_REGISTRY_WEB_015_2026-09-04.md`
Depends on: Accepted `W0-003`, Accepted `I0-001`

## 1. Selection rationale

The E0 Earnings/Fundamental lane is Accepted through E0-007. The integrated Critical Path branches after E0 into `N1 / O0 / X0`.

- X0 remains gated by other local/news/official lane dependencies.
- N1 can begin taxonomy work, but later N1 extraction depends on the N0 news-acquisition lane.
- O0-001 has its W0/I0 prerequisites satisfied and independently opens the Official Context lane.

Therefore O0-001 was selected as the next bounded Core cycle.

## 2. Web implementation scope

Implemented an immutable v0.1 official Actor/source registry from the accepted WEB-015 research seed.

Changed/added files:

- `analysis/app/orderscope_local/official/__init__.py`
- `analysis/app/orderscope_local/official/registry.py`
- `analysis/tests/official/test_registry.py`

## 3. Actor boundary

The registry fixes five source-owner/content-actor identities:

- The White House
- U.S. Department of the Treasury
- Board of Governors of the Federal Reserve System
- Federal Open Market Committee
- U.S. Securities and Exchange Commission

FOMC remains distinct from the Federal Reserve Board. Individual officials are not pre-created or assigned from office/title guesses; later item processing must resolve an explicitly declared person when present.

## 4. Source registry seed

The implementation carries the twelve WEB-015 official discovery entries:

- White House: News, Briefings & Statements, Presidential Actions, Fact Sheets
- Treasury: Press Releases, Statements & Remarks
- Federal Reserve Board: News & Events, Press Releases, Speeches & Testimony
- SEC Agency: Newsroom, Press Releases, Speeches & Statements

Each source retains:

- internal `source_id`
- source lane
- canonical entry URL
- owner and publisher Actor IDs
- source type
- content-actor resolution mode
- OrderScope policy adoption date
- Web observation timestamp
- official evidence reference IDs

## 5. Permanent semantic boundaries

- Hostname alone never establishes content Actor identity.
- Canonical item URLs are not generated from path/slug patterns in O0-001.
- Listing query/filter state is not part of canonical source identity.
- White House item actor mode is `ITEM_DECLARED`; the site owner is not silently substituted for an unresolved President/official.
- FOMC publications are not collapsed into the Federal Reserve Board Actor.
- SEC Agency Newsroom sources remain separate from the existing SEC EDGAR filing lane.
- District Federal Reserve Banks are not added to the v0.1 source allowlist.
- `policy_valid_from=2026-09-04` is an OrderScope adoption date, not an inferred external source launch date.

## 6. Focused tests encoded

Tests cover:

- five unique Actor identities and twelve unique source identities
- owner/publisher references resolve to registered Actors
- FOMC remains distinct from Fed Board
- SEC Agency seed contains no EDGAR source
- White House declared-item Actor behavior
- lane/hostname mismatch rejection
- query-bearing canonical entry URL rejection
- unknown Actor reference rejection
- fixed policy-adoption/observation timestamps from WEB-015

## 7. Explicit non-scope

O0-001 does not yet:

- fetch official feeds/pages
- decide RSS/API/listing pagination strategy
- resolve redirects
- classify updates/deletes
- parse item publication/effective times
- distinguish statement/proposal from implemented/effective policy Fact
- link official items to AMD/NVDA or semiconductor themes

Those remain O0-002 through O0-005. WEB-016 is the existing research input for O0-002 feed behavior.

## 8. Local verification boundary

Before promoting O0-001 to Accepted, run:

```bash
uv run pytest -q analysis/tests/official/test_registry.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, the full regression suite, and clean diff check. Semantic review should confirm that owner/publisher identity is not treated as automatic item content-actor identity and that SEC Agency remains separate from SEC EDGAR.

## 9. Next action after acceptance

If local verification passes, promote O0-001 to Accepted and begin `O0-002 — official-feed adapter` as a separate cycle, reconciling the registry against `REPORT_OFFICIAL_FEED_BEHAVIOR_WEB_016_2026-09-04.md` and the accepted I0-007 adapter contracts.
