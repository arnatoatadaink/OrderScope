from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.listing_compliance import (
    ListingComplianceEvent,
    ListingComplianceEventType,
    ListingComplianceState,
    ListingRepricingInterpretationType,
    assess_listing_repricing,
    derive_compliance_state,
)


UTC = timezone.utc


def _dt(day: int, hour: int = 0) -> datetime:
    return datetime(2026, 7, day, hour, tzinfo=UTC)


def _event(
    event_id: str,
    event_type: ListingComplianceEventType,
    *,
    day: int,
    evidence: str,
    rule_reference: str | None = None,
) -> ListingComplianceEvent:
    event_at = _dt(day, 12)
    return ListingComplianceEvent(
        event_id=event_id,
        subject_ref="security:LVWR",
        venue="NYSE",
        event_type=event_type,
        event_at=event_at,
        available_at=event_at + timedelta(minutes=5),
        accepted_at=event_at + timedelta(minutes=10),
        evidence_record_ids=(evidence,),
        rule_reference=rule_reference,
    )


def test_event_requires_utc_and_monotonic_source_times() -> None:
    with pytest.raises(ContractViolation, match="event_at must be normalized to UTC"):
        ListingComplianceEvent(
            event_id="listing:1",
            subject_ref="security:LVWR",
            venue="NYSE",
            event_type=ListingComplianceEventType.DEFICIENCY_NOTICE,
            event_at=datetime(2026, 7, 23, 12),
            available_at=_dt(23, 13),
            accepted_at=_dt(23, 14),
            evidence_record_ids=("evidence:listing:1",),
        )

    with pytest.raises(ContractViolation, match="event_at cannot be later than available_at"):
        ListingComplianceEvent(
            event_id="listing:2",
            subject_ref="security:LVWR",
            venue="NYSE",
            event_type=ListingComplianceEventType.DEFICIENCY_NOTICE,
            event_at=_dt(23, 14),
            available_at=_dt(23, 13),
            accepted_at=_dt(23, 15),
            evidence_record_ids=("evidence:listing:2",),
        )


def test_deficiency_cure_regained_progression() -> None:
    assessment = derive_compliance_state(
        (
            _event(
                "listing:deficiency",
                ListingComplianceEventType.DEFICIENCY_NOTICE,
                day=23,
                evidence="evidence:deficiency",
                rule_reference="NYSE:continued-listing:minimum-price",
            ),
            _event(
                "listing:cure",
                ListingComplianceEventType.COMPLIANCE_PERIOD_STARTED,
                day=24,
                evidence="evidence:cure",
            ),
            _event(
                "listing:regained",
                ListingComplianceEventType.COMPLIANCE_REGAINED,
                day=31,
                evidence="evidence:regained",
            ),
        )
    )

    assert assessment.state is ListingComplianceState.REGAINED_CONFIRMED
    assert assessment.basis_event_ids == (
        "listing:deficiency",
        "listing:cure",
        "listing:regained",
    )
    assert assessment.basis_evidence_record_ids == (
        "evidence:deficiency",
        "evidence:cure",
        "evidence:regained",
    )


def test_cure_window_without_deficiency_is_rejected() -> None:
    with pytest.raises(ContractViolation, match="cure window cannot start before a deficiency notice"):
        derive_compliance_state(
            (
                _event(
                    "listing:cure",
                    ListingComplianceEventType.COMPLIANCE_PERIOD_STARTED,
                    day=24,
                    evidence="evidence:cure",
                ),
            )
        )


def test_regained_without_deficiency_is_rejected() -> None:
    with pytest.raises(ContractViolation, match="regained compliance requires prior deficiency evidence"):
        derive_compliance_state(
            (
                _event(
                    "listing:regained",
                    ListingComplianceEventType.COMPLIANCE_REGAINED,
                    day=31,
                    evidence="evidence:regained",
                ),
            )
        )


