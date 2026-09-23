from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import (
    ContentHash,
    ContractViolation,
    MacroMarketObservation,
    MacroMarketRegion,
    MacroMarketSeriesKind,
    Provenance,
    SourceReference,
    SourceTimestamp,
)


UTC = timezone.utc
OBSERVED = datetime(2026, 9, 14, 1, 0, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 14, 1, 5, tzinfo=UTC)


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("fred:DGS10"),
        content_hash=ContentHash("a" * 64),
        retrieved_at=ACCEPTED,
        available_at=OBSERVED,
        accepted_at=ACCEPTED,
        event_time=SourceTimestamp.at(OBSERVED),
    )


def test_sovereign_yield_requires_tenor_and_materializes_as_fact() -> None:
    observation = MacroMarketObservation(
        subject_ref="macro.us.ust.10y",
        series_kind=MacroMarketSeriesKind.SOVEREIGN_YIELD,
        region=MacroMarketRegion.US,
        series_id="DGS10",
        value=4.12,
        unit="percent",
        observed_at=SourceTimestamp.at(OBSERVED),
        accepted_at=ACCEPTED,
        provenance=provenance(),
        tenor="10Y",
    )

    fact = observation.to_fact(record_id="fact.macro.us.ust.10y.20260914", evidence_record_ids=("evidence.macro.1",))

    assert fact.fact_type == "macro_market.sovereign_yield"
    assert fact.subject_ref == "macro.us.ust.10y"
    assert fact.value == 4.12
    assert fact.unit == "percent"
    assert fact.period_start == SourceTimestamp.at(OBSERVED)


def test_fx_requires_cross_market_region() -> None:
    with pytest.raises(ContractViolation, match="CROSS_MARKET"):
        MacroMarketObservation(
            subject_ref="macro.fx.usdjpy",
            series_kind=MacroMarketSeriesKind.FX_RATE,
            region=MacroMarketRegion.US,
            series_id="USDJPY",
            value=145.2,
            unit="jpy_per_usd",
            observed_at=SourceTimestamp.at(OBSERVED),
            accepted_at=ACCEPTED,
            provenance=provenance(),
        )


def test_sovereign_yield_without_tenor_is_rejected() -> None:
    with pytest.raises(ContractViolation, match="requires tenor"):
        MacroMarketObservation(
            subject_ref="macro.jp.jgb",
            series_kind=MacroMarketSeriesKind.SOVEREIGN_YIELD,
            region=MacroMarketRegion.JP,
            series_id="JGB",
            value=1.1,
            unit="percent",
            observed_at=SourceTimestamp.at(OBSERVED),
            accepted_at=ACCEPTED,
            provenance=provenance(),
        )


def test_contract_contains_no_capital_movement_or_carry_classification() -> None:
    names = {item.value for item in MacroMarketSeriesKind}
    assert "carry_unwind" not in names
    assert "capital_movement" not in names
    assert "deleveraging" not in names
