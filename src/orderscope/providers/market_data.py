from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Sequence

from orderscope.domain.market import BarCadence, NormalizedBar


class MarketCalendarDay:
    """Placeholder contract until calendar/session design is fixed in detail."""

    def __init__(
        self,
        trading_date: date,
        is_open: bool,
        open_at_utc: datetime | None,
        close_at_utc: datetime | None,
        is_shortened: bool = False,
    ) -> None:
        self.trading_date = trading_date
        self.is_open = is_open
        self.open_at_utc = open_at_utc
        self.close_at_utc = close_at_utc
        self.is_shortened = is_shortened


class MarketDataProvider(ABC):
    """Provider boundary defined by the v0.1 Code of Truth."""

    @abstractmethod
    def historical_bars(
        self,
        symbols: Sequence[str],
        cadence: BarCadence,
        start_utc: datetime,
        end_utc: datetime,
    ) -> Sequence[NormalizedBar]:
        raise NotImplementedError

    @abstractmethod
    def latest_bars(
        self,
        symbols: Sequence[str],
        cadence: BarCadence,
    ) -> Sequence[NormalizedBar]:
        raise NotImplementedError

    @abstractmethod
    def market_calendar(
        self,
        start_date: date,
        end_date: date,
    ) -> Sequence[MarketCalendarDay]:
        raise NotImplementedError
