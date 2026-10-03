"""Deterministic on-chain anomaly × market-context join for REL-11C / C0-003.

The join reuses accepted crypto-context and derivatives observations.  It may
label market structure as consistent with deleveraging or new-short formation,
but never establishes causality or a security incident.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from orderscope_local.crypto_context.models import BtcRelativePair, CryptoReturnObservation
from orderscope_local.crypto_derivatives.models import CryptoDerivativeObservation, LiquidationObservation

from .flow_metrics import AbnormalFlowAssessment, AbnormalFlowState
from .models import CryptoOnchainContractError


class MarketStructureInterpretation(StrEnum):
    DELEVERAGING_CANDIDATE = "deleveraging_candidate"
    NEW_SHORT_CANDIDATE = "new_short_candidate"
    MIXED_OR_INSUFFICIENT = "mixed_or_insufficient"


class CausalityStatus(StrEnum):
    NOT_ESTABLISHED = "not_established"


@dataclass(frozen=True, kw_only=True)
class OnchainMarketContext:
    event_time: datetime
    context_as_of: datetime
    onchain_state: AbnormalFlowState
    token_return_decimal: float
    btc_return_decimal: float
    btc_relative_return_decimal: float
    oi_delta_usd: float | None
    funding_rate_delta: float | None
    derivatives_volume_usd: float | None
    long_liquidation_usd: float | None
    short_liquidation_usd: float | None
    interpretation: MarketStructureInterpretation
    causality: CausalityStatus
    source_record_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_utc(self.event_time, "event_time")
        _require_utc(self.context_as_of, "context_as_of")
        if self.event_time > self.context_as_of:
            raise CryptoOnchainContractError("event_time cannot be later than context_as_of")
        if not isinstance(self.onchain_state, AbnormalFlowState):
            raise CryptoOnchainContractError("onchain_state must be AbnormalFlowState")
        for value, field in (
            (self.token_return_decimal, "token_return_decimal"),
            (self.btc_return_decimal, "btc_return_decimal"),
            (self.btc_relative_return_decimal, "btc_relative_return_decimal"),
        ):
            _require_finite(value, field)
        for value, field in (
            (self.oi_delta_usd, "oi_delta_usd"),
            (self.funding_rate_delta, "funding_rate_delta"),
            (self.derivatives_volume_usd, "derivatives_volume_usd"),
            (self.long_liquidation_usd, "long_liquidation_usd"),
            (self.short_liquidation_usd, "short_liquidation_usd"),
        ):
            if value is not None:
                _require_finite(value, field)
        if not isinstance(self.interpretation, MarketStructureInterpretation):
            raise CryptoOnchainContractError("interpretation must be MarketStructureInterpretation")
        if self.causality is not CausalityStatus.NOT_ESTABLISHED:
            raise CryptoOnchainContractError("REL-11C cannot establish causality")
        if not self.source_record_ids or len(self.source_record_ids) != len(set(self.source_record_ids)):
            raise CryptoOnchainContractError("source_record_ids must be non-empty and unique")
        if any(not isinstance(value, str) or not value.strip() for value in self.source_record_ids):
            raise CryptoOnchainContractError("source_record_ids must contain non-blank strings")


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise CryptoOnchainContractError(f"{field} must be normalized to UTC")


def _require_finite(value: float, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise CryptoOnchainContractError(f"{field} must be finite")


def _validate_derivative_pair(
    before: CryptoDerivativeObservation | None,
    after: CryptoDerivativeObservation | None,
    *,
    event_time: datetime,
    context_as_of: datetime,
) -> None:
    if (before is None) != (after is None):
        raise CryptoOnchainContractError("derivatives_before and derivatives_after must be supplied together")
    if before is None or after is None:
        return
    if before.venue != after.venue or before.instrument_id != after.instrument_id:
        raise CryptoOnchainContractError("derivative snapshots must refer to the same venue and instrument")
    if before.observed_at > event_time:
        raise CryptoOnchainContractError("derivatives_before must not be observed after event_time")
    if after.observed_at < event_time:
        raise CryptoOnchainContractError("derivatives_after must not be observed before event_time")
    if before.accepted_at > context_as_of or after.accepted_at > context_as_of:
        raise CryptoOnchainContractError("derivative snapshots cannot look ahead of context_as_of")
    if before.observed_at > after.observed_at:
        raise CryptoOnchainContractError("derivative snapshots are out of order")


def _interpret(token_return: float, oi_delta_usd: float | None) -> MarketStructureInterpretation:
    if oi_delta_usd is None or token_return >= 0 or oi_delta_usd == 0:
        return MarketStructureInterpretation.MIXED_OR_INSUFFICIENT
    if oi_delta_usd < 0:
        return MarketStructureInterpretation.DELEVERAGING_CANDIDATE
    return MarketStructureInterpretation.NEW_SHORT_CANDIDATE


def join_onchain_market_context(
    assessment: AbnormalFlowAssessment,
    *,
    context_as_of: datetime,
    token_return: CryptoReturnObservation,
    btc_return: CryptoReturnObservation,
    derivatives_before: CryptoDerivativeObservation | None = None,
    derivatives_after: CryptoDerivativeObservation | None = None,
    liquidation: LiquidationObservation | None = None,
) -> OnchainMarketContext:
    """Join C0-002 evidence with accepted market observations without causal attribution."""

    if not isinstance(assessment, AbnormalFlowAssessment):
        raise CryptoOnchainContractError("assessment must be AbnormalFlowAssessment")
    _require_utc(context_as_of, "context_as_of")
    event_time = assessment.as_of
    if event_time > context_as_of:
        raise CryptoOnchainContractError("assessment cannot look ahead of context_as_of")

    pair = BtcRelativePair(btc=btc_return, target=token_return)
    if pair.target.window_end > context_as_of:
        raise CryptoOnchainContractError("return window cannot look ahead of context_as_of")
    if not (pair.target.window_start <= event_time <= pair.target.window_end):
        raise CryptoOnchainContractError("return window must contain the on-chain event time")

    _validate_derivative_pair(
        derivatives_before,
        derivatives_after,
        event_time=event_time,
        context_as_of=context_as_of,
    )

    oi_delta_usd: float | None = None
    funding_delta: float | None = None
    derivatives_volume_usd: float | None = None
    source_ids = list(pair.target.source_record_ids + pair.btc.source_record_ids)

    if derivatives_before is not None and derivatives_after is not None:
        if derivatives_before.open_interest_usd is not None and derivatives_after.open_interest_usd is not None:
            oi_delta_usd = derivatives_after.open_interest_usd - derivatives_before.open_interest_usd
        if derivatives_before.funding_rate is not None and derivatives_after.funding_rate is not None:
            funding_delta = derivatives_after.funding_rate - derivatives_before.funding_rate
        derivatives_volume_usd = derivatives_after.derivatives_volume_usd
        source_ids.extend((derivatives_before.observation_id, derivatives_after.observation_id))

    long_liquidation_usd: float | None = None
    short_liquidation_usd: float | None = None
    if liquidation is not None:
        if liquidation.accepted_at > context_as_of:
            raise CryptoOnchainContractError("liquidation observation cannot look ahead of context_as_of")
        if liquidation.bucket_end < event_time or liquidation.bucket_start > context_as_of:
            raise CryptoOnchainContractError("liquidation bucket must overlap the event-to-context interval")
        long_liquidation_usd = liquidation.long_liquidation_usd
        short_liquidation_usd = liquidation.short_liquidation_usd
        source_ids.append(liquidation.observation_id)

    relative_return = token_return.return_decimal - btc_return.return_decimal
    unique_source_ids = tuple(dict.fromkeys(source_ids))

    return OnchainMarketContext(
        event_time=event_time,
        context_as_of=context_as_of,
        onchain_state=assessment.state,
        token_return_decimal=float(token_return.return_decimal),
        btc_return_decimal=float(btc_return.return_decimal),
        btc_relative_return_decimal=float(relative_return),
        oi_delta_usd=oi_delta_usd,
        funding_rate_delta=funding_delta,
        derivatives_volume_usd=derivatives_volume_usd,
        long_liquidation_usd=long_liquidation_usd,
        short_liquidation_usd=short_liquidation_usd,
        interpretation=_interpret(float(token_return.return_decimal), oi_delta_usd),
        causality=CausalityStatus.NOT_ESTABLISHED,
        source_record_ids=unique_source_ids,
    )
