from datetime import datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.provenance import ContentHash, Provenance, SourceReference, SourceTimestamp
from orderscope_local.cross_market.btc_iv30 import BtcIv30Observation, BtcIvMethodology

UTC = timezone.utc
OBSERVED = datetime(2026, 9, 27, 14, 30, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 27, 14, 31, tzinfo=UTC)


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("official:btc-iv:fixture"),
        content_hash=ContentHash("a" * 64),
        retrieved_at=ACCEPTED,
        available_at=OBSERVED,
        accepted_at=ACCEPTED,
        event_time=SourceTimestamp.at(OBSERVED),
    )


def observation(**overrides) -> BtcIv30Observation:
    values = dict(
        subject_ref="volatility.crypto.btc.iv30",
        source_instrument_ref="index.btc.iv30",
        methodology=BtcIvMethodology.PUBLISHED_INDEX,
        annualized_iv_percent=Decimal("52.5"),
        horizon_days=30,
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        provenance=provenance(),
    )
    values.update(overrides)
    return BtcIv30Observation(**values)


def test_materializes_source_neutral_btc_iv_fact() -> None:
    fact = observation().to_fact(record_id="fact.btc.iv30.1", evidence_record_ids=("evidence.btc.iv.1",))
    assert fact.fact_type == "volatility.crypto.btc.iv30"
    assert fact.value["horizon_days"] == 30


def test_percent_normalizes_to_fraction() -> None:
    assert observation(annualized_iv_percent=Decimal("52.5")).normalized_fraction == Decimal("0.525")


def test_non_btc_underlying_rejected() -> None:
    with pytest.raises(ContractViolation, match="requires BTC"):
        observation(underlying_ref="equity.mstr")


def test_horizon_must_be_exactly_30_days() -> None:
    with pytest.raises(ContractViolation, match="30-day horizon"):
        observation(horizon_days=7)


def test_methodology_must_be_typed() -> None:
    with pytest.raises(ContractViolation, match="BtcIvMethodology"):
        observation(methodology="published_index")  # type: ignore[arg-type]


def test_iv_must_be_decimal() -> None:
    with pytest.raises(ContractViolation, match="must be Decimal"):
        observation(annualized_iv_percent=52.5)  # type: ignore[arg-type]


def test_negative_iv_rejected() -> None:
    with pytest.raises(ContractViolation, match="cannot be negative"):
        observation(annualized_iv_percent=Decimal("-0.1"))


def test_acceptance_cannot_precede_observation() -> None:
    with pytest.raises(ContractViolation, match="cannot precede"):
        observation(accepted_at=datetime(2026, 9, 27, 14, 29, tzinfo=UTC))


def test_provenance_acceptance_must_match() -> None:
    with pytest.raises(ContractViolation, match="must match provenance"):
        observation(accepted_at=datetime(2026, 9, 27, 14, 32, tzinfo=UTC))


def test_fact_requires_evidence_lineage() -> None:
    with pytest.raises(ContractViolation, match="requires evidence lineage"):
        observation().to_fact(record_id="fact.btc.iv30.1", evidence_record_ids=())
