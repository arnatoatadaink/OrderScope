"""Deterministic classification helpers for UWBS-071."""

from __future__ import annotations

from datetime import datetime, time

from .models import AnalysisWindow, CryptoDayType, CryptoTimeContext, TraditionalBoundaryContext


def _contains(window: AnalysisWindow, clock: time) -> bool:
    """Return whether a UTC wall-clock time belongs to a possibly wrapping window."""

    if window.start_utc < window.end_utc:
        return window.start_utc <= clock < window.end_utc
    return clock >= window.start_utc or clock < window.end_utc


def classify_crypto_time(
    observed_at: datetime,
    *,
    windows: tuple[AnalysisWindow, ...] = (),
    boundary_contexts: tuple[TraditionalBoundaryContext, ...] = (),
) -> CryptoTimeContext:
    """Classify one UTC crypto observation without inferring participant identity.

    ``windows`` are explicit analysis buckets and may overlap.  Boundary
    contexts are caller-supplied evidence and are preserved unchanged.
    """

    clock = observed_at.timetz().replace(tzinfo=None)
    matching = tuple(window.window_id for window in windows if _contains(window, clock))
    day_type = CryptoDayType.WEEKEND if observed_at.weekday() >= 5 else CryptoDayType.WEEKDAY
    return CryptoTimeContext(
        observed_at=observed_at,
        utc_date=observed_at.date().isoformat(),
        utc_hour=observed_at.hour,
        day_type=day_type,
        analysis_window_ids=matching,
        boundary_contexts=boundary_contexts,
    )


def default_analysis_windows() -> tuple[AnalysisWindow, ...]:
    """Return conservative fixed UTC buckets used only for comparative analysis.

    The labels intentionally describe broad clock windows, not exchange
    sessions or participant geography.  They overlap so handoff periods remain
    observable instead of being forced into one mutually exclusive bucket.
    """

    return (
        AnalysisWindow("asia_clock_window", time(0, 0), time(9, 0)),
        AnalysisWindow("europe_clock_window", time(7, 0), time(16, 0)),
        AnalysisWindow("us_clock_window", time(13, 0), time(22, 0)),
    )
