from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.contracts.commodity_interpretation import (
    CommodityInterpretationAssessment,
    CommodityInterpretationRating,
    CommodityInterpretationType,
)


UTC = timezone.utc
START = datetime(2026, 9, 21, 13, 30, tzinfo=UTC)
END = datetime(2026, 9, 21, 20, 0, tzinfo=UTC)
GENERATED = datetime(2026, 9, 21, 20, 5, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 21, 20, 6, tzinfo=UTC)


def assessment(**overrides) -> CommodityInterpretationAssessment:
    values = dict(
        interpretation_type=CommodityInterpretationType.OIL_DOWN_SUPPLY_RELIEF_CANDIDATE,
        rating=CommodityInterpretationRating.SUPPORT,
        subject_ref="commodity.crude.oil_down",
        observed_window_start=START,
        observed_window_end=END,
        price_metric_refs=("metric.wti.return",),
        fundamental_metric_refs=("fact.eia.crude.production",),
        event_fact_refs=(),
        macro_metric_refs=(),
        contradicting_evidence_refs=(),
        generated_at=GENERATED,
    )
    values.update(overrides)
    return CommodityInterpretationAssessment(**values)


def test_supply_relief_candidate_requires_independent_price_and_supply_signal() -> None:
    item = assessment()
    record = item.to_interpretation(record_id="interp.oil.supply_relief.1", accepted_at=ACCEPTED)

    assert record.interpretation_type == "oil_down_supply_relief_candidate"
    assert record.statement["rating"] == "SUPPORT"
    assert record.statement["price_signal_count"] == 1
    assert record.statement["fundamental_signal_count"] == 1


def test_single_price_move_cannot_establish_supported_reason() -> None:
    with pytest.raises(ContractViolation, match="at least two independent signal classes"):
        assessment(
            interpretation_type=CommodityInterpretationType.OIL_DOWN_INVENTORY_BUILD_CANDIDATE,
            fundamental_metric_refs=(),
        )


def test_inventory_build_candidate_requires_fundamental_evidence() -> None:
    with pytest.raises(ContractViolation, match="inventory-build candidate"):
        assessment(
            interpretation_type=CommodityInterpretationType.OIL_DOWN_INVENTORY_BUILD_CANDIDATE,
            fundamental_metric_refs=(),
            event_fact_refs=("fact.event.storage.release",),
        )


def test_demand_weakness_candidate_can_use_macro_with_price() -> None:
    item = assessment(
        interpretation_type=CommodityInterpretationType.OIL_DOWN_DEMAND_WEAKNESS_CANDIDATE,
        fundamental_metric_refs=(),
        macro_metric_refs=("metric.us.growth.slowdown",),
    )
    assert item.rating is CommodityInterpretationRating.SUPPORT


def test_disinflation_candidate_requires_macro_signal() -> None:
    with pytest.raises(ContractViolation, match="disinflation candidate"):
        assessment(
            interpretation_type=CommodityInterpretationType.DISINFLATION_SUPPORT_CANDIDATE,
            macro_metric_refs=(),
        )


def test_contradict_rating_requires_contradicting_evidence() -> None:
    with pytest.raises(ContractViolation, match="requires contradicting evidence"):
        assessment(
            rating=CommodityInterpretationRating.CONTRADICT,
            price_metric_refs=(),
            fundamental_metric_refs=(),
        )


def test_unknown_carries_no_directional_evidence() -> None:
    item = assessment(
        rating=CommodityInterpretationRating.UNKNOWN,
        price_metric_refs=(),
        fundamental_metric_refs=(),
    )
    assert item.basis_record_ids == ()

    with pytest.raises(ContractViolation, match="UNKNOWN assessment"):
        assessment(
            rating=CommodityInterpretationRating.UNKNOWN,
            price_metric_refs=("metric.wti.return",),
            fundamental_metric_refs=(),
        )


def test_signal_classes_cannot_reuse_same_reference() -> None:
    with pytest.raises(ContractViolation, match="cannot reuse references"):
        assessment(
            price_metric_refs=("record.same",),
            fundamental_metric_refs=("record.same",),
        )
