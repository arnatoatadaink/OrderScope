from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.cross_market.alpaca_daily import (
    DEFAULT_A0_ALPACA_BINDINGS,
    DailySeriesBinding,
    collect_a0_alpaca_daily,
)
from orderscope_local.cross_market.validation import SeriesMeasure, SeriesRole

UTC = timezone.utc


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def get_daily_bars(self, **kwargs):
        self.calls.append(kwargs)
        crypto = kwargs["crypto"]
        token = kwargs["page_token"]
        if crypto:
            return {
                "bars": {
                    "BTC/USD": [
                        {"t": "2026-09-01T00:00:00Z", "c": 110000.0, "v": 12.5},
                        {"t": "2026-09-02T00:00:00Z", "c": 111000.0, "v": 13.5},
                    ]
                },
                "next_page_token": None,
            }
        if token is None:
            return {
                "bars": {
                    "CBRS": [{"t": "2026-09-01T04:00:00Z", "c": 41.0, "v": 1000.0}],
                    "NVDA": [{"t": "2026-09-01T04:00:00Z", "c": 180.0, "v": 2000.0}],
                },
                "next_page_token": "page-2",
            }
        return {
            "bars": {
                "QQQ": [{"t": "2026-09-01T04:00:00Z", "c": 620.0, "v": 3000.0}],
                "SOXX": [{"t": "2026-09-01T04:00:00Z", "c": 350.0, "v": 4000.0}],
            },
            "next_page_token": None,
        }


def test_collects_stock_and_crypto_price_volume_with_pagination() -> None:
    transport = FakeTransport()
    result = collect_a0_alpaca_daily(
        transport=transport,
        start=date(2026, 8, 26),
        end_exclusive=date(2026, 9, 5),
    )
    assert len(result) == 12
    assert [call["crypto"] for call in transport.calls] == [False, False, True]
    assert transport.calls[1]["page_token"] == "page-2"
    keys = {(item.role, item.measure, item.analysis_date) for item in result}
    assert (SeriesRole.CBRS, SeriesMeasure.PRICE, date(2026, 9, 1)) in keys
    assert (SeriesRole.CBRS, SeriesMeasure.VOLUME, date(2026, 9, 1)) in keys
    assert (SeriesRole.BTC, SeriesMeasure.PRICE, date(2026, 9, 2)) in keys


def test_stock_daily_value_becomes_available_at_1600_new_york() -> None:
    result = collect_a0_alpaca_daily(
        transport=FakeTransport(),
        start=date(2026, 9, 1),
        end_exclusive=date(2026, 9, 2),
    )
    cbrs = next(item for item in result if item.role is SeriesRole.CBRS and item.measure is SeriesMeasure.PRICE)
    assert cbrs.available_at == datetime(2026, 9, 1, 20, 0, tzinfo=UTC)


def test_crypto_daily_value_becomes_available_at_next_utc_day() -> None:
    result = collect_a0_alpaca_daily(
        transport=FakeTransport(),
        start=date(2026, 9, 1),
        end_exclusive=date(2026, 9, 3),
    )
    btc = next(item for item in result if item.role is SeriesRole.BTC and item.measure is SeriesMeasure.PRICE and item.analysis_date == date(2026, 9, 1))
    assert btc.available_at == datetime(2026, 9, 2, 0, 0, tzinfo=UTC)


def test_default_bindings_cover_four_stock_roles_and_btc() -> None:
    assert {(item.role, item.is_crypto) for item in DEFAULT_A0_ALPACA_BINDINGS} == {
        (SeriesRole.CBRS, False),
        (SeriesRole.NVDA, False),
        (SeriesRole.US_MARKET, False),
        (SeriesRole.AI_SEMICONDUCTOR_PROXY, False),
        (SeriesRole.BTC, True),
    }


def test_rejects_invalid_bar_shape() -> None:
    class BadTransport:
        def get_daily_bars(self, **kwargs):
            return {"bars": {"CBRS": [{"t": "2026-09-01T04:00:00Z", "c": "bad", "v": 1.0}]}, "next_page_token": None}

    with pytest.raises(ContractViolation, match="close must be numeric"):
        collect_a0_alpaca_daily(
            transport=BadTransport(),
            start=date(2026, 9, 1),
            end_exclusive=date(2026, 9, 2),
            bindings=(DailySeriesBinding(role=SeriesRole.CBRS, symbol="CBRS", source_ref="alpaca:stock:CBRS"),),
        )
