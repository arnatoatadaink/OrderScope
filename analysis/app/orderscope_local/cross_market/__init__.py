"""A0-002 cross-market validation contracts."""

from .alpaca_daily import (
    AlpacaDailyBarsTransport,
    AlpacaDailyRequestFailure,
    DailySeriesBinding,
    DEFAULT_A0_ALPACA_BINDINGS,
    collect_a0_alpaca_daily,
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
    "DailySeriesBinding",
    "DEFAULT_A0_ALPACA_BINDINGS",
    "HypothesisRating",
    "HypothesisResult",
    "SeriesMeasure",
    "SeriesObservation",
    "SeriesRole",
    "SeriesSpec",
    "aligned_timeline",
    "collect_a0_alpaca_daily",
    "load_source_manifest",
]
