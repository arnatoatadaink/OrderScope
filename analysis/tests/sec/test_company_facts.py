from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.sec import (
    SEC_DATA_ORIGIN,
    SecCompanyFactsAdapter,
    SecRequestFailure,
    XbrlDimension,
    XbrlPeriod,
    normalize_xbrl_fact,
)


NOW = datetime(2026, 9, 8, 1, tzinfo=timezone.utc)


class Transport:
    def __init__(self, value):
        self.value = value
        self.calls = []

    def get_json(self, url, *, user_agent):
        self.calls.append((url, user_agent))
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class Limiter:
    def __init__(self):
        self.calls = 0

    def acquire(self):
        self.calls += 1


def payload():
    return {
        "cik": 2488,
        "entityName": "ADVANCED MICRO DEVICES INC",
        "facts": {"us-gaap": {"RevenueFromContractWithCustomerExcludingAssessedTax": {
            "label": "Revenue", "description": "provider-only metadata",
            "units": {"USD": [
                {"start": "2026-03-29", "end": "2026-06-27", "val": 7685000000,
                 "accn": "0000002488-26-000121", "fy": 2026, "fp": "Q2", "form": "10-Q",
                 "filed": "2026-08-04", "frame": "CY2026Q2"},
                {"start": "2025-01-01", "end": "2025-12-31", "val": 1,
                 "accn": "0000002488-26-000010", "form": "10-K", "filed": "2025-12-31"},
            ]}
        }}}
    }


def make_adapter(value):
    transport, limiter = Transport(value), Limiter()
    adapter = SecCompanyFactsAdapter(transport=transport, limiter=limiter,
                                     user_agent="OrderScope ops@example.test", clock=lambda: NOW)
    return adapter, transport, limiter


def test_company_facts_normalizes_unit_period_and_source_without_provider_json():
    adapter, transport, limiter = make_adapter(payload())
    page = adapter.fetch(source_key="sec:companyfacts:amd", window_start=date(2026, 1, 1),
                         window_end=date(2027, 1, 1), page_size=10)

    assert page.error is None
    assert len(page.facts) == 1
    fact = page.facts[0]
    assert fact.concept == "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
    assert fact.value == Decimal("7685000000")
    assert fact.unit == "USD"
    assert (fact.period.start, fact.period.end, fact.period.instant) == (
        date(2026, 3, 29), date(2026, 6, 27), None)
    assert fact.dimensions == ()
    assert fact.source_accession == "0000002488-26-000121"
    assert fact.filing_source_ref.endswith("/2488/000000248826000121")
    assert not hasattr(fact, "label") and not hasattr(fact, "frame") and not hasattr(fact, "provider_json")
    assert transport.calls == [(f"{SEC_DATA_ORIGIN}/api/xbrl/companyfacts/CIK0000002488.json",
                                "OrderScope ops@example.test")]
    assert limiter.calls == 1


def test_generic_xbrl_normalizer_preserves_canonical_dimensions_and_instant():
    fact = normalize_xbrl_fact(
        concept="amd:SegmentRevenue", value="12.50", unit="USD",
        start=None, end="2026-06-27",
        dimensions={"srt:ProductOrServiceAxis": "amd:DataCenterMember",
                    "us-gaap:StatementBusinessSegmentsAxis": "amd:ReportableSegmentMember"},
        accession="0000002488-26-000121", form="10-Q", filed="2026-08-04",
        source_ref="https://www.sec.gov/ixviewer/doc/action",
    )
    assert fact.value == Decimal("12.50")
    assert fact.period.instant == date(2026, 6, 27)
    assert fact.dimensions == tuple(sorted(fact.dimensions, key=lambda item: (item.axis, item.member)))
    assert all(isinstance(value, XbrlDimension) for value in fact.dimensions)


def test_company_facts_paginates_after_window_filtering():
    adapter, _, limiter = make_adapter(payload())
    first = adapter.fetch(source_key="sec:companyfacts:amd", window_start=date(2025, 1, 1),
                          window_end=date(2027, 1, 1), page_size=1)
    second = adapter.fetch(source_key="sec:companyfacts:amd", window_start=date(2025, 1, 1),
                           window_end=date(2027, 1, 1), cursor=first.next_cursor, page_size=1)
    assert first.next_cursor == "offset:1"
    assert [first.facts[0].filed_on, second.facts[0].filed_on] == [date(2025, 12, 31), date(2026, 8, 4)]
    assert second.next_cursor is None
    assert limiter.calls == 2


def test_invalid_provider_shape_and_transport_failure_are_sanitized():
    adapter, _, _ = make_adapter({"cik": 2488, "facts": {"us-gaap": []}})
    page = adapter.fetch(source_key="sec:companyfacts:amd", window_start=date(2026, 1, 1),
                         window_end=date(2027, 1, 1))
    assert page.error.category == "invalid_response"
    assert page.error.retryable is False
    assert page.facts == ()

    adapter, _, _ = make_adapter(SecRequestFailure("rate_limited", True))
    page = adapter.fetch(source_key="sec:companyfacts:amd", window_start=date(2026, 1, 1),
                         window_end=date(2027, 1, 1))
    assert page.error.category == "rate_limited"
    assert page.error.retryable is True
    assert page.error.message == "SEC Company Facts request failed"


@pytest.mark.parametrize(
    "observation_change",
    [
        {"form": None},
        {"accn": "0001045810-26-000121"},
    ],
)
def test_rejects_malformed_or_cross_company_fact_sources(observation_change):
    value = payload()
    observation = value["facts"]["us-gaap"]["RevenueFromContractWithCustomerExcludingAssessedTax"]["units"]["USD"][0]
    observation.update(observation_change)
    adapter, _, _ = make_adapter(value)

    page = adapter.fetch(source_key="sec:companyfacts:amd", window_start=date(2026, 1, 1),
                         window_end=date(2027, 1, 1))

    assert page.error.category == "invalid_response"
    assert page.error.retryable is False
    assert page.facts == ()


def test_rejects_ambiguous_periods_dimensions_and_unbounded_inputs():
    with pytest.raises(ContractViolation, match="QName"):
        XbrlDimension("axis", "amd:Member")
    with pytest.raises(ContractViolation, match="both instant and duration"):
        XbrlPeriod(date(2026, 1, 1), date(2026, 3, 31), date(2026, 3, 31))
    adapter, _, _ = make_adapter(payload())
    with pytest.raises(ContractViolation, match="cursor"):
        adapter.fetch(source_key="sec:companyfacts:amd", window_start=date(2026, 1, 1),
                      window_end=date(2027, 1, 1), cursor="1")
    with pytest.raises(ContractViolation, match="corporate canary"):
        adapter.fetch(source_key="sec:companyfacts:msft", window_start=date(2026, 1, 1),
                      window_end=date(2027, 1, 1))


def test_untyped_transport_failure_remains_retryable_without_leaking_details():
    adapter, _, _ = make_adapter(RuntimeError("provider body secret-token"))
    page = adapter.fetch(source_key="sec:companyfacts:amd", window_start=date(2026, 1, 1),
                         window_end=date(2027, 1, 1))
    assert page.error.category == "transport_error"
    assert page.error.retryable is True
    assert "secret-token" not in page.error.message
