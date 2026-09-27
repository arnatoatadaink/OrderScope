from __future__ import annotations

import pytest

from orderscope_local.contracts import ContractViolation, MacroMarketRegion, MacroMarketSeriesKind
from orderscope_local.cross_market.fred_alfred import FredSeriesDescriptor
from orderscope_local.cross_market.fred_fallback_policy import (
    FallbackSeriesExpectation,
    MacroSourceSelection,
    OfficialSourceState,
    select_macro_source,
)


def _expectation() -> FallbackSeriesExpectation:
    return FallbackSeriesExpectation(
        series_kind=MacroMarketSeriesKind.SOVEREIGN_YIELD,
        region=MacroMarketRegion.US,
        unit="percent",
        official_source_ref="federal-reserve:h15:dgs10",
        tenor="10Y",
    )


def _fallback() -> FredSeriesDescriptor:
    return FredSeriesDescriptor(
        series_id="DGS10",
        series_kind=MacroMarketSeriesKind.SOVEREIGN_YIELD,
        region=MacroMarketRegion.US,
        unit="percent",
        underlying_source_ref="federal-reserve:h15:dgs10",
        terms_ref="fred:terms-reviewed",
        tenor="10Y",
    )


def test_official_direct_wins_even_when_fallback_exists() -> None:
    decision = select_macro_source(
        official_state=OfficialSourceState.AVAILABLE,
        expectation=_expectation(),
        fallback_descriptor=_fallback(),
    )
    assert decision.selection is MacroSourceSelection.OFFICIAL_DIRECT
    assert decision.source_ref == "federal-reserve:h15:dgs10"
    assert decision.terms_ref is None


def test_reviewed_fred_fallback_allowed_only_when_official_unavailable() -> None:
    decision = select_macro_source(
        official_state=OfficialSourceState.UNAVAILABLE,
        expectation=_expectation(),
        fallback_descriptor=_fallback(),
    )
    assert decision.selection is MacroSourceSelection.FRED_FALLBACK
    assert decision.source_ref == "fred:DGS10"
    assert decision.terms_ref == "fred:terms-reviewed"


def test_unavailable_without_fallback_fails_closed() -> None:
    with pytest.raises(ContractViolation, match="no reviewed fallback descriptor"):
        select_macro_source(
            official_state=OfficialSourceState.UNAVAILABLE,
            expectation=_expectation(),
        )


def test_semantic_substitution_fails_closed() -> None:
    bad = FredSeriesDescriptor(
        series_id="DGS5",
        series_kind=MacroMarketSeriesKind.SOVEREIGN_YIELD,
        region=MacroMarketRegion.US,
        unit="percent",
        underlying_source_ref="federal-reserve:h15:dgs5",
        terms_ref="fred:terms-reviewed",
        tenor="5Y",
    )
    with pytest.raises(ContractViolation, match="semantics do not match"):
        select_macro_source(
            official_state=OfficialSourceState.UNAVAILABLE,
            expectation=_expectation(),
            fallback_descriptor=bad,
        )
