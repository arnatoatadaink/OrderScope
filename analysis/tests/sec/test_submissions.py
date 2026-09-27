from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import (
    AdapterRequest,
    ContractViolation,
    StableIdentity,
    assert_page_contract,
    checkpoint_for_page,
    collect_pages,
)
from orderscope_local.sec import (
    SEC_DATA_ORIGIN,
    FixedIntervalSecRateLimiter,
    SecRequestFailure,
    SecSubmissionsAdapter,
)


NOW = datetime(2026, 9, 8, 1, tzinfo=timezone.utc)
WINDOW_START = datetime(2025, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 9, 1, tzinfo=timezone.utc)


def columns(*rows):
    names = ("accessionNumber", "filingDate", "reportDate", "acceptanceDateTime", "form", "primaryDocument")
    return {name: [row[index] for row in rows] for index, name in enumerate(names)}


AMD_RECENT = columns(
    ("0000002488-26-000121", "2026-08-04", "2026-06-27", "20260804161624", "8-K", "amd-20260804.htm"),
    ("0000002488-24-000001", "2024-12-31", "", "", "10-K", "amd-old.htm"),
)
AMD_HISTORY = columns(
    ("0000002488-25-000108", "2025-07-30", "2025-06-28", "20250730160000", "10-Q", "amd-20250628.htm"),
)


class FixtureTransport:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def get_json(self, url, *, user_agent):
        self.calls.append((url, user_agent))
        value = self.payloads[url]
        if isinstance(value, Exception):
            raise value
        return value


class CountingLimiter:
    def __init__(self):
        self.calls = 0

    def acquire(self):
        self.calls += 1


def root(recent=AMD_RECENT, files=()):
    return {"cik": 2488, "lastModified": "2026-09-08T00:00:00Z", "filings": {"recent": recent, "files": list(files)}}


def adapter(payloads):
    transport = FixtureTransport(payloads)
    limiter = CountingLimiter()
    return SecSubmissionsAdapter(
        transport=transport,
        user_agent="OrderScope ops@example.test",
        limiter=limiter,
        clock=lambda: NOW,
    ), transport, limiter


def test_fetches_only_bounded_amd_rows_and_normalizes_provider_json():
    url = f"{SEC_DATA_ORIGIN}/submissions/CIK0000002488.json"
    value, transport, limiter = adapter({url: root()})
    request = AdapterRequest("sec:submissions:amd", WINDOW_START, WINDOW_END, page_size=10)

    page = value.fetch(request)

    assert_page_contract(page, request)
    assert len(page.items) == 1
    item = page.items[0]
    assert item.normalized == {
        "cik": "0000002488",
        "ticker": "AMD",
        "accession": "0000002488-26-000121",
        "form": "8-K",
        "filed_on": "2026-08-04",
        "period_end": "2026-06-27",
        "source_accepted_at": "20260804161624",
        "primary_document": "amd-20260804.htm",
    }
    assert item.content_identity.identity == StableIdentity.filing_accession("0000002488-26-000121")
    assert "filings" not in item.normalized and "recent" not in item.normalized
    assert transport.calls == [(url, "OrderScope ops@example.test")]
    assert limiter.calls == 1


def test_loads_only_intersecting_history_and_paginates_within_original_window():
    root_url = f"{SEC_DATA_ORIGIN}/submissions/CIK0000002488.json"
    history_url = f"{SEC_DATA_ORIGIN}/submissions/CIK0000002488-submissions-001.json"
    payload = root(
        files=(
            {"name": "CIK0000002488-submissions-001.json", "filingFrom": "2025-01-01", "filingTo": "2025-12-31"},
            {"name": "CIK0000002488-submissions-002.json", "filingFrom": "2020-01-01", "filingTo": "2020-12-31"},
        )
    )
    value, transport, limiter = adapter({root_url: payload, history_url: AMD_HISTORY})
    request = AdapterRequest("sec:submissions:amd", WINDOW_START, WINDOW_END, page_size=1)

    pages = collect_pages(value, request)

    assert [item.normalized["accession"] for page in pages for item in page.items] == [
        "0000002488-25-000108", "0000002488-26-000121"
    ]
    assert pages[0].next_cursor == "offset:1"
    assert limiter.calls == 4
    assert all("submissions-002" not in call[0] for call in transport.calls)
    final = checkpoint_for_page(provider_key="sec", request=AdapterRequest(
        request.source_key, request.window_start, request.window_end, cursor="offset:1", page_size=1
    ), page=pages[-1])
    assert final.resume_cursor is None


