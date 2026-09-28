from datetime import datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.provenance import ContentHash, Provenance, SourceReference, SourceTimestamp
from orderscope_local.cross_market.btc_iv30 import BtcIv30Observation, BtcIvMethodology
from orderscope_local.cross_market.mstr_btc_iv30 import MstrBtcIv30Differential
from orderscope_local.cross_market.mstr_iv30 import MstrIv30Observation, MstrIvMethodology

UTC = timezone.utc
BTC_OBSERVED = datetime(2026, 9, 28, 3, 10, tzinfo=UTC)
MSTR_OBSERVED = datetime(2026, 9, 28, 3, 10, 30, tzinfo=UTC)
INPUT_ACCEPTED = datetime(2026, 9, 28, 3, 11, tzinfo=UTC)
CALCULATED = datetime(2026, 9, 28, 3, 12, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 28, 3, 13, tzinfo=UTC)


def provenance(source: str, observed_at: datetime) -> Provenance:
    return Provenance(
        source_ref=SourceReference(source),
        content_hash=ContentHash("a" * 64),
        retrieved_at=INPUT_ACCEPTED,
        available_at=observed_at,
        accepted_at=INPUT_ACCEPTED,
        event_time=SourceTimestamp.at(observed_at),
    )


def btc(iv: str = "60.00") -> BtcIv30Observation:
    return BtcIv30Observation(
        subject_ref="volatility.crypto.btc.iv30",
        source_instrument_ref="options.btc.30d",
        methodology=BtcIvMethodology.PUBLISHED_INDEX,
        annualized_iv_percent=Decimal(iv),
        horizon_days=30,
        observed_at=BTC_OBSERVED,
        accepted_at=INPUT_ACCEPTED,
        provenance=provenance("official:btc-iv:fixture", BTC_OBSERVED),
    )


def mstr(iv: str = "82.50") -> MstrIv30Observation:
    return MstrIv30Observation(
        subject_ref="volatility.equity.mstr.iv30",
        source_instrument_ref="options.mstr.30d",
        methodology=MstrIvMethodology.ATM_OPTION_SURFACE,
        annualized_iv_percent=Decimal(iv),
        horizon_days=30,
        observed_at=MSTR_OBSERVED,
        accepted_at=INPUT_ACCEPTED,
        provenance=provenance("official:mstr-options:fixture", MSTR_OBSERVED),
    )


def comparison(**overrides) -> MstrBtcIv30Differential:
    values = dict(
        mstr=mstr(),
        btc=btc(),
        calculated_at=CALCULATED,
        accepted_at=ACCEPTED,
    )
    values.update(overrides)
    return MstrBtcIv30Differential(**values)


def test_differential_is_mstr_minus_btc() -> None:
    result = comparison(mstr=mstr("82.50"), btc=btc("60.00"))
    assert result.differential_percentage_points == Decimal("22.50")
    assert result.differential_fraction == Decimal("0.225")


def test_differential_can_be_negative_without_becoming_an_interpretation() -> None:
    result = comparison(mstr=mstr("55.00"), btc=btc("60.00"))
    assert result.differential_percentage_points == Decimal("-5.00")


def test_as_of_is_latest_source_observation() -> None:
    assert comparison().as_of == MSTR_OBSERVED


def test_materializes_derived_metric_with_complete_lineage() -> None:
    metric = comparison().to_derived_metric(
        record_id="metric.volatility.mstr-btc.iv30.1",
        subject_ref="comparison.mstr-btc.iv30",
        input_record_ids=("fact.volatility.mstr.iv30.1", "fact.volatility.btc.iv30.1"),
    )
    assert metric.metric_name == "volatility.mstr_btc.iv30_differential"
    assert metric.value["differential_percentage_points"] == "22.50"
    assert metric.value["horizon_days"] == 30
    assert metric.calculation_method == "mstr_iv30_minus_btc_iv30"
    assert metric.as_of == MSTR_OBSERVED
    assert metric.input_record_ids == (
        "fact.volatility.mstr.iv30.1",
        "fact.volatility.btc.iv30.1",
    )


def test_requires_mstr_observation_type() -> None:
    with pytest.raises(ContractViolation, match="MstrIv30Observation"):
        comparison(mstr=btc())  # type: ignore[arg-type]


def test_requires_btc_observation_type() -> None:
    with pytest.raises(ContractViolation, match="BtcIv30Observation"):
        comparison(btc=mstr())  # type: ignore[arg-type]


def test_calculation_cannot_precede_latest_input_observation() -> None:
    with pytest.raises(ContractViolation, match="cannot precede the latest input observation"):
        comparison(calculated_at=BTC_OBSERVED)


def test_acceptance_cannot_precede_calculation() -> None:
    with pytest.raises(ContractViolation, match="cannot precede calculated_at"):
        comparison(accepted_at=datetime(2026, 9, 28, 3, 11, 30, tzinfo=UTC))


def test_derived_metric_requires_exactly_two_distinct_input_records() -> None:
    with pytest.raises(ContractViolation, match="exactly two input record ids"):
        comparison().to_derived_metric(
            record_id="metric.volatility.mstr-btc.iv30.1",
            subject_ref="comparison.mstr-btc.iv30",
            input_record_ids=("fact.volatility.mstr.iv30.1",),  # type: ignore[arg-type]
        )
    with pytest.raises(ContractViolation, match="must be distinct"):
        comparison().to_derived_metric(
            record_id="metric.volatility.mstr-btc.iv30.1",
            subject_ref="comparison.mstr-btc.iv30",
            input_record_ids=("fact.volatility.mstr.iv30.1", "fact.volatility.mstr.iv30.1"),
        )
