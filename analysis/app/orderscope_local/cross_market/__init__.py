"""Macro and cross-market contracts for the reconstructed v0.1 lineage."""

from .cftc_positioning import CftcTffPositioningPoint, parse_cftc_tff_csv
from .fred_alfred import (
    FredSeriesDescriptor,
    FredVintageDate,
    FredVintageObservation,
    parse_fred_observations_json,
    parse_fred_vintage_dates_json,
)
from .fred_fallback_policy import (
    FallbackSelectionDecision,
    FallbackSeriesExpectation,
    MacroSourceSelection,
    OfficialSourceState,
    select_macro_source,
)
from .japan_macro_sources import JapanMacroRawPoint, parse_boj_usdjpy_json, parse_mof_jgb_csv
from .macro_metrics import (
    CurveChange,
    CurveShape,
    MacroMetricInput,
    classify_curve_change,
    classify_curve_shape,
    cross_country_spread,
    curve_slope,
    series_delta,
    series_velocity_per_day,
)
from .ny_fed_rates import NyFedReferenceRatePoint, parse_ny_fed_reference_rates_json
from .official_macro_sources import (
    OfficialMacroRawPoint,
    TREASURY_PAR_YIELD_SOURCE,
    parse_treasury_par_yield_csv,
)
from .relative_repricing import (
    METHOD_VERSION as RELATIVE_REPRICING_METHOD_VERSION,
    RelativeRepricingMetrics,
    evaluate_relative_repricing,
)
from .validation import SeriesMeasure, SeriesObservation, SeriesRole

__all__ = [
    "CftcTffPositioningPoint",
    "CurveChange",
    "CurveShape",
    "FallbackSelectionDecision",
    "FallbackSeriesExpectation",
    "FredSeriesDescriptor",
    "FredVintageDate",
    "FredVintageObservation",
    "JapanMacroRawPoint",
    "MacroMetricInput",
    "MacroSourceSelection",
    "NyFedReferenceRatePoint",
    "OfficialMacroRawPoint",
    "OfficialSourceState",
    "RELATIVE_REPRICING_METHOD_VERSION",
    "RelativeRepricingMetrics",
    "SeriesMeasure",
    "SeriesObservation",
    "SeriesRole",
    "TREASURY_PAR_YIELD_SOURCE",
    "classify_curve_change",
    "classify_curve_shape",
    "cross_country_spread",
    "curve_slope",
    "evaluate_relative_repricing",
    "parse_boj_usdjpy_json",
    "parse_cftc_tff_csv",
    "parse_fred_observations_json",
    "parse_fred_vintage_dates_json",
    "parse_mof_jgb_csv",
    "parse_ny_fed_reference_rates_json",
    "parse_treasury_par_yield_csv",
    "select_macro_source",
    "series_delta",
    "series_velocity_per_day",
]
