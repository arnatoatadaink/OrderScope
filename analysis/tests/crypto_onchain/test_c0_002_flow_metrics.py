from dataclasses import fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from orderscope_local.crypto_onchain import (
    AbnormalFlowAssessment,
    AbnormalFlowState,
    AlternativeExplanation,
    BaselineStats,
    ConfirmedTransferFact,
    DestinationClass,
    FlowThresholds,
    assess_abnormal_flow,
)


UTC = timezone.utc
AS_OF = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
ADDRESS = "treasury.near"


def _transfer(
    *,
    minutes_ago: int,
    amount_usd: str | None,
    destination: str = "exchange.near",
    from_address: str = ADDRESS,
    available_offset_minutes: int = 0,
    accepted_offset_minutes: int = 0,
    tx_suffix: str = "x",
) -> ConfirmedTransferFact:
    confirmed_at = AS_OF - timedelta(minutes=minutes_ago)
    available_at = confirmed_at + timedelta(minutes=available_offset_minutes)
    accepted_at = available_at + timedelta(minutes=accepted_offset_minutes)
    return ConfirmedTransferFact(
        chain_id="near-mainnet",
        tx_hash=f"tx-{minutes_ago}-{tx_suffix}",
        transfer_index=0,
        asset_id="NEAR",
        amount=Decimal("1"),
        usd_notional=Decimal(amount_usd) if amount_usd is not None else None,
        from_address=from_address,
        to_address=destination,
        confirmed_at=confirmed_at,
        available_at=available_at,
        accepted_at=accepted_at,
        source_ref="fixture:near",
    )


def _baseline(mean: str = "100", stddev: str = "25") -> dict[int, BaselineStats]:
    return {minutes: BaselineStats(mean_usd=Decimal(mean), stddev_usd=Decimal(stddev)) for minutes in (5, 15, 60)}


def test_windows_are_exact_and_start_boundary_is_exclusive() -> None:
    transfers = [
        _transfer(minutes_ago=4, amount_usd="40", tx_suffix="a"),
        _transfer(minutes_ago=5, amount_usd="50", tx_suffix="b"),
        _transfer(minutes_ago=14, amount_usd="60", tx_suffix="c"),
        _transfer(minutes_ago=60, amount_usd="70", tx_suffix="d"),
    ]
    result = assess_abnormal_flow(transfers, monitored_address=ADDRESS, as_of=AS_OF, baselines=_baseline("1000", "100"))
    assert result.window(5).transfer_count == 1
    assert result.window(5).outflow_usd == Decimal("40")
    assert result.window(15).transfer_count == 3
    assert result.window(15).outflow_usd == Decimal("150")
    assert result.window(60).transfer_count == 3


def test_no_lookahead_requires_available_and_accepted_at_by_as_of() -> None:
    future_available = _transfer(minutes_ago=1, amount_usd="100", available_offset_minutes=2, tx_suffix="a")
    accepted_late = _transfer(minutes_ago=2, amount_usd="100", accepted_offset_minutes=3, tx_suffix="b")
    eligible = _transfer(minutes_ago=3, amount_usd="50", tx_suffix="c")
    result = assess_abnormal_flow(
        [future_available, accepted_late, eligible],
        monitored_address=ADDRESS,
        as_of=AS_OF,
        baselines=_baseline(),
    )
    assert result.window(5).transfer_count == 1
    assert result.window(5).outflow_usd == Decimal("50")


def test_only_outbound_transfers_for_monitored_address_are_counted() -> None:
    outbound = _transfer(minutes_ago=1, amount_usd="100", tx_suffix="a")
    inbound_or_other = _transfer(minutes_ago=1, amount_usd="999", from_address="other.near", destination=ADDRESS, tx_suffix="b")
    result = assess_abnormal_flow([outbound, inbound_or_other], monitored_address=ADDRESS, as_of=AS_OF, baselines=_baseline())
    assert result.window(5).transfer_count == 1
    assert result.window(5).outflow_usd == Decimal("100")


def test_missing_usd_notional_fails_closed_instead_of_treating_missing_as_zero() -> None:
    result = assess_abnormal_flow(
        [_transfer(minutes_ago=1, amount_usd=None)],
        monitored_address=ADDRESS,
        as_of=AS_OF,
        baselines=_baseline(),
    )
    metric = result.window(5)
    assert metric.transfer_count == 1
    assert metric.usd_transfer_count == 0
    assert metric.outflow_usd is None
    assert metric.usd_notional_complete is False
    assert metric.baseline_ratio is None
    assert metric.zscore is None
    assert result.state is AbnormalFlowState.UNKNOWN


def test_balance_baseline_ratio_and_zscore_are_deterministic() -> None:
    result = assess_abnormal_flow(
        [_transfer(minutes_ago=1, amount_usd="300")],
        monitored_address=ADDRESS,
        as_of=AS_OF,
        current_balance_usd=Decimal("1000"),
        baselines=_baseline("100", "50"),
    )
    metric = result.window(5)
    assert metric.balance_ratio == Decimal("0.3")
    assert metric.baseline_ratio == Decimal("3")
    assert metric.zscore == Decimal("4")
    assert result.state is AbnormalFlowState.ABNORMAL_FLOW_CANDIDATE


def test_zero_stddev_suppresses_zscore_but_keeps_baseline_ratio() -> None:
    baselines = {5: BaselineStats(mean_usd=Decimal("100"), stddev_usd=Decimal("0"))}
    result = assess_abnormal_flow(
        [_transfer(minutes_ago=1, amount_usd="150")],
        monitored_address=ADDRESS,
        as_of=AS_OF,
        baselines=baselines,
    )
    assert result.window(5).baseline_ratio == Decimal("1.5")
    assert result.window(5).zscore is None
    assert result.state is AbnormalFlowState.NORMAL


def test_burst_and_destination_metrics_are_preserved() -> None:
    transfers = [
        _transfer(minutes_ago=1, amount_usd="20", destination="cex.near", tx_suffix="a"),
        _transfer(minutes_ago=2, amount_usd="20", destination="bridge.near", tx_suffix="b"),
        _transfer(minutes_ago=3, amount_usd="20", destination="unknown.near", tx_suffix="c"),
    ]
    result = assess_abnormal_flow(
        transfers,
        monitored_address=ADDRESS,
        as_of=AS_OF,
        baselines=_baseline("100", "50"),
        destination_classes={
            "cex.near": DestinationClass.EXCHANGE,
            "bridge.near": DestinationClass.BRIDGE,
        },
        thresholds=FlowThresholds(burst_transfer_count=3),
    )
    metric = result.window(5)
    assert metric.burst is True
    assert metric.distinct_destination_count == 3
    assert dict(metric.destination_counts) == {
        DestinationClass.BRIDGE: 1,
        DestinationClass.EXCHANGE: 1,
        DestinationClass.UNKNOWN: 1,
    }


def test_candidate_state_transitions_are_bounded_and_deterministic() -> None:
    normal = assess_abnormal_flow(
        [_transfer(minutes_ago=1, amount_usd="100", tx_suffix="n")],
        monitored_address=ADDRESS,
        as_of=AS_OF,
        baselines=_baseline("100", "100"),
    )
    elevated = assess_abnormal_flow(
        [_transfer(minutes_ago=1, amount_usd="220", tx_suffix="e")],
        monitored_address=ADDRESS,
        as_of=AS_OF,
        baselines=_baseline("100", "100"),
    )
    abnormal = assess_abnormal_flow(
        [_transfer(minutes_ago=1, amount_usd="320", tx_suffix="a")],
        monitored_address=ADDRESS,
        as_of=AS_OF,
        baselines=_baseline("100", "100"),
    )
    assert normal.state is AbnormalFlowState.NORMAL
    assert elevated.state is AbnormalFlowState.ELEVATED
    assert abnormal.state is AbnormalFlowState.ABNORMAL_FLOW_CANDIDATE


def test_alternative_explanations_are_separate_from_candidate_severity() -> None:
    result = assess_abnormal_flow(
        [_transfer(minutes_ago=1, amount_usd="400")],
        monitored_address=ADDRESS,
        as_of=AS_OF,
        baselines=_baseline("100", "50"),
        alternatives=[AlternativeExplanation.TREASURY_MOVEMENT, AlternativeExplanation.BRIDGE_REBALANCE],
    )
    assert result.state is AbnormalFlowState.ABNORMAL_FLOW_CANDIDATE
    assert result.alternatives == (
        AlternativeExplanation.BRIDGE_REBALANCE,
        AlternativeExplanation.TREASURY_MOVEMENT,
    )


def test_missing_baseline_and_balance_produces_unknown_not_incident_state() -> None:
    result = assess_abnormal_flow(
        [_transfer(minutes_ago=1, amount_usd="500")],
        monitored_address=ADDRESS,
        as_of=AS_OF,
    )
    assert result.state is AbnormalFlowState.UNKNOWN
    assert result.alternatives == (AlternativeExplanation.UNKNOWN,)
    names = {field.name for field in fields(AbnormalFlowAssessment)}
    forbidden = {"incident", "hack", "exploit", "theft", "malicious", "attribution"}
    assert names.isdisjoint(forbidden)
