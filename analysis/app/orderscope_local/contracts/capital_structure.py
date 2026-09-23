"""UWBS-019 capital-structure Interpretation boundary.

This module distinguishes removal of one convertible-note dilution overhang from
removal of all issuer dilution risk. Remaining warrants or other instruments are
kept as explicit residual-exposure references.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .capital_instrument_state import CapitalInstrumentKind, CapitalInstrumentState
from .errors import ContractViolation
from .fact_store import Interpretation, InterpretationAssertionKind


class CapitalStructureInterpretationType(StrEnum):
    CONVERTIBLE_NOTE_OVERHANG_REMOVED = "convertible_note_overhang_removed"
    CAPITAL_STRUCTURE_REGIME_CHANGE = "capital_structure_regime_change"


class ResidualDilutionState(StrEnum):
    NONE_KNOWN = "none_known"
    REMAINS = "remains"
    UNKNOWN = "unknown"


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str, *, required: bool = False) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if required and not values:
        raise ContractViolation(f"{field} cannot be empty")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
            raise ContractViolation(f"{field} must contain bounded canonical references")


@dataclass(frozen=True, kw_only=True)
class CapitalStructureAssessment:
    interpretation_type: CapitalStructureInterpretationType
    subject_ref: str
    instrument_ref: str
    instrument_kind: CapitalInstrumentKind
    terminal_state: CapitalInstrumentState
    residual_dilution_state: ResidualDilutionState
    instrument_fact_record_ids: tuple[str, ...]
    resolution_evidence_record_ids: tuple[str, ...]
    residual_instrument_record_ids: tuple[str, ...] = ()
    generated_at: datetime
    method_version: str = "capital-structure-v0.1"

    def __post_init__(self) -> None:
        for value, field in ((self.subject_ref, "subject_ref"), (self.instrument_ref, "instrument_ref"), (self.method_version, "method_version")):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if not isinstance(self.interpretation_type, CapitalStructureInterpretationType):
            raise ContractViolation("interpretation_type must be CapitalStructureInterpretationType")
        if self.instrument_kind is not CapitalInstrumentKind.CONVERTIBLE_NOTE:
            raise ContractViolation("UWBS-019 assessment is limited to convertible-note overhang")
        if self.terminal_state not in {CapitalInstrumentState.FULLY_REPAID, CapitalInstrumentState.CONVERTED, CapitalInstrumentState.TERMINATED}:
            raise ContractViolation("convertible-note overhang removal requires a terminal instrument state")
        if not isinstance(self.residual_dilution_state, ResidualDilutionState):
            raise ContractViolation("residual_dilution_state must be ResidualDilutionState")
        _utc(self.generated_at, "generated_at")
        _refs(self.instrument_fact_record_ids, "instrument_fact_record_ids", required=True)
        _refs(self.resolution_evidence_record_ids, "resolution_evidence_record_ids", required=True)
        _refs(self.residual_instrument_record_ids, "residual_instrument_record_ids")
        groups = [set(self.instrument_fact_record_ids), set(self.resolution_evidence_record_ids), set(self.residual_instrument_record_ids)]
        for index, left in enumerate(groups):
            for right in groups[index + 1:]:
                if left & right:
                    raise ContractViolation("capital-structure evidence classes cannot reuse record references")
        if self.residual_dilution_state is ResidualDilutionState.REMAINS and not self.residual_instrument_record_ids:
            raise ContractViolation("residual dilution marked REMAINS requires residual instrument lineage")
        if self.residual_dilution_state is ResidualDilutionState.NONE_KNOWN and self.residual_instrument_record_ids:
            raise ContractViolation("NONE_KNOWN cannot include residual instrument references")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return self.instrument_fact_record_ids + self.resolution_evidence_record_ids + self.residual_instrument_record_ids

    def to_interpretation(self, *, record_id: str, accepted_at: datetime, supersedes_record_id: str | None = None) -> Interpretation:
        _utc(accepted_at, "accepted_at")
        if accepted_at < self.generated_at:
            raise ContractViolation("accepted_at cannot precede generated_at")
        return Interpretation(
            record_id=record_id,
            schema_version="capital-structure-interpretation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            supersedes_record_id=supersedes_record_id,
            interpretation_type=self.interpretation_type.value,
            statement={
                "instrument_ref": self.instrument_ref,
                "instrument_kind": self.instrument_kind.value,
                "terminal_state": self.terminal_state.value,
                "residual_dilution_state": self.residual_dilution_state.value,
                "all_dilution_removed": False if self.residual_dilution_state is not ResidualDilutionState.NONE_KNOWN else None,
            },
            basis_record_ids=self.basis_record_ids,
            method="capital_structure_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )
