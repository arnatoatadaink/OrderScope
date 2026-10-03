from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.crypto_context.models import CryptoReturnObservation
from orderscope_local.crypto_derivatives.models import (
    ContractType,
    CryptoDerivativeObservation,
    LiquidationObservation,
    MarginType,
)
from orderscope_local.crypto_onchain import (
    AbnormalFlowAssessment,
    AbnormalFlowState,
    AlternativeExplanation,
    CausalityStatus,
    CryptoOnchainContractError,
    MarketStructureInterpretation,
    join_onchain_market_context,
)


UTC = timezone.utc
EVENT = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
CONTEXT = EVENT + timedelta(minutes=2)
WINDOW_START = EVENT - timedelta(minutes=5)
WINDOW_END = EVENT + timedelta(minutes=1)


def _assessment() -> AbnormalFlowAssessment:
    return AbnormalFlowAssessment(
        monitored_address="treasury.near",
        as_of=EVENT,
        windows=(),
        state=AbnormalFlowState.ABNORMAL_FLOW_CANDIDATE,
        alternatives=(AlternativeExplanation.UNKNOWN,),
    )


def _returns(token_return: float = -0.04, btc_return: float = -0.01):
    token = CryptoReturnObservation(
        instrument_ref="NEARUSD",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        return_decimal=token_return,
        source_record_ids=("near-bars",),
    )
    btc = CryptoReturnObservation(
        instrument_ref="BTCUSD",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        return_decimal=btc_return,
        source_record_ids=("btc-bars",),
    )
    return token, btc


def _derivative(observation_id: str, observed_at: datetime, accepted_at: datetime, oi: float, funding: float):
    return CryptoDerivativeObservation(
        observation_id=observation_id,
        venue="binance",
        instrument_id="NEARUSDT-PERP",
        contract_type=ContractType.PERPETUAL,
        margin_type=MarginType.LINEAR,
        quote_asset="USDT",
        observed_at=observed_at,
        available_at=observed_at,
        accepted_at=accepted_at,
        source_ref="fixture:binance",
        open_interest_usd=oi,
        funding_rate=funding,
        derivatives_volume_usd=500000.0,
    )


def test_price_down_oi_down_is_deleveraging_candidate() -> None:
    token, btc = _returns()
    before = _derivative("d-before", EVENT - timedelta(minutes=1), EVENT, 10_000_000.0, 0.0010)
    after = _derivative("d-after", EVENT + timedelta(minutes=1), CONTEXT, 9_000_000.0, 0.0005)

    joined = join_onchain_market_context(
        _assessment(),
        context_as_of=CONTEXT,
        token_return=token,
        btc_return=btc,
        derivatives_before=before,
        derivatives_after=after,
    )

    assert joined.oi_delta_usd == -1_000_000.0
    assert joined.funding_rate_delta == pytest.approx(-0.0005)
    assert joined.btc_relative_return_decimal == pytest.approx(-0.03)
    assert joined.interpretation is MarketStructureInterpretation.DELEVERAGING_CANDIDATE
    assert joined.causality is CausalityStatus.NOT_ESTABLISHED


def test_price_down_oi_up_is_new_short_candidate() -> None:
    token, btc = _returns()
    before = _derivative("d-before", EVENT - timedelta(minutes=1), EVENT, 10_000_000.0, 0.0010)
    after = _derivative("d-after", EVENT + timedelta(minutes=1), CONTEXT, 11_000_000.0, 0.0015)

    joined = join_onchain_market_context(
        _assessment(),
        context_as_of=CONTEXT,
        token_return=token,
        btc_return=btc,
        derivatives_before=before,
        derivatives_after=after,
    )

    assert joined.oi_delta_usd == 1_000_000.0
    assert joined.interpretation is MarketStructureInterpretation.NEW_SHORT_CANDIDATE


def test_liquidation_evidence_and_source_ids_are_preserved() -> None:
    token, btc = _returns()
    liquidation = LiquidationObservation(
        observation_id="liq-1",
        venue="binance",
        instrument_id="NEARUSDT-PERP",
        bucket_start=EVENT,
        bucket_end=EVENT + timedelta(minutes=1),
        accepted_at=CONTEXT,
        source_ref="fixture:liquidations",
        long_liquidation_usd=250000.0,
        short_liquidation_usd=50000.0,
    )

    joined = join_onchain_market_context(
        _assessment(),
        context_as_of=CONTEXT,
        token_return=token,
        btc_return=btc,
        liquidation=liquidation,
    )

    assert joined.long_liquidation_usd == 250000.0
    assert joined.short_liquidation_usd == 50000.0
    assert joined.source_record_ids == ("near-bars", "btc-bars", "liq-1")
    assert joined.interpretation is MarketStructureInterpretation.MIXED_OR_INSUFFICIENT


def test_derivative_snapshots_cannot_look_ahead_of_context() -> None:
    token, btc = _returns()
    before = _derivative("d-before", EVENT - timedelta(minutes=1), EVENT, 10_000_000.0, 0.0010)
    after = _derivative("d-after", EVENT + timedelta(minutes=1), CONTEXT + timedelta(minutes=1), 9_000_000.0, 0.0005)

    with pytest.raises(CryptoOnchainContractError, match="cannot look ahead"):
        join_onchain_market_context(
            _assessment(),
            context_as_of=CONTEXT,
            token_return=token,
            btc_return=btc,
            derivatives_before=before,
            derivatives_after=after,
        )


def test_return_window_must_contain_event_and_not_look_ahead() -> None:
    token = CryptoReturnObservation(
        instrument_ref="NEARUSD",
        window_start=EVENT + timedelta(seconds=1),
        window_end=CONTEXT,
        return_decimal=-0.04,
        source_record_ids=("near-bars",),
    )
    btc = CryptoReturnObservation(
        instrument_ref="BTCUSD",
        window_start=EVENT + timedelta(seconds=1),
        window_end=CONTEXT,
        return_decimal=-0.01,
        source_record_ids=("btc-bars",),
    )
    with pytest.raises(CryptoOnchainContractError, match="must contain"):
        join_onchain_market_context(
            _assessment(), context_as_of=CONTEXT, token_return=token, btc_return=btc
        )

    token2, btc2 = _returns()
    object.__setattr__(token2, "window_end", CONTEXT + timedelta(minutes=1))
    object.__setattr__(btc2, "window_end", CONTEXT + timedelta(minutes=1))
    with pytest.raises(CryptoOnchainContractError, match="look ahead"):
        join_onchain_market_context(
            _assessment(), context_as_of=CONTEXT, token_return=token2, btc_return=btc2
        )


def test_derivative_pair_must_match_venue_and_instrument() -> None:
    token, btc = _returns()
    before = _derivative("d-before", EVENT - timedelta(minutes=1), EVENT, 10_000_000.0, 0.0010)
    after = CryptoDerivativeObservation(
        observation_id="d-after",
        venue="okx",
        instrument_id="NEARUSDT-PERP",
        contract_type=ContractType.PERPETUAL,
        margin_type=MarginType.LINEAR,
        quote_asset="USDT",
        observed_at=EVENT + timedelta(minutes=1),
        available_at=EVENT + timedelta(minutes=1),
        accepted_at=CONTEXT,
        source_ref="fixture:okx",
        open_interest_usd=9_000_000.0,
    )
    with pytest.raises(CryptoOnchainContractError, match="same venue and instrument"):
        join_onchain_market_context(
            _assessment(),
            context_as_of=CONTEXT,
            token_return=token,
            btc_return=btc,
            derivatives_before=before,
            derivatives_after=after,
        )


def test_positive_price_is_not_forced_into_short_or_deleveraging_label() -> None:
    token, btc = _returns(token_return=0.02, btc_return=0.01)
    before = _derivative("d-before", EVENT - timedelta(minutes=1), EVENT, 10_000_000.0, 0.0010)
    after = _derivative("d-after", EVENT + timedelta(minutes=1), CONTEXT, 11_000_000.0, 0.0015)
    joined = join_onchain_market_context(
        _assessment(),
        context_as_of=CONTEXT,
        token_return=token,
        btc_return=btc,
        derivatives_before=before,
        derivatives_after=after,
    )
    assert joined.interpretation is MarketStructureInterpretation.MIXED_OR_INSUFFICIENT
    assert joined.causality is CausalityStatus.NOT_ESTABLISHED
