"""Historical event replay contracts for REL-11D / C0-004.

This module keeps source-grounded event timestamp classes distinct and builds
fixed post-event return windows from accepted market observations.  Historical
market response never establishes exploit causality by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Mapping

from orderscope_local.crypto_context.models import CryptoReturnObservation

from .market_context import CausalityStatus, OnchainMarketContext
from .models import CryptoOnchainContractError


class ReplayAnchorKind(StrEnum):
    FIRST_ONCHAIN_DETECTABLE = "first_onchain_detectable"
    FIRST_PUBLIC = "first_public"
    FIRST_OFFICIAL = "first_official"


class ReplayWindow(StrEnum):
    M15 = "15m"
    H1 = "1h"
    H6 = "6h"
    H24 = "24h"
    H48 = "48h"
    D5 = "5d"
    D30 = "30d"

    @property
    def delta(self) -> timedelta:
        return {
            ReplayWindow.M15: timedelta(minutes=15),
            ReplayWindow.H1: timedelta(hours=1),
            ReplayWindow.H6: timedelta(hours=6),
            ReplayWindow.H24: timedelta(hours=24),
            ReplayWindow.H48: timedelta(hours=48),
            ReplayWindow.D5: timedelta(days=5),
            ReplayWindow.D30: timedelta(days=30),
        }[self]


REPLAY_WINDOWS = (
    ReplayWindow.M15,
    ReplayWindow.H1,
    ReplayWindow.H6,
    ReplayWindow.H24,
    ReplayWindow.H48,
    ReplayWindow.D5,
    ReplayWindow.D30,
)


@dataclass(frozen=True, kw_only=True)
class HistoricalEventTimestamps:
    event_id: str
    first_onchain_detectable_at: datetime | None = None
    first_public_at: datetime | None = None
    first_official_at: datetime | None = None
    onchain_source_ref: str | None = None
    public_source_ref: str | None = None
    official_source_ref: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.event_id, "event_id")
        pairs = (
            (self.first_onchain_detectable_at, self.onchain_source_ref, "first_onchain_detectable"),
            (self.first_public_at, self.public_source_ref, "first_public"),
            (self.first_official_at, self.official_source_ref, "first_official"),
        )
        if all(timestamp is None for timestamp, _, _ in pairs):
            raise CryptoOnchainContractError("at least one historical event timestamp is required")
        for timestamp, source_ref, label in pairs:
            if (timestamp is None) != (source_ref is None):
                raise CryptoOnchainContractError(f"{label} timestamp and source_ref must be supplied together")
            if timestamp is not None:
                _require_utc(timestamp, f"{label}_at")
                _require_text(source_ref, f"{label}_source_ref")

    def anchor(self, kind: ReplayAnchorKind) -> tuple[datetime, str]:
        if kind is ReplayAnchorKind.FIRST_ONCHAIN_DETECTABLE:
            value = self.first_onchain_detectable_at
            source = self.onchain_source_ref
        elif kind is ReplayAnchorKind.FIRST_PUBLIC:
            value = self.first_public_at
            source = self.public_source_ref
        elif kind is ReplayAnchorKind.FIRST_OFFICIAL:
            value = self.first_official_at
            source = self.official_source_ref
        else:
            raise CryptoOnchainContractError("unsupported replay anchor")
        if value is None or source is None:
            raise CryptoOnchainContractError(f"selected replay anchor is unavailable: {kind.value}")
        return value, source


@dataclass(frozen=True, kw_only=True)
class HistoricalWindowResult:
    window: ReplayWindow
    window_start: datetime
    window_end: datetime
    token_return_decimal: float | None
    btc_return_decimal: float | None
    btc_relative_return_decimal: float | None
    source_record_ids: tuple[str, ...]
    complete: bool

    def __post_init__(self) -> None:
        _require_utc(self.window_start, "window_start")
        _require_utc(self.window_end, "window_end")
        if self.window_end - self.window_start != self.window.delta:
            raise CryptoOnchainContractError("historical replay window duration does not match window label")
        if self.complete:
            if None in (self.token_return_decimal, self.btc_return_decimal, self.btc_relative_return_decimal):
                raise CryptoOnchainContractError("complete historical window requires token/BTC returns")
            if not self.source_record_ids:
                raise CryptoOnchainContractError("complete historical window requires source ids")
        else:
            if any(value is not None for value in (self.token_return_decimal, self.btc_return_decimal, self.btc_relative_return_decimal)):
                raise CryptoOnchainContractError("incomplete historical window cannot carry partial return values")


@dataclass(frozen=True, kw_only=True)
class HistoricalReplay:
    event: HistoricalEventTimestamps
    anchor_kind: ReplayAnchorKind
    anchor_at: datetime
    anchor_source_ref: str
    windows: tuple[HistoricalWindowResult, ...]
    market_phases: tuple[OnchainMarketContext, ...] = ()
    causality: CausalityStatus = CausalityStatus.NOT_ESTABLISHED

    def __post_init__(self) -> None:
        _require_utc(self.anchor_at, "anchor_at")
        _require_text(self.anchor_source_ref, "anchor_source_ref")
        if tuple(result.window for result in self.windows) != REPLAY_WINDOWS:
            raise CryptoOnchainContractError("historical replay windows must use the canonical ordered set")
        if self.causality is not CausalityStatus.NOT_ESTABLISHED:
            raise CryptoOnchainContractError("historical market replay cannot establish causality")
        if any(phase.causality is not CausalityStatus.NOT_ESTABLISHED for phase in self.market_phases):
            raise CryptoOnchainContractError("market phases must retain non-causal status")

    def window(self, window: ReplayWindow) -> HistoricalWindowResult:
        for result in self.windows:
            if result.window is window:
                return result
        raise KeyError(window)


def build_historical_replay(
    event: HistoricalEventTimestamps,
    *,
    anchor_kind: ReplayAnchorKind,
    token_returns: Mapping[ReplayWindow, CryptoReturnObservation],
    btc_returns: Mapping[ReplayWindow, CryptoReturnObservation],
    market_phases: tuple[OnchainMarketContext, ...] = (),
) -> HistoricalReplay:
    """Build the canonical REL-11D event-window replay.

    Missing either side of a token/BTC pair yields an explicitly incomplete
    window.  Partial returns are never inferred or backfilled.
    """

    if not isinstance(event, HistoricalEventTimestamps):
        raise CryptoOnchainContractError("event must be HistoricalEventTimestamps")
    if not isinstance(anchor_kind, ReplayAnchorKind):
        raise CryptoOnchainContractError("anchor_kind must be ReplayAnchorKind")
    anchor_at, anchor_source_ref = event.anchor(anchor_kind)

    unknown_token = set(token_returns) - set(REPLAY_WINDOWS)
    unknown_btc = set(btc_returns) - set(REPLAY_WINDOWS)
    if unknown_token or unknown_btc:
        raise CryptoOnchainContractError("return mappings contain unsupported replay windows")

    results: list[HistoricalWindowResult] = []
    for window in REPLAY_WINDOWS:
        token = token_returns.get(window)
        btc = btc_returns.get(window)
        expected_end = anchor_at + window.delta

        if token is None or btc is None:
            results.append(
                HistoricalWindowResult(
                    window=window,
                    window_start=anchor_at,
                    window_end=expected_end,
                    token_return_decimal=None,
                    btc_return_decimal=None,
                    btc_relative_return_decimal=None,
                    source_record_ids=(),
                    complete=False,
                )
            )
            continue

        _validate_return(token, anchor_at, expected_end, "token")
        _validate_return(btc, anchor_at, expected_end, "btc")
        if token.instrument_ref == btc.instrument_ref:
            raise CryptoOnchainContractError("token and BTC return instruments must differ")

        source_ids = tuple(dict.fromkeys(token.source_record_ids + btc.source_record_ids))
        results.append(
            HistoricalWindowResult(
                window=window,
                window_start=anchor_at,
                window_end=expected_end,
                token_return_decimal=float(token.return_decimal),
                btc_return_decimal=float(btc.return_decimal),
                btc_relative_return_decimal=float(token.return_decimal - btc.return_decimal),
                source_record_ids=source_ids,
                complete=True,
            )
        )

    ordered_phases = tuple(sorted(market_phases, key=lambda phase: phase.context_as_of))
    if any(phase.event_time < anchor_at for phase in ordered_phases):
        raise CryptoOnchainContractError("market phase cannot precede selected historical anchor")

    return HistoricalReplay(
        event=event,
        anchor_kind=anchor_kind,
        anchor_at=anchor_at,
        anchor_source_ref=anchor_source_ref,
        windows=tuple(results),
        market_phases=ordered_phases,
        causality=CausalityStatus.NOT_ESTABLISHED,
    )


def _validate_return(observation: CryptoReturnObservation, start: datetime, end: datetime, label: str) -> None:
    if not isinstance(observation, CryptoReturnObservation):
        raise CryptoOnchainContractError(f"{label} return must be CryptoReturnObservation")
    if observation.window_start != start or observation.window_end != end:
        raise CryptoOnchainContractError(f"{label} return does not match canonical historical replay window")


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise CryptoOnchainContractError(f"{field} must be normalized to UTC")


def _require_text(value: str | None, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CryptoOnchainContractError(f"{field} must be non-blank and trimmed")
