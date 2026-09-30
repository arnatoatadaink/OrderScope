"""Conservative UWBS-067 listing-compliance state derivation."""

from __future__ import annotations

from collections.abc import Iterable

from orderscope_local.contracts.errors import ContractViolation

from .models import (
    ListingComplianceAssessment,
    ListingComplianceEvent,
    ListingComplianceEventType,
    ListingComplianceState,
    ListingRepricingAssessment,
    ListingRepricingInterpretationType,
)


def derive_compliance_state(events: Iterable[ListingComplianceEvent]) -> ListingComplianceAssessment:
    ordered = tuple(sorted(events, key=lambda item: (item.event_at, item.available_at, item.accepted_at, item.event_id)))
    if not ordered:
        raise ContractViolation("at least one listing-compliance event is required")

    subject_ref = ordered[0].subject_ref
    venue = ordered[0].venue
    if any(item.subject_ref != subject_ref for item in ordered):
        raise ContractViolation("all listing events must describe the same subject")
    if any(item.venue != venue for item in ordered):
        raise ContractViolation("all listing events must describe the same venue")

    state = ListingComplianceState.UNKNOWN
    seen_deficiency = False
    seen_regained = False

    for event in ordered:
        kind = event.event_type
        if kind is ListingComplianceEventType.DEFICIENCY_NOTICE:
            state = ListingComplianceState.DEFICIENT
            seen_deficiency = True
            seen_regained = False
        elif kind is ListingComplianceEventType.COMPLIANCE_PERIOD_STARTED:
            if not seen_deficiency:
                raise ContractViolation("cure window cannot start before a deficiency notice")
            state = ListingComplianceState.CURE_WINDOW_ACTIVE
        elif kind is ListingComplianceEventType.EXTENSION_GRANTED:
            if state not in {ListingComplianceState.DEFICIENT, ListingComplianceState.CURE_WINDOW_ACTIVE}:
                raise ContractViolation("extension requires an active deficiency or cure window")
            state = ListingComplianceState.CURE_WINDOW_ACTIVE
        elif kind is ListingComplianceEventType.COMPLIANCE_REGAINED:
            if not seen_deficiency:
                raise ContractViolation("regained compliance requires prior deficiency evidence")
            state = ListingComplianceState.REGAINED_CONFIRMED
            seen_regained = True
        elif kind in {
            ListingComplianceEventType.HEARING_REQUESTED,
            ListingComplianceEventType.HEARING_DECISION,
            ListingComplianceEventType.SUSPENSION_ANNOUNCED,
            ListingComplianceEventType.DELISTING_ANNOUNCED,
        }:
            if not seen_deficiency and not seen_regained:
                raise ContractViolation("listing-risk escalation requires prior compliance history")
            state = ListingComplianceState.DELISTING_RISK_ACTIVE
        elif kind is ListingComplianceEventType.DELISTING_EFFECTIVE:
            state = ListingComplianceState.DELISTING_EFFECTIVE
        elif kind is ListingComplianceEventType.UNKNOWN:
            # Unknown observations never erase a source-grounded prior state.
            pass

    evidence_ids: list[str] = []
    for event in ordered:
        for evidence_id in event.evidence_record_ids:
            if evidence_id not in evidence_ids:
                evidence_ids.append(evidence_id)

    return ListingComplianceAssessment(
        subject_ref=subject_ref,
        venue=venue,
        state=state,
        as_of=max(item.accepted_at for item in ordered),
        basis_event_ids=tuple(item.event_id for item in ordered),
        basis_evidence_record_ids=tuple(evidence_ids),
    )


def assess_listing_repricing(
    *,
    compliance: ListingComplianceAssessment,
    generated_at,
    company_evidence_record_ids: tuple[str, ...] = (),
    market_metric_record_ids: tuple[str, ...] = (),
) -> ListingRepricingAssessment:
    """Produce a conservative interpretation without inferring causality from price alone."""

    if compliance.state is ListingComplianceState.REGAINED_CONFIRMED:
        if company_evidence_record_ids or market_metric_record_ids:
            interpretation = ListingRepricingInterpretationType.LISTING_REPRICING_CANDIDATE
        else:
            interpretation = ListingRepricingInterpretationType.LISTING_OVERHANG_REMOVED
    elif compliance.state in {
        ListingComplianceState.DEFICIENT,
        ListingComplianceState.CURE_WINDOW_ACTIVE,
        ListingComplianceState.DELISTING_RISK_ACTIVE,
    }:
        interpretation = ListingRepricingInterpretationType.LISTING_RISK_REMAINS
    else:
        interpretation = ListingRepricingInterpretationType.INSUFFICIENT_EVIDENCE

    return ListingRepricingAssessment(
        subject_ref=compliance.subject_ref,
        interpretation_type=interpretation,
        listing_evidence_record_ids=compliance.basis_evidence_record_ids,
        company_evidence_record_ids=company_evidence_record_ids,
        market_metric_record_ids=market_metric_record_ids,
        generated_at=generated_at,
    )
