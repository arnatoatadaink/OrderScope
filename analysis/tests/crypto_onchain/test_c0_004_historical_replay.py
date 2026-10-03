from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.crypto_context.models import CryptoReturnObservation
from orderscope_local.crypto_onchain import (
    AbnormalFlowState,
    CausalityStatus,
    CryptoOnchainContractError,
    HistoricalEventTimestamps,
    MarketStructureInterpretation,
    OnchainMarketContext,
    ReplayAnchorKind,
    ReplayWindow,
    build_historical_replay,
)


UTC = timezone.utc
ANCHOR = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
PUBLIC = ANCHOR + timedelta(hours=1)
OFFICIAL = ANCHOR + timedelta(hours=3)


def _event() -> HistoricalEventTimestamps:
    return HistoricalEventTimestamps(
        event_id="near-intents-2026-10-01",
        first_onchain_detectable_at=ANCHOR,
        first_public_at=PUBLIC,
        first_official_at=OFFICIAL,
        onchain_source_ref="chain:near:fixture",
        public_source_ref="public:fixture",
        official_source_ref="official:fixture",
    )


def _return(instrument: str, window: ReplayWindow, value: float, source_id: str) -> CryptoReturnObservation:
    return CryptoReturnObservation(
        instrument_ref=instrument,
        window_start=ANCHOR,
        window_end=ANCHOR + window.delta,
        return_decimal=value,
        source_record_ids=(source_id,),
    )


def _phase(
    context_at: datetime,
    interpretation: MarketStructureInterpretation,
    oi_delta: float,
    *,
    event_time: datetime = ANCHOR,
) -> OnchainMarketContext:
    return OnchainMarketContext(
        event_time=event_time,
        context_as_of=context_at,
        onchain_state=AbnormalFlowState.ABNORMAL_FLOW_CANDIDATE,
        token_return_decimal=-0.04,
        btc_return_decimal=-0.01,
        btc_relative_return_decimal=-0.03,
        oi_delta_usd=oi_delta,
        funding_rate_delta=None,
        derivatives_volume_usd=None,
        long_liquidation_usd=None,
        short_liquidation_usd=None,
        interpretation=interpretation,
        causality=CausalityStatus.NOT_ESTABLISHED,
        source_record_ids=(f"phase:{context_at.isoformat()}",),
    )


def test_timestamp_classes_remain_distinct_and_selectable() -> None:
    event = _event()
    assert event.first_onchain_detectable_at == ANCHOR
    assert event.first_public_at == PUBLIC
    assert event.first_official_at == OFFICIAL
    assert event.anchor(ReplayAnchorKind.FIRST_ONCHAIN_DETECTABLE) == (ANCHOR, "chain:near:fixture")
    assert event.anchor(ReplayAnchorKind.FIRST_PUBLIC) == (PUBLIC, "public:fixture")
    assert event.anchor(ReplayAnchorKind.FIRST_OFFICIAL) == (OFFICIAL, "official:fixture")


def test_replay_builds_exact_canonical_windows_and_relative_returns() -> None:
    token = {window: _return("NEARUSD", window, -0.10, f"near:{window.value}") for window in ReplayWindow}
    btc = {window: _return("BTCUSD", window, -0.04, f"btc:{window.value}") for window in ReplayWindow}

    replay = build_historical_replay(
        _event(),
        anchor_kind=ReplayAnchorKind.FIRST_ONCHAIN_DETECTABLE,
        token_returns=token,
        btc_returns=btc,
    )

    assert tuple(result.window for result in replay.windows) == tuple(ReplayWindow)
    assert all(result.complete for result in replay.windows)
    assert replay.window(ReplayWindow.H24).btc_relative_return_decimal == pytest.approx(-0.06)
    assert replay.window(ReplayWindow.D30).window_end == ANCHOR + timedelta(days=30)
    assert replay.causality is CausalityStatus.NOT_ESTABLISHED


def test_missing_one_side_fails_closed_as_incomplete_window() -> None:
    token = {ReplayWindow.M15: _return("NEARUSD", ReplayWindow.M15, -0.02, "near:15m")}
    replay = build_historical_replay(
        _event(),
        anchor_kind=ReplayAnchorKind.FIRST_ONCHAIN_DETECTABLE,
        token_returns=token,
        btc_returns={},
    )
    result = replay.window(ReplayWindow.M15)
    assert result.complete is False
    assert result.token_return_decimal is None
    assert result.btc_return_decimal is None
    assert result.btc_relative_return_decimal is None
    assert result.source_record_ids == ()


def test_wrong_market_window_is_rejected_instead_of_resampled() -> None:
    token = CryptoReturnObservation(
        instrument_ref="NEARUSD",
        window_start=ANCHOR,
        window_end=ANCHOR + timedelta(minutes=16),
        return_decimal=-0.02,
        source_record_ids=("near:bad",),
    )
    btc = _return("BTCUSD", ReplayWindow.M15, -0.01, "btc:15m")
    with pytest.raises(CryptoOnchainContractError, match="canonical historical replay window"):
        build_historical_replay(
            _event(),
            anchor_kind=ReplayAnchorKind.FIRST_ONCHAIN_DETECTABLE,
            token_returns={ReplayWindow.M15: token},
            btc_returns={ReplayWindow.M15: btc},
        )


def test_missing_selected_anchor_is_explicit_error() -> None:
    event = HistoricalEventTimestamps(
        event_id="partial-event",
        first_public_at=PUBLIC,
        public_source_ref="public:fixture",
    )
    with pytest.raises(CryptoOnchainContractError, match="selected replay anchor is unavailable"):
        build_historical_replay(
            event,
            anchor_kind=ReplayAnchorKind.FIRST_ONCHAIN_DETECTABLE,
            token_returns={},
            btc_returns={},
        )


def test_near_intents_two_phase_market_structure_is_preserved_in_order() -> None:
    phase_1700_jst = _phase(
        datetime(2026, 10, 1, 8, 0, tzinfo=UTC),
        MarketStructureInterpretation.DELEVERAGING_CANDIDATE,
        -1_000_000.0,
    )
    phase_2200_jst = _phase(
        datetime(2026, 10, 1, 13, 0, tzinfo=UTC),
        MarketStructureInterpretation.NEW_SHORT_CANDIDATE,
        1_000_000.0,
    )

    replay = build_historical_replay(
        _event(),
        anchor_kind=ReplayAnchorKind.FIRST_ONCHAIN_DETECTABLE,
        token_returns={},
        btc_returns={},
        market_phases=(phase_2200_jst, phase_1700_jst),
    )

    assert replay.market_phases[0].interpretation is MarketStructureInterpretation.DELEVERAGING_CANDIDATE
    assert replay.market_phases[1].interpretation is MarketStructureInterpretation.NEW_SHORT_CANDIDATE
    assert all(phase.causality is CausalityStatus.NOT_ESTABLISHED for phase in replay.market_phases)


def test_market_phase_before_selected_anchor_is_rejected() -> None:
    phase = _phase(
        ANCHOR - timedelta(minutes=1),
        MarketStructureInterpretation.DELEVERAGING_CANDIDATE,
        -1.0,
        event_time=ANCHOR - timedelta(minutes=2),
    )
    with pytest.raises(CryptoOnchainContractError, match="cannot precede"):
        build_historical_replay(
            _event(),
            anchor_kind=ReplayAnchorKind.FIRST_ONCHAIN_DETECTABLE,
            token_returns={},
            btc_returns={},
            market_phases=(phase,),
        )
