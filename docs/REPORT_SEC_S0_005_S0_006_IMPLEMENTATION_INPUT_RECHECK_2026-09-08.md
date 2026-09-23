# OrderScope — SEC S0-005 / S0-006 Implementation Input Recheck

Status: Web recheck complete / local handoff ready
Date: 2026-09-08
Scope: `S0-005` filing-document acquisition / `S0-006` Company Facts/XBRL adapter
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Checked at: 2026-09-07T22:10Z
Evidence class: official SEC documentation

## 1. Purpose

Reconfirm the SEC public interfaces and access constraints needed immediately before local implementation of `S0-005` and `S0-006`. This report does not mark either parent task complete; implementation, fixtures, retry behavior, persistence, and acceptance tests remain local work.

## 2. S0-005 — filing-document acquisition

### Confirmed official behavior

- Public EDGAR filing documents are available under `/Archives/edgar/data/{CIK}/{accession-without-dashes}/...`.
- A filing directory contains all documents submitted for that filing.
- The filing index page is available as `.../{accession}-index.html`; machine-readable directory indexes (`index.json`, `index.xml`) are also available in CIK/accession directories.
- The accession number is the stable EDGAR submission identifier and must remain distinct from document identity/hash.
- SEC guidance states filings are often available on `sec.gov` within roughly 1–3 minutes of the EDGAR system timestamp. Therefore a Submissions record can precede document availability; document acquisition failure must remain retryable rather than being treated as a permanent missing document.

### Local implementation consequence

Recommended acquisition sequence:

1. Start from the accepted `FilingRecord` accession/CIK/primary-document reference from `S0-003`.
2. Construct the accession directory using the accession number with dashes removed.
3. Fetch only the required primary document or explicitly selected attachment; do not crawl the entire archive tree.
4. Hash the retrieved bytes/content and register them through the accepted `I0-006` temporary-content lifecycle.
5. Preserve HTTP/retrieval failure as retryable state. Do not convert a temporarily unavailable document into a durable `missing` Fact.
6. Keep accession identity, document reference, and content hash as separate fields.

## 3. S0-006 — Company Facts/XBRL adapter

### Confirmed official behavior

- `data.sec.gov` exposes public REST JSON APIs without API keys/authentication.
- Company Facts endpoint: `/api/xbrl/companyfacts/CIK##########.json`.
- Company Concept endpoint: `/api/xbrl/companyconcept/CIK##########/{taxonomy}/{tag}.json`.
- SEC states Company Facts aggregates facts across submissions only when they use a non-custom taxonomy (for example `us-gaap`, `ifrs-full`, `dei`, `srt`) and apply to the entire filing entity.
- Company Concept/Company Facts organize reported values by unit of measure; unit must therefore be preserved rather than normalized away at ingestion.
- SEC explicitly warns that company reporting calendars and reporting periods do not necessarily align with calendar-quarter boundaries.
- APIs are updated throughout the day; SEC documentation describes typical XBRL API processing delay as under one minute, while noting peak-period delays can be longer.
- Bulk `companyfacts.zip` exists and is updated nightly, but the current AMD/NVDA Canary does not require bulk ingestion.

### Important limitation for Fact normalization

Company Facts is not a complete representation of every filing-level XBRL fact. The official API boundary excludes custom-taxonomy facts and restricts aggregation to facts applying to the entire entity. Therefore:

- absence from Company Facts must not be interpreted as "the company did not disclose this value";
- dimensional/segment extraction may require filing-instance XBRL or filing-table fallback;
- the `E0-005` fallback chain (`Company Facts → XBRL Dimension → Filing Fallback`) remains necessary;
- source taxonomy/tag, unit, period/context, accession/source reference, and retrieval timestamps must be retained before any provider-neutral mapping.

## 4. Access / Fair Access recheck

Current SEC guidance continues to state:

- maximum automated access guideline: 10 requests/second total per user/IP scope described by SEC;
- scripted clients should declare a User-Agent identifying the requester and contact information;
- clients should download only what is needed and avoid excessive crawling;
- `data.sec.gov` does not support browser CORS, which is irrelevant to the local Python adapter but should not be mistaken for an API failure.

The existing source-wide limiter and declared User-Agent requirements from `WEB-005` remain valid implementation inputs.

## 5. Suggested local tests

### S0-005

- accession path construction removes dashes only for the directory component;
- primary-document fetch produces a deterministic content hash;
- duplicate fetch of identical content is idempotent;
- temporary 404/availability lag remains retryable;
- document body is registered as temporary content and is not embedded in durable `FilingRecord` metadata;
- User-Agent and source-wide limiter are applied.

### S0-006

- Company Facts values preserve taxonomy/tag, unit, start/end or instant period, accession/form/source reference, and filed/retrieval provenance where supplied/derived by the accepted contract;
- multiple units for a concept do not collapse into one value;
- entity-wide standard-taxonomy facts normalize successfully;
- absence of a desired segment/custom fact produces an explicit fallback reason rather than a fabricated zero/null semantic;
- duplicate API retrieval is idempotent;
- non-calendar fiscal periods are not forced into calendar-quarter labels.

## 6. Effect on Critical Path

No task status changes from this Web recheck.

- `S0-005`: remains Ready; Web implementation inputs reconfirmed.
- `S0-006`: remains Ready; Web implementation inputs reconfirmed.
- `S0-007`: remains Provisional until `S0-004..006` are integrated and the formal AMD/NVDA acceptance test is executed.

The next Core CP action remains one bounded local implementation cycle for either `S0-005` or `S0-006`.

## 7. Official evidence

- SEC — EDGAR Application Programming Interfaces (APIs): https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC — Accessing EDGAR Data: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- SEC — Developer Resources: https://www.sec.gov/about/developer-resources
- SEC — Webmaster Frequently Asked Questions: https://www.sec.gov/about/webmaster-frequently-asked-questions
- SEC — Web Site Privacy and Security Policy: https://www.sec.gov/about/privacy-information
- SEC Data APIs: https://data.sec.gov/

## 8. Unknowns / not completed here

- Exact local temporary-content storage implementation for filing documents.
- Exact provider-neutral Python type mapping for Company Facts/XBRL.
- AMD/NVDA live-fetch acceptance evidence.
- S0-007 formal acceptance thresholds/evidence after S0-005 and S0-006 integration.

Do not infer these from this report; resolve them from local implementation/test evidence.
