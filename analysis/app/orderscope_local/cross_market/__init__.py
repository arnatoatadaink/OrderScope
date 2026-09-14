"""A0 cross-market validation and macro-source helpers."""

from .alpaca_daily import (
    AlpacaDailyBarsTransport,
    AlpacaDailyRequestFailure,
    DailySeriesBinding,
    DEFAULT_A0_ALPACA_BINDINGS,
    collect_a0_alpaca_daily,
)
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
from .source_manifest import A0SourceManifest, load_source_manifest
from .validation import (
    A0ValidationCase,
    A0ValidationWindows,
    HypothesisRating,
    HypothesisResult,
    SeriesMeasure,
    SeriesObservation,
    SeriesRole,
    SeriesSpec,
    aligned_timeline,
)

__all__ = [
    "A0SourceManifest",
    "A0ValidationCase",
    "A0ValidationWindows",
    "AlpacaDailyBarsTransport",
    "AlpacaDailyRequestFailure",
    "CurveChange",
    "CurveShape",
    "DailySeriesBinding",
    "DEFAULT_A0_ALPACA_BINDINGS",
    "HypothesisRating",
    "HypothesisResult",
    "MacroMetricInput",
    "NyFedReferenceRatePoint",
    "OfficialMacroRawPoint",
    "RELATIVE_REPRICING_METHOD_VERSION",
    "RelativeRepricingMetrics",
    "SeriesMeasure",
    "SeriesObservation",
    "SeriesRole",
    "SeriesSpec",
    "TREASURY_PAR_YIELD_SOURCE",
    "aligned_timeline",
    "classify_curve_change",
    "classify_curve_shape",
    "collect_a0_alpaca_daily",
    "cross_country_spread",
    "curve_slope",
    "evaluate_relative_repricing",
    "load_source_manifest",
    "parse_ny_fed_reference_rates_json",
    "parse_treasury_par_yield_csv",
    "series_delta",
    "series_velocity_per_day",
]
