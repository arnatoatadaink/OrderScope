from datetime import datetime, timezone
from decimal import Decimal

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.provenance import ContentHash, Provenance, SourceReference, SourceTimestamp
from orderscope_local.cross_market.mstr_iv30 import MstrIv30Observation, MstrIvMethodology

UTC = timezone.utc
OBSERVED = datetime(2026, 9, 28, 3, 10, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 28, 3, 11, tzinfo=UTC)


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("official:mstr-options:fixture"),
        content_hash=ContentHash("9" * 64),
        retrieved_at=ACCEPTED,
        available_at=OBSERVED,
        accepted_at=ACCEPTED,
        event_time=SourceTimestamp.at(OBSERVED),
    )


def observation(**overrides) -> MstrIv30Observation:
    values = dict(
        subject_ref="volatility.equity.mstr.iv30",
        source_instrument_ref="options.mstr.30d",
        methodology=MstrIvMethodology.ATM_OPTION_SURFACE,
        annualized_iv_percent=Decimal("82.50"),
        horizon_days=30,
        observed_at=OBSERVED,
        accepted_at=ACCEPTED,
        provenance=provenance(),
    )
    values.update(overrides)
    return MstrIv30Observation(**values)


def test_materializes_mstr_iv30_fact() -> None:
    fact = observation().to_fact(
        record_id="fact.volatility.mstr.iv30.1",
        evidence_record_ids=("evidence.mstr.options.1",),
    )
    assert fact.fact_type == "volatility.equity.mstr.iv30"
    assert fact.value["underlying_ref"] == "equity.us.mstr"
    assert fact.value["horizon_days"] == 30


def test_normalized_fraction_is_percent_divided_by_100() -> None:
    assert observation(annualized_iv_percent=Decimal("82.50")).normalized_fraction == Decimal("0.825")


def test_requires_mstr_equity_underlying() -> None:
    with pytest.raises(ContractViolation, match="requires MSTR equity"):
        observation(underlying_ref="crypto.btc")


def test_requires_exact_30_day_horizon() -> None:
    with pytest.raises(ContractViolation, match="explicit 30-day horizon"):
        observation(horizon_days=29)


def test_iv_must_be_decimal() -> None:
    with pytest.raises(ContractViolation, match="must be Decimal"):
        observation(annualized_iv_percent=82.5)  # type: ignore[arg-type]


def test_iv_must_be_finite_and_non_negative() -> None:
    with pytest.raises(ContractViolation, match="must be finite"):
        observation(annualized_iv_percent=Decimal("NaN"))
    with pytest.raises(ContractViolation, match="cannot be negative"):
        observation(annualized_iv_percent=Decimal("-0.01"))


def test_methodology_is_explicit() -> None:
    with pytest.raises(ContractViolation, match="MstrIvMethodology"):
        observation(methodology="atm_option_surface")  # type: ignore[arg-type]


def test_acceptance_cannot_precede_observation() -> None:
    with pytest.raises(ContractViolation, match="cannot precede observed_at"):
        observation(accepted_at=datetime(2026, 9, 28, 3, 9, tzinfo=UTC))


def test_acceptance_must_match_provenance() -> None:
    with pytest.raises(ContractViolation, match="must match provenance"):
        observation(accepted_at=datetime(2026, 9, 28, 3, 12, tzinfo=UTC))


def test_fact_requires_evidence_lineage() -> None:
    with pytest.raises(ContractViolation, match="requires evidence lineage"):
        observation().to_fact(record_id="fact.volatility.mstr.iv30.1", evidence_record_ids=())
