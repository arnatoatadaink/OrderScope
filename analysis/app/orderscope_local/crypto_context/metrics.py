"""Deterministic BTC-relative metrics for crypto context."""

from __future__ import annotations

from statistics import fmean

from orderscope_local.contracts.fact_store import DerivedMetric

from .models import BtcRelativePair, CryptoBreadthObservation


def btc_adjusted_residual_metric(*, metric_id: str, pair: BtcRelativePair, accepted_at, created_at) -> DerivedMetric:
    value = pair.target.return_decimal - pair.btc.return_decimal
    return DerivedMetric(
        record_id=metric_id,
        schema_version="uwbs-069.v1",
        subject_ref=pair.target.instrument_ref,
        accepted_at=accepted_at,
        created_at=created_at,
        metric_name="btc_adjusted_residual_return",
        value=value,
        calculation_method="target_return_minus_btc_return",
        method_version="uwbs-069.v1",
        as_of=pair.target.window_end,
        input_record_ids=pair.btc.source_record_ids + pair.target.source_record_ids,
        unit="decimal_return",
    )


def same_direction_breadth_metric(*, metric_id: str, observation: CryptoBreadthObservation, accepted_at, created_at) -> DerivedMetric:
    btc_sign = 1 if observation.btc_return_decimal > 0 else -1 if observation.btc_return_decimal < 0 else 0
    if btc_sign == 0:
        same = sum(1 for value in observation.member_returns if value == 0)
    else:
        same = sum(1 for value in observation.member_returns if (value > 0) == (btc_sign > 0) and value != 0)
    breadth = same / len(observation.member_returns)
    return DerivedMetric(
        record_id=metric_id,
        schema_version="uwbs-069.v1",
        subject_ref="crypto-market",
        accepted_at=accepted_at,
        created_at=created_at,
        metric_name="crypto_breadth_same_direction",
        value=breadth,
        calculation_method="same_direction_fraction_vs_btc",
        method_version="uwbs-069.v1",
        as_of=observation.as_of,
        input_record_ids=observation.input_record_ids,
        unit="ratio",
    )


def mean_altcoin_return_metric(*, metric_id: str, observation: CryptoBreadthObservation, accepted_at, created_at) -> DerivedMetric:
    return DerivedMetric(
        record_id=metric_id,
        schema_version="uwbs-069.v1",
        subject_ref="crypto-market",
        accepted_at=accepted_at,
        created_at=created_at,
        metric_name="mean_altcoin_return",
        value=fmean(observation.member_returns),
        calculation_method="arithmetic_mean_member_return",
        method_version="uwbs-069.v1",
        as_of=observation.as_of,
        input_record_ids=observation.input_record_ids,
        unit="decimal_return",
    )
