"""UWBS-092 Physical-SaaS classifier / applicability guard.

This module decides whether the Physical-SaaS analysis lane is applicable to a
subject before downstream deployment, financial-quality, M&A-integration, or
Canary logic is used.  Applicability is an Interpretation, never a company Fact.
A single hardware shipment, software product, subscription metric, or M&A event
is insufficient by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import (
    Interpretation,
    InterpretationAssertionKind,
)


class PhysicalSaasEvidenceClass(StrEnum):
    PHYSICAL_DEPLOYMENT = "physical_deployment"
    RECURRING_SERVICE = "recurring_service"
    CONNECTED_OPERATIONS = "connected_operations"
    CUSTOMER_WORKFLOW_EMBEDDING = "customer_workflow_embedding"
    FINANCIAL_RECURRING_REVENUE = "financial_recurring_revenue"


class PhysicalSaasApplicabilityRating(StrEnum):
    APPLICABLE = "applicable"
    CONDITIONAL = "conditional"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


@dataclass(frozen=True, kw_only=True)
class PhysicalSaasApplicabilityAssessment:
    subject_ref: str
    rating: PhysicalSaasApplicabilityRating
    evidence_classes: tuple[PhysicalSaasEvidenceClass, ...]
    supporting_record_ids: tuple[str, ...]
    contradicting_record_ids: tuple[str, ...] = ()
    generated_at: datetime
    method_version: str = "physical-saas-applicability-v0.1"

    def __post_init__(self) -> None:
        if not isinstance(self.subject_ref, str) or not self.subject_ref.strip() or self.subject_ref != self.subject_ref.strip():
            raise ContractViolation("subject_ref must be canonical non-empty text")
        if not isinstance(self.rating, PhysicalSaasApplicabilityRating):
            raise ContractViolation("rating must be PhysicalSaasApplicabilityRating")
        if not isinstance(self.evidence_classes, tuple):
            raise ContractViolation("evidence_classes must be an immutable tuple")
        if len(self.evidence_classes) != len(set(self.evidence_classes)):
            raise ContractViolation("evidence_classes cannot contain duplicates")
        if any(not isinstance(item, PhysicalSaasEvidenceClass) for item in self.evidence_classes):
            raise ContractViolation("evidence_classes contains unsupported value")
        _refs(self.supporting_record_ids, "supporting_record_ids")
        _refs(self.contradicting_record_ids, "contradicting_record_ids")
        if set(self.supporting_record_ids) & set(self.contradicting_record_ids):
            raise ContractViolation("supporting and contradicting records cannot overlap")
        _utc(self.generated_at, "generated_at")
        if not isinstance(self.method_version, str) or not self.method_version.strip():
            raise ContractViolation("method_version cannot be blank")
        _validate_rating(self)

    @property
    def downstream_allowed(self) -> bool:
        """Only a clean APPLICABLE result opens downstream Physical-SaaS logic."""

        return self.rating is PhysicalSaasApplicabilityRating.APPLICABLE

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return self.supporting_record_ids + self.contradicting_record_ids

    def to_interpretation(
        self,
        *,
        record_id: str,
        accepted_at: datetime,
        supersedes_record_id: str | None = None,
    ) -> Interpretation:
        _utc(accepted_at, "accepted_at")
        if accepted_at < self.generated_at:
            raise ContractViolation("accepted_at cannot precede generated_at")
        if not self.basis_record_ids:
            raise ContractViolation("applicability Interpretation requires evidence lineage")
        return Interpretation(
            record_id=record_id,
            schema_version="physical-saas-applicability-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            supersedes_record_id=supersedes_record_id,
            interpretation_type="physical_saas_applicability",
            statement={
                "rating": self.rating.value,
                "downstream_allowed": self.downstream_allowed,
                "evidence_class_count": len(self.evidence_classes),
                "contradicting_count": len(self.contradicting_record_ids),
            },
            basis_record_ids=self.basis_record_ids,
            method="physical_saas_applicability_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )


def classify_physical_saas_applicability(
    *,
    subject_ref: str,
    evidence_by_class: tuple[tuple[PhysicalSaasEvidenceClass, tuple[str, ...]], ...],
    contradicting_record_ids: tuple[str, ...],
    generated_at: datetime,
) -> PhysicalSaasApplicabilityAssessment:
    """Classify applicability without inferring unsupported business-model Facts."""

    classes: list[PhysicalSaasEvidenceClass] = []
    supporting: list[str] = []
    for evidence_class, record_ids in evidence_by_class:
        if not isinstance(evidence_class, PhysicalSaasEvidenceClass):
            raise ContractViolation("evidence_by_class contains unsupported evidence class")
        _refs(record_ids, "evidence_by_class.record_ids")
        if record_ids:
            classes.append(evidence_class)
            supporting.extend(record_ids)

    if len(classes) != len(set(classes)):
        raise ContractViolation("evidence_by_class cannot repeat an evidence class")
    if len(supporting) != len(set(supporting)):
        raise ContractViolation("supporting record IDs cannot be reused across evidence classes")
    _refs(contradicting_record_ids, "contradicting_record_ids")

    class_set = set(classes)
    has_physical = PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT in class_set
    has_recurring = bool(
        {
            PhysicalSaasEvidenceClass.RECURRING_SERVICE,
            PhysicalSaasEvidenceClass.FINANCIAL_RECURRING_REVENUE,
        }
        & class_set
    )

    if not supporting and not contradicting_record_ids:
        rating = PhysicalSaasApplicabilityRating.UNKNOWN
    elif has_physical and has_recurring and not contradicting_record_ids:
        rating = PhysicalSaasApplicabilityRating.APPLICABLE
    elif contradicting_record_ids and not (has_physical and has_recurring):
        rating = PhysicalSaasApplicabilityRating.NOT_APPLICABLE
    else:
        rating = PhysicalSaasApplicabilityRating.CONDITIONAL

    return PhysicalSaasApplicabilityAssessment(
        subject_ref=subject_ref,
        rating=rating,
        evidence_classes=tuple(classes),
        supporting_record_ids=tuple(supporting),
        contradicting_record_ids=contradicting_record_ids,
        generated_at=generated_at,
    )


def _validate_rating(item: PhysicalSaasApplicabilityAssessment) -> None:
    classes = set(item.evidence_classes)
    has_physical = PhysicalSaasEvidenceClass.PHYSICAL_DEPLOYMENT in classes
    has_recurring = bool(
        {
            PhysicalSaasEvidenceClass.RECURRING_SERVICE,
            PhysicalSaasEvidenceClass.FINANCIAL_RECURRING_REVENUE,
        }
        & classes
    )
    if item.rating is PhysicalSaasApplicabilityRating.UNKNOWN:
        if item.supporting_record_ids or item.contradicting_record_ids or item.evidence_classes:
            raise ContractViolation("UNKNOWN applicability cannot carry directional evidence")
    elif item.rating is PhysicalSaasApplicabilityRating.APPLICABLE:
        if not (has_physical and has_recurring):
            raise ContractViolation("APPLICABLE requires physical-deployment and recurring-service evidence")
        if item.contradicting_record_ids:
            raise ContractViolation("APPLICABLE cannot carry unresolved contradictory evidence")
    elif item.rating is PhysicalSaasApplicabilityRating.NOT_APPLICABLE:
        if not item.contradicting_record_ids:
            raise ContractViolation("NOT_APPLICABLE requires contradicting evidence")
    elif item.rating is PhysicalSaasApplicabilityRating.CONDITIONAL:
        if not item.supporting_record_ids and not item.contradicting_record_ids:
            raise ContractViolation("CONDITIONAL requires evidence")


def _refs(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
            raise ContractViolation(f"{field} must contain bounded canonical references")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
