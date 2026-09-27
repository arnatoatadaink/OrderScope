"""UWBS-083 oil-down / inflation-growth interpretation boundary.

This module never turns a single price move, inventory print, or geopolitical
headline into a causal conclusion.  It stores bounded candidate assessments over
independent signal classes and preserves contradictory evidence explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import Interpretation, InterpretationAssertionKind


class CommodityInterpretationType(StrEnum):
    OIL_DOWN_SUPPLY_RELIEF_CANDIDATE = "oil_down_supply_relief_candidate"
    OIL_DOWN_DEMAND_WEAKNESS_CANDIDATE = "oil_down_demand_weakness_candidate"
    OIL_DOWN_INVENTORY_BUILD_CANDIDATE = "oil_down_inventory_build_candidate"
    DISINFLATION_SUPPORT_CANDIDATE = "disinflation_support_candidate"
    GROWTH_RISK_WARNING_CANDIDATE = "growth_risk_warning_candidate"


class CommodityInterpretationRating(StrEnum):
    SUPPORT = "SUPPORT"
    PARTIAL = "PARTIAL"
    CONTRADICT = "CONTRADICT"
    UNKNOWN = "UNKNOWN"


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
            raise ContractViolation(f"{field} must contain bounded canonical references")


@dataclass(frozen=True, kw_only=True)
class CommodityInterpretationAssessment:
    interpretation_type: CommodityInterpretationType
    rating: CommodityInterpretationRating
    subject_ref: str
    observed_window_start: datetime
    observed_window_end: datetime
    price_metric_refs: tuple[str, ...]
    fundamental_metric_refs: tuple[str, ...] = ()
    event_fact_refs: tuple[str, ...] = ()
    macro_metric_refs: tuple[str, ...] = ()
    contradicting_evidence_refs: tuple[str, ...] = ()
    generated_at: datetime
    method_version: str = "commodity-interpretation-v0.1"

    def __post_init__(self) -> None:
        if not isinstance(self.interpretation_type, CommodityInterpretationType):
            raise ContractViolation("interpretation_type must be CommodityInterpretationType")
        if not isinstance(self.rating, CommodityInterpretationRating):
            raise ContractViolation("rating must be CommodityInterpretationRating")
        if not isinstance(self.subject_ref, str) or not self.subject_ref.strip() or self.subject_ref != self.subject_ref.strip():
            raise ContractViolation("subject_ref must be canonical non-empty text")
        if not isinstance(self.method_version, str) or not self.method_version.strip():
            raise ContractViolation("method_version cannot be blank")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end:
            raise ContractViolation("observed window must be non-empty and half-open")
        if self.generated_at < self.observed_window_end:
            raise ContractViolation("generated_at cannot precede observed window end")

        groups = (
            (self.price_metric_refs, "price_metric_refs"),
            (self.fundamental_metric_refs, "fundamental_metric_refs"),
            (self.event_fact_refs, "event_fact_refs"),
            (self.macro_metric_refs, "macro_metric_refs"),
            (self.contradicting_evidence_refs, "contradicting_evidence_refs"),
        )
        for values, field in groups:
            _refs(values, field)
        sets = [set(values) for values, _ in groups]
        for index, left in enumerate(sets):
            for right in sets[index + 1 :]:
                if left & right:
                    raise ContractViolation("commodity interpretation evidence classes cannot reuse references")

        supporting_groups = sum(
            bool(values)
            for values in (
                self.price_metric_refs,
                self.fundamental_metric_refs,
                self.event_fact_refs,
                self.macro_metric_refs,
            )
        )
        if self.rating is CommodityInterpretationRating.UNKNOWN:
            if supporting_groups or self.contradicting_evidence_refs:
                raise ContractViolation("UNKNOWN assessment cannot carry directional evidence")
            return
        if self.rating is CommodityInterpretationRating.CONTRADICT:
            if not self.contradicting_evidence_refs:
                raise ContractViolation("CONTRADICT assessment requires contradicting evidence")
            return

        if not self.price_metric_refs:
            raise ContractViolation("supported oil-down interpretation requires price evidence")
        if supporting_groups < 2:
            raise ContractViolation("supported commodity interpretation requires at least two independent signal classes")

        if self.interpretation_type is CommodityInterpretationType.OIL_DOWN_SUPPLY_RELIEF_CANDIDATE:
            if not (self.fundamental_metric_refs or self.event_fact_refs):
                raise ContractViolation("supply-relief candidate requires fundamental or event evidence")
        elif self.interpretation_type is CommodityInterpretationType.OIL_DOWN_DEMAND_WEAKNESS_CANDIDATE:
            if not (self.fundamental_metric_refs or self.macro_metric_refs):
                raise ContractViolation("demand-weakness candidate requires fundamental or macro evidence")
        elif self.interpretation_type is CommodityInterpretationType.OIL_DOWN_INVENTORY_BUILD_CANDIDATE:
            if not self.fundamental_metric_refs:
                raise ContractViolation("inventory-build candidate requires fundamental evidence")
        elif self.interpretation_type is CommodityInterpretationType.DISINFLATION_SUPPORT_CANDIDATE:
            if not self.macro_metric_refs:
                raise ContractViolation("disinflation candidate requires macro evidence")
        elif self.interpretation_type is CommodityInterpretationType.GROWTH_RISK_WARNING_CANDIDATE:
            if not self.macro_metric_refs:
                raise ContractViolation("growth-risk candidate requires macro evidence")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return (
            self.price_metric_refs
            + self.fundamental_metric_refs
            + self.event_fact_refs
            + self.macro_metric_refs
            + self.contradicting_evidence_refs
        )

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
            raise ContractViolation("Fact Store Interpretation requires evidence lineage")
        return Interpretation(
            record_id=record_id,
            schema_version="commodity-interpretation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            supersedes_record_id=supersedes_record_id,
            interpretation_type=self.interpretation_type.value,
            statement={
                "rating": self.rating.value,
                "observed_window_start": self.observed_window_start.isoformat(),
                "observed_window_end": self.observed_window_end.isoformat(),
                "price_signal_count": len(self.price_metric_refs),
                "fundamental_signal_count": len(self.fundamental_metric_refs),
                "event_signal_count": len(self.event_fact_refs),
                "macro_signal_count": len(self.macro_metric_refs),
                "contradicting_count": len(self.contradicting_evidence_refs),
            },
            basis_record_ids=self.basis_record_ids,
            method="commodity_interpretation_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )
