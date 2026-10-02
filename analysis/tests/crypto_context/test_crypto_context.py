from datetime import datetime, timezone

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.crypto_context import (
    BtcContextState,
    BtcRelativePair,
    CryptoBreadthObservation,
    CryptoReturnObservation,
    btc_adjusted_residual_metric,
    build_btc_context_interpretation,
    mean_altcoin_return_metric,
    same_direction_breadth_metric,
)


T0 = datetime(2026, 9, 20, 0, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 9, 20, 1, 0, tzinfo=timezone.utc)


def obs(ref: str, ret: float, record: str) -> CryptoReturnObservation:
    return CryptoReturnObservation(
        instrument_ref=ref,
        window_start=T0,
        window_end=T1,
        return_decimal=ret,
        source_record_ids=(record,),
    )


def test_return_observation_requires_utc_and_positive_window():
    with pytest.raises(ContractViolation):
        CryptoReturnObservation(
            instrument_ref="BTCUSD",
            window_start=datetime(2026, 9, 20, 0, 0),
            window_end=T1,
            return_decimal=0.01,
            source_record_ids=("btc-1",),
        )


def test_pair_requires_aligned_distinct_instruments():
    with pytest.raises(ContractViolation):
        BtcRelativePair(btc=obs("BTCUSD", 0.01, "btc-1"), target=obs("BTCUSD", 0.02, "btc-2"))


def test_btc_adjusted_residual_is_target_minus_btc():
    pair = BtcRelativePair(btc=obs("BTCUSD", 0.01, "btc-1"), target=obs("NEARUSD", 0.05, "near-1"))
    metric = btc_adjusted_residual_metric(
        metric_id="metric-residual",
        pair=pair,
        accepted_at=T1,
        created_at=T1,
    )
    assert metric.value == pytest.approx(0.04)
    assert metric.input_record_ids == ("btc-1", "near-1")


def test_same_direction_breadth_counts_members_matching_btc_sign():
    observation = CryptoBreadthObservation(
        as_of=T1,
        btc_return_decimal=0.02,
        member_returns=(0.01, 0.03, -0.01, 0.0),
        input_record_ids=("a", "b", "c", "d"),
    )
    metric = same_direction_breadth_metric(
        metric_id="metric-breadth",
        observation=observation,
        accepted_at=T1,
        created_at=T1,
    )
    assert metric.value == pytest.approx(0.5)


def test_zero_btc_return_only_matches_zero_members():
    observation = CryptoBreadthObservation(
        as_of=T1,
        btc_return_decimal=0.0,
        member_returns=(0.0, 0.01, 0.0, -0.01),
        input_record_ids=("a", "b", "c", "d"),
    )
    metric = same_direction_breadth_metric(
        metric_id="metric-breadth-zero",
        observation=observation,
        accepted_at=T1,
        created_at=T1,
    )
    assert metric.value == pytest.approx(0.5)


def test_mean_altcoin_return_is_deterministic():
    observation = CryptoBreadthObservation(
        as_of=T1,
        btc_return_decimal=0.01,
        member_returns=(0.02, 0.04),
        input_record_ids=("a", "b"),
    )
    metric = mean_altcoin_return_metric(
        metric_id="metric-mean",
        observation=observation,
        accepted_at=T1,
        created_at=T1,
    )
    assert metric.value == pytest.approx(0.03)


def test_interpretation_marks_relative_strength_without_claiming_causality():
    interpretation = build_btc_context_interpretation(
        record_id="interp-1",
        subject_ref="NEARUSD",
        accepted_at=T1,
        created_at=T1,
        residual_metric_id="metric-residual",
        breadth_metric_id="metric-breadth",
        residual_return=0.05,
        same_direction_breadth=0.8,
    )
    assert interpretation.statement["state"] == BtcContextState.ALTCOIN_RELATIVE_STRENGTH.value
    assert interpretation.statement["causal_status"] == "candidate_only"


def test_interpretation_uses_insufficient_evidence_when_breadth_is_low():
    interpretation = build_btc_context_interpretation(
        record_id="interp-2",
        subject_ref="NEARUSD",
        accepted_at=T1,
        created_at=T1,
        residual_metric_id="metric-residual",
        breadth_metric_id="metric-breadth",
        residual_return=0.10,
        same_direction_breadth=0.2,
    )
    assert interpretation.statement["state"] == BtcContextState.INSUFFICIENT_EVIDENCE.value


def test_interpretation_rejects_invalid_breadth():
    with pytest.raises(ContractViolation):
        build_btc_context_interpretation(
            record_id="interp-3",
            subject_ref="NEARUSD",
            accepted_at=T1,
            created_at=T1,
            residual_metric_id="metric-residual",
            breadth_metric_id="metric-breadth",
            residual_return=0.01,
            same_direction_breadth=1.1,
        )
