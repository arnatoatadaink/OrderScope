# OrderScope — N0-002 Web Implementation Handoff

Status: **Accepted — local verification passed**
Date: 2026-09-09
Task: `N0-002`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `I0-007`, Accepted `N0-001`
Provider decision: `ADR_NEWS_PROVIDER_v0.1.md`

## 1. WBS completion boundary

N0-002 fetches AMD/NVDA News metadata through a bounded window/cursor and normalizes article identity, headline, publisher, URL, and timestamps without leaking provider JSON into Core.

The implementation adds a provider-specific Alpaca decoder behind the Accepted common AdapterPage/AdapterItem boundary. It does not persist News Facts and does not perform N0-003 canonical-URL or syndication decisions.

## 2. Changed/added files

- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/app/orderscope_local/news/alpaca.py`
- `analysis/tests/news/test_alpaca_news_metadata_adapter.py`

## 3. Accepted local verification

User-reported local verification after the cursor-loop fix:

```text
focused N0-002 tests -> 13 passed
full pytest suite     -> 268 passed
git diff --check      -> clean / no findings
```

The earlier `7 failed, 4 passed` run was caused solely by treating terminal `None == None` as a repeated cursor. The repository fix limits cursor-loop detection to repeated non-null opaque tokens; the final local verification above confirms the fix and full regression.

## 4. Bounded request contract

Accepted source keys are limited to the Corporate Canary:

- `news:alpaca:amd` -> provider query symbol `AMD`
- `news:alpaca:nvda` -> provider query symbol `NVDA`

The adapter maps the common UTC `AdapterRequest.window_start/window_end` to Alpaca RFC-3339 `start/end`, forwards the opaque `page_token`, uses ascending update order, and enforces Alpaca's documented page limit of 1–50.

The local common contract remains half-open. The provider query itself is the acquisition bound; item `created_at` is not used to discard an item because Alpaca orders News by update date and an older article may legitimately be returned after an in-window update.

## 5. Body exclusion

N0-002 always calls the transport with `include_content = false`.

If a provider payload nevertheless contains an article `content` field, the page is rejected as a sanitized non-retryable `body_leak` error.

`AdapterItem.temporary_content` is always `None` in N0-002. N0-004 is the only lane allowed to acquire a body into the Accepted temporary-content lifecycle.

## 6. Normalized metadata

`NewsArticleMetadata` preserves provider key, stable provider article ID, query symbol, headline, publisher/source, optional provider URL, created/published time, updated time, optional author/summary, provider symbol tags, and body-capability metadata.

Provider symbol tags are observations only and are not treated as Corporate identity truth.

## 7. Identity / idempotency handoff

Each normalized article becomes an Accepted I0-004 `ContentIdentity`:

- stable identity: provider-scoped article ID (`alpaca-news`, article ID)
- content hash: deterministic SHA-256 over normalized metadata only

Retrieval time, cursor, credentials, raw provider response, and body content do not participate in the content identity.

N0-002 does not decide whether two different provider article IDs are syndicated duplicates. That is N0-003.

## 8. Timestamp / error boundary

- `created_at` and `updated_at` remain separate `SourceTimestamp` values.
- `updated_at < created_at` is rejected.
- an older created article may be retained when returned after a later update.
- 429 and transport failures are sanitized and do not advance the cursor.
- terminal `next_page_token=None` is valid; only a repeated non-null token is a cursor loop.

## 9. News lane state

```text
N0-001 Accepted
N0-002 Accepted
N0-003 Ready
N0-004 Ready
N1-001 Ready independently
```

## 10. Next action

Proceed to N0-003 canonical URL / duplicate / syndication handling. N0-004 may proceed later in parallel where file overlap is controlled.
