"""A0-018 / UWBS-105 macro release observation contract.

REL-12A records released macro values and expectation/revision inputs as explicit
observations. Surprise calculation, event-window transmission and carry-state
interpretation are intentionally deferred to later REL-12 stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite

from .errors import ContractViolation
from .fact_store import Fact, FactAssertionKind
from .provenance import Provenance, SourceTimestamp


class MacroReleaseFamily(StrEnum):
    PCE = "pce"
    DURABLE_GOODS = "durable_goods"


class MacroReleaseValueRole(StrEnum):
    ACTUAL = "actual"
    CONSENSUS = "consensus"
    PRIOR = "prior"
    REVISED_PRIOR = "revised_prior"


@dataclass(frozen=True, kw_only=True)
class MacroReleaseObservation:
    release_id: str
    family: MacroReleaseFamily
    metric_id: str
    period_ref: str
    value_role: MacroReleaseValueRole
    value: float
    unit: str
    released_at: SourceTimestamp
    accepted_at: datetime
    provenance: Provenance
    revision_of_period_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.family, MacroReleaseFamily):
            raise ContractViolation("family must be MacroReleaseFamily")
        if not isinstance(self.value_role, MacroReleaseValueRole):
            raise ContractViolation("value_role must be MacroReleaseValueRole")

        for value, field in (
            (self.release_id, "release_id"),
            (self.metric_id, "metric_id"),
            (self.period_ref, "period_ref"),
            (self.unit, "unit"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")

        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or not isfinite(float(self.value)):
            raise ContractViolation("value must be a finite numeric observation")
        if not isinstance(self.released_at, SourceTimestamp):
            raise ContractViolation("released_at must be SourceTimestamp")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be Provenance")
        if self.accepted_at.tzinfo is None or self.accepted_at.utcoffset() != timedelta(0):
            raise ContractViolation("accepted_at must be normalized to UTC")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("accepted_at must match provenance.accepted_at")

        if self.value_role is MacroReleaseValueRole.REVISED_PRIOR:
            if self.revision_of_period_ref is None:
                raise ContractViolation("revised_prior requires revision_of_period_ref")
            if (
                not isinstance(self.revision_of_period_ref, str)
                or not self.revision_of_period_ref.strip()
                or self.revision_of_period_ref != self.revision_of_period_ref.strip()
            ):
                raise ContractViolation("revision_of_period_ref must be canonical non-empty text")
        elif self.revision_of_period_ref is not None:
            raise ContractViolation("revision_of_period_ref is only valid for revised_prior")

    def to_fact(self, *, record_id: str, evidence_record_ids: tuple[str, ...]) -> Fact:
        return Fact(
            record_id=record_id,
            schema_version="macro-release-observation-v0.1",
            subject_ref=f"macro.release.{self.release_id}.{self.metric_id}",
            accepted_at=self.accepted_at,
            created_at=self.accepted_at,
            provenance=self.provenance,
            fact_type=f"macro_release.{self.family.value}.{self.value_role.value}",
            value=float(self.value),
            assertion_kind=FactAssertionKind.OBSERVATION,
            evidence_record_ids=evidence_record_ids,
            unit=self.unit,
            period_start=self.released_at,
            period_end=self.released_at,
        )
