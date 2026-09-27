from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import ContentHash, ContractViolation, Provenance, SourceReference, SourceTimestamp
from orderscope_local.physical_saas.integration_overlay import (
    IntegrationAssessment,
    IntegrationEventKind,
    IntegrationEventObservation,
    IntegrationEventState,
    IntegrationInterpretationRating,
    IntegrationInterpretationType,
)

UTC = timezone.utc
ACCEPTED = datetime(2026, 9, 27, 11, 0, tzinfo=UTC)
START = SourceTimestamp.date_only(date(2026, 9, 1))


def provenance() -> Provenance:
    return Provenance(
        source_ref=SourceReference("official:physical-saas:integration-fixture"),
        content_hash=ContentHash("d" * 64),
        retrieved_at=ACCEPTED,
        available_at=ACCEPTED,
        accepted_at=ACCEPTED,
        event_time=START,
    )


def event(**overrides) -> IntegrationEventObservation:
    values = dict(
        subject_ref="company.powerfleet.fixture",
        event_kind=IntegrationEventKind.ACQUISITION_CLOSED,
        state=IntegrationEventState.COMPLETED,
        accepted_at=ACCEPTED,
        provenance=provenance(),
        acquisition_ref="acquisition.fixture",
        acquired_entity_ref="company.acquired.fixture",
        effective_start=START,
    )
    values.update(overrides)
    return IntegrationEventObservation(**values)


def assessment(**overrides) -> IntegrationAssessment:
    values = dict(
        interpretation_type=IntegrationInterpretationType.INTEGRATION_SUCCESS_CANDIDATE,
        rating=IntegrationInterpretationRating.SUPPORT,
        subject_ref="company.powerfleet.fixture",
        observed_window_start=datetime(2026, 9, 1, tzinfo=UTC),
        observed_window_end=datetime(2026, 9, 20, tzinfo=UTC),
        milestone_fact_refs=("fact.integration.closed",),
        deployment_metric_refs=("metric.deployment.funnel",),
        generated_at=datetime(2026, 9, 20, 1, tzinfo=UTC),
    )
    values.update(overrides)
    return IntegrationAssessment(**values)


def test_acquisition_close_materializes_as_fact() -> None:
    fact = event().to_fact(record_id="fact.integration.closed", evidence_record_ids=("evidence.official.1",))
    assert fact.fact_type == "physical_saas_integration.acquisition_closed"
    assert fact.value["acquisition_ref"] == "acquisition.fixture"


def test_acquisition_event_requires_acquisition_and_entity_identity() -> None:
    with pytest.raises(ContractViolation, match="acquisition_ref"):
        event(acquisition_ref=None)


def test_platform_migration_requires_platform_identity() -> None:
    with pytest.raises(ContractViolation, match="platform_ref"):
        event(
            event_kind=IntegrationEventKind.PLATFORM_MIGRATION_STARTED,
            state=IntegrationEventState.IN_PROGRESS,
            acquisition_ref=None,
            acquired_entity_ref=None,
        )


def test_legacy_retirement_requires_legacy_identity() -> None:
    with pytest.raises(ContractViolation, match="legacy_system_ref"):
        event(
            event_kind=IntegrationEventKind.LEGACY_SYSTEM_RETIREMENT,
            acquisition_ref=None,
            acquired_entity_ref=None,
        )


def test_customer_migration_requires_customer_identity() -> None:
    with pytest.raises(ContractViolation, match="customer_ref"):
        event(
            event_kind=IntegrationEventKind.CUSTOMER_MIGRATION_COMPLETED,
            acquisition_ref=None,
            acquired_entity_ref=None,
        )


def test_supported_assessment_requires_two_independent_evidence_classes() -> None:
    with pytest.raises(ContractViolation, match="at least two"):
        assessment(deployment_metric_refs=())


def test_migration_slippage_requires_deployment_metric_evidence() -> None:
    with pytest.raises(ContractViolation, match="deployment metric"):
        assessment(
            interpretation_type=IntegrationInterpretationType.MIGRATION_SLIPPAGE_CANDIDATE,
            deployment_metric_refs=(),
            financial_metric_refs=("metric.financial.cash_conversion",),
        )


def test_unknown_cannot_carry_directional_evidence() -> None:
    with pytest.raises(ContractViolation, match="UNKNOWN"):
        assessment(rating=IntegrationInterpretationRating.UNKNOWN)


def test_evidence_reference_cannot_be_reused_between_classes() -> None:
    with pytest.raises(ContractViolation, match="cannot reuse"):
        assessment(financial_metric_refs=("metric.deployment.funnel",))


def test_supported_assessment_materializes_as_interpretation_not_fact() -> None:
    item = assessment(financial_metric_refs=("metric.financial.cash_conversion",))
    interpretation = item.to_interpretation(
        record_id="interpretation.integration.success",
        accepted_at=datetime(2026, 9, 20, 2, tzinfo=UTC),
    )
    assert interpretation.interpretation_type == "integration_success_candidate"
    assert interpretation.statement["rating"] == "SUPPORT"
    assert interpretation.basis_record_ids == (
        "fact.integration.closed",
        "metric.deployment.funnel",
        "metric.financial.cash_conversion",
    )
