from __future__ import annotations

from datetime import datetime, timezone

import pytest

from orderscope_local.crypto_derivatives import (
    ContractType,
    CryptoDerivativeContractError,
    CryptoDerivativeObservation,
    MarginType,
    comparable_snapshot_group,
    diagnose_funding_rate,
    diagnose_mark_price,
    diagnose_open_interest_usd,
)

UTC = timezone.utc


def _obs(
    venue: str,
    *,
    second: int = 0,
    instrument: str = "BTCUSDT",
    oi: float | None = 1_000.0,
    funding: float | None = 0.0001,
    mark: float | None = 100.0,
) -> CryptoDerivativeObservation:
    observed_at = datetime(2026, 10, 1, 0, 0, second, tzinfo=UTC)
    return CryptoDerivativeObservation(
        observation_id=f"{venue}:{instrument}:{second}",
        venue=venue,
        instrument_id=instrument,
        contract_type=ContractType.PERPETUAL,
        margin_type=MarginType.LINEAR,
        quote_asset="USDT",
        observed_at=observed_at,
        available_at=observed_at,
        accepted_at=observed_at,
        source_ref=f"test:{venue}",
        open_interest_usd=oi,
        funding_rate=funding,
        mark_price=mark,
    )


def test_group_requires_unique_venues_and_deterministic_order() -> None:
    grouped = comparable_snapshot_group((_obs("OKX"), _obs("BINANCE"), _obs("BYBIT")))
    assert tuple(item.venue for item in grouped) == ("BINANCE", "BYBIT", "OKX")


def test_group_rejects_mixed_instrument() -> None:
    with pytest.raises(CryptoDerivativeContractError):
        comparable_snapshot_group((_obs("BINANCE"), _obs("BYBIT", instrument="ETHUSDT")))


def test_group_rejects_duplicate_venue() -> None:
    with pytest.raises(CryptoDerivativeContractError):
        comparable_snapshot_group((_obs("BINANCE"), _obs("BINANCE", second=1)))


def test_group_rejects_excess_time_skew() -> None:
    with pytest.raises(CryptoDerivativeContractError):
        comparable_snapshot_group((_obs("BINANCE", second=0), _obs("BYBIT", second=20)), max_skew_seconds=10)


def test_open_interest_diagnostic_uses_median_and_lineage() -> None:
    diagnostic = diagnose_open_interest_usd(
        (
            _obs("BINANCE", oi=900.0),
            _obs("BYBIT", oi=1_000.0),
            _obs("OKX", oi=1_300.0),
        )
    )
    assert diagnostic.median_value == 1_000.0
    assert diagnostic.max_abs_deviation == 300.0
    assert diagnostic.max_relative_deviation == pytest.approx(0.3)
    assert diagnostic.method_version == "uwbs-077-v1"
    assert diagnostic.input_observation_ids == tuple(
        item.observation_id for item in comparable_snapshot_group(
            (_obs("BINANCE", oi=900.0), _obs("BYBIT", oi=1_000.0), _obs("OKX", oi=1_300.0))
        )
    )


def test_funding_diagnostic_handles_negative_values() -> None:
    diagnostic = diagnose_funding_rate(
        (
            _obs("BINANCE", funding=-0.0002),
            _obs("BYBIT", funding=0.0),
            _obs("OKX", funding=0.0004),
        )
    )
    assert diagnostic.median_value == 0.0
    assert diagnostic.max_abs_deviation == pytest.approx(0.0004)
    assert diagnostic.max_relative_deviation is None


def test_mark_price_diagnostic_reports_relative_deviation() -> None:
    diagnostic = diagnose_mark_price((_obs("BINANCE", mark=100.0), _obs("BYBIT", mark=102.0)))
    assert diagnostic.median_value == 101.0
    assert diagnostic.max_abs_deviation == 1.0
    assert diagnostic.max_relative_deviation == pytest.approx(1 / 101)


def test_diagnostic_rejects_missing_metric() -> None:
    with pytest.raises(CryptoDerivativeContractError):
        diagnose_open_interest_usd((_obs("BINANCE", oi=None), _obs("BYBIT", oi=1_000.0)))


def test_group_rejects_less_than_two_observations() -> None:
    with pytest.raises(CryptoDerivativeContractError):
        comparable_snapshot_group((_obs("BINANCE"),))


def test_group_rejects_invalid_skew_argument() -> None:
    with pytest.raises(CryptoDerivativeContractError):
        comparable_snapshot_group((_obs("BINANCE"), _obs("BYBIT")), max_skew_seconds=-1)
