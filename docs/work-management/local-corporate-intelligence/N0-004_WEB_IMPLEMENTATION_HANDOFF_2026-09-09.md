# OrderScope — N0-004 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `N0-004`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `I0-006`, Accepted `N0-002`

## 1. Local acceptance carried into this cycle

`N0-003` was promoted to Accepted from user-reported local evidence:

```text
focused N0-003 tests -> 11 passed
full pytest suite     -> 279 passed
git diff --check      -> clean / no findings
```

## 2. WBS completion boundary

N0-004 must keep News body content outside durable metadata and allow only extraction-time access through expiring content references.

This implementation connects Alpaca News body capability to the Accepted I0-006 TemporaryContent lifecycle without changing Fact Store or N0-002 durable metadata.

## 3. Changed/added files

- `analysis/app/orderscope_local/news/body.py`
- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/tests/news/test_news_temporary_body_access.py`

## 4. Body acquisition boundary

`AlpacaNewsBodyAccessor` receives two injected boundaries:

- `NewsBodyTransport`: fetch one provider article body by stable provider article ID;
- `TemporaryBodyStore`: stage that body in temporary storage and return an opaque content reference.

The accessor itself does not expose a body-bearing result. `NewsBodyAcquisition` contains only:

- provider article ID;
- SHA-256 content hash;
- Accepted `TemporaryContent` audit record.

The raw body exists only between the injected transport and temporary store call.

## 5. Retention policy

Newly acquired content is staged as:

```text
retention_class = temporary_success
state           = staged
```

Default success TTL is 6 hours and is configurable only within `(0, 1 day]` in this bounded implementation. This is intentionally much shorter than the exception maximum and leaves N1-005 responsible for deletion after extraction.

`exception_record()` creates `temporary_exception` lifecycle records and delegates the Accepted I0-006 maximum of 30 days to the common contract.

## 6. Capability and rights guardrail

Acquisition is rejected before provider access when `body_capability` is false. N0-004 therefore cannot bypass a provider/account rights decision by scraping the publisher URL.

The N0-001 provider ADR remains authoritative: Alpaca body use is only authorized for the current personal/non-commercial local Canary boundary and must be re-reviewed before business/commercial/redistributed use.

## 7. Error boundary

Provider failures use sanitized `AlpacaNewsRequestFailure` values.

- provider 429 or retryable failure remains retryable with optional retry-after;
- unexpected transport exception -> `body_transport_error`, retryable;
- empty/missing content -> `body_unavailable`, non-retryable for that provider observation;
- body over 5 MiB -> `body_too_large`, non-retryable at this bounded implementation;
- temporary storage failure -> `temporary_store_error`, retryable.

Provider body text, local paths, and exception messages are not copied into the returned failure metadata.

## 8. Hash / durable handoff

The accessor hashes the UTF-8 body before staging and returns only `ContentHash` metadata with the opaque `content_ref`. This supports later Evidence/extraction lineage after the raw body has been deleted.

The body hash is not an article canonicalization key and does not replace N0-003 article identity/syndication logic.

## 9. Focused fixtures encoded

The focused test module contains 8 tests covering:

1. body is staged but absent from returned durable result;
2. success TTL is bounded to one day;
3. provider body capability false blocks transport access;
4. sanitized retryable provider/rate-limit failure;
5. empty body as non-retryable unavailable content;
6. temporary-store failure sanitization;
7. exception retention is accepted at 30 days and rejected beyond 30 days;
8. naive/non-UTC capture clock is rejected.

These tests use in-memory injected fixtures. They do not perform live Alpaca requests or write body content to the repository.

## 10. Explicit non-scope

N0-004 does not yet:

- implement a concrete credential-bearing HTTP transport;
- implement physical temporary storage or encryption-at-rest policy;
- run extraction;
- mark extraction success;
- delete successful/exception bodies;
- produce deletion proof;
- expose body content through HTTP/API;
- bypass provider body capability via publisher scraping.

N1-003 owns the extraction boundary and N1-005 owns retention/deletion control.

## 11. Local verification boundary

Before promoting N0-004 to Accepted, run:

```bash
uv run pytest -q analysis/tests/news/test_news_temporary_body_access.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full regression, and clean diff check.

## 12. News lane state

```text
N0-001 Accepted
N0-002 Accepted
N0-003 Accepted
N0-004 Provisional result — local test pending

N1-001 Ready
N1-002 waits for N1-001 (N0-003 already Accepted)
N1-003 waits for N0-004 + N1-002
```

## 13. Next action after acceptance

After N0-004 acceptance, the News acquisition lane is complete at the contract/fixture boundary. The shortest path toward N1-005/X0 then moves to `N1-001 — freeze event taxonomy`, followed by deterministic N1-002 extraction.
