# OrderScope — N0-002 Web Implementation Handoff

Status: **Provisional result — cursor-loop fix applied / local recheck pending**
Date: 2026-09-09
Task: `N0-002`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `I0-007`, Accepted `N0-001`
Provider decision: `ADR_NEWS_PROVIDER_v0.1.md`

## 1. WBS completion boundary

N0-002 must fetch AMD/NVDA News metadata through a bounded window/cursor and normalize article identity, headline, publisher, URL, and timestamps without leaking provider JSON into Core.

This implementation adds a provider-specific Alpaca decoder behind the Accepted common AdapterPage/AdapterItem boundary. It does not persist News Facts and does not perform N0-003 canonical-URL or syndication decisions.

## 2. Changed/added files

- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/app/orderscope_local/news/alpaca.py`
- `analysis/tests/news/test_alpaca_news_metadata_adapter.py`

## 3. Bounded request contract

Accepted source keys are limited to the Corporate Canary:

- `news:alpaca:amd` -> provider query symbol `AMD`
- `news:alpaca:nvda` -> provider query symbol `NVDA`

The adapter maps the common UTC `AdapterRequest.window_start/window_end` to Alpaca RFC-3339 `start/end`, forwards the opaque `page_token`, uses ascending update order, and enforces Alpaca's documented page limit of 1–50.

The local common contract remains half-open. The provider query itself is the acquisition bound; item `created_at` is not used to discard an item because Alpaca orders News by update date and an older article may legitimately be returned after an in-window update.

## 4. Body exclusion

N0-002 always calls the transport with:

```text
include_content = false
```

If a provider payload nevertheless contains an article `content` field, the page is rejected as a sanitized non-retryable `body_leak` error.

`AdapterItem.temporary_content` is always `None` in N0-002. N0-004 is the only lane allowed to acquire a body into the Accepted temporary-content lifecycle.

## 5. Normalized metadata

`NewsArticleMetadata` preserves:

- provider key (`alpaca-news`)
- stable provider article ID
- query symbol used for acquisition
- headline
- publisher/source string
- provider-supplied article URL when available
- source `created_at` as `published_at`
- provider `updated_at` separately
- author when available
- summary when available
- provider symbol tags as observations only
- provider body-capability flag

Alpaca documents article URL as applicable rather than universal; therefore `article_url` is nullable. Stable provider article ID remains required.

Provider symbol tags are not treated as Corporate identity truth. For example, an AMD query may return an item tagged only NVDA; the adapter retains both the AMD query scope and the provider tag without silently changing the Corporate subject.

## 6. Identity / idempotency handoff

Each normalized article becomes an Accepted I0-004 `ContentIdentity`:

- stable identity: provider-scoped article ID (`alpaca-news`, article ID)
- content hash: deterministic SHA-256 over normalized metadata only

Retrieval time, cursor, credentials, raw provider response, and body content do not participate in the content identity.

N0-002 does not decide whether two different provider article IDs are syndicated duplicates. That is N0-003.

## 7. Timestamp boundary

Alpaca RFC-3339 `created_at` and `updated_at` are normalized into `SourceTimestamp` UTC instants.

- `created_at` is preserved independently from `updated_at`.
- `updated_at < created_at` is rejected as invalid provider response.
- an article created before the requested window may still be retained if the provider returns it because of a later update.
- `retrieved_at` remains a separate operational timestamp and is never copied into source publication/update time.

## 8. Partial/error/rate-limit behavior

The transport may raise a sanitized `AlpacaNewsRequestFailure` with category, retryable flag, and optional retry-after.

The adapter converts it to the common `ErrorInfo` contract without provider body or credentials. In particular:

- rate limiting can be represented as retryable with bounded retry-after;
- error pages never advance the cursor;
- generic transport exceptions become sanitized retryable `transport_error`;
- malformed provider responses become non-retryable `invalid_response`;
- a repeated **non-null** next-page token is rejected as `cursor_loop`;
- `next_page_token=None` with `request.cursor=None` is a normal terminal page, not a cursor loop.

No permanent Alpaca RPM constant is embedded in the adapter.

## 9. Local failure and fix

The first local focused run reported:

```text
7 failed, 4 passed
```

All seven failures shared one root cause: the adapter compared `next_cursor == request.cursor` without excluding the normal `None == None` terminal state. A successful first/last page with no next token was therefore incorrectly converted to `cursor_loop` before article normalization.

Repository fix:

```python
if next_cursor is not None and request.cursor is not None and next_cursor == request.cursor:
    raise AlpacaNewsRequestFailure("cursor_loop", False)
```

Regression fixtures now separately cover:

- terminal `None` cursor is accepted;
- repeated non-null opaque token is rejected as `cursor_loop`.

The failure was pagination-state logic only; it did not indicate a metadata normalization/body-boundary defect.

## 10. Focused fixtures encoded

The focused test module now contains 13 tests covering:

1. AMD bounded metadata acquisition with `include_content=false`;
2. opaque page-token forwarding/return;
3. terminal `None` token is a valid completion state;
4. repeated non-null page token is a cursor loop;
5. provider symbol tags remain observations rather than query identity truth;
6. article created before the window is retained when returned as an updated article;
7. missing provider article URL remains nullable metadata;
8. body field rejection at the N0-002 boundary;
9. retryable 429-style failure with no cursor advance;
10. generic transport failure sanitization;
11. AMD/NVDA source scope and provider page-size enforcement;
12. invalid updated-before-created timestamp rejection;
13. deterministic ContentIdentity for repeated identical metadata.

Fixtures are provider-contract cases only and make no live claim about current AMD/NVDA News coverage.

## 11. Explicit non-scope

N0-002 does not yet:

- perform live Alpaca credential/entitlement checks;
- provide a concrete HTTP client implementation with key headers;
- parse or retain full News body content;
- canonicalize article URLs;
- detect syndication across different provider article IDs;
- decide duplicate/update/conflict beyond the common stable-identity handoff;
- map provider ticker tags to durable company/instrument identity;
- generate event Facts.

Canonical URL / duplicate / syndication handling is N0-003. Temporary body access is N0-004.

## 12. Current official provider documentation checked during implementation

The current Alpaca REST News reference documents:

- endpoint `GET https://data.alpaca.markets/v1beta1/news`;
- `start`, `end`, `symbols`, `limit` 1–50, `page_token`, and `include_content`;
- sorting by updated date;
- 429 rate-limit behavior and rate-limit response headers.

The current real-time News schema documents article ID, headline, summary, author, created/updated RFC-3339 timestamps, content, URL when applicable, symbols, and source.

These provider-specific fields remain isolated to the Alpaca adapter.

## 13. Local verification boundary

Before promoting N0-002 to Accepted, rerun:

```bash
uv run pytest -q analysis/tests/news/test_alpaca_news_metadata_adapter.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full regression, and clean diff check. Semantic review should confirm that News body content never crosses N0-002, provider ticker tags do not become identity truth, and terminal/repeated cursor behavior remains compatible with I0-007.

## 14. News lane state

```text
N0-001 Accepted
N0-002 Provisional result — cursor fix applied / local recheck pending
N0-003 gated by N0-002 acceptance
N0-004 gated by N0-002 acceptance
N1-001 Ready independently
```

## 15. Next action after acceptance

After N0-002 acceptance, the shortest News critical path is N0-003 — canonical URL / duplicate handling. N0-004 may then proceed in parallel where file overlap is controlled. N1-001 remains a safe independent parallel task.
