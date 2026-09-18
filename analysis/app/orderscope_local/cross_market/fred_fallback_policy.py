"""UWBS-035 explicit FRED/ALFRED fallback selection policy.

Official-direct sources remain preferred. FRED/ALFRED may be selected only when
the direct source is explicitly unavailable and the reviewed descriptor matches
the expected source semantics. The policy never merges direct and fallback data
inside one selection decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from orderscope_local.contracts import ContractViolation, MacroMarketRegion, MacroMarketSeriesKind
from .fred_alfred import FredSeriesDescriptor


class OfficialSourceState(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class MacroSourceSelection(StrEnum):
    OFFICIAL_DIRECT = "OFFICIAL_DIRECT"
    FRED_FALLBACK = "FRED_FALLBACK"


@dataclass(frozen=True, kw_only=True, slots=True)
class FallbackSeriesExpectation:
    series_kind: MacroMarketSeriesKind
    region: MacroMarketRegion
    unit: str
    official_source_ref: str
    tenor: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.series_kind, MacroMarketSeriesKind):
            raise ContractViolation("series_kind must be MacroMarketSeriesKind")
        if not isinstance(self.region, MacroMarketRegion):
            raise ContractViolation("region must be MacroMarketRegion")
        for value, field in ((self.unit, "unit"), (self.official_source_ref, "official_source_ref")):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if self.tenor is not None and (not self.tenor.strip() or self.tenor != self.tenor.strip()):
            raise ContractViolation("tenor must be canonical non-empty text")


@dataclass(frozen=True, kw_only=True, slots=True)
class FallbackSelectionDecision:
    selection: MacroSourceSelection
    source_ref: str
    terms_ref: str | None


def select_macro_source(
    *,
    official_state: OfficialSourceState,
    expectation: FallbackSeriesExpectation,
    fallback_descriptor: FredSeriesDescriptor | None = None,
) -> FallbackSelectionDecision:
    if not isinstance(official_state, OfficialSourceState):
        raise ContractViolation("official_state must be OfficialSourceState")
    if not isinstance(expectation, FallbackSeriesExpectation):
        raise ContractViolation("expectation must be FallbackSeriesExpectation")

    if official_state is OfficialSourceState.AVAILABLE:
        return FallbackSelectionDecision(
            selection=MacroSourceSelection.OFFICIAL_DIRECT,
            source_ref=expectation.official_source_ref,
            terms_ref=None,
        )

    if fallback_descriptor is None:
        raise ContractViolation("official source unavailable and no reviewed fallback descriptor supplied")
    if not isinstance(fallback_descriptor, FredSeriesDescriptor):
        raise ContractViolation("fallback_descriptor must be FredSeriesDescriptor")

    expected_semantics = (
        expectation.series_kind,
        expectation.region,
        expectation.unit,
        expectation.tenor,
        expectation.official_source_ref,
    )
    fallback_semantics = (
        fallback_descriptor.series_kind,
        fallback_descriptor.region,
        fallback_descriptor.unit,
        fallback_descriptor.tenor,
        fallback_descriptor.underlying_source_ref,
    )
    if fallback_semantics != expected_semantics:
        raise ContractViolation("FRED fallback semantics do not match the reviewed official series")

    return FallbackSelectionDecision(
        selection=MacroSourceSelection.FRED_FALLBACK,
        source_ref=f"fred:{fallback_descriptor.series_id}",
        terms_ref=fallback_descriptor.terms_ref,
    )
