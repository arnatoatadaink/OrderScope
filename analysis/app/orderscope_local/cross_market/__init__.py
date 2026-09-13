"""A0-002 cross-market validation contracts."""

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
    "HypothesisRating",
    "HypothesisResult",
    "SeriesMeasure",
    "SeriesObservation",
    "SeriesRole",
    "SeriesSpec",
    "aligned_timeline",
    "load_source_manifest",
]
