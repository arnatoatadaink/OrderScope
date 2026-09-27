"""UWBS-093 Physical-SaaS Canary evaluation.

The Canary keeps held-out expected labels out of classification.  It combines
accepted UWBS-089..092 outputs only after the Physical-SaaS applicability guard
opens the downstream lane, then compares the observed classification with the
held-out expectation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.physical_saas.applicability import (
    PhysicalSaasApplicabilityAssessment,
)


class PhysicalSaasCanaryLabel(StrEnum):
    SUPPORT = "support"
    CAUTION = "caution"
    REJECT = "reject"
    UNKNOWN = "unknown"


class PhysicalSaasCanaryDecision(StrEnum):
    ACCEPT = "accept"
    REVIEW = "review"
    REJECT = "reject"


@dataclass(frozen=True, kw_only=True)
class PhysicalSaasCanarySignals:
    applicability: PhysicalSaasApplicabilityAssessment
    deployment_support_refs: tuple[str, ...] = ()
    deployment_caution_refs: tuple[str, ...] = ()
    financial_support_refs: tuple[str, ...] = ()
    financial_caution_refs: tuple[str, ...] = ()
    integration_support_refs: tuple[str, ...] = ()
    integration_caution_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.applicability, PhysicalSaasApplicabilityAssessment):
            raise ContractViolation("applicability must be PhysicalSaasApplicabilityAssessment")
        groups = (
            self.deployment_support_refs,
            self.deployment_caution_refs,
            self.financial_support_refs,
            self.financial_caution_refs,
            self.integration_support_refs,
            self.integration_caution_refs,
        )
        for group in groups:
            _refs(group)
        all_refs = tuple(ref for group in groups for ref in group)
        if len(all_refs) != len(set(all_refs)):
            raise ContractViolation("Canary signal references cannot be reused across classes")

    @property
    def support_class_count(self) -> int:
        return sum(
            bool(group)
            for group in (
                self.deployment_support_refs,
                self.financial_support_refs,
                self.integration_support_refs,
            )
        )

    @property
    def caution_class_count(self) -> int:
        return sum(
            bool(group)
            for group in (
                self.deployment_caution_refs,
                self.financial_caution_refs,
                self.integration_caution_refs,
            )
        )


@dataclass(frozen=True, kw_only=True)
class PhysicalSaasCanaryObservation:
    label: PhysicalSaasCanaryLabel
    alert: bool
    support_class_count: int
    caution_class_count: int


@dataclass(frozen=True, kw_only=True)
class PhysicalSaasCanaryResult:
    expected_label: PhysicalSaasCanaryLabel
    expected_alert: bool
    observed: PhysicalSaasCanaryObservation
    false_positive_count: int
    false_negative_count: int
    label_mismatch_count: int
    decision: PhysicalSaasCanaryDecision

    @property
    def clean(self) -> bool:
        return (
            self.false_positive_count == 0
            and self.false_negative_count == 0
            and self.label_mismatch_count == 0
        )


def classify_physical_saas_canary(
    signals: PhysicalSaasCanarySignals,
) -> PhysicalSaasCanaryObservation:
    """Classify without any held-out expected label input."""

    if not isinstance(signals, PhysicalSaasCanarySignals):
        raise TypeError("signals must be PhysicalSaasCanarySignals")

    if not signals.applicability.downstream_allowed:
        return PhysicalSaasCanaryObservation(
            label=PhysicalSaasCanaryLabel.REJECT,
            alert=True,
            support_class_count=signals.support_class_count,
            caution_class_count=signals.caution_class_count,
        )

    support = signals.support_class_count
    caution = signals.caution_class_count

    if caution >= 2:
        label = PhysicalSaasCanaryLabel.CAUTION
        alert = True
    elif support >= 2 and caution == 0:
        label = PhysicalSaasCanaryLabel.SUPPORT
        alert = False
    elif support == 0 and caution == 0:
        label = PhysicalSaasCanaryLabel.UNKNOWN
        alert = False
    else:
        label = PhysicalSaasCanaryLabel.CAUTION
        alert = True

    return PhysicalSaasCanaryObservation(
        label=label,
        alert=alert,
        support_class_count=support,
        caution_class_count=caution,
    )


def evaluate_physical_saas_canary(
    *,
    expected_label: PhysicalSaasCanaryLabel,
    expected_alert: bool,
    observed: PhysicalSaasCanaryObservation,
) -> PhysicalSaasCanaryResult:
    """Compare an already-produced observation with a held-out expectation."""

    if not isinstance(expected_label, PhysicalSaasCanaryLabel):
        raise ContractViolation("expected_label must be PhysicalSaasCanaryLabel")
    if not isinstance(expected_alert, bool):
        raise ContractViolation("expected_alert must be bool")
    if not isinstance(observed, PhysicalSaasCanaryObservation):
        raise ContractViolation("observed must be PhysicalSaasCanaryObservation")

    false_positive = int(observed.alert and not expected_alert)
    false_negative = int(expected_alert and not observed.alert)
    mismatch = int(observed.label is not expected_label)

    if false_negative or mismatch:
        decision = PhysicalSaasCanaryDecision.REJECT
    elif false_positive:
        decision = PhysicalSaasCanaryDecision.REVIEW
    else:
        decision = PhysicalSaasCanaryDecision.ACCEPT

    return PhysicalSaasCanaryResult(
        expected_label=expected_label,
        expected_alert=expected_alert,
        observed=observed,
        false_positive_count=false_positive,
        false_negative_count=false_negative,
        label_mismatch_count=mismatch,
        decision=decision,
    )


def _refs(values: tuple[str, ...]) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation("Canary signal references must be immutable tuples")
    if len(values) != len(set(values)):
        raise ContractViolation("Canary signal references cannot contain duplicates")
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
            raise ContractViolation("Canary signal references must be bounded canonical references")
