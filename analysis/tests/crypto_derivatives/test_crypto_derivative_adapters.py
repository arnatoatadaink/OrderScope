from datetime import datetime, timezone

import pytest

from orderscope_local.crypto_derivatives import (
    ContractType,
    CryptoDerivativeAdapterError,
    MarginType,
    normalize_binance_coinm_open_interest,
    normalize_bybit_ticker,
    normalize_hyperliquid_asset_ctx,
    normalize_okx_public_snapshot,
)


UTC = timezone.utc
ACCEPTED = datetime(2026, 9, 30, 12, 5, tzinfo=UTC)
OBSERVED = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)


def test_binance_coinm_open_interest_normalizes_contracts() -> None:
    result = normalize_binance_coinm_open_interest(
        {
            "symbol": "BTCUSD_PERP",
            "pair": "BTCUSD",
            "openInterest": "15004",
            "contractType": "PERPETUAL",
            "time": 1790769600000,
        },
        accepted_at=ACCEPTED,
        source_ref="binance:/dapi/v1/openInterest",
    )
    assert result.venue == "BINANCE"
    assert result.contract_type is ContractType.PERPETUAL
    assert result.margin_type is MarginType.INVERSE
    assert result.open_interest_contracts == 15004.0


def test_binance_quarter_contract_stays_future() -> None:
    result = normalize_binance_coinm_open_interest(
        {
            "symbol": "BTCUSD_261225",
            "openInterest": "120",
            "contractType": "CURRENT_QUARTER",
            "time": 1790769600000,
        },
        accepted_at=ACCEPTED,
        source_ref="binance:/dapi/v1/openInterest",
    )
    assert result.contract_type is ContractType.FUTURE


def test_bybit_linear_ticker_preserves_oi_value_funding_and_basis() -> None:
    result = normalize_bybit_ticker(
        {
            "symbol": "BTCUSDT",
            "markPrice": "64010",
            "indexPrice": "64000",
            "openInterest": "1250",
            "openInterestValue": "80000000",
            "fundingRate": "0.0001",
            "turnover24h": "3500000000",
        },
        category="linear",
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        source_ref="bybit:/v5/market/tickers",
        funding_interval_seconds=28800,
    )
    assert result.margin_type is MarginType.LINEAR
    assert result.open_interest_base == 1250.0
    assert result.open_interest_usd == 80000000.0
    assert result.funding_rate == pytest.approx(0.0001)
    assert result.basis == 10.0


def test_bybit_inverse_does_not_mislabel_open_interest_as_base() -> None:
    result = normalize_bybit_ticker(
        {"symbol": "BTCUSD", "openInterest": "5000000", "openInterestValue": "5000000"},
        category="inverse",
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        source_ref="bybit:/v5/market/tickers",
    )
    assert result.margin_type is MarginType.INVERSE
    assert result.open_interest_base is None
    assert result.open_interest_usd == 5000000.0


def test_bybit_rejects_unknown_category() -> None:
    with pytest.raises(CryptoDerivativeAdapterError):
        normalize_bybit_ticker(
            {"symbol": "BTCUSDT", "openInterest": "1"},
            category="option",
            observed_at=OBSERVED,
            accepted_at=ACCEPTED,
            source_ref="bybit",
        )


def test_okx_joined_snapshot_keeps_missing_fields_explicit() -> None:
    result = normalize_okx_public_snapshot(
        {"instId": "BTC-USDT-SWAP", "instType": "SWAP", "oi": "200", "markPx": "64000"},
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        source_ref="okx:joined-public-snapshot",
    )
    assert result.contract_type is ContractType.PERPETUAL
    assert result.open_interest_contracts == 200.0
    assert result.index_price is None
    assert result.basis is None


def test_okx_joined_snapshot_computes_explicit_mark_index_basis() -> None:
    result = normalize_okx_public_snapshot(
        {
            "instId": "ETH-USDT-SWAP",
            "instType": "SWAP",
            "oi": "300",
            "oiUsd": "750000",
            "fundingRate": "-0.0002",
            "fundingIntervalSeconds": 28800,
            "markPx": "2501",
            "idxPx": "2500",
            "volCcy24h": "125000000",
        },
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        source_ref="okx:joined-public-snapshot",
    )
    assert result.open_interest_usd == 750000.0
    assert result.funding_rate == pytest.approx(-0.0002)
    assert result.basis == 1.0


def test_hyperliquid_asset_ctx_derives_oi_usd_only_from_observed_mark() -> None:
    result = normalize_hyperliquid_asset_ctx(
        "BTC",
        {
            "funding": "0.00005",
            "openInterest": "1000",
            "markPx": "64000",
            "oraclePx": "63990",
            "dayNtlVlm": "1250000000",
        },
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        source_ref="hyperliquid:metaAndAssetCtxs",
    )
    assert result.venue == "HYPERLIQUID"
    assert result.open_interest_base == 1000.0
    assert result.open_interest_usd == 64000000.0
    assert result.basis == 10.0


def test_hyperliquid_does_not_fabricate_oi_usd_without_mark() -> None:
    result = normalize_hyperliquid_asset_ctx(
        "NEAR",
        {"openInterest": "500000", "funding": "0.00001"},
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        source_ref="hyperliquid:metaAndAssetCtxs",
    )
    assert result.open_interest_base == 500000.0
    assert result.open_interest_usd is None


def test_invalid_numeric_provider_field_is_rejected() -> None:
    with pytest.raises(CryptoDerivativeAdapterError):
        normalize_hyperliquid_asset_ctx(
            "BTC",
            {"openInterest": "not-a-number", "markPx": "64000"},
            observed_at=OBSERVED,
            accepted_at=ACCEPTED,
            source_ref="hyperliquid:metaAndAssetCtxs",
        )


def test_adapter_layer_has_no_network_or_credentials_contract() -> None:
    import inspect
    import orderscope_local.crypto_derivatives.adapters as adapters

    source = inspect.getsource(adapters)
    assert "requests." not in source
    assert "httpx." not in source
    assert "api_key" not in source.lower()
    assert "secret" not in source.lower()