def test_canary_scope_declared_user_agent_and_cursor_are_strict():
    value, _, _ = adapter({})
    with pytest.raises(ContractViolation, match="corporate canary"):
        value.fetch(AdapterRequest("sec:submissions:msft", WINDOW_START, WINDOW_END))
    with pytest.raises(ContractViolation, match="cursor"):
        value.fetch(AdapterRequest("sec:submissions:amd", WINDOW_START, WINDOW_END, cursor="1"))
    with pytest.raises(ContractViolation, match="User-Agent"):
        SecSubmissionsAdapter(transport=FixtureTransport({}), user_agent="generic-bot", limiter=CountingLimiter())


def test_transport_failure_is_sanitized_retryable_and_does_not_advance_cursor():
    url = f"{SEC_DATA_ORIGIN}/submissions/CIK0001045810.json"
    value, _, limiter = adapter({url: SecRequestFailure("rate_limited", True, timedelta(minutes=10))})
    request = AdapterRequest("sec:submissions:nvda", WINDOW_START, WINDOW_END, page_size=10)

    page = value.fetch(request)

    assert page.items == ()
    assert page.next_cursor is None
    assert page.error.category == "rate_limited"
    assert page.error.retry_after == timedelta(minutes=10)
    assert page.error.message == "SEC request failed"
    assert "rate_limited" not in page.error.message
    assert limiter.calls == 1
    assert_page_contract(page, request)


@pytest.mark.parametrize("bad_recent", [
    {"accessionNumber": ["0000002488-26-000121"]},
    columns(("bad-accession", "2026-08-04", "", "", "8-K", "doc.htm")),
])
def test_malformed_provider_shape_becomes_nonretryable_sanitized_error(bad_recent):
    url = f"{SEC_DATA_ORIGIN}/submissions/CIK0000002488.json"
    value, _, _ = adapter({url: root(recent=bad_recent)})

    page = value.fetch(AdapterRequest("sec:submissions:amd", WINDOW_START, WINDOW_END))

    assert page.error.category == "invalid_response"
    assert page.error.retryable is False
    assert page.items == ()


def test_rejects_mismatched_cik_and_history_file_before_cross_company_fetch():
    root_url = f"{SEC_DATA_ORIGIN}/submissions/CIK0000002488.json"
    wrong_cik = root()
    wrong_cik["cik"] = 1045810
    value, _, _ = adapter({root_url: wrong_cik})
    assert value.fetch(AdapterRequest("sec:submissions:amd", WINDOW_START, WINDOW_END)).error.category == "invalid_response"

    wrong_history = root(files=(
        {"name": "CIK0001045810-submissions-001.json", "filingFrom": "2025-01-01", "filingTo": "2025-12-31"},
    ))
    value, transport, _ = adapter({root_url: wrong_history})
    page = value.fetch(AdapterRequest("sec:submissions:amd", WINDOW_START, WINDOW_END))
    assert page.error.category == "invalid_response"
    assert len(transport.calls) == 1


def test_rejects_non_utc_or_unbounded_request_before_network_access():
    value, transport, _ = adapter({})
    with pytest.raises(ContractViolation, match="UTC"):
        value.fetch(AdapterRequest("sec:submissions:amd", WINDOW_START.replace(tzinfo=None), WINDOW_END))
    with pytest.raises(ContractViolation, match="page_size"):
        value.fetch(AdapterRequest("sec:submissions:amd", WINDOW_START, WINDOW_END, page_size=0))
    assert transport.calls == []


def test_fixed_interval_limiter_enforces_configured_rate_and_public_ceiling():
    timestamps = iter((0.0, 0.0, 0.125))
    sleeps = []
    limiter = FixedIntervalSecRateLimiter(
        requests_per_second=8,
        monotonic=lambda: next(timestamps),
        sleep=sleeps.append,
    )

    limiter.acquire()
    limiter.acquire()

    assert sleeps == [0.125]
    with pytest.raises(ContractViolation, match="10"):
        FixedIntervalSecRateLimiter(requests_per_second=10.1)
