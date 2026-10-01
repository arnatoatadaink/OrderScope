"""UWBS-063 event-to-theme hypotheses; no fixed numeric coefficients."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import Interpretation, InterpretationAssertionKind

from .ontology import ThemeId, require_ref, require_refs, require_utc


class ReactionDirection(StrEnum):
    STRONG_NEGATIVE = "STRONG_NEGATIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL_OR_UNKNOWN = "NEUTRAL_OR_UNKNOWN"
    POSITIVE = "POSITIVE"
    STRONG_POSITIVE = "STRONG_POSITIVE"

    @property
    def sign(self) -> int:
        if self in (self.STRONG_NEGATIVE, self.NEGATIVE):
            return -1
        if self in (self.POSITIVE, self.STRONG_POSITIVE):
            return 1
        return 0


class RelationType(StrEnum):
    DEMAND_ACCELERATOR = "DEMAND_ACCELERATOR"
    RISK_ACCELERATOR = "RISK_ACCELERATOR"
    REGULATORY_ACCELERATOR = "REGULATORY_ACCELERATOR"
    SUPPLY_RELIEF = "SUPPLY_RELIEF"
    SUPPLY_CONSTRAINT = "SUPPLY_CONSTRAINT"
    ADOPTION_ACCELERATOR = "ADOPTION_ACCELERATOR"
    ADOPTION_DECELERATOR = "ADOPTION_DECELERATOR"
    THREAT_ACCELERATOR = "THREAT_ACCELERATOR"
    CONTROL_REQUIREMENT = "CONTROL_REQUIREMENT"


@dataclass(frozen=True, kw_only=True)
class EventThemeHypothesis:
    event_ref: str
    event_class: str
    theme: ThemeId
    relation: RelationType
    expected_direction: ReactionDirection
    event_evidence_refs: tuple[str, ...]
    rationale_ref: str
    accepted_at: datetime
    method_version: str = "event-theme-hypothesis-v0.1"

    def __post_init__(self) -> None:
        for field in ("event_ref", "event_class", "rationale_ref", "method_version"):
            require_ref(getattr(self, field), field)
        if not isinstance(self.theme, ThemeId):
            raise ContractViolation("theme must be a versioned ThemeId")
        if not isinstance(self.relation, RelationType) or not isinstance(self.expected_direction, ReactionDirection):
            raise ContractViolation("relation and expected_direction must use categorical enums")
        require_refs(self.event_evidence_refs, "event_evidence_refs")
        require_utc(self.accepted_at, "accepted_at")

    def to_interpretation(self, *, record_id: str, accepted_at: datetime) -> Interpretation:
        """Materialize a hypothesis as Interpretation, never as a source Fact."""
        require_utc(accepted_at, "accepted_at")
        if accepted_at < self.accepted_at:
            raise ContractViolation("interpretation acceptance cannot precede hypothesis acceptance")
        return Interpretation(
            record_id=record_id,
            schema_version="event-theme-hypothesis-v0.1",
            subject_ref=f"theme:{self.theme.value}",
            accepted_at=accepted_at,
            created_at=self.accepted_at,
            interpretation_type="event_theme_hypothesis",
            statement={
                "event_ref": self.event_ref,
                "event_class": self.event_class,
                "relation": self.relation.value,
                "expected_direction": self.expected_direction.value,
                "rationale_ref": self.rationale_ref,
            },
            basis_record_ids=self.event_evidence_refs,
            method="event_theme_hypothesis",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )


@dataclass(frozen=True)
class EventThemeHypotheses:
    """One event may affect several themes, including same-direction siblings."""

    hypotheses: tuple[EventThemeHypothesis, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.hypotheses, tuple) or not self.hypotheses:
            raise ContractViolation("hypotheses must be a non-empty immutable tuple")
        if len({item.event_ref for item in self.hypotheses}) != 1:
            raise ContractViolation("hypotheses must describe one event")
        themes = [item.theme for item in self.hypotheses]
        if len(themes) != len(set(themes)):
            raise ContractViolation("one event cannot have duplicate theme hypotheses")

    @property
    def event_ref(self) -> str:
        return self.hypotheses[0].event_ref
