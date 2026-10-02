"""Provider payload adapters for UWBS-073.

These helpers normalize already-fetched public market payloads into the
source-neutral UWBS-068 derivatives contract. They do not perform network I/O,
authentication, provider activation, retries, or persistence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .models import ContractType, CryptoDerivativeObservation, MarginType


class CryptoDerivativeAdapterError(ValueError):
    """Raised when a provider payload cannot be normalized safely."""


def _float(value: Any, field: str, *, allow_none: bool = True) -> float | None:
    if value in (None, "") and allow_none:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise CryptoDerivativeAdapterError(f"{field} must be numeric") from exc
    return result


def _ms_utc(value: Any, field: str) -> datetime:
    try:
        ms = int(value)
    except (TypeError, ValueError) as exc:
        raise CryptoDerivativeAdapterError(f"{field} must be epoch milliseconds") from exc
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def _iso_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise CryptoDerivativeAdapterError(f"{field} must be ISO-8601 text")
    text = value.replace("Z", "+00:00")
    try:
        result = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CryptoDerivativeAdapterError(f"{field} must be ISO-8601 text") from exc
    if result.tzinfo is None:
        raise CryptoDerivativeAdapterError(f"{field} must include timezone")
    return result.astimezone(timezone.utc)


def _basis(mark: float | None, index: float | None) -> float | None:
    if mark is None or index is None or index == 0:
        return None
    return mark - index


def normalize_binance_coinm_open_interest(
    payload: Mapping[str, Any],
    *,
    accepted_at: datetime,
    source_ref: str,
    quote_asset: str = "USD",
) -> CryptoDerivativeObservation:
    """Normalize Binance COIN-M current OI response."""

    symbol = str(payload.get("symbol", "")).strip()
    contract_raw = str(payload.get("contractType", "")).upper()
    contract_type = ContractType.PERPETUAL if contract_raw == "PERPETUAL" or symbol.endswith("_PERP") else ContractType.FUTURE
    observed_at = _ms_utc(payload.get("time"), "time")
    oi_contracts = _float(payload.get("openInterest"), "openInterest", allow_none=False)
    return CryptoDerivativeObservation(
        observation_id=f"binance-coinm:{symbol}:{int(observed_at.timestamp() * 1000)}",
        venue="BINANCE",
        instrument_id=symbol,
        contract_type=contract_type,
        margin_type=MarginType.INVERSE,
        quote_asset=quote_asset,
        observed_at=observed_at,
        available_at=observed_at,
        accepted_at=accepted_at,
        source_ref=source_ref,
        open_interest_contracts=oi_contracts,
    )


def normalize_bybit_ticker(
    payload: Mapping[str, Any],
    *,
    category: str,
    observed_at: datetime,
    accepted_at: datetime,
    source_ref: str,
    quote_asset: str = "USDT",
    funding_interval_seconds: int | None = None,
) -> CryptoDerivativeObservation:
    """Normalize a Bybit V5 derivatives ticker row."""

    symbol = str(payload.get("symbol", "")).strip()
    category_norm = category.lower()
    if category_norm not in {"linear", "inverse"}:
        raise CryptoDerivativeAdapterError("Bybit category must be linear or inverse")
    margin_type = MarginType.LINEAR if category_norm == "linear" else MarginType.INVERSE
    mark = _float(payload.get("markPrice"), "markPrice")
    index = _float(payload.get("indexPrice"), "indexPrice")
    funding = _float(payload.get("fundingRate"), "fundingRate")
    if funding is None:
        funding_interval_seconds = None
    oi_value = _float(payload.get("openInterestValue"), "openInterestValue")
    oi_base = _float(payload.get("openInterest"), "openInterest")
    return CryptoDerivativeObservation(
        observation_id=f"bybit:{category_norm}:{symbol}:{int(observed_at.timestamp() * 1000)}",
        venue="BYBIT",
        instrument_id=symbol,
        contract_type=ContractType.PERPETUAL,
        margin_type=margin_type,
        quote_asset=quote_asset,
        observed_at=observed_at,
        available_at=observed_at,
        accepted_at=accepted_at,
        source_ref=source_ref,
        open_interest_base=oi_base if margin_type == MarginType.LINEAR else None,
        open_interest_usd=oi_value,
        funding_rate=funding,
        funding_interval_seconds=funding_interval_seconds,
        mark_price=mark,
        index_price=index,
        basis=_basis(mark, index),
        derivatives_volume_usd=_float(payload.get("turnover24h"), "turnover24h"),
    )


def normalize_okx_public_snapshot(
    payload: Mapping[str, Any],
    *,
    observed_at: datetime,
    accepted_at: datetime,
    source_ref: str,
    quote_asset: str = "USDT",
) -> CryptoDerivativeObservation:
    """Normalize a joined OKX public-market snapshot.

    The caller may join open-interest, funding, mark and index endpoint payloads
    before calling this function. Missing fields remain explicit None values.
    """

    inst_id = str(payload.get("instId", "")).strip()
    inst_type = str(payload.get("instType", "SWAP")).upper()
    contract_type = ContractType.PERPETUAL if inst_type == "SWAP" else ContractType.FUTURE
    mark = _float(payload.get("markPx"), "markPx")
    index = _float(payload.get("idxPx"), "idxPx")
    return CryptoDerivativeObservation(
        observation_id=f"okx:{inst_id}:{int(observed_at.timestamp() * 1000)}",
        venue="OKX",
        instrument_id=inst_id,
        contract_type=contract_type,
        margin_type=MarginType.UNKNOWN,
        quote_asset=quote_asset,
        observed_at=observed_at,
        available_at=observed_at,
        accepted_at=accepted_at,
        source_ref=source_ref,
        open_interest_contracts=_float(payload.get("oi"), "oi"),
        open_interest_usd=_float(payload.get("oiUsd"), "oiUsd"),
        funding_rate=_float(payload.get("fundingRate"), "fundingRate"),
        funding_interval_seconds=payload.get("fundingIntervalSeconds"),
        mark_price=mark,
        index_price=index,
        basis=_basis(mark, index),
        derivatives_volume_usd=_float(payload.get("volCcy24h"), "volCcy24h"),
    )


def normalize_hyperliquid_asset_ctx(
    asset: str,
    payload: Mapping[str, Any],
    *,
    observed_at: datetime,
    accepted_at: datetime,
    source_ref: str,
    quote_asset: str = "USD",
) -> CryptoDerivativeObservation:
    """Normalize Hyperliquid perpetual asset context."""

    asset = asset.strip()
    mark = _float(payload.get("markPx"), "markPx")
    oracle = _float(payload.get("oraclePx"), "oraclePx")
    oi_base = _float(payload.get("openInterest"), "openInterest")
    oi_usd = None
    if oi_base is not None and mark is not None:
        oi_usd = oi_base * mark
    return CryptoDerivativeObservation(
        observation_id=f"hyperliquid:{asset}:{int(observed_at.timestamp() * 1000)}",
        venue="HYPERLIQUID",
        instrument_id=asset,
        contract_type=ContractType.PERPETUAL,
        margin_type=MarginType.LINEAR,
        quote_asset=quote_asset,
        observed_at=observed_at,
        available_at=observed_at,
        accepted_at=accepted_at,
        source_ref=source_ref,
        open_interest_base=oi_base,
        open_interest_usd=oi_usd,
        funding_rate=_float(payload.get("funding"), "funding"),
        mark_price=mark,
        index_price=oracle,
        basis=_basis(mark, oracle),
        derivatives_volume_usd=_float(payload.get("dayNtlVlm"), "dayNtlVlm"),
    )


__all__ = [
    "CryptoDerivativeAdapterError",
    "normalize_binance_coinm_open_interest",
    "normalize_bybit_ticker",
    "normalize_okx_public_snapshot",
    "normalize_hyperliquid_asset_ctx",
]
