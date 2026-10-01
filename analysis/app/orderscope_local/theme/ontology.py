"""UWBS-062 versioned theme identities and evidence-backed structural exposure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation


class ThemeId(StrEnum):
    AI = "AI"
    AI_FOUNDATION = "AI_FOUNDATION"
    AI_APPLICATION = "AI_APPLICATION"
    PHYSICAL_AI = "PHYSICAL_AI"
    AI_SECURITY = "AI_SECURITY"
    AI_GOVERNANCE = "AI_GOVERNANCE"
    CYBERSECURITY = "CYBERSECURITY"
    DEFENSE_INDUSTRIAL = "DEFENSE_INDUSTRIAL"


PARENT_THEME: dict[ThemeId, ThemeId | None] = {
    ThemeId.AI: None,
    ThemeId.AI_FOUNDATION: ThemeId.AI,
    ThemeId.AI_APPLICATION: ThemeId.AI,
    ThemeId.PHYSICAL_AI: ThemeId.AI_APPLICATION,
    ThemeId.AI_SECURITY: ThemeId.AI,
    ThemeId.AI_GOVERNANCE: ThemeId.AI,
    ThemeId.CYBERSECURITY: None,
    ThemeId.DEFENSE_INDUSTRIAL: None,
}


class ExposureStrength(StrEnum):
    CORE = "CORE"
    MATERIAL = "MATERIAL"
    SECONDARY = "SECONDARY"
    INCIDENTAL = "INCIDENTAL"
    UNKNOWN = "UNKNOWN"


def require_ref(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 255:
        raise ContractViolation(f"{field} must be a bounded canonical reference")


def require_refs(values: tuple[str, ...], field: str, *, nonempty: bool = True) -> None:
    if not isinstance(values, tuple) or (nonempty and not values):
        raise ContractViolation(f"{field} must be a non-empty immutable tuple")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicate references")
    for value in values:
        require_ref(value, field)


def require_utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


@dataclass(frozen=True, kw_only=True)
class ThemeExposure:
    subject_ref: str
    theme: ThemeId
    strength: ExposureStrength
    evidence_refs: tuple[str, ...]
    effective_from: datetime
    accepted_at: datetime
    effective_to: datetime | None = None
    ontology_version: str = "theme-ontology-v0.1"

    def __post_init__(self) -> None:
        require_ref(self.subject_ref, "subject_ref")
        require_ref(self.ontology_version, "ontology_version")
        if not isinstance(self.theme, ThemeId) or not isinstance(self.strength, ExposureStrength):
            raise ContractViolation("theme and strength must use the versioned enums")
        require_refs(self.evidence_refs, "evidence_refs")
        require_utc(self.effective_from, "effective_from")
        require_utc(self.accepted_at, "accepted_at")
        if self.effective_to is not None:
            require_utc(self.effective_to, "effective_to")
            if self.effective_to <= self.effective_from:
                raise ContractViolation("effective_to must follow effective_from")
        if self.accepted_at < self.effective_from:
            raise ContractViolation("accepted_at cannot precede effective_from")


@dataclass(frozen=True)
class ThemeExposureSet:
    """A subject may hold multiple independent structural exposures."""

    exposures: tuple[ThemeExposure, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.exposures, tuple) or not self.exposures:
            raise ContractViolation("exposures must be a non-empty immutable tuple")
        subjects = {item.subject_ref for item in self.exposures}
        if len(subjects) != 1:
            raise ContractViolation("all exposures must belong to one subject")
        themes = [item.theme for item in self.exposures]
        if len(themes) != len(set(themes)):
            raise ContractViolation("one subject cannot have duplicate current theme exposures")
        versions = {item.ontology_version for item in self.exposures}
        if len(versions) != 1:
            raise ContractViolation("exposures must use one ontology version")

    @property
    def subject_ref(self) -> str:
        return self.exposures[0].subject_ref

    def has_explicit(self, theme: ThemeId) -> bool:
        return any(item.theme is theme and item.strength is not ExposureStrength.UNKNOWN for item in self.exposures)