def test_temporary_price_recovery_does_not_remove_listing_risk() -> None:
    compliance = derive_compliance_state(
        (
            _event(
                "listing:deficiency",
                ListingComplianceEventType.DEFICIENCY_NOTICE,
                day=23,
                evidence="evidence:deficiency",
            ),
            _event(
                "listing:cure",
                ListingComplianceEventType.COMPLIANCE_PERIOD_STARTED,
                day=24,
                evidence="evidence:cure",
            ),
        )
    )

    repricing = assess_listing_repricing(
        compliance=compliance,
        generated_at=_dt(25, 12),
        market_metric_record_ids=("metric:price-recovery",),
    )

    assert repricing.interpretation_type is ListingRepricingInterpretationType.LISTING_RISK_REMAINS
    assert "metric:price-recovery" in repricing.market_metric_record_ids


def test_regained_compliance_without_market_or_company_evidence_is_overhang_removed_only() -> None:
    compliance = derive_compliance_state(
        (
            _event(
                "listing:deficiency",
                ListingComplianceEventType.DEFICIENCY_NOTICE,
                day=23,
                evidence="evidence:deficiency",
            ),
            _event(
                "listing:regained",
                ListingComplianceEventType.COMPLIANCE_REGAINED,
                day=31,
                evidence="evidence:regained",
            ),
        )
    )

    repricing = assess_listing_repricing(compliance=compliance, generated_at=_dt(31, 14))
    assert repricing.interpretation_type is ListingRepricingInterpretationType.LISTING_OVERHANG_REMOVED


def test_listing_and_earnings_evidence_remain_distinct_in_interpretation_lineage() -> None:
    compliance = derive_compliance_state(
        (
            _event(
                "listing:deficiency",
                ListingComplianceEventType.DEFICIENCY_NOTICE,
                day=23,
                evidence="evidence:deficiency",
            ),
            _event(
                "listing:regained",
                ListingComplianceEventType.COMPLIANCE_REGAINED,
                day=31,
                evidence="evidence:regained",
            ),
        )
    )

    repricing = assess_listing_repricing(
        compliance=compliance,
        generated_at=_dt(31, 14),
        company_evidence_record_ids=("evidence:earnings",),
        market_metric_record_ids=("metric:abnormal-return", "metric:abnormal-volume"),
    )

    assert repricing.interpretation_type is ListingRepricingInterpretationType.LISTING_REPRICING_CANDIDATE
    interpretation = repricing.to_interpretation(
        record_id="interpretation:lvwr:listing-repricing",
        accepted_at=_dt(31, 15),
    )
    assert interpretation.basis_record_ids == (
        "evidence:deficiency",
        "evidence:regained",
        "evidence:earnings",
        "metric:abnormal-return",
        "metric:abnormal-volume",
    )
    assert interpretation.statement["listing_evidence_count"] == 2
    assert interpretation.statement["company_evidence_count"] == 1
    assert interpretation.statement["market_metric_count"] == 2


def test_evidence_classes_cannot_reuse_same_record() -> None:
    compliance = derive_compliance_state(
        (
            _event(
                "listing:deficiency",
                ListingComplianceEventType.DEFICIENCY_NOTICE,
                day=23,
                evidence="evidence:deficiency",
            ),
            _event(
                "listing:regained",
                ListingComplianceEventType.COMPLIANCE_REGAINED,
                day=31,
                evidence="evidence:regained",
            ),
        )
    )

    with pytest.raises(ContractViolation, match="evidence classes must remain distinct"):
        assess_listing_repricing(
            compliance=compliance,
            generated_at=_dt(31, 14),
            company_evidence_record_ids=("evidence:regained",),
        )


def test_delisting_effective_is_explicit_terminal_observation() -> None:
    compliance = derive_compliance_state(
        (
            _event(
                "listing:deficiency",
                ListingComplianceEventType.DEFICIENCY_NOTICE,
                day=23,
                evidence="evidence:deficiency",
            ),
            _event(
                "listing:effective",
                ListingComplianceEventType.DELISTING_EFFECTIVE,
                day=31,
                evidence="evidence:delisting-effective",
            ),
        )
    )

    assert compliance.state is ListingComplianceState.DELISTING_EFFECTIVE
    repricing = assess_listing_repricing(compliance=compliance, generated_at=_dt(31, 14))
    assert repricing.interpretation_type is ListingRepricingInterpretationType.INSUFFICIENT_EVIDENCE
