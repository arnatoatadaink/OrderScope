"""UWBS-066 historical-case summaries without invented reaction coefficients."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from statistics import median

from orderscope_local.contracts.errors import ContractViolation

from .observation import ThemeReactionObservation
from .ontology import ThemeId, require_ref, require_refs


class CaseLabel(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    CONTROL = "CONTROL"
    CONTRADICTORY = "CONTRADICTORY"


@dataclass(frozen=True, kw_only=True)
class HistoricalThemeCase:
    case_ref: str
    event_class: str
    observation: ThemeReactionObservation
    label: CaseLabel
    source_refs: tuple[str, ...]
    review_ref: str

    def __post_init__(self) -> None:
        require_ref(self.case_ref, "case_ref")
        require_ref(self.event_class, "event_class")
        require_ref(self.review_ref, "review_ref")
        require_refs(self.source_refs, "source_refs")
        if not isinstance(self.label, CaseLabel):
            raise ContractViolation("label must be CaseLabel")
        if self.event_class != self.observation.hypothesis.event_class:
            raise ContractViolation("case event class must match the observation")


@dataclass(frozen=True)
class ThemeCalibrationSummary:
    theme: ThemeId
    event_class: str
    case_count: int
    label_counts: tuple[tuple[CaseLabel, int], ...]
    median_relative_return_pct: float
    median_directional_breadth: float | None
    case_refs: tuple[str, ...]
    review_refs: tuple[str, ...]
    ready_for_threshold_review: bool


def summarize_historical_cases(cases: tuple[HistoricalThemeCase, ...]) -> ThemeCalibrationSummary:
    """Describe the reviewed sample; never manufacture a confirmation threshold."""
    if not isinstance(cases, tuple) or not cases:
        raise ContractViolation("cases must be a non-empty immutable tuple")
    if any(not isinstance(item, HistoricalThemeCase) for item in cases):
        raise ContractViolation("cases must contain HistoricalThemeCase")
    if len({item.case_ref for item in cases}) != len(cases):
        raise ContractViolation("case references cannot repeat")
    themes = {item.observation.hypothesis.theme for item in cases}
    classes = {item.event_class for item in cases}
    if len(themes) != 1 or len(classes) != 1:
        raise ContractViolation("calibration summary requires one event class and one theme")
    labels = tuple((label, sum(item.label is label for item in cases)) for label in CaseLabel)
    breadths = [item.observation.directional_breadth for item in cases if item.observation.directional_breadth is not None]
    present = {item.label for item in cases}
    return ThemeCalibrationSummary(
        theme=cases[0].observation.hypothesis.theme,
        event_class=cases[0].event_class,
        case_count=len(cases),
        label_counts=labels,
        median_relative_return_pct=median(item.observation.median_relative_return_pct for item in cases),
        median_directional_breadth=median(breadths) if breadths else None,
        case_refs=tuple(item.case_ref for item in cases),
        review_refs=tuple(item.review_ref for item in cases),
        ready_for_threshold_review=CaseLabel.POSITIVE in present and CaseLabel.NEGATIVE in present and CaseLabel.CONTROL in present,
    )
